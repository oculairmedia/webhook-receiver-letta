#!/usr/bin/env python3
"""
Examine the GDELT structure to make precise fixes
"""

def examine_structure():
    """Examine the structure around GDELT functions"""
    
    with open('flask_webhook_receiver.py', 'r') as f:
        lines = f.readlines()
    
    print("🔍 EXAMINING GDELT STRUCTURE")
    print("="*60)
    
    # Look around line 1128
    print("\n📍 AROUND LINE 1128:")
    print("-" * 40)
    start = max(0, 1128 - 15)
    end = min(len(lines), 1128 + 15)
    
    for i in range(start, end):
        line_num = i + 1
        line = lines[i].rstrip()
        prefix = ">>> " if line_num in [1128, 1129] else "    "
        print(f"{prefix}{line_num:4d}: {line}")
    
    # Look around line 1140
    print("\n📍 AROUND LINE 1140:")
    print("-" * 40)
    start = max(0, 1140 - 15)
    end = min(len(lines), 1140 + 15)
    
    for i in range(start, end):
        line_num = i + 1
        line = lines[i].rstrip()
        prefix = ">>> " if line_num in [1140, 1141] else "    "
        print(f"{prefix}{line_num:4d}: {line}")

if __name__ == "__main__":
    examine_structure()