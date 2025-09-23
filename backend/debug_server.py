# Save this as debug_server.py

import requests
import json

def debug_server():
    base_url = "http://127.0.0.1:5000"
    
    print("="*60)
    print("DEBUGGING YOUR CURRENT SERVER")
    print("="*60)
    
    # Test different endpoints to see what's available
    endpoints_to_test = [
        "/",
        "/health",
        "/symbols", 
        "/stock/graph?symbols=AAPL&graph_type=daily_returns",
        "/api/stocks/AAPL",
        "/test"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting: {base_url}{endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    data = response.json()
                    print(f"JSON Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    # If not JSON, show content type and first few chars
                    print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                    if 'image' in response.headers.get('content-type', ''):
                        print(f"✅ Image response ({len(response.content)} bytes)")
                    else:
                        print(f"Text Response: {response.text[:100]}...")
            elif response.status_code == 404:
                print("❌ Endpoint not found")
            else:
                print(f"❌ Error: {response.text[:100]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection refused - server not running")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    print("="*60)
    
    # Test basic connection
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 404:
            print("✅ Server is running but missing routes")
            print("📝 Your server needs these routes:")
            print("   - /health (for status check)")
            print("   - /stock/graph (for generating graphs)")
            print("   - /symbols (for available symbols)")
    except:
        print("❌ Server is not running")
        print("📝 Start your server with: python app.py")

if __name__ == "__main__":
    debug_server()