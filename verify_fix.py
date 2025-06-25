#!/usr/bin/env python3
"""
Verify if the GDELT fix was applied correctly
"""

def verify_fix():
    """Check if the GDELT trigger functions were properly updated"""
    
    with open('flask_webhook_receiver.py', 'r') as f:
        lines = f.readlines()
    
    print("🔍 VERIFYING GDELT FIX")
    print("="*50)
    
    # Check around line 1128
    print("\n📍 CHECKING LINE 1128 AREA:")
    print("-" * 30)
    start = max(0, 1128 - 5)
    end = min(len(lines), 1128 + 15)
    
    for i in range(start, end):
        line_num = i + 1
        line = lines[i].rstrip()
        if 'def should_trigger_gdelt_search' in line:
            print(f">>> {line_num:4d}: {line}")
            # Check the next few lines to see if it's still dummy
            for j in range(i + 1, min(len(lines), i + 10)):
                next_line = lines[j].rstrip()
                print(f"    {j+1:4d}: {next_line}")
                if 'return False' in next_line:
                    print("❌ STILL DUMMY FUNCTION!")
                    break
                elif 'message_lower' in next_line:
                    print("✅ PROPER IMPLEMENTATION FOUND!")
                    break
        else:
            print(f"    {line_num:4d}: {line}")
    
    # Check around line 1204
    print("\n📍 CHECKING LINE 1204 AREA:")
    print("-" * 30)
    start = max(0, 1204 - 5)
    end = min(len(lines), 1204 + 15)
    
    for i in range(start, end):
        line_num = i + 1
        line = lines[i].rstrip()
        if 'def should_trigger_gdelt_search' in line:
            print(f">>> {line_num:4d}: {line}")
            # Check the next few lines
            for j in range(i + 1, min(len(lines), i + 10)):
                next_line = lines[j].rstrip()
                print(f"    {j+1:4d}: {next_line}")
                if 'return False' in next_line:
                    print("❌ STILL DUMMY FUNCTION!")
                    break
                elif 'message_lower' in next_line:
                    print("✅ PROPER IMPLEMENTATION FOUND!")
                    break
        else:
            print(f"    {line_num:4d}: {line}")

if __name__ == "__main__":
    verify_fix()