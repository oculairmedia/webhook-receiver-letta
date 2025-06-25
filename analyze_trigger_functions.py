#!/usr/bin/env python3
"""
Script to analyze the trigger functions for BigQuery and GDELT integrations
"""

def analyze_trigger_functions():
    """Analyze the actual trigger function implementations"""
    
    print("🔍 ANALYZING TRIGGER FUNCTIONS")
    print("="*60)
    
    # Read the flask_webhook_receiver.py file
    with open('flask_webhook_receiver.py', 'r') as f:
        lines = f.readlines()
    
    # Find and display should_invoke_bigquery function around line 1167
    print("\n📊 BIGQUERY TRIGGER FUNCTION (around line 1167):")
    print("-" * 50)
    bigquery_start = max(0, 1167 - 10)
    bigquery_end = min(len(lines), 1167 + 30)  # More lines to see the full function
    
    for i in range(bigquery_start, bigquery_end):
        line_num = i + 1
        line = lines[i].rstrip()
        print(f"    {line_num:4d}: {line}")
    
    # Find and display the actual trigger check around line 1521
    print("\n📊 BIGQUERY TRIGGER CHECK (around line 1521):")
    print("-" * 50)
    trigger_start = max(0, 1521 - 10)
    trigger_end = min(len(lines), 1521 + 20)
    
    for i in range(trigger_start, trigger_end):
        line_num = i + 1
        line = lines[i].rstrip()
        prefix = ">>> " if line_num == 1521 else "    "
        print(f"{prefix}{line_num:4d}: {line}")
    
    # Find GDELT trigger function
    print("\n📰 GDELT TRIGGER CHECK (around line 1572):")
    print("-" * 50)
    gdelt_start = max(0, 1572 - 5)
    gdelt_end = min(len(lines), 1572 + 15)
    
    for i in range(gdelt_start, gdelt_end):
        line_num = i + 1
        line = lines[i].rstrip()
        prefix = ">>> " if line_num == 1572 else "    "
        print(f"{prefix}{line_num:4d}: {line}")
    
    # Search for should_trigger_gdelt_search function
    print("\n📰 SEARCHING FOR GDELT TRIGGER FUNCTION:")
    print("-" * 50)
    for i, line in enumerate(lines):
        if 'should_trigger_gdelt_search' in line and ('def ' in line or 'function' in line):
            print(f"Found GDELT trigger function at line {i+1}: {line.strip()}")
            # Show the function
            func_start = i
            func_end = min(len(lines), i + 50)
            for j in range(func_start, func_end):
                if j > func_start and (lines[j].strip().startswith('def ') or lines[j].strip().startswith('class ')):
                    break
                print(f"    {j+1:4d}: {lines[j].rstrip()}")
            break
    
    print("\n🎯 INVESTIGATION SUMMARY:")
    print("-" * 50)
    print("1. BigQuery trigger function is at line ~1167")
    print("2. BigQuery trigger check is at line 1521") 
    print("3. GDELT trigger check calls should_trigger_gdelt_search() at line 1572")
    print("4. Need to examine the actual implementation of these functions")

if __name__ == "__main__":
    analyze_trigger_functions()