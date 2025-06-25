#!/usr/bin/env python3
"""
Test GDELT trigger function directly to see what's happening
"""

import os

def test_gdelt_directly():
    """Test the GDELT trigger function directly"""
    
    print("🔍 TESTING GDELT TRIGGER DIRECTLY")
    print("="*50)
    
    # Check environment variable
    gdelt_enabled = os.environ.get("GDELT_API_ENABLED", "true").lower() in ("true", "1", "yes")
    print(f"📋 GDELT_API_ENABLED environment variable: {gdelt_enabled}")
    
    # Try to import the GDELT integration
    try:
        print("🔄 Attempting to import demo_gdelt_webhook_integration...")
        from demo_gdelt_webhook_integration import GDELTWebhookIntegration
        print("✅ Successfully imported GDELTWebhookIntegration")
        import_successful = True
        gdelt_integration = GDELTWebhookIntegration()
    except ImportError as e:
        print(f"❌ Failed to import GDELTWebhookIntegration: {e}")
        import_successful = False
        
        # Use the DummyGDELTIntegration from the file
        print("🔄 Using DummyGDELTIntegration...")
        
        class DummyGDELTIntegration:
            def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
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
                
                return False, ''

        gdelt_integration = DummyGDELTIntegration()
    
    # Test the trigger function
    test_query = "What breaking events are happening globally today?"
    print(f"\n🧪 Testing with query: '{test_query}'")
    
    should_trigger, category = gdelt_integration.should_trigger_gdelt_search(test_query)
    
    print(f"📊 Result: should_trigger = {should_trigger}, category = '{category}'")
    
    if should_trigger:
        print("✅ SUCCESS: GDELT trigger is working correctly!")
    else:
        print("❌ FAILURE: GDELT trigger is not working")
    
    # Check final GDELT_ENABLED status
    GDELT_ENABLED = import_successful and gdelt_enabled
    print(f"\n📋 Final GDELT_ENABLED status: {GDELT_ENABLED}")
    print(f"   - Import successful: {import_successful}")
    print(f"   - Environment enabled: {gdelt_enabled}")

if __name__ == "__main__":
    test_gdelt_directly()