import requests
import json

url = "http://localhost:8000/api/create-order"
data = {
    "email": "test@example.com",
    "shop_name": "Test Shop"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
