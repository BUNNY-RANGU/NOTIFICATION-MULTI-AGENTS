import requests
import json

url = "http://localhost:8000/api/register-shop"
data = {
    "shop_name": "Test Shop",
    "owner_name": "Test Owner",
    "owner_email": "test@example.com",
    "owner_phone": "1234567890",
    "sheet_name": "Sheet1"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
