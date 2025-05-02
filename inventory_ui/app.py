from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from decimal import Decimal
import json
import os
import requests
import decimal

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# API Gateway endpoint
API_ENDPOINT = 'https://cwr7lqwfg9.execute-api.us-east-1.amazonaws.com/Stage'

def make_api_request(method, path, data=None):
    try:
        url = f"{API_ENDPOINT}{path}"
        headers = {'Content-Type': 'application/json'}
        
        # Debug print request details
        print(f"\nMaking {method} request to: {url}")
        if data:
            print(f"Request data: {json.dumps(data, indent=2)}")
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise Exception(f"Unsupported HTTP method: {method}")
        
        # Debug print response details
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        try:
            response_data = response.json()
            print(f"Response body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Raw response body: {response.text}")
        
        return response
    except Exception as e:
        print(f"Error in make_api_request: {str(e)}")
        raise

@app.route('/')
def index():
    try:
        response = make_api_request('GET', '/inventory')
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            json = response.json()
            items = json['items']
            
            # Convert price to proper format if it exists
            for item in items:
                if 'price' in item:
                    try:
                        # Try to convert price to Decimal
                        if isinstance(item['price'], str):
                            item['price'] = float(Decimal(item['price']))
                        elif isinstance(item['price'], (int, float)):
                            item['price'] = float(item['price'])
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        # If conversion fails, set a default or keep as is
                        print(f"Warning: Invalid price format for item {item.get('product_id', 'unknown')}")
                        
            return render_template('index.html', items=items)
        else:
            print(response)
            flash(f'Error retrieving items: {response.get("body", {}).get("error", "Unknown error")}', 'error')
            return render_template('index.html', items=[])
    except Exception as e:
        flash(f'Error retrieving items: {str(e)}', 'error')
        return render_template('index.html', items=[])

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        try:
            item = {
                'product_id': request.form['product_id'],
                'name': request.form['name'],
                'price': float(request.form['price']),
                'stock_quantity': int(request.form['stock_quantity']),
                'category': request.form.get('category', ''),
                'description': request.form.get('description', '')
            }
            
            response = make_api_request('POST', '/inventory', data=item)
            if response.status_code in [200, 201]:
                flash('Item added successfully!', 'success')
                return redirect(url_for('index'))
            else:
                error_msg = "Unknown error"
                try:
                    response_data = response.json()
                    error_msg = response_data.get('error', 'Unknown error')
                except:
                    pass
                flash(f'Error adding item: {error_msg}', 'error')
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
    return render_template('add.html')

@app.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit_item(product_id):
    if request.method == 'POST':
        try:
            # First, get the current item to calculate stock change
            current_response = make_api_request('GET', '/inventory')
            current_data = current_response.json()
            current_item = next((item for item in current_data['items'] 
                               if item.get('product_id') == product_id), None)
            
            if not current_item:
                flash('Item not found', 'error')
                return redirect(url_for('index'))

            # Calculate stock change
            new_stock = int(request.form['stock_quantity'])
            current_stock = int(current_item.get('stock_quantity', 0))
            stock_change = new_stock - current_stock

            # Prepare the update data
            item_update = {
                'table_name': 'InventoryTable',  # Add this if your API requires it
                'product_id': product_id,
                'name': request.form['name'],
                'price': str(float(request.form['price'])),  # Convert to string
                'stock_change': stock_change,  # Add the stock change
                'category': request.form.get('category', ''),
                'description': request.form.get('description', '')
            }
            
            print("Updating item with data:", item_update)
            
            # Make the update request
            response = make_api_request('PUT', '/inventory', data=item_update)
            print("Update response status:", response.status_code)
            print("Update response:", response.text)
            
            if response.status_code in [200, 201]:
                flash('Item updated successfully!', 'success')
                return redirect(url_for('index'))
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', 'Unknown error')
                except:
                    error_msg = f"Server returned status code {response.status_code}"
                flash(f'Error updating item: {error_msg}', 'error')
                # Return to form with current values
                return render_template('edit.html', item={
                    'product_id': product_id,
                    'name': request.form['name'],
                    'price': request.form['price'],
                    'stock_quantity': request.form['stock_quantity'],
                    'category': request.form.get('category', ''),
                    'description': request.form.get('description', '')
                })
                
        except Exception as e:
            print("Exception occurred:", str(e))
            flash(f'Error updating item: {str(e)}', 'error')
            # Return to form with submitted values
            return render_template('edit.html', item={
                'product_id': product_id,
                'name': request.form.get('name', ''),
                'price': request.form.get('price', 0),
                'stock_quantity': request.form.get('stock_quantity', 0),
                'category': request.form.get('category', ''),
                'description': request.form.get('description', '')
            })
    else:  # GET request
        try:
            response = make_api_request('GET', '/inventory')
            print("GET response:", response.status_code)
            
            if response.status_code == 200:
                data = response.json()
                # Find the specific item
                item = next((item for item in data['items'] 
                           if item.get('product_id') == product_id), None)
                
                if item:
                    # Ensure all fields are present with proper types
                    item_data = {
                        'product_id': item.get('product_id', product_id),
                        'name': item.get('name', ''),
                        'price': item.get('price', 0),
                        'stock_quantity': item.get('stock_quantity', 0),
                        'category': item.get('category', ''),
                        'description': item.get('description', '')
                    }
                    return render_template('edit.html', item=item_data)
                else:
                    flash('Item not found', 'error')
                    return redirect(url_for('index'))
            else:
                flash('Error retrieving item details', 'error')
                return redirect(url_for('index'))
        except Exception as e:
            print("Exception in GET:", str(e))
            flash(f'Error retrieving item: {str(e)}', 'error')
            return redirect(url_for('index'))

@app.route('/delete/<product_id>')
def delete_item(product_id):
    try:
        response = make_api_request('DELETE', f'/inventory/{product_id}')
        if response.status_code == 200:
            flash('Item deleted successfully!', 'success')
        else:
            error_msg = "Unknown error"
            try:
                response_data = response.json()
                error_msg = response_data.get('error', 'Unknown error')
            except:
                pass
            flash(f'Error deleting item: {error_msg}', 'error')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 