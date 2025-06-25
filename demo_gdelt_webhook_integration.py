#!/usr/bin/env python3
"""
Demo: GDELT API Integration with Webhook System
==============================================

This script demonstrates how to integrate the GDELT API with the existing webhook receiver
to provide real-time global news context for LLM conversations.
Requires: pip install pycountry
"""

import requests
import json
from datetime import datetime
from gdelt_api_client import GDELTAPIClient, build_gdelt_query
import pycountry


class GDELTWebhookIntegration:
    """Integrates GDELT API with the webhook system"""
    
    def __init__(self, webhook_url: str = "http://localhost:5005/webhook/letta"):
        """
        Initialize the integration
        
        Args:
            webhook_url: URL of the webhook receiver
        """
        self.webhook_url = webhook_url
        self.gdelt_client = GDELTAPIClient(timeout=15)
        
        # Generate comprehensive country list from pycountry
        self.country_names = set()
        for country in pycountry.countries:
            # Add the official name in lowercase
            self.country_names.add(country.name.lower())
            # Add common name if different
            if hasattr(country, 'common_name') and country.common_name:
                self.country_names.add(country.common_name.lower())
        
        # Add manual list of common regions and alternative geopolitical terms
        self.regional_terms = {
            'europe', 'asia', 'africa', 'america', 'americas', 'middle east',
            'baltics', 'scandinavia', 'balkans', 'caucasus',
            'southeast asia', 'persian gulf', 'horn of africa', 'sahel',
            'uk', 'usa', 'uae', 'drc', 'north korea', 'south korea',
            'east asia', 'west africa', 'central asia', 'south america',
            'north america', 'eastern europe', 'western europe',
            'mediterranean', 'caribbean', 'pacific islands', 'arctic'
        }
        
        # Combine country names with regional terms for geographic matching
        self.geographic_indicators = self.country_names.union(self.regional_terms)
        
        # Keywords that trigger GDELT searches
        self.trigger_keywords = {
            'global_events': [
                'world news', 'global events', 'international news',
                'breaking news', 'current events', 'latest news',
                'breaking events', 'world events', 'global situation',
                'happening globally', 'global developments', 'world situation',
                'international events', 'worldwide events', 'global news'
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
    
    def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
        """
        Determine if a message should trigger a GDELT search
        
        Args:
            message: User message to analyze
            
        Returns:
            Tuple of (should_trigger, category)
        """
        message_lower = message.lower()
        
        for category, keywords in self.trigger_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return True, category
        
        # Check for geographic indicators (countries and regions)
        for indicator in self.geographic_indicators:
            if indicator in message_lower:
                return True, 'geographic'
        
        return False, ''
    
    def generate_gdelt_context(self, message: str, category: str) -> dict:
        """
        Generate relevant GDELT context for a message
        
        Args:
            message: User message
            category: Category of news to focus on
            
        Returns:
            Dict containing GDELT search results and context
        """
        try:
            # Build appropriate search query based on category and message
            search_query = self._build_search_query(message, category)
            
            print(f"GDELT search query: {search_query}")
            
            # Get recent articles (last 24 hours for freshness)
            articles = self.gdelt_client.search_articles(
                query=search_query,
                max_records=10,
                timespan="24h",
                sort="hybridrel"
            )
            
            # Get news volume timeline for trend analysis
            timeline = self.gdelt_client.search_news_volume_timeline(
                query=search_query,
                timespan="3days",
                smooth=2
            )
            
            # Get tone analysis
            tone_dist = self.gdelt_client.get_tone_distribution(
                query=search_query,
                timespan="24h"
            )
            
            # Process and format results
            context = self._format_gdelt_context(articles, timeline, tone_dist, category)
            
            return {
                'success': True,
                'query': search_query,
                'category': category,
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': search_query if 'search_query' in locals() else '',
                'category': category,
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_search_query(self, message: str, category: str) -> str:
        """Build a GDELT search query based on the message and category"""
        
        # Extract key terms from the message
        message_words = message.lower().split()
        
        # Category-specific query building
        if category == 'global_events':
            # Broad search for major international events
            return build_gdelt_query(
                or_keywords=["breaking news", "major event", "international"],
                tone_lt=-2  # Focus on significant (often negative) events
            )
        
        elif category == 'geopolitics':
            # Political and diplomatic news
            political_terms = [word for word in message_words 
                             if word in ['election', 'government', 'president', 'minister', 'parliament']]
            
            if political_terms:
                return build_gdelt_query(
                    keywords=political_terms,
                    or_keywords=["politics", "government", "diplomatic"]
                )
            else:
                return "theme:GENERAL_GOVERNMENT OR theme:DIPLOMACY"
        
        elif category == 'conflicts':
            # Conflict and security news
            return build_gdelt_query(
                or_keywords=["conflict", "war", "crisis", "protest", "violence"],
                tone_lt=-1  # Negative events
            )
        
        elif category == 'economics':
            # Economic and financial news
            return build_gdelt_query(
                or_keywords=["economy", "market", "trade", "financial", "economic"],
                theme="ECON"
            )
        
        elif category == 'disasters':
            # Natural disasters and emergencies
            return build_gdelt_query(
                or_keywords=["disaster", "earthquake", "flood", "hurricane", "emergency"],
                theme="ENV_DISASTER"
            )
        
        elif category == 'technology':
            # Technology and innovation news
            return build_gdelt_query(
                or_keywords=["technology", "artificial intelligence", "innovation", "digital"],
                theme="SCIENCE"
            )
        
        elif category == 'geographic':
            # Country or region-specific news
            geographic_terms = []
            
            # Check for any geographic indicators in the message
            for indicator in self.geographic_indicators:
                if indicator in message.lower():
                    geographic_terms.append(indicator)
            
            if geographic_terms:
                # Search for news involving specific countries/regions
                # Use the first few matched terms to avoid overly complex queries
                primary_terms = geographic_terms[:3]
                country_query = " OR ".join([f"sourcecountry:{term}" for term in primary_terms])
                general_query = " OR ".join(primary_terms)
                return f"({country_query}) OR ({general_query})"
            else:
                return "international OR global"
        
        # Fallback: use message words directly
        message_keywords = [word for word in message_words if len(word) > 3][:3]
        if message_keywords:
            return build_gdelt_query(keywords=message_keywords)
        else:
            return "breaking news"
    
    def _format_gdelt_context(self, articles: dict, timeline: dict, tone_dist: dict, category: str) -> str:
        """Format GDELT results into readable context"""
        
        context_parts = []
        
        # Add category header
        context_parts.append(f"**Recent Global News Context ({category.replace('_', ' ').title()})**\n")
        
        # Process articles
        if articles and articles.get('articles'):
            context_parts.append("**Top Recent Articles:**")
            
            for i, article in enumerate(articles['articles'][:5], 1):
                title = article.get('title', 'No title')
                domain = article.get('domain', 'Unknown source')
                url = article.get('url', '')
                date = article.get('seendate', 'Unknown date')
                tone = article.get('tone', 0)
                
                # Format tone
                if tone > 2:
                    tone_desc = "positive"
                elif tone < -2:
                    tone_desc = "negative"
                else:
                    tone_desc = "neutral"
                
                context_parts.append(f"{i}. **{title}**")
                if url:
                    context_parts.append(f"   Source: {domain} | Date: {date} | Tone: {tone_desc}")
                    context_parts.append(f"   URL: {url}")
                else:
                    context_parts.append(f"   Source: {domain} | Date: {date} | Tone: {tone_desc}")
            
            context_parts.append("")  # Empty line
        
        # Process timeline trends
        if timeline and timeline.get('timeline'):
            timeline_data = timeline['timeline']
            if len(timeline_data) >= 2:
                recent_activity = timeline_data[-1].get('value', 0)
                previous_activity = timeline_data[-2].get('value', 0)
                
                if recent_activity > previous_activity * 1.2:
                    context_parts.append("📈 **Trend**: Coverage volume is increasing significantly")
                elif recent_activity < previous_activity * 0.8:
                    context_parts.append("📉 **Trend**: Coverage volume is decreasing")
                else:
                    context_parts.append("📊 **Trend**: Coverage volume is stable")
                
                context_parts.append("")
        
        # Process tone distribution
        if tone_dist and tone_dist.get('data'):
            # Find the dominant tone
            tone_bins = tone_dist['data']
            if tone_bins:
                # Find bin with most articles
                max_bin = max(tone_bins, key=lambda x: x.get('count', 0))
                tone_range = max_bin.get('bin', 'unknown')
                count = max_bin.get('count', 0)
                
                context_parts.append(f"**Sentiment Analysis**: Most coverage ({count} articles) has {tone_range} tone")
                context_parts.append("")
        
        # Add timestamp
        context_parts.append(f"*Data from GDELT Global News Database - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*")
        
        return "\n".join(context_parts)
    
    def test_webhook_integration(self, test_message: str) -> dict:
        """
        Test the integration by sending a message to the webhook
        
        Args:
            test_message: Message to test with
            
        Returns:
            Webhook response
        """
        # Check if message should trigger GDELT
        should_trigger, category = self.should_trigger_gdelt_search(test_message)
        
        print(f"Message: {test_message}")
        print(f"Should trigger GDELT: {should_trigger} (category: {category})")
        
        if not should_trigger:
            print("Message does not trigger GDELT search")
            return {'triggered': False, 'reason': 'No relevant keywords found'}
        
        # Generate GDELT context
        print("Generating GDELT context...")
        gdelt_context = self.generate_gdelt_context(test_message, category)
        
        if not gdelt_context['success']:
            print(f"GDELT search failed: {gdelt_context['error']}")
            return gdelt_context
        
        print(f"GDELT context generated ({len(gdelt_context['context'])} chars)")
        
        # Prepare webhook payload
        payload = {
            "prompt": test_message,
            "gdelt_context": gdelt_context['context'],
            "gdelt_metadata": {
                "query": gdelt_context['query'],
                "category": gdelt_context['category'],
                "timestamp": gdelt_context['timestamp']
            },
            "request": {
                "path": "/v1/agents/agent-gdelt-test/chat",
                "body": {
                    "messages": [
                        {
                            "role": "user",
                            "content": test_message
                        }
                    ]
                }
            }
        }
        
        # Send to webhook
        try:
            print(f"Sending to webhook: {self.webhook_url}")
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"Webhook response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'webhook_response': result,
                    'gdelt_context': gdelt_context
                }
            else:
                return {
                    'success': False,
                    'error': f"Webhook returned {response.status_code}: {response.text[:500]}",
                    'gdelt_context': gdelt_context
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Webhook request failed: {e}",
                'gdelt_context': gdelt_context
            }


def demo_gdelt_webhook():
    """Run a demonstration of the GDELT webhook integration"""
    
    print("GDELT Webhook Integration Demo")
    print("=" * 50)
    
    integration = GDELTWebhookIntegration()
    
    # Test cases
    test_cases = [
        {
            "name": "Global Events Query",
            "message": "What's happening in the world today? Any major international events?",
            "expected_trigger": True
        },
        {
            "name": "Ukraine Crisis Query",
            "message": "Tell me about the latest developments in Ukraine",
            "expected_trigger": True
        },
        {
            "name": "Economic News Query",
            "message": "How are global markets performing this week?",
            "expected_trigger": True
        },
        {
            "name": "Weather Query (No Trigger)",
            "message": "What's the weather like today in New York?",
            "expected_trigger": False
        },
        {
            "name": "Technology News Query",
            "message": "What are the latest AI breakthroughs in the news?",
            "expected_trigger": True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 40)
        
        result = integration.test_webhook_integration(test_case['message'])
        
        # Verify expectation
        triggered = result.get('triggered', True)  # Assume triggered unless explicitly False
        if triggered != test_case['expected_trigger']:
            print(f"❌ EXPECTATION MISMATCH: Expected trigger={test_case['expected_trigger']}, got {triggered}")
        else:
            print(f"✅ EXPECTATION MET: Trigger behavior as expected")
        
        if result.get('success'):
            print("✅ Integration test successful")
            
            # Show GDELT context preview
            gdelt_context = result.get('gdelt_context', {})
            if gdelt_context.get('context'):
                context_preview = gdelt_context['context'][:300] + "..."
                print(f"GDELT Context Preview: {context_preview}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Integration test failed: {error}")
        
        print()


def demo_gdelt_standalone():
    """Demonstrate GDELT API usage without webhook integration"""
    
    print("GDELT Standalone Demo")
    print("=" * 30)
    
    integration = GDELTWebhookIntegration()
    
    # Test different types of queries
    queries = [
        ("Global politics", "global_events"),
        ("China trade war", "economics"),
        ("Ukraine conflict", "conflicts"),
        ("earthquake Japan", "disasters"),
        ("AI breakthrough", "technology")
    ]
    
    for query, category in queries:
        print(f"\nTesting: {query} (category: {category})")
        print("-" * 40)
        
        result = integration.generate_gdelt_context(query, category)
        
        if result['success']:
            print("✅ GDELT search successful")
            print(f"Query used: {result['query']}")
            print(f"Context length: {len(result['context'])} characters")
            print("Context preview:")
            print(result['context'][:400] + "...")
        else:
            print(f"❌ GDELT search failed: {result['error']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "webhook":
            demo_gdelt_webhook()
        elif sys.argv[1] == "standalone":
            demo_gdelt_standalone()
        else:
            print("Usage: python demo_gdelt_webhook_integration.py [webhook|standalone]")
    else:
        print("Running both demos...\n")
        demo_gdelt_standalone()
        print("\n" + "=" * 60 + "\n")
        demo_gdelt_webhook()