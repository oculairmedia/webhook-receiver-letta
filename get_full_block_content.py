#!/usr/bin/env python3
"""
Get the full content of the graphiti_context memory block without truncation.
"""

import requests
import json

# Configuration
BASE_URL = "https://letta2.oculair.ca/v1"
LETTA_PASSWORD = "lettaSecurePass123"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
    "Authorization": f"Bearer {LETTA_PASSWORD}"
}

def get_graphiti_block():
    """Get the graphiti_context block from global blocks."""
    try:
        url = f"{BASE_URL}/blocks"
        params = {"label": "graphiti_context", "templates_only": "false"}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        blocks = data if isinstance(data, list) else data.get("blocks", [])
        
        if blocks:
            return blocks[0]
        return None
    except Exception as e:
        print(f"Error fetching block: {e}")
        return None

def main():
    block = get_graphiti_block()
    if not block:
        print("No graphiti_context block found!")
        return
    
    content = block.get('value', '')
    print(f"Block ID: {block.get('id')}")
    print(f"Block Label: {block.get('label')}")
    print(f"Content Length: {len(content)} characters")
    print("\n" + "="*80)
    print("FULL CONTENT:")
    print("="*80)
    print(content)
    
    # Count timestamps to see how many context entries there are
    import re
    timestamps = re.findall(r'\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC\)', content)
    print(f"\n\nTotal context entries: {len(timestamps)}")
    print("Timestamps found:")
    for ts in timestamps:
        print(f"  - {ts}")

if __name__ == "__main__":
    main()