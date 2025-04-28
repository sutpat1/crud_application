import boto3
import json
import logging
from decimal import Decimal
from botocore.exceptions import ClientError
from datetime import datetime
from dynamo_crud import DynamoCRUD
from boto3.dynamodb.conditions import Key, Attr

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert Decimal to float for JSON serialization
        elif isinstance(obj, datetime):
            return obj.isoformat()  # Convert datetime to ISO format string
        return super(DecimalEncoder, self).default(obj)

def create_response(status_code, body):
    """Create a standardized response object"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # For CORS support
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def lambda_handler(event, context):
    """
    Main Lambda handler for inventory operations using HTTP methods
    
    HTTP Method mapping:
    - GET + no product_id: list_items (list all items)
    - GET + product_id: get_item (get a specific item)
    - POST: add_item (create a new item)
    - PUT: update_stock (update an existing item's stock)
    - DELETE: remove_item (delete an item)
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Determine if request is coming from API Gateway or direct invocation
        if 'httpMethod' in event:
            # API Gateway request
            http_method = event['httpMethod']
            logger.info(f"HTTP Method: {http_method}")
            
            # Parse path parameters
            path_parameters = event.get('pathParameters', {}) or {}
            if path_parameters:
                product_id = path_parameters.get('product_id')
                path = path_parameters.get('proxy', '')
            else:
                # Check if product_id or path is in the request URI
                resource_path = event.get('path', '')
                parts = resource_path.strip('/').split('/')
                if len(parts) > 1:
                    product_id = parts[-1]
                    path = ''
                else:
                    product_id = None
                    path = ''
            
            # Parse query string parameters
            body = event.get('queryStringParameters', {}) or {}
            
            # Parse body if present
            if 'body' in event and event['body']:
                if isinstance(event['body'], str):
                    body = json.loads(event['body'])
                else:
                    body = event['body']
            else:
                body = {}
                
            # Set table name from environment variable or body
            table_name = body.get('table_name', None)
            if not table_name:
                # Try to get from environment variable
                import os
                table_name = os.environ.get('INVENTORY_TABLE')
                
            if not table_name:
                return create_response(400, {'error': 'Missing table_name parameter'})
                
            # Combine all parameters
            params = {
                'table_name': table_name,
                **query_params,
                **body
            }
            
            if product_id:
                params['product_id'] = product_id
        else:
            # Direct Lambda invocation - use explicit operation field
            http_method = event.get('http_method', 'GET')
            product_id = event.get('product_id')
            path = event.get('path', '')
            params = event
            table_name = params.get('table_name')
            
            if not table_name:
                return create_response(400, {'error': 'Missing table_name parameter'})
        
        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        crud = DynamoCRUD("InventoryTable")
        # Route request based on HTTP method and path
        if http_method == 'GET':
            if product_id:
                return get_inventory_item(table, params)
            else:
                return list_inventory_items(table, params)
        elif http_method == 'POST':
            item = json.loads(event['body'])
            return add_inventory_item(table, item)
        elif http_method == 'PUT':
            return update_stock_quantity(table, params)
        elif http_method == 'DELETE':
            return remove_inventory_item(table, params)
        elif http_method == 'OPTIONS':
            # Handle CORS preflight requests
            return create_response(200, {'message': 'CORS preflight request handled successfully'})
        else:
            return create_response(405, {'error': 'Method not allowed'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return create_response(500, {'error': str(e)})

def add_inventory_item(table, item):
    """Add a new item to the inventory"""
    
    
    # If no explicit item object is provided, build from parameters
    if not item:
        item = {}
        # Required fields
        # for field in ['product_id', 'name', 'price', 'stock_quantity']:
        #     if field in params:
        #         item[field] = params[field]
        
        # # Optional fields
        # for field in ['category', 'description', 'reorder_threshold']:
        #     if field in params:
        #         item[field] = params[field]
    
    if not item:
        return create_response(400, {'error': 'Missing item data for adding inventory item'})
    
    # Validate required fields
    required_fields = ['product_id', 'name', 'price', 'stock_quantity']
    missing_fields = [field for field in required_fields if field not in item]
    
    if missing_fields:
        return create_response(400, {'error': f'Missing required fields: {", ".join(missing_fields)}'})
    
    # Convert numeric values to Decimal for DynamoDB
    for key, value in item.items():
        if isinstance(value, (int, float)):
            item[key] = Decimal(str(value))
    
    # Add timestamps
    current_time = datetime.now().isoformat()
    item['created_at'] = current_time
    item['updated_at'] = current_time
    
    try:
        # Check if item already exists
        response = table.get_item(Key={'product_id': item['product_id']})
        if 'Item' in response:
            return create_response(409, {'error': f'Item with product_id {item["product_id"]} already exists'})
        
        # Add the item
        table.put_item(Item=item)
        return create_response(201, {'message': 'Inventory item added successfully', 'item': item})
    except ClientError as e:
        logger.error(f"Error adding inventory item: {e.response['Error']['Message']}")
        return create_response(500, {'error': e.response['Error']['Message']})

def update_stock_quantity(table, params):
    """Update the stock quantity of an inventory item"""
    product_id = params.get('product_id')
    stock_change = params.get('stock_change')
    
    if not product_id:
        return create_response(400, {'error': 'Missing product_id for stock update'})
    
    if stock_change is None:
        # If no stock_change is provided, check if there's a new_quantity
        new_quantity = params.get('new_quantity')
        if new_quantity is None:
            return create_response(400, {'error': 'Missing stock_change or new_quantity for stock update'})
        
        # If using new_quantity, we'll calculate the stock_change below
        using_new_quantity = True
    else:
        using_new_quantity = False
    
    # Convert numeric values to Decimal
    if not using_new_quantity and isinstance(stock_change, (int, float)):
        stock_change = Decimal(str(stock_change))
    if using_new_quantity and isinstance(new_quantity, (int, float)):
        new_quantity = Decimal(str(new_quantity))
    
    try:
        # Check if item exists
        response = table.get_item(Key={'product_id': product_id})
        if 'Item' not in response:
            return create_response(404, {'error': f'Item with product_id {product_id} not found'})
        
        item = response['Item']
        current_stock = Decimal(str(item.get('stock_quantity', 0)))
        
        if using_new_quantity:
            # Calculate the stock change based on new quantity
            stock_change = new_quantity - current_stock
        
        new_stock = current_stock + stock_change
        
        # Prevent negative stock
        if new_stock < 0:
            return create_response(400, {'error': f'Cannot reduce stock below zero. Current stock: {current_stock}, Requested change: {stock_change}'})
        
        # Update the stock quantity
        update_response = table.update_item(
            Key={'product_id': product_id},
            UpdateExpression="set stock_quantity = :q, updated_at = :t",
            ExpressionAttributeValues={
                ':q': new_stock,
                ':t': datetime.now().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        updated_item = update_response.get('Attributes', {})
        
        # Check if stock is below threshold after update
        threshold = item.get('reorder_threshold', 0)
        warning = None
        if threshold and new_stock <= Decimal(str(threshold)):
            warning = f"WARNING: Stock level ({new_stock}) is at or below reorder threshold ({threshold})"
        
        result = {
            'message': 'Stock quantity updated successfully',
            'product_id': product_id,
            'previous_stock': float(current_stock),
            'stock_change': float(stock_change),
            'new_stock': float(new_stock),
            'updated_item': updated_item
        }
        
        if warning:
            result['warning'] = warning
            
        return create_response(200, result)
    except ClientError as e:
        logger.error(f"Error updating stock quantity: {e.response['Error']['Message']}")
        return create_response(500, {'error': e.response['Error']['Message']})

def get_inventory_item(table, params):
    """Get details of an inventory item"""
    product_id = params.get('product_id')
    
    if not product_id:
        return create_response(400, {'error': 'Missing product_id for getting inventory item'})
    
    try:
        response = table.get_item(Key={'product_id': product_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': f'Item with product_id {product_id} not found'})
            
        return create_response(200, {'item': response['Item']})
    except ClientError as e:
        logger.error(f"Error getting inventory item: {e.response['Error']['Message']}")
        return create_response(500, {'error': e.response['Error']['Message']})

def list_inventory_items(table, params):
    """List all inventory items, optionally filtered by category"""
    try:
        # Extract optional parameters
        category = params.get('category')
        max_items = params.get('max_items')
        
        scan_kwargs = {}
        
        # Add filter for category if provided
        if category:
            scan_kwargs['FilterExpression'] = 'category = :cat'
            scan_kwargs['ExpressionAttributeValues'] = {':cat': category}
            
        if max_items:
            try:
                scan_kwargs['Limit'] = int(max_items)
            except (ValueError, TypeError):
                # If max_items can't be converted to int, ignore it
                pass
            
        response = table.scan(**scan_kwargs)
        items = response.get('Items', [])
        
        # Handle pagination for large tables
        last_evaluated_key = response.get('LastEvaluatedKey')
        
        result = {
            'items': items,
            'count': len(items),
            'scanned_count': response.get('ScannedCount', 0)
        }
        
        if last_evaluated_key:
            result['last_evaluated_key'] = last_evaluated_key
            result['has_more'] = True
            
        return create_response(200, result)
    except ClientError as e:
        logger.error(f"Error listing inventory items: {e.response['Error']['Message']}")
        return create_response(500, {'error': e.response['Error']['Message']})

def remove_inventory_item(table, params):
    """Remove an item from inventory"""
    product_id = params.get('product_id')
    
    if not product_id:
        return create_response(400, {'error': 'Missing product_id for removing inventory item'})
    
    try:
        # Check if item exists first
        response = table.get_item(Key={'product_id': product_id})
        if 'Item' not in response:
            return create_response(404, {'error': f'Item with product_id {product_id} not found'})
            
        # Delete the item
        delete_response = table.delete_item(
            Key={'product_id': product_id},
            ReturnValues='ALL_OLD'
        )
        
        deleted_item = delete_response.get('Attributes')
        
        return create_response(200, {
            'message': 'Inventory item removed successfully',
            'deleted_item': deleted_item
        })
    except ClientError as e:
        logger.error(f"Error removing inventory item: {e.response['Error']['Message']}")
        return create_response(500, {'error': e.response['Error']['Message']})