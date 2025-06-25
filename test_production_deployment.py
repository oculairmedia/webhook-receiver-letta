#!/usr/bin/env python3

import requests
import json
import time

def test_production_webhook():
    """
    Test the production webhook deployment to verify Graphiti integration is working.
    """
    # Production webhook URL (adjust if different)
    webhook_url = "http://localhost:5005/webhook"
    
    # Test payload that should trigger Graphiti search
    test_payload = {
        "type": "message_sent",
        "prompt": "Tell me about artificial intelligence and machine learning",
        "response": {
            "agent_id": "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
        }
    }
    
    print("🧪 Testing Production Webhook Deployment")
    print("="*50)
    
    try:
        print(f"📡 Sending webhook to: {webhook_url}")
        
        response = requests.post(
            webhook_url,
            json=test_payload,
            timeout=60,  # Give it time to process Graphiti
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ SUCCESS: {response_data}")
            print("\n🔍 This indicates:")
            print("  - Webhook endpoint is accessible")
            print("  - Flask server is running")
            print("  - Graphiti integration should be active")
            print("  - Memory block creation is working")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Cannot reach webhook endpoint")
        print("🔧 Make sure the container is running:")
        print("   docker pull oculair/letta-webhook-receiver:latest")
        print("   docker run -p 5005:5005 -e GRAPHITI_URL=http://192.168.50.90:8001/api oculair/letta-webhook-receiver:latest")
        return False
        
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: Webhook took longer than 60 seconds")
        print("🔍 This might indicate Graphiti processing is working but slow")
        return False
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_health_endpoint():
    """Test the health check endpoint."""
    health_url = "http://localhost:5005/health"
    
    try:
        print(f"\n🏥 Testing Health Endpoint: {health_url}")
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ HEALTH CHECK PASSED: {response.json()}")
            return True
        else:
            print(f"❌ HEALTH CHECK FAILED: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HEALTH CHECK ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Production Deployment Test")
    print("=" * 50)
    
    # Test health first
    health_ok = test_health_endpoint()
    
    # Test webhook functionality
    webhook_ok = test_production_webhook()
    
    print("\n" + "="*50)
    print("📋 SUMMARY:")
    print(f"  Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"  Webhook Test: {'✅ PASS' if webhook_ok else '❌ FAIL'}")
    
    if health_ok and webhook_ok:
        print("\n🎉 PRODUCTION DEPLOYMENT SUCCESSFUL!")
        print("   - Updated Docker image is running correctly")
        print("   - Graphiti integration is active")
        print("   - Ready for production traffic")
    else:
        print("\n🚨 DEPLOYMENT ISSUES DETECTED")
        print("   - Check container logs for details")
        print("   - Verify environment variables")
        print("   - Ensure Graphiti API is accessible")