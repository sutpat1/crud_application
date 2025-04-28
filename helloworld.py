import requests



print("Hello World")

response = requests.get('https://api.github.com')

# Check the status code
print(f"Status code: {response.status_code}")

# Print the response content
print(response.text)

# Parse JSON response
json_response = response.json()
print(json_response)