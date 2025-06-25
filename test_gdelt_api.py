#!/usr/bin/env python3
"""
Test script for GDELT API Client
"""

import sys
import json
from gdelt_api_client import GDELTAPIClient, build_gdelt_query


def test_basic_functionality():
    """Test basic GDELT API functionality"""
    print("Testing GDELT API Basic Functionality")
    print("=" * 50)
    
    client = GDELTAPIClient(timeout=10)
    
    # Test 1: Simple article search
    print("\n1. Testing Simple Article Search")
    try:
        results = client.search_articles(
            query="ukraine",
            max_records=3,
            timespan="24h"
        )
        
        if isinstance(results, dict):
            print(f"✅ Success: Received response type: {type(results)}")
            
            # Check for expected fields
            if 'articles' in results:
                print(f"   Articles found: {len(results['articles'])}")
                if results['articles']:
                    article = results['articles'][0]
                    print(f"   Sample title: {article.get('title', 'No title')[:100]}...")
                    print(f"   Sample domain: {article.get('domain', 'No domain')}")
                    print(f"   Sample date: {article.get('seendate', 'No date')}")
            else:
                print(f"   Response keys: {list(results.keys())}")
        else:
            print(f"❌ Unexpected response type: {type(results)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Timeline search
    print("\n2. Testing Timeline Search")
    try:
        timeline = client.search_news_volume_timeline(
            query="artificial intelligence",
            timespan="3days"
        )
        
        if isinstance(timeline, dict):
            print(f"✅ Success: Timeline response received")
            
            if 'timeline' in timeline:
                print(f"   Timeline points: {len(timeline['timeline'])}")
                if timeline['timeline']:
                    point = timeline['timeline'][0]
                    print(f"   Sample point: {point}")
            else:
                print(f"   Timeline keys: {list(timeline.keys())}")
        else:
            print(f"❌ Unexpected timeline response type: {type(timeline)}")
            
    except Exception as e:
        print(f"❌ Timeline error: {e}")
    
    # Test 3: Different output formats
    print("\n3. Testing Different Output Formats")
    try:
        # CSV format
        csv_result = client.search_articles(
            query="climate change",
            format_type="csv",
            max_records=3,
            timespan="24h"
        )
        
        if isinstance(csv_result, str) and csv_result.strip():
            lines = csv_result.strip().split('\n')
            print(f"✅ CSV format: {len(lines)} lines")
            print(f"   CSV header: {lines[0][:100]}...")
        else:
            print(f"❌ CSV format failed or empty")
            
    except Exception as e:
        print(f"❌ CSV error: {e}")


def test_advanced_queries():
    """Test advanced query building and search"""
    print("\n" + "=" * 50)
    print("Testing Advanced Query Features")
    print("=" * 50)
    
    client = GDELTAPIClient(timeout=10)
    
    # Test 1: Country-specific search
    print("\n1. Testing Country-Specific Search")
    try:
        country_results = client.search_by_country(
            query="renewable energy",
            country="germany",
            max_records=3,
            timespan="1week"
        )
        
        if country_results and 'articles' in country_results:
            print(f"✅ Found {len(country_results['articles'])} German articles")
            for i, article in enumerate(country_results['articles'][:2], 1):
                print(f"   {i}. {article.get('title', 'No title')[:80]}...")
        else:
            print(f"❌ No German articles found or unexpected format")
            
    except Exception as e:
        print(f"❌ Country search error: {e}")
    
    # Test 2: Language-specific search
    print("\n2. Testing Language-Specific Search")
    try:
        lang_results = client.search_by_language(
            query="technology",
            language="spanish",
            max_records=3,
            timespan="3days"
        )
        
        if lang_results and 'articles' in lang_results:
            print(f"✅ Found {len(lang_results['articles'])} Spanish articles")
            for i, article in enumerate(lang_results['articles'][:2], 1):
                print(f"   {i}. {article.get('title', 'No title')[:80]}...")
        else:
            print(f"❌ No Spanish articles found")
            
    except Exception as e:
        print(f"❌ Language search error: {e}")
    
    # Test 3: Domain-specific search
    print("\n3. Testing Domain-Specific Search")
    try:
        domain_results = client.search_by_domain(
            query="biden",
            domain="cnn.com",
            max_records=3,
            timespan="3days"
        )
        
        if domain_results and 'articles' in domain_results:
            print(f"✅ Found {len(domain_results['articles'])} CNN articles")
            for i, article in enumerate(domain_results['articles'][:2], 1):
                print(f"   {i}. {article.get('title', 'No title')[:80]}...")
        else:
            print(f"❌ No CNN articles found")
            
    except Exception as e:
        print(f"❌ Domain search error: {e}")
    
    # Test 4: Complex query building
    print("\n4. Testing Complex Query Building")
    
    # Build a complex query
    complex_query = build_gdelt_query(
        or_keywords=["climate change", "global warming"],
        source_country="united states",
        exclude=["hoax"],
        tone_gt=2  # Positive articles only
    )
    
    print(f"   Built query: {complex_query}")
    
    try:
        complex_results = client.search_articles(
            query=complex_query,
            max_records=3,
            timespan="1week"
        )
        
        if complex_results and 'articles' in complex_results:
            print(f"✅ Complex query found {len(complex_results['articles'])} articles")
            for article in complex_results['articles'][:2]:
                title = article.get('title', 'No title')
                tone = article.get('tone', 'No tone')
                print(f"   - {title[:80]}... (tone: {tone})")
        else:
            print(f"❌ Complex query failed")
            
    except Exception as e:
        print(f"❌ Complex query error: {e}")


def test_image_search():
    """Test image search capabilities"""
    print("\n" + "=" * 50)
    print("Testing Image Search Capabilities")
    print("=" * 50)
    
    client = GDELTAPIClient(timeout=10)
    
    # Test 1: Basic image search
    print("\n1. Testing Basic Image Search")
    try:
        image_results = client.search_images(
            query='imagetag:"protest"',
            max_records=5,
            timespan="3days"
        )
        
        if image_results and 'images' in image_results:
            print(f"✅ Found {len(image_results['images'])} protest images")
            for i, image in enumerate(image_results['images'][:3], 1):
                print(f"   {i}. URL: {image.get('url', 'No URL')}")
                context = image.get('contextText', 'No context')
                print(f"      Context: {context[:100]}...")
        elif image_results:
            print(f"   Image result keys: {list(image_results.keys())}")
        else:
            print(f"❌ No protest images found")
            
    except Exception as e:
        print(f"❌ Image search error: {e}")
    
    # Test 2: Multi-tag image search
    print("\n2. Testing Multi-Tag Image Search")
    try:
        disaster_images = client.search_images(
            query='(imagetag:"flood" OR imagetag:"fire")',
            max_records=3,
            timespan="1week"
        )
        
        if disaster_images and 'images' in disaster_images:
            print(f"✅ Found {len(disaster_images['images'])} disaster images")
        else:
            print(f"❌ No disaster images found")
            
    except Exception as e:
        print(f"❌ Disaster image search error: {e}")


def test_tone_analysis():
    """Test tone analysis features"""
    print("\n" + "=" * 50)
    print("Testing Tone Analysis")
    print("=" * 50)
    
    client = GDELTAPIClient(timeout=10)
    
    # Test 1: Tone timeline
    print("\n1. Testing Tone Timeline")
    try:
        tone_timeline = client.search_tone_timeline(
            query="donald trump",
            timespan="3days"
        )
        
        if tone_timeline and 'timeline' in tone_timeline:
            print(f"✅ Tone timeline has {len(tone_timeline['timeline'])} points")
            if tone_timeline['timeline']:
                # Show a few sample points
                for i, point in enumerate(tone_timeline['timeline'][:3]):
                    date = point.get('date', 'No date')
                    tone = point.get('tone', 'No tone')
                    print(f"   {i+1}. {date}: {tone}")
        else:
            print(f"❌ No tone timeline data")
            
    except Exception as e:
        print(f"❌ Tone timeline error: {e}")
    
    # Test 2: Tone distribution
    print("\n2. Testing Tone Distribution")
    try:
        tone_dist = client.get_tone_distribution(
            query="climate change",
            timespan="1week"
        )
        
        if tone_dist and 'data' in tone_dist:
            print(f"✅ Tone distribution has {len(tone_dist['data'])} bins")
            for i, bin_data in enumerate(tone_dist['data'][:5]):
                tone_range = bin_data.get('bin', 'Unknown')
                count = bin_data.get('count', 0)
                print(f"   {tone_range}: {count} articles")
        else:
            print(f"❌ No tone distribution data")
            if tone_dist:
                print(f"   Available keys: {list(tone_dist.keys())}")
            
    except Exception as e:
        print(f"❌ Tone distribution error: {e}")


def run_interactive_demo():
    """Run an interactive demo of the GDELT API"""
    print("\n" + "=" * 50)
    print("Interactive GDELT API Demo")
    print("=" * 50)
    
    client = GDELTAPIClient()
    
    while True:
        print("\nChoose a demo option:")
        print("1. Search recent articles")
        print("2. Get news volume timeline")
        print("3. Analyze sentiment/tone")
        print("4. Search images")
        print("5. Country-specific news")
        print("6. Custom query")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            query = input("Enter search terms: ").strip()
            if query:
                try:
                    results = client.search_articles(query, max_records=5, timespan="24h")
                    if results and 'articles' in results:
                        print(f"\nFound {len(results['articles'])} articles:")
                        for i, article in enumerate(results['articles'], 1):
                            print(f"{i}. {article.get('title', 'No title')}")
                            print(f"   Source: {article.get('domain', 'Unknown')}")
                    else:
                        print("No articles found")
                except Exception as e:
                    print(f"Error: {e}")
        
        elif choice == "2":
            query = input("Enter search terms for timeline: ").strip()
            if query:
                try:
                    timeline = client.search_news_volume_timeline(query, timespan="1week")
                    if timeline and 'timeline' in timeline:
                        print(f"\nTimeline has {len(timeline['timeline'])} data points")
                        print("Recent activity:")
                        for point in timeline['timeline'][-5:]:
                            print(f"  {point.get('date', 'Unknown')}: {point.get('value', 0):.4f}")
                    else:
                        print("No timeline data found")
                except Exception as e:
                    print(f"Error: {e}")
        
        elif choice == "3":
            query = input("Enter search terms for tone analysis: ").strip()
            if query:
                try:
                    tone_dist = client.get_tone_distribution(query, timespan="3days")
                    if tone_dist and 'data' in tone_dist:
                        print(f"\nTone distribution:")
                        for bin_data in tone_dist['data'][:7]:
                            tone_range = bin_data.get('bin', 'Unknown')
                            count = bin_data.get('count', 0)
                            print(f"  {tone_range}: {count} articles")
                    else:
                        print("No tone data found")
                except Exception as e:
                    print(f"Error: {e}")
        
        elif choice == "4":
            tag = input("Enter image tag (e.g., 'protest', 'fire', 'flood'): ").strip()
            if tag:
                try:
                    images = client.search_images(f'imagetag:"{tag}"', max_records=3, timespan="3days")
                    if images and 'images' in images:
                        print(f"\nFound {len(images['images'])} images:")
                        for i, image in enumerate(images['images'], 1):
                            print(f"{i}. {image.get('url', 'No URL')}")
                    else:
                        print("No images found")
                except Exception as e:
                    print(f"Error: {e}")
        
        elif choice == "5":
            query = input("Enter search terms: ").strip()
            country = input("Enter country name: ").strip()
            if query and country:
                try:
                    results = client.search_by_country(query, country, max_records=3, timespan="3days")
                    if results and 'articles' in results:
                        print(f"\nFound {len(results['articles'])} articles from {country}:")
                        for i, article in enumerate(results['articles'], 1):
                            print(f"{i}. {article.get('title', 'No title')}")
                    else:
                        print(f"No articles found from {country}")
                except Exception as e:
                    print(f"Error: {e}")
        
        elif choice == "6":
            print("\nCustom query builder:")
            keywords = input("Keywords (comma-separated): ").strip()
            country = input("Source country (optional): ").strip()
            domain = input("Domain (optional): ").strip()
            
            query_params = {}
            if keywords:
                query_params['keywords'] = [k.strip() for k in keywords.split(',')]
            if country:
                query_params['source_country'] = country
            if domain:
                query_params['domain'] = domain
            
            if query_params:
                custom_query = build_gdelt_query(**query_params)
                print(f"\nBuilt query: {custom_query}")
                
                try:
                    results = client.search_articles(custom_query, max_records=3, timespan="24h")
                    if results and 'articles' in results:
                        print(f"\nFound {len(results['articles'])} articles:")
                        for i, article in enumerate(results['articles'], 1):
                            print(f"{i}. {article.get('title', 'No title')}")
                    else:
                        print("No articles found")
                except Exception as e:
                    print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "basic":
            test_basic_functionality()
        elif sys.argv[1] == "advanced":
            test_advanced_queries()
        elif sys.argv[1] == "images":
            test_image_search()
        elif sys.argv[1] == "tone":
            test_tone_analysis()
        elif sys.argv[1] == "interactive":
            run_interactive_demo()
        else:
            print("Usage: python test_gdelt_api.py [basic|advanced|images|tone|interactive]")
    else:
        print("Running all tests...")
        test_basic_functionality()
        test_advanced_queries()
        test_image_search()
        test_tone_analysis()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        print("\nTo run interactive demo: python test_gdelt_api.py interactive")