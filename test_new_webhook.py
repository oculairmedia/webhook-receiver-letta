import requests
import json

def test_webhook():
    """Sends a test POST request to the new webhook server."""
    url = "http://localhost:8290/webhook"
    payload = {
        "type": "message_sent",
        "prompt": "This is a test prompt for the new webhook server.",
        "response": {
            "agent_id": "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
        }
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Sending POST request to {url} with payload: {json.dumps(payload)}")
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        print("\n--- Webhook Test Successful! ---")
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("Response content (not JSON):")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("\n--- Webhook Test Failed: Request timed out. ---")
    except requests.exceptions.RequestException as e:
        print(f"\n--- Webhook Test Failed: {e} ---")

if __name__ == "__main__":
    test_webhook()