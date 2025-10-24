"""
Test login directly with requests
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

print("=" * 80)
print("  TESTING LOGIN ENDPOINT")
print("=" * 80)

# Test data
credentials = {
    "email": "buyer@test.com",
    "password": "testpass123"
}

print(f"\n1. Testing login with:")
print(f"   URL: {BASE_URL}/auth/login/")
print(f"   Email: {credentials['email']}")
print(f"   Password: {credentials['password']}")

try:
    response = requests.post(
        f"{BASE_URL}/auth/login/",
        json=credentials,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n2. Response:")
    print(f"   Status Code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    
    try:
        data = response.json()
        print(f"\n3. Response Body:")
        print(json.dumps(data, indent=2))
        
        if response.status_code == 200:
            print("\n✅ LOGIN SUCCESSFUL!")
            if 'access' in data:
                print(f"   Access Token: {data['access'][:50]}...")
        else:
            print(f"\n❌ LOGIN FAILED!")
            print(f"   Error: {data}")
    except:
        print(f"\n   Raw Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ CONNECTION ERROR!")
    print("   Make sure Django server is running:")
    print("   python manage.py runserver")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")

print("\n" + "=" * 80)
