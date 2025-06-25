#!/usr/bin/env python3
"""
Graphiti Timeout Fix - Apply robust timeout handling to flask_webhook_receiver.py
"""

import re

def apply_timeout_fix():
    """Apply timeout fixes to the flask webhook receiver"""
    
    # Read the current file
    with open('flask_webhook_receiver.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the timeout=15 with a more robust approach
    # Find the fallback function's requests calls
    
    # Pattern 1: Replace simple timeout in nodes search
    pattern1 = r'nodes_response = requests\.post\(search_url_nodes, json=nodes_payload, timeout=15\)'
    replacement1 = '''nodes_response = requests.post(search_url_nodes, json=nodes_payload, timeout=30)'''
    
    # Pattern 2: Replace simple timeout in facts search  
    pattern2 = r'facts_response = requests\.post\(search_url_facts, json=facts_payload, timeout=15\)'
    replacement2 = '''facts_response = requests.post(search_url_facts, json=facts_payload, timeout=30)'''
    
    # Apply replacements
    content = re.sub(pattern1, replacement1, content)
    content = re.sub(pattern2, replacement2, content)
    
    # Add retry logic after the URL construction
    timeout_fix_code = '''            # Handle empty or None graphiti_url
            if not graphiti_url:
                print(f"[FALLBACK DEBUG] Warning: Empty graphiti_url provided, using default")
                graphiti_url = "http://192.168.50.90:8001/api"
            
            # Use the improved Graphiti API approach with proper parameters and retry logic
            search_url_nodes = f"{graphiti_url}/search/nodes"
            search_url_facts = f"{graphiti_url}/search/facts"
            
            # Configure session with retry logic
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)'''
    
    # Replace the current URL construction section
    pattern3 = r'            # Handle empty or None graphiti_url\s+if not graphiti_url:\s+print\(f"\[FALLBACK DEBUG\] Warning: Empty graphiti_url provided, using default"\)\s+graphiti_url = "http://192\.168\.50\.90:8001/api"\s+\s+# Use the improved Graphiti API approach with proper parameters\s+search_url_nodes = f"\{graphiti_url\}/search/nodes"\s+search_url_facts = f"\{graphiti_url\}/search/facts"'
    
    if re.search(pattern3, content, re.MULTILINE | re.DOTALL):
        content = re.sub(pattern3, timeout_fix_code, content, flags=re.MULTILINE | re.DOTALL)
    else:
        print("Warning: Could not find the exact pattern to replace. Manual intervention may be needed.")
    
    # Replace requests.post calls with session calls
    content = content.replace(
        'nodes_response = requests.post(search_url_nodes, json=nodes_payload, timeout=30)',
        '''nodes_response = session.post(search_url_nodes, json=nodes_payload, timeout=30)'''
    )
    
    content = content.replace(
        'facts_response = requests.post(search_url_facts, json=facts_payload, timeout=30)', 
        '''facts_response = session.post(search_url_facts, json=facts_payload, timeout=30)'''
    )
    
    # Add session cleanup at the end of the try block
    session_cleanup = '''            
            # Clean up session
            session.close()'''
    
    # Find the return statement in the fallback function and add cleanup before it
    pattern4 = r'(\s+)(return final_context, "Identity Unknown \(Fallback\)", group_ids)'
    replacement4 = r'\1session.close()\1\2'
    content = re.sub(pattern4, replacement4, content)
    
    # Write the updated content back
    with open('flask_webhook_receiver.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Applied timeout fixes to flask_webhook_receiver.py")
    print("Changes made:")
    print("- Increased timeout from 15s to 30s")
    print("- Added retry logic with exponential backoff")
    print("- Added proper session management")

if __name__ == "__main__":
    apply_timeout_fix()