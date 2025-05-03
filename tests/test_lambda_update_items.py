import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import patch
from inventory_lambda import lambda_handler

class TestLambdaListItems(unittest.TestCase):
    def test_update_inventory_item(self):
        event = {
            "httpMethod": "PUT",
            "path": f"/inventory/apple",
            "queryStringParameters": None,
            "body": '{"product_id": "apple", "name": "Grannysmith Apple", "price": 3.0, "new_quantity": 15, "category": "Fruit"}',
            "headers": {"Content-Type": "application/json"},
            "pathParameters": None
        }

        os.environ['INVENTORY_TABLE'] = 'InventoryTable'

        response = lambda_handler(event, None)
        assert response['statusCode'] == 200
        assert 'updated' in response['body'] or 'success' in response['body'] or 'message' in response['body']

if __name__ == '__main__':
    unittest.main() 