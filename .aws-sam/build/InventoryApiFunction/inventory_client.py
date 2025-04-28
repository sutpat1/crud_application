import requests 
import json
import argparse
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def make_request(method, url, payload=None):
    """Make HTTP request to API endpoint"""
    try:
        headers = {'Content-Type': 'application/json'}
        if payload:
            response = requests.request(method, url, json=payload, headers=headers)
        else:
            response = requests.request(method, url, headers=headers)
        
        print(f"Response status code: {response.status_code}")
        if response.text:
            try:
                result = response.json()
                print("\nResponse body:")
                print(json.dumps(result, indent=2, cls=DecimalEncoder))
            except json.JSONDecodeError:
                print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"Request failed: {str(e)}")
        import traceback
        traceback.print_exc()

def add_item(args):
    """Add a new item to inventory"""
    try:
        if args.item:
            item = json.loads(args.item)
        else:
            item = {
                "product_id": args.product_id,
                "name": args.name,
                "price": args.price,
                "stock_quantity": args.stock_quantity
            }
            if args.category:
                item["category"] = args.category
            if args.reorder_threshold:
                item["reorder_threshold"] = args.reorder_threshold
            if args.description:
                item["description"] = args.description
    except json.JSONDecodeError:
        print("Error: The item must be valid JSON")
        return
        
    make_request('POST', f"{args.api_url}/items", item)

def update_stock(args):
    """Update stock quantity of an item"""
    payload = {
        "stock_change": args.stock_change
    }
    make_request('PATCH', f"{args.api_url}/items/{args.product_id}/stock", payload)

def get_item(args):

    """Get a specific inventory item"""
    make_request('GET', f"{args.api_url}/items/{args.product_id}")

def list_items(args):
    """List inventory items, optionally filtered by category"""
    params = {}
    if args.category:
        params['category'] = args.category
    if args.max_items:
        params['max_items'] = args.max_items
    
    make_request('GET', f"{args.api_url}/items", params)

def remove_item(args):
    """Remove an item from inventory"""
    make_request('DELETE', f"{args.api_url}/items/{args.product_id}")


def main():
    parser = argparse.ArgumentParser(description='Inventory Management Client')
    parser.add_argument('--api-url', required=True, help='API Gateway URL')
    
    subparsers = parser.add_subparsers(dest='operation', help='Operation to perform')
    subparsers.required = True
    
    # Add Item parser
    add_parser = subparsers.add_parser('add', help='Add a new inventory item')
    add_parser.add_argument('--item', help='Full item JSON')
    add_parser.add_argument('--product-id', help='Product ID')
    add_parser.add_argument('--name', help='Product name')
    add_parser.add_argument('--price', type=float, help='Product price')
    add_parser.add_argument('--stock-quantity', type=int, help='Initial stock quantity')
    add_parser.add_argument('--category', help='Product category')
    add_parser.add_argument('--description', help='Product description')
    add_parser.add_argument('--reorder-threshold', type=int, help='Reorder threshold')
    add_parser.set_defaults(func=add_item)
    
    # Update Stock parser
    update_parser = subparsers.add_parser('update-stock', help='Update stock quantity')
    update_parser.add_argument('--product-id', required=True, help='Product ID')
    update_parser.add_argument('--stock-change', required=True, type=int, help='Stock change (positive for increase, negative for decrease)')
    update_parser.set_defaults(func=update_stock)
    
    # Get Item parser
    get_parser = subparsers.add_parser('get', help='Get inventory item details')
    get_parser.add_argument('--product-id', required=True, help='Product ID')
    get_parser.set_defaults(func=get_item)
    
    # List Items parser
    list_parser = subparsers.add_parser('list', help='List inventory items')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--max-items', type=int, help='Maximum number of items to return')
    list_parser.set_defaults(func=list_items)
    
    # Remove Item parser
    remove_parser = subparsers.add_parser('remove', help='Remove inventory item')
    remove_parser.add_argument('--product-id', required=True, help='Product ID')
    remove_parser.set_defaults(func=remove_item)
    

    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()