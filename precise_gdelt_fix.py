#!/usr/bin/env python3
"""
Precise fix for GDELT trigger functions in both DummyGDELTIntegration classes
"""

def fix_gdelt_triggers():
    """Fix the GDELT trigger functions with proper implementation"""
    
    # Read the current file
    with open('flask_webhook_receiver.py', 'r') as f:
        content = f.read()
    
    # Define the new trigger function implementation
    new_trigger_function = '''            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
                """
                Determine if GDELT search should be triggered based on message content.
                Returns: (should_trigger: bool, category: str)
                """
                if not message or not message.strip():
                    return False, ''
                
                message_lower = message.lower()
                
                # News and current events keywords
                news_keywords = [
                    'news', 'breaking', 'latest', 'current events', 'headlines',
                    'happening', 'today', 'recent', 'update', 'developments'
                ]
                
                # Global and political keywords
                global_keywords = [
                    'global', 'world', 'international', 'worldwide', 'country',
                    'nations', 'politics', 'political', 'government', 'diplomatic'
                ]
                
                # Crisis and conflict keywords
                crisis_keywords = [
                    'crisis', 'conflict', 'war', 'protest', 'violence', 'attack',
                    'terrorism', 'disaster', 'emergency', 'urgent'
                ]
                
                # Economic keywords
                economic_keywords = [
                    'economic', 'economy', 'market', 'financial', 'trade',
                    'stocks', 'gdp', 'inflation', 'recession'
                ]
                
                # Check for news/events triggers
                if any(keyword in message_lower for keyword in news_keywords):
                    if any(keyword in message_lower for keyword in global_keywords):
                        return True, 'global_news'
                    if any(keyword in message_lower for keyword in crisis_keywords):
                        return True, 'crisis_events'
                    return True, 'general_news'
                
                # Check for global events
                if any(keyword in message_lower for keyword in global_keywords):
                    return True, 'global_events'
                
                # Check for crisis/conflict
                if any(keyword in message_lower for keyword in crisis_keywords):
                    return True, 'crisis_events'
                
                # Check for economic events
                if any(keyword in message_lower for keyword in economic_keywords):
                    return True, 'economic_events'
                
                # Specific phrases that should trigger GDELT
                trigger_phrases = [
                    'what is happening', 'what\\'s happening', 'current situation',
                    'breaking events', 'world events', 'global situation',
                    'latest developments', 'recent events'
                ]
                
                if any(phrase in message_lower for phrase in trigger_phrases):
                    return True, 'general_events'
                
                return False, ''
'''
    
    # Replace both dummy functions using exact matches
    old_function_pattern = "            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:\n                return False, ''"
    
    # Count occurrences first
    count = content.count(old_function_pattern)
    print(f"Found {count} occurrences of the dummy function to replace")
    
    # Replace all occurrences
    content = content.replace(old_function_pattern, new_trigger_function)
    
    # Write the fixed content back
    with open('flask_webhook_receiver.py', 'w') as f:
        f.write(content)
    
    print("✅ GDELT trigger functions updated successfully!")
    print("🔧 Updated both DummyGDELTIntegration classes")
    print("📋 New trigger logic includes:")
    print("   • News and current events keywords")
    print("   • Global and political keywords") 
    print("   • Crisis and conflict keywords")
    print("   • Economic keywords")
    print("   • Specific trigger phrases")
    print("📊 Will now properly detect queries like:")
    print("   • 'What breaking events are happening globally today?'")
    print("   • 'Latest world news'")
    print("   • 'Current global situation'")

if __name__ == "__main__":
    fix_gdelt_triggers()