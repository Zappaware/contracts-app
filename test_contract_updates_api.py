#!/usr/bin/env python3
"""
Quick test script to verify contract updates API is working
"""
import httpx
import json

def test_api():
    try:
        print("Testing contract updates API endpoint...")
        with httpx.Client(timeout=10.0) as client:
            response = client.get("http://localhost:8000/api/v1/contract-updates/")
            print(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                updates = response.json()
                print(f"Found {len(updates)} contract updates")
                
                if updates:
                    print("\nFirst update sample:")
                    print(json.dumps(updates[0], indent=2, default=str))
                else:
                    print("\n⚠️  No contract updates returned from API (but they exist in DB)")
            else:
                print(f"❌ API returned error: {response.status_code}")
                print(response.text)
    except Exception as e:
        print(f"❌ Error calling API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()



