#!/usr/bin/env python3
"""
Check the real GDELT integration file
"""

def check_real_gdelt():
    """Check the actual GDELT integration trigger function"""
    
    print("🔍 CHECKING REAL GDELT INTEGRATION")
    print("="*50)
    
    try:
        with open('demo_gdelt_webhook_integration.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Look around line 82
        print("\n📍 AROUND LINE 82 (should_trigger_gdelt_search):")
        print("-" * 40)
        start = max(0, 82 - 5)
        end = min(len(lines), 82 + 15)
        
        for i in range(start, end):
            line_num = i + 1
            line = lines[i].rstrip()
            prefix = ">>> " if line_num == 82 else "    "
            print(f"{prefix}{line_num:4d}: {line}")
            
    except FileNotFoundError:
        print("❌ demo_gdelt_webhook_integration.py not found")
    except UnicodeDecodeError:
        print("❌ Unicode decode error - trying with different encoding")
        try:
            with open('demo_gdelt_webhook_integration.py', 'r', encoding='latin1') as f:
                lines = f.readlines()
            
            # Look around line 82
            print("\n📍 AROUND LINE 82 (should_trigger_gdelt_search):")
            print("-" * 40)
            start = max(0, 82 - 5)
            end = min(len(lines), 82 + 15)
            
            for i in range(start, end):
                line_num = i + 1
                line = lines[i].rstrip()
                prefix = ">>> " if line_num == 82 else "    "
                print(f"{prefix}{line_num:4d}: {line}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    check_real_gdelt()