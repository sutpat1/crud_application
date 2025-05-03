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
    if request.method == 'GET':
        response = make_api_request('GET', f'/inventory')
        if response.status_code == 200:
            data = response.json()
            # Find the item with the matching product_id
            item = next((i for i in data.get('items', []) if i.get('product_id') == product_id), None)
            print("Item being sent to template:", item)
            if item:
                print("API response:", response.json())
                return render_template('edit.html', item=item)
            else:
                flash('Item not found', 'error')
                return redirect(url_for('index'))
        else:
            flash('Error retrieving item', 'error')
            return redirect(url_for('index'))
    elif request.method == 'POST':
        try:
            stock_quantity_str = request.form.get('stock_quantity', '').strip()
            
            try:
                new_quantity = (float(stock_quantity_str))
            except ValueError:
                flash('Invalid stock quantity', 'error')
                return render_template('edit.html', item=item)

            item_update = {
                'product_id': product_id,
                'name': request.form['name'],
                'category': request.form.get('category', ''),
                'price': float(request.form['price']),
                'new_quantity': new_quantity,
                'description': request.form.get('description', '')
            }
            
            response = make_api_request('PUT', f'/inventory/{product_id}', data=item_update)
            if response.status_code == 200:
                flash('Item updated successfully!', 'success')
                return redirect(url_for('index'))
            else:
                error_msg = "Unknown error"
                try:
                    response_data = response.json()
                    error_msg = response_data.get('error', 'Unknown error')
                except:
                    pass
                flash(f'Error updating item: {error_msg}', 'error')
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'error')

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