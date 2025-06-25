#!/usr/bin/env python3
"""
Debug webhook to see exactly what data is being received.
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/debug-webhook', methods=['POST'])
def debug_webhook():
    """Debug endpoint to see raw webhook data."""
    try:
        print(f"\n{'='*80}")
        print(f"WEBHOOK DEBUG - {datetime.now()}")
        print(f"{'='*80}")
        
        print("RAW REQUEST DATA:")
        print(f"Content-Type: {request.content_type}")
        print(f"Method: {request.method}")
        print(f"Headers: {dict(request.headers)}")
        
        # Get raw data
        raw_data = request.get_data(as_text=True)
        print(f"\nRAW BODY:")
        print(raw_data)
        
        # Try to parse as JSON
        try:
            json_data = request.json
            print(f"\nPARSED JSON:")
            print(json.dumps(json_data, indent=2))
            
            # Extract key fields
            print(f"\nKEY FIELDS:")
            print(f"Type: {json_data.get('type', 'NOT_FOUND')}")
            print(f"Prompt: {json_data.get('prompt', 'NOT_FOUND')}")
            
            if json_data.get('response'):
                print(f"Response agent_id: {json_data['response'].get('agent_id', 'NOT_FOUND')}")
            
            if json_data.get('request'):
                print(f"Request path: {json_data['request'].get('path', 'NOT_FOUND')}")
                
        except Exception as e:
            print(f"JSON parsing error: {e}")
        
        print(f"{'='*80}\n")
        
        return jsonify({"status": "debug_received", "timestamp": str(datetime.now())}), 200
        
    except Exception as e:
        print(f"Debug webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "debug_healthy"}), 200

if __name__ == "__main__":
    print("Starting debug webhook server on port 5006...")
    app.run(host="0.0.0.0", port=5006, debug=True)