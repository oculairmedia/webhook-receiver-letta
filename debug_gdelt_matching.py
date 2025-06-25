#!/usr/bin/env python3
"""
Debug the exact matching logic in GDELT trigger
"""

def debug_matching():
    """Debug why the matching is failing"""
    
    print("🔍 DEBUG GDELT MATCHING LOGIC")
    print("="*50)
    
    # Simulate the exact logic from the function
    query = "What breaking events are happening globally today?"
    message_lower = query.lower()
    
    trigger_keywords = {
        'global_events': [
            'world news', 'global events', 'international news',
            'breaking news', 'current events', 'latest news'
        ],
        'geopolitics': [
            'politics', 'election', 'government', 'diplomatic',
            'foreign policy', 'international relations', 'summit'
        ],
        'conflicts': [
            'war', 'conflict', 'crisis', 'protest', 'violence',
            'terrorism', 'military', 'security', 'sanctions'
        ],
        'economics': [
            'economy', 'market', 'trade', 'economic', 'financial',
            'recession', 'inflation', 'gdp', 'stock market'
        ],
        'disasters': [
            'disaster', 'earthquake', 'flood', 'hurricane', 'fire',
            'emergency', 'evacuation', 'natural disaster', 'climate'
        ],
        'technology': [
            'ai', 'artificial intelligence', 'technology', 'cyber',
            'digital', 'innovation', 'tech', 'breakthrough'
        ]
    }
    
    print(f"🧪 Query: '{query}'")
    print(f"📝 message_lower: '{message_lower}'")
    print()
    
    # Test the exact logic from the function
    for category, keywords in trigger_keywords.items():
        print(f"🔍 Testing category: {category}")
        for keyword in keywords:
            is_match = keyword in message_lower
            print(f"   '{keyword}' in '{message_lower}' = {is_match}")
            if is_match:
                print(f"✅ MATCH FOUND! Should return True, '{category}'")
                return
        print()
    
    print("❌ NO MATCHES FOUND - This explains why it returns False")
    
    print("\n💡 ANALYSIS:")
    print("The query has 'breaking events' but keywords look for 'breaking news'")
    print("The query has words that should trigger, but exact phrase matching fails")
    
    print("\n🔧 POTENTIAL FIXES:")
    print("1. Add 'breaking events' to global_events keywords")
    print("2. Change matching logic to check individual words")
    print("3. Add more flexible keyword variations")

if __name__ == "__main__":
    debug_matching()