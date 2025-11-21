#!/usr/bin/env python3
"""
Entry point for the webhook server that handles imports correctly
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the app
from webhook_server.app import app
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Webhook Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5005, help="Port to listen on")
    args = parser.parse_args()
    
    print(f"Starting webhook server on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)