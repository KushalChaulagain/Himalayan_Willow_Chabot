"""Test API call with requests library"""
import requests
import json

url = "http://localhost:8000/api/chat/message"
payload = {
    "message": "Hello, show me cricket bats",
    "session_id": None
}

print("Sending request to:", url)
print("Payload:", json.dumps(payload, indent=2))

try:
    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✓ SUCCESS!")
    else:
        print(f"\n✗ ERROR: HTTP {response.status_code}")
        
except Exception as e:
    print(f"\n✗ Exception: {type(e).__name__}: {str(e)}")
