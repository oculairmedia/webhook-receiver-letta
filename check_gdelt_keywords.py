#!/usr/bin/env python3
"""
Check the GDELT keywords and test why trigger is failing
"""

def check_gdelt_keywords():
    """Check the GDELT keywords and test the trigger"""
    
    print("🔍 CHECKING GDELT KEYWORDS AND TESTING TRIGGER")
    print("="*50)
    
    try:
        with open('demo_gdelt_webhook_integration.py', 'r', encoding='latin1') as f:
            lines = f.readlines()
        
        # Find the trigger_keywords definition
        print("\n📍 SEARCHING FOR trigger_keywords:")
        print("-" * 40)
        
        in_keywords_section = False
        for i, line in enumerate(lines):
            line_num = i + 1
            line_clean = line.rstrip()
            
            if 'trigger_keywords' in line and '=' in line:
                in_keywords_section = True
                print(f">>> {line_num:4d}: {line_clean}")
                # Show next 20 lines
                for j in range(i + 1, min(len(lines), i + 25)):
                    next_line = lines[j].rstrip()
                    print(f"    {j+1:4d}: {next_line}")
                    if '}' in next_line and not next_line.strip().startswith('#'):
                        break
                break
        
        if not in_keywords_section:
            print("❌ Could not find trigger_keywords definition")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")
    
    # Now test with the actual class
    print("\n🧪 TESTING WITH ACTUAL GDELT CLASS:")
    print("-" * 40)
    
    try:
        from demo_gdelt_webhook_integration import GDELTWebhookIntegration
        gdelt = GDELTWebhookIntegration()
        
        # Check what keywords are defined
        if hasattr(gdelt, 'trigger_keywords'):
            print("📋 Available trigger keyword categories:")
            for category, keywords in gdelt.trigger_keywords.items():
                print(f"   {category}: {keywords}")
        
        # Test our query
        test_query = "What breaking events are happening globally today?"
        print(f"\n🧪 Testing query: '{test_query}'")
        
        # Check each word against keywords
        query_words = test_query.lower().split()
        print(f"📝 Query words: {query_words}")
        
        # Manual check
        for category, keywords in gdelt.trigger_keywords.items():
            matches = [word for word in query_words if any(keyword in word or word in keyword for keyword in keywords)]
            if matches:
                print(f"✅ Found matches in {category}: {matches}")
            else:
                print(f"   No matches in {category}")
        
        # Test the actual function
        should_trigger, category = gdelt.should_trigger_gdelt_search(test_query)
        print(f"\n📊 Function result: should_trigger={should_trigger}, category='{category}'")
        
    except ImportError as e:
        print(f"❌ Could not import GDELTWebhookIntegration: {e}")

if __name__ == "__main__":
    check_gdelt_keywords()