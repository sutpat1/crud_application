from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from decimal import Decimal
import json
import os
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# API Gateway endpoint
API_ENDPOINT = 'https://cwr7lqwfg9.execute-api.us-east-1.amazonaws.com/v1/inventory'

def make_api_request(method, path, data=None):
    try:
        url = f"{API_ENDPOINT}{path}"
        headers = {'Content-Type': 'application/json'}
        
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
            
        return response.json()
    except Exception as e:
        raise Exception(f"Error making API request: {str(e)}")

@app.route('/')
def index():
    try:
        response = make_api_request('GET', '/inventory')
        if response.get('statusCode') == 200:
            items = response.get('body', [])
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
                'price': Decimal(str(request.form['price'])),
                'stock_quantity': int(request.form['stock_quantity']),
                'category': request.form.get('category', ''),
                'description': request.form.get('description', '')
            }
            
            response = make_api_request('POST', '/inventory', data=item)
            if response.get('statusCode') in [200, 201]:
                flash('Item added successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Error adding item: {response.get("body", {}).get("error", "Unknown error")}', 'error')
        except Exception as e:
            flash(f'Error adding item: {str(e)}', 'error')
    return render_template('add.html')

@app.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit_item(product_id):
    if request.method == 'POST':
        try:
            item = {
                'product_id': product_id,
                'name': request.form['name'],
                'price': Decimal(str(request.form['price'])),
                'stock_quantity': int(request.form['stock_quantity']),
                'category': request.form.get('category', ''),
                'description': request.form.get('description', '')
            }
            
            response = make_api_request('PUT', f'/inventory/{product_id}', data=item)
            if response.get('statusCode') == 200:
                flash('Item updated successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(f'Error updating item: {response.get("body", {}).get("error", "Unknown error")}', 'error')
        except Exception as e:
            flash(f'Error updating item: {str(e)}', 'error')
    else:
        try:
            response = make_api_request('GET', f'/inventory/{product_id}')
            if response.get('statusCode') == 200:
                item = response.get('body', {})
                return render_template('edit.html', item=item)
            else:
                flash(f'Error retrieving item: {response.get("body", {}).get("error", "Unknown error")}', 'error')
                return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error retrieving item: {str(e)}', 'error')
            return redirect(url_for('index'))

@app.route('/delete/<product_id>')
def delete_item(product_id):
    try:
        response = make_api_request('DELETE', f'/inventory/{product_id}')
        if response.get('statusCode') == 200:
            flash('Item deleted successfully!', 'success')
        else:
            flash(f'Error deleting item: {response.get("body", {}).get("error", "Unknown error")}', 'error')
    except Exception as e:
        flash(f'Error deleting item: {str(e)}', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 