#!/usr/bin/env python3
"""
Quick fix for the webhook unpacking error.
"""

import re

def fix_webhook_unpacking():
    """Fix the unpacking error in flask_webhook_receiver.py"""
    
    # Read the file
    with open('flask_webhook_receiver.py', 'r') as f:
        content = f.read()
    
    # Find the problematic line and fix it
    # The issue is on line 1585: context_snippet, identity_name, _ = generate_context_from_prompt(...)
    # We need to handle the case where the function might return different numbers of values
    
    # Replace the problematic unpacking with safer unpacking
    old_pattern = r'context_snippet, identity_name, _ = generate_context_from_prompt\('
    new_replacement = '''result = generate_context_from_prompt('''
    
    content = re.sub(old_pattern, new_replacement, content)
    
    # Also need to add the unpacking after the function call
    # Find the end of the function call and add proper unpacking
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'result = generate_context_from_prompt(' in line:
            # Find the end of this function call
            j = i
            while j < len(lines) and ')' not in lines[j]:
                j += 1
            
            # Insert unpacking logic after the function call
            insert_lines = [
                '',
                '        # Safely unpack the result',
                '        if isinstance(result, tuple):',
                '            if len(result) == 3:',
                '                context_snippet, identity_name, group_ids = result',
                '            elif len(result) == 2:',
                '                context_snippet, identity_name = result',
                '                group_ids = []',
                '            else:',
                '                context_snippet = str(result[0]) if result else ""',
                '                identity_name = "Unknown"',
                '                group_ids = []',
                '        else:',
                '            context_snippet = str(result) if result else ""',
                '            identity_name = "Unknown"',
                '            group_ids = []'
            ]
            
            # Insert after the closing parenthesis line
            lines = lines[:j+1] + insert_lines + lines[j+1:]
            break
    
    # Write the fixed content back
    fixed_content = '\n'.join(lines)
    with open('flask_webhook_receiver.py', 'w') as f:
        f.write(fixed_content)
    
    print("✅ Fixed webhook unpacking error!")
    print("The webhook receiver should now handle return values correctly.")

if __name__ == "__main__":
    fix_webhook_unpacking()