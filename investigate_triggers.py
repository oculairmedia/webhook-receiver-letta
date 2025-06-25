#!/usr/bin/env python3
"""
Script to investigate trigger logic for BigQuery and GDELT integrations
"""

def analyze_trigger_logic():
    """Analyze the trigger logic by extracting relevant sections"""
    
    print("🔍 INVESTIGATING TRIGGER LOGIC")
    print("="*60)
    
    # Read the flask_webhook_receiver.py file
    with open('flask_webhook_receiver.py', 'r') as f:
        lines = f.readlines()
    
    # BigQuery trigger logic (around line 1563)
    print("\n📊 BIGQUERY TRIGGER LOGIC:")
    print("-" * 40)
    bigquery_start = max(0, 1563 - 20)  # 20 lines before
    bigquery_end = min(len(lines), 1563 + 20)  # 20 lines after
    
    for i in range(bigquery_start, bigquery_end):
        line_num = i + 1
        line = lines[i].rstrip()
        prefix = ">>> " if line_num == 1563 else "    "
        print(f"{prefix}{line_num:4d}: {line}")
    
    # GDELT trigger logic (around line 1631)
    print("\n📰 GDELT TRIGGER LOGIC:")
    print("-" * 40)
    gdelt_start = max(0, 1631 - 20)  # 20 lines before
    gdelt_end = min(len(lines), 1631 + 20)  # 20 lines after
    
    for i in range(gdelt_start, gdelt_end):
        line_num = i + 1
        line = lines[i].rstrip()
        prefix = ">>> " if line_num == 1631 else "    "
        print(f"{prefix}{line_num:4d}: {line}")
    
    print("\n🎯 ANALYSIS:")
    print("-" * 40)
    print("Looking for conditional logic that determines when integrations are triggered...")
    
    # Look for 'if' statements around these areas
    print("\n🔍 CONDITIONAL STATEMENTS NEAR TRIGGERS:")
    
    # Search for if statements in the BigQuery section
    bigquery_section = lines[max(0, 1563-30):min(len(lines), 1563+10)]
    gdelt_section = lines[max(0, 1631-30):min(len(lines), 1631+10)]
    
    print("\nBigQuery section conditionals:")
    for i, line in enumerate(bigquery_section):
        if 'if ' in line.strip() or 'else' in line.strip():
            actual_line_num = max(0, 1563-30) + i + 1
            print(f"  Line {actual_line_num}: {line.strip()}")
    
    print("\nGDELT section conditionals:")
    for i, line in enumerate(gdelt_section):
        if 'if ' in line.strip() or 'else' in line.strip():
            actual_line_num = max(0, 1631-30) + i + 1
            print(f"  Line {actual_line_num}: {line.strip()}")

if __name__ == "__main__":
    analyze_trigger_logic()