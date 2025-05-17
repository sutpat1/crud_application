markdown# Inventory Management System

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

# Inventory Management System - Web UI Setup

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

