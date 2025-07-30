#!/usr/bin/env python3
"""
Quick performance test for the GroceryGhost API
"""
import time
import requests
import sys
from datetime import datetime

API_BASE = "http://localhost:8000/api"

def test_endpoint(name, url):
    """Test an API endpoint and measure response time"""
    print(f"\n🔍 Testing {name}...")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: {response_time:.2f}s - Status: {response.status_code}")
            
            if 'sessions' in data:
                print(f"   📊 Found {len(data['sessions'])} sessions")
                for session in data['sessions'][:3]:  # Show first 3
                    print(f"   - {session['name']}: {session['status']} ({session['product_count']} products)")
            
            elif 'products' in data:
                print(f"   📦 Found {len(data['products'])} products")
                print(f"   🎯 Total products: {data.get('total_products', 'unknown')}")
                
        else:
            print(f"❌ {name}: {response_time:.2f}s - Status: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Request failed - {str(e)}")
    except Exception as e:
        print(f"❌ {name}: Unexpected error - {str(e)}")

def main():
    print("🚀 GroceryGhost API Performance Test")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing API at: {API_BASE}")
    
    # Test sessions endpoint
    test_endpoint("Sessions List", f"{API_BASE}/sessions")
    
    # Get first session ID for detail test
    try:
        sessions_response = requests.get(f"{API_BASE}/sessions", timeout=10)
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            if sessions_data.get('sessions'):
                first_session_id = sessions_data['sessions'][0]['id']
                test_endpoint("Session Detail", f"{API_BASE}/session/{first_session_id}")
                
                # Test paginated products endpoint
                test_endpoint("Paginated Products", f"{API_BASE}/session/{first_session_id}/products?limit=50")
            else:
                print("\n⚠️  No sessions found to test session details")
        else:
            print(f"\n⚠️  Could not fetch sessions: {sessions_response.status_code}")
    except Exception as e:
        print(f"\n⚠️  Error getting session for detail test: {e}")
    
    print(f"\n✨ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
