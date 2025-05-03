import boto3
import json
import logging
from decimal import Decimal
from botocore.exceptions import ClientError
from datetime import datetime
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
            query_params = event.get('queryStringParameters', {}) or {}
            
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
    product_id = params.get('product_id')
    stock_change = params.get('stock_change')
    new_quantity = params.get('new_quantity')

    # Prepare update expressions
    update_expression = []
    expression_values = {}
    expression_names = {}

    # Handle stock update
    if stock_change is not None:
        update_expression.append('stock_quantity = stock_quantity + :stock_change')
        expression_values[':stock_change'] = Decimal(str(stock_change))
    elif new_quantity is not None:
        update_expression.append(f'stock_quantity = :new_quantity')
        expression_values[':new_quantity'] = Decimal(str(new_quantity))

    # Handle other fields
    for field in ['name', 'category', 'price', 'description']:
        if field in params and params[field] not in [None, '']:
            if field == 'name':
                update_expression.append("#n = :name")
                expression_values[":name"] = params["name"]
                expression_names["#n"] = "name"
            elif field == 'price':
                update_expression.append("price = :price")
                expression_values[":price"] = Decimal(str(params["price"]))
            else:
                update_expression.append(f"{field} = :{field}")
                expression_values[f":{field}"] = params[field]

    if not update_expression:
        return create_response(400, {'error': 'No fields to update'})

    # Always update the updated_at timestamp
    update_expression.append('updated_at = :updated_at')
    expression_values[':updated_at'] = datetime.now().isoformat()

    try:
        update_kwargs = {
            "Key": {"product_id": product_id},
            "UpdateExpression": "SET " + ", ".join(update_expression),
            "ExpressionAttributeValues": expression_values,
        }
        if expression_names:
            update_kwargs["ExpressionAttributeNames"] = expression_names

        table.update_item(**update_kwargs)
        return create_response(200, {'message': 'Item updated successfully'})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return create_response(500, {'error': str(e)})

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

if __name__ == "__main__":
    print("\n=== Starting Inventory Lambda Function ===")
    
    # Create a mock event for listing all items
    event = {
        'httpMethod': 'GET',
        'path': '/inventory',
        'queryStringParameters': {},
        'body': json.dumps({
            'table_name': 'InventoryTable',
            'operation': 'list'
        })
    }
    
    print("\n1. Creating mock event for listing items...")
    print(f"   HTTP Method: {event['httpMethod']}")
    print(f"   Path: {event['path']}")
    print(f"   Body: {event['body']}")
    
    try:
        print("\n2. Invoking lambda_handler...")
        response = lambda_handler(event, None)
        
        print("\n3. Processing response:")
        print(f"   Status Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            items = body.get('items', [])
            
            if not items:
                print("\n   ÷ found in the inventory table.")
            else:
                print(f"\n   Found {len(items)} items:")
                print("-" * 50)
                
                for index, item in enumerate(items, 1):
                    print(f"\n   Item #{index}:")
                    print(f"   - Product ID: {item.get('product_id')}")
                    print(f"   - Name: {item.get('name')}")
                    print(f"   - Price: {item.get('price')}")
                    print(f"   - Stock Quantity: {item.get('stock_quantity')}")
                    
                    if 'category' in item:
                        print(f"   - Category: {item.get('category')}")
                    if 'description' in item:
                        print(f"   - Description: {item.get('description')}")
                    if 'last_updated' in item:
                        print(f"   - Last Updated: {item.get('last_updated')}")
                    
                    print("   " + "-" * 50)
        else:
            print(f"\n   Error: {response['body']}")
            
    except Exception as e:
        print("\n❌ Error occurred during execution:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error message: {str(e)}")
        print("\nStack trace:")
        import traceback
        traceback.print_exc()
    
    print("\n=== Inventory Lambda Function Execution Completed ===")