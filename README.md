# Inventory Management System

A serverless, scalable inventory management application built with **AWS Lambda**, **DynamoDB**, **API Gateway**, and **Flask** for comprehensive product inventory tracking and management.

## 🚀 Features

- ☁️ **Serverless Architecture**: Built on AWS Lambda for scalability and cost efficiency.
- 🗄️ **NoSQL Database**: DynamoDB for flexible and fast data storage.
- 🔄 **RESTful API**: Comprehensive API endpoints for all inventory operations.
- 🖥️ **Web Interface**: User-friendly Flask-based UI for managing inventory.
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices.
- 🔧 **CLI Support**: Command-line interface for programmatic inventory control.
- 🔒 **Error Handling**: Robust validation and error handling throughout.

---

## 🛠️ Tech Stack

- **Backend**: AWS Lambda, Python 3.9
- **Database**: Amazon DynamoDB
- **API**: Amazon API Gateway
- **Frontend**: Flask, Bootstrap 5
- **Infrastructure**: AWS SAM (Serverless Application Model)

---

## 📁 Folder Structure

<pre lang="markdown">
.
├── .vscode/                  # VS Code configuration
├── inventory_ui/             # Flask web interface
│   ├── templates/            # HTML templates
│   │   ├── add.html          # Add item form
│   │   ├── base.html         # Base template
│   │   ├── edit.html         # Edit item form
│   │   └── index.html        # Item listing page
│   ├── app.py                # Flask application
│   └── requirements.txt      # Python dependencies for UI
├── tests/                    # Test cases
│   └── test_lambda_update_items.py
├── inventory_client.py       # CLI client for API interactions
├── inventory_lambda.py       # AWS Lambda function
├── requirements.txt          # Python dependencies for Lambda
├── template.yaml             # AWS SAM template
└── samconfig.toml            # SAM deployment configuration
</pre>

---

## 🚀 Getting Started

**Prerequisites**

* AWS Account with appropriate permissions
* AWS SAM CLI installed
* Python 3.9+
* Pip (Python package manager)

## Deployment

### Backend Setup

1. Install dependencies

   ```bash
   pip install -r requirements.txt

2. Deploy using AWS SAM
  ```bash
  sam build
  sam deploy
  ```

3. Note the API Gateway endpoint URL from the deployment outputs

### Web UI Setup

This document guides you through setting up and running the Flask-based web interface for the Inventory Management System.

---

## Prerequisites

- Python 3.9 or higher installed  
- Pip (Python package manager) installed  
- API Gateway endpoint URL deployed from the backend setup (AWS SAM deployment)

---

## Setup Instructions

### 1. Navigate to the Web UI Directory

```bash
cd inventory_ui
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Update the API_ENDPOINT in app.py with your deployed API Gateway URL

### 4. Run the Flask application

```bash
python app.py
```

### 5. Access the web UI at http://localhost:5000

---

## 📱 Features Breakdown

**RESTful API**

* Complete CRUD operations for inventory items
* JSON format for data exchange
* Proper HTTP status codes and error handling
* CORS support for cross-origin requests

**Web Interface**

* Responsive Bootstrap-based design
* Interactive tables for inventory display
* Forms for adding and editing items
* Confirmation dialogs for delete operations

**Serverless Backend**

* Event-driven Lambda functions
* DynamoDB for scalable NoSQL storage
* API Gateway for HTTP endpoint management
* CloudFormation for infrastructure as code

**Command-Line Interface**

* Python-based CLI for automation
* Support for all inventory operations
* JSON output formatting
* Parameter validation and helpful error messages

---

## 🔧 CLI Usage Examples

```bash
# List all items
python inventory_client.py --api-url <your-api-url> list

# Add an item
python inventory_client.py --api-url <your-api-url> add --product-id "apple" --name "Apple" --price 1.99 --stock-quantity 100 --category "Fruit"

# Get a specific item
python inventory_client.py --api-url <your-api-url> get --product-id "apple"

# Update stock quantity
python inventory_client.py --api-url <your-api-url> update-stock --product-id "apple" --stock-change 10

# Remove an item
python inventory_client.py --api-url <your-api-url> remove --product-id "apple"
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /inventory | List all inventory items |
| GET | /inventory/{product_id} | Get details of a specific item |
| POST | /inventory | Add a new inventory item |
| PUT | /inventory/{product_id} | Update an existing item |
| DELETE | /inventory/{product_id} | Remove an item from inventory |
| GET | /inventory/low-stock | List items with stock below threshold |

---

## 🔍 Customization

To adapt this application for your needs:

* Modify the DynamoDB schema in `template.yaml`
* Add additional fields to the inventory items
* Customize the Flask UI templates
* Extend the Lambda function with additional business logic
* Add authentication to protect API endpoints

---

## 🧪 Testing

Run tests using the unittest framework:

```bash
python -m tests.test_lambda_update_items
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 🤝 Acknowledgements

* AWS for the serverless infrastructure
* Flask team for the web framework
* Bootstrap for the responsive UI components



