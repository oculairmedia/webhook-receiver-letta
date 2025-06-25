#!/usr/bin/env python3
"""
Verify the actual content of a memory block to see if updates are present.
This will show the full content without any UI truncation.
"""

import requests
import json
import sys
import re
from datetime import datetime

# Configuration
BASE_URL = "https://letta2.oculair.ca/v1"
LETTA_PASSWORD = "lettaSecurePass123"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-BARE-PASSWORD": f"password {LETTA_PASSWORD}",
    "Authorization": f"Bearer {LETTA_PASSWORD}"
}
AGENT_ID = "agent-78bb8df1-6350-4c8b-80f5-59a5b99ba9b2"  # Your agent ID from the logs

def get_memory_blocks(agent_id):
    """Get all memory blocks for an agent using the correct Letta API structure."""
    try:
        # Try the agent's core memory blocks first
        url = f"{BASE_URL}/agents/{agent_id}/core-memory/blocks"
        headers = HEADERS.copy()
        headers["user_id"] = agent_id
        
        print(f"Trying agent blocks URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if isinstance(data, list):
            return data
        else:
            return data.get("blocks", [])
    except Exception as e:
        print(f"Error fetching agent blocks: {e}")
        
        # Fallback to global blocks
        try:
            url = f"{BASE_URL}/blocks"
            params = {"label": "graphiti_context", "templates_only": "false"}
            
            print(f"Trying global blocks URL: {url}")
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, list):
                return data
            else:
                return data.get("blocks", [])
        except Exception as e2:
            print(f"Error fetching global blocks: {e2}")
            return None

def get_memory_block_by_label(agent_id, label):
    """Get a specific memory block by label."""
    blocks = get_memory_blocks(agent_id)
    if not blocks:
        return None
    
    for block in blocks:
        if block.get('label') == label:
            return block
    return None

def format_block_content(content):
    """Format the block content for better readability."""
    # Split by timestamp patterns to show individual entries
    import re
    
    # Pattern to match timestamps like (2025-06-06 18:35:19 UTC)
    timestamp_pattern = r'\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC\)'
    
    # Split content by timestamps
    parts = re.split(f'({timestamp_pattern})', content)
    
    formatted = []
    for i in range(0, len(parts)-1, 2):
        if i+1 < len(parts):
            timestamp = parts[i+1]
            text = parts[i+2] if i+2 < len(parts) else ""
            formatted.append(f"\n{'='*80}\n{timestamp}\n{'='*80}\n{text.strip()}")
    
    return "\n".join(formatted)

def main():
    print(f"Fetching memory blocks for agent: {AGENT_ID}")
    print("-" * 80)
    
    # Get the graphiti_context block
    block = get_memory_block_by_label(AGENT_ID, "graphiti_context")
    
    if not block:
        print("No 'graphiti_context' block found!")
        return
    
    print(f"Block ID: {block.get('id')}")
    print(f"Block Label: {block.get('label')}")
    print(f"Last Updated: {block.get('updated_at', 'Unknown')}")
    print(f"\nTotal Content Length: {len(block.get('value', ''))} characters")
    print("\n" + "="*80)
    print("FULL BLOCK CONTENT:")
    print("="*80)
    
    content = block.get('value', '')
    
    # Try to format it nicely
    formatted_content = format_block_content(content)
    print(formatted_content)
    
    # Also save to file for easier viewing
    output_file = f"memory_block_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Memory Block Content Verification\n")
        f.write(f"Agent ID: {AGENT_ID}\n")
        f.write(f"Block Label: graphiti_context\n")
        f.write(f"Retrieved at: {datetime.now()}\n")
        f.write(f"Content Length: {len(content)} characters\n")
        f.write("="*80 + "\n\n")
        f.write(formatted_content)
    
    print(f"\n\nFull content also saved to: {output_file}")
    
    # Count the number of context entries
    entry_count = content.count(" UTC)")
    print(f"\nTotal context entries found: {entry_count}")
    
    # Show the most recent entries
    if entry_count > 0:
        print("\nMost recent 3 timestamps found:")
        timestamps = re.findall(r'\(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC\)', content)
        for ts in timestamps[-3:]:
            print(f"  - {ts}")

if __name__ == "__main__":
    main()