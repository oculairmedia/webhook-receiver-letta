#!/usr/bin/env python3
"""
Script to fix the GDELT trigger function with proper logic
"""

def create_gdelt_trigger_fix():
    """Create a proper GDELT trigger function"""
    
    # Read the current flask_webhook_receiver.py
    with open('flask_webhook_receiver.py', 'r') as f:
        content = f.read()
    
    # Define the new GDELT trigger function with proper logic
    new_gdelt_trigger = '''            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
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
                    'what is happening', 'what\'s happening', 'current situation',
                    'breaking events', 'world events', 'global situation',
                    'latest developments', 'recent events'
                ]
                
                if any(phrase in message_lower for phrase in trigger_phrases):
                    return True, 'general_events'
                
                return False, ""'''
    
    # Also create a standalone version for the DummyGDELTIntegration class
    standalone_gdelt_trigger = '''    def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
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
    
    # Replace the dummy function at line 1128
    old_dummy_function = '''            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
                return False, \'\''''
    
    # Replace the standalone dummy function at line 1140
    old_standalone_function = '''def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
    return False, \'\'"""'''
    
    # Perform the replacements
    content = content.replace(old_dummy_function, new_gdelt_trigger)
    
    # Also replace the standalone version
    content = content.replace('    def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:\n        return False, \'\'', standalone_gdelt_trigger)
    
    # Write the fixed content back
    with open('flask_webhook_receiver.py', 'w') as f:
        f.write(content)
    
    print("✅ GDELT trigger function updated with proper logic!")
    print("🔍 Added keyword detection for:")
    print("   - News and current events")
    print("   - Global and political keywords") 
    print("   - Crisis and conflict keywords")
    print("   - Economic keywords")
    print("   - Specific trigger phrases")

if __name__ == "__main__":
    create_gdelt_trigger_fix()