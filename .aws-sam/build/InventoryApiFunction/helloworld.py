import requests



print("Hello World")

response = requests.get('https://cwr7lqwfg9.execute-api.us-east-1.amazonaws.com/v1/inventory')


# Check the status code
print(f"Status code: {response.status_code}")

# Print the response content
print(response.text)

# Parse JSON response
json_response = response.json()
print(json_response)