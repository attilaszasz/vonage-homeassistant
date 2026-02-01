#!/usr/bin/env python3
"""
Test script to check the correct Vonage SDK usage patterns.
"""

def test_vonage_api():
    try:
        from vonage import Vonage, Auth
        
        # Test with dummy credentials
        auth = Auth(api_key='test_key', api_secret='test_secret')
        client = Vonage(auth=auth)
        
        print("✅ Vonage client created successfully")
        
        # Check account methods
        print(f"Account methods: {[m for m in dir(client.account) if not m.startswith('_')]}")
        
        # Check SMS methods  
        print(f"SMS methods: {[m for m in dir(client.sms) if not m.startswith('_')]}")
        
        # Check Voice methods
        print(f"Voice methods: {[m for m in dir(client.voice) if not m.startswith('_')]}")
        
        # Try to see the SMS send method signature
        import inspect
        try:
            sig = inspect.signature(client.sms.send)
            print(f"SMS send signature: {sig}")
        except Exception as e:
            print(f"Could not get SMS signature: {e}")
            
        # Try to see the voice create_call method signature  
        try:
            sig = inspect.signature(client.voice.create_call)
            print(f"Voice create_call signature: {sig}")
        except Exception as e:
            print(f"Could not get Voice signature: {e}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_vonage_api()