#!/usr/bin/env python3
"""
Fix the real GDELT integration by adding better keywords
"""

def fix_gdelt_real():
    """Fix the actual GDELT integration keywords"""
    
    print("🔧 FIXING REAL GDELT INTEGRATION")
    print("="*50)
    
    try:
        # Read the file
        with open('demo_gdelt_webhook_integration.py', 'r', encoding='latin1') as f:
            content = f.read()
        
        # Define the updated keywords with more variations
        old_keywords = """        self.trigger_keywords = {
            'global_events': [
                'world news', 'global events', 'international news',
                'breaking news', 'current events', 'latest news'
            ],"""
        
        new_keywords = """        self.trigger_keywords = {
            'global_events': [
                'world news', 'global events', 'international news',
                'breaking news', 'current events', 'latest news',
                'breaking events', 'world events', 'global situation',
                'happening globally', 'global developments', 'world situation',
                'international events', 'worldwide events', 'global news'
            ],"""
        
        # Replace the keywords
        if old_keywords in content:
            content = content.replace(old_keywords, new_keywords)
            
            # Write back to file
            with open('demo_gdelt_webhook_integration.py', 'w', encoding='latin1') as f:
                f.write(content)
            
            print("✅ Successfully updated GDELT keywords!")
            print("📋 Added new trigger phrases:")
            print("   - 'breaking events'")
            print("   - 'world events'") 
            print("   - 'global situation'")
            print("   - 'happening globally'")
            print("   - 'global developments'")
            print("   - 'world situation'")
            print("   - 'international events'")
            print("   - 'worldwide events'")
            print("   - 'global news'")
            
        else:
            print("❌ Could not find the target keywords section to replace")
            print("🔍 Searching for alternative patterns...")
            
            # Check if we can find the section differently
            if 'global_events' in content and 'breaking news' in content:
                print("✅ Found keywords section, but format may be different")
                print("📝 Manual fix may be required")
            else:
                print("❌ Keywords section not found at all")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_gdelt_real()