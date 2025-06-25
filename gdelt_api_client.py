#!/usr/bin/env python3
"""
GDELT API Client
================

A Python client for querying the GDELT Full Text Search API v2.0
Provides access to global news coverage across 65 languages with various output formats.

API Documentation: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
Base URL: https://api.gdeltproject.org/api/v2/doc/doc
"""

import requests
import json
import urllib.parse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import csv
import io


class GDELTAPIClient:
    """Client for interacting with the GDELT DOC 2.0 API"""
    
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the GDELT API client
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GDELT-Python-Client/1.0'
        })
    
    def search_articles(
        self,
        query: str,
        mode: str = "artlist",
        format_type: str = "json",
        timespan: Optional[str] = None,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        max_records: int = 75,
        sort: str = "hybridrel",
        **kwargs
    ) -> Union[Dict, str]:
        """
        Search for articles using the GDELT API
        
        Args:
            query: Search query (supports keywords, phrases, and operators)
            mode: Output mode (artlist, timeline, imagecollage, etc.)
            format_type: Output format (json, csv, html, rss)
            timespan: Time range (e.g., "1week", "3days", "24h")
            start_datetime: Start date/time (YYYYMMDDHHMMSS)
            end_datetime: End date/time (YYYYMMDDHHMMSS)
            max_records: Maximum number of records to return (up to 250)
            sort: Sort order (hybridrel, datedesc, dateasc, tonedesc, toneasc)
            **kwargs: Additional API parameters
            
        Returns:
            API response as dict (JSON) or string (other formats)
        """
        params = {
            "query": query,
            "mode": mode,
            "format": format_type,
            "maxrecords": max_records,
            "sort": sort
        }
        
        if timespan:
            params["timespan"] = timespan
        if start_datetime:
            params["startdatetime"] = start_datetime
        if end_datetime:
            params["enddatetime"] = end_datetime
            
        # Add any additional parameters
        params.update(kwargs)
        
        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if format_type.lower() == "json":
                return response.json()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"GDELT API request failed: {e}")
    
    def search_news_volume_timeline(
        self,
        query: str,
        timespan: str = "1week",
        smooth: int = 0
    ) -> Dict:
        """
        Get a timeline of news volume for a query
        
        Args:
            query: Search query
            timespan: Time range to search
            smooth: Timeline smoothing (0-30)
            
        Returns:
            Timeline data as dict
        """
        params = {"timelinesmooth": smooth} if smooth > 0 else {}
        
        return self.search_articles(
            query=query,
            mode="timelinevol",
            format_type="json",
            timespan=timespan,
            **params
        )
    
    def search_tone_timeline(
        self,
        query: str,
        timespan: str = "1week",
        smooth: int = 0
    ) -> Dict:
        """
        Get a timeline of tone/sentiment for a query
        
        Args:
            query: Search query
            timespan: Time range to search
            smooth: Timeline smoothing (0-30)
            
        Returns:
            Tone timeline data as dict
        """
        params = {"timelinesmooth": smooth} if smooth > 0 else {}
        
        return self.search_articles(
            query=query,
            mode="timelinetone",
            format_type="json",
            timespan=timespan,
            **params
        )
    
    def search_images(
        self,
        query: str,
        mode: str = "imagecollageinfo",
        max_records: int = 50,
        timespan: str = "1week"
    ) -> Dict:
        """
        Search for images using GDELT's Visual Knowledge Graph
        
        Args:
            query: Image search query (use imagetag:, imagewebtag:, etc.)
            mode: Image mode (imagecollage, imagecollageinfo, imagegallery)
            max_records: Maximum images to return
            timespan: Time range to search
            
        Returns:
            Image search results as dict
        """
        return self.search_articles(
            query=query,
            mode=mode,
            format_type="json",
            max_records=max_records,
            timespan=timespan
        )
    
    def get_tone_distribution(
        self,
        query: str,
        timespan: str = "1week"
    ) -> Dict:
        """
        Get tone distribution histogram for a query
        
        Args:
            query: Search query
            timespan: Time range to search
            
        Returns:
            Tone chart data as dict
        """
        return self.search_articles(
            query=query,
            mode="tonechart",
            format_type="json",
            timespan=timespan
        )
    
    def search_by_country(
        self,
        query: str,
        country: str,
        timespan: str = "1week",
        max_records: int = 75
    ) -> Dict:
        """
        Search for articles from a specific country
        
        Args:
            query: Search query
            country: Country name or 2-letter code
            timespan: Time range to search
            max_records: Maximum articles to return
            
        Returns:
            Search results as dict
        """
        country_query = f"{query} sourcecountry:{country.lower().replace(' ', '')}"
        
        return self.search_articles(
            query=country_query,
            mode="artlist",
            format_type="json",
            timespan=timespan,
            max_records=max_records
        )
    
    def search_by_language(
        self,
        query: str,
        language: str,
        timespan: str = "1week",
        max_records: int = 75
    ) -> Dict:
        """
        Search for articles in a specific language
        
        Args:
            query: Search query
            language: Language name or 3-letter code
            timespan: Time range to search
            max_records: Maximum articles to return
            
        Returns:
            Search results as dict
        """
        lang_query = f"{query} sourcelang:{language.lower()}"
        
        return self.search_articles(
            query=lang_query,
            mode="artlist",
            format_type="json",
            timespan=timespan,
            max_records=max_records
        )
    
    def search_by_domain(
        self,
        query: str,
        domain: str,
        timespan: str = "1week",
        max_records: int = 75
    ) -> Dict:
        """
        Search for articles from a specific news domain
        
        Args:
            query: Search query
            domain: News domain (e.g., cnn.com, bbc.com)
            timespan: Time range to search
            max_records: Maximum articles to return
            
        Returns:
            Search results as dict
        """
        domain_query = f"{query} domain:{domain.lower()}"
        
        return self.search_articles(
            query=domain_query,
            mode="artlist",
            format_type="json",
            timespan=timespan,
            max_records=max_records
        )


def demo_gdelt_api():
    """Demonstrate various GDELT API queries"""
    
    client = GDELTAPIClient()
    
    print("GDELT API Demo")
    print("=" * 50)
    
    # 1. Basic article search
    print("\n1. Basic Article Search - 'climate change'")
    try:
        results = client.search_articles(
            query="climate change",
            max_records=5,
            timespan="3days"
        )
        
        if results and 'articles' in results:
            print(f"Found {len(results['articles'])} articles")
            for i, article in enumerate(results['articles'][:3], 1):
                print(f"  {i}. {article.get('title', 'No title')}")
                print(f"     Source: {article.get('domain', 'Unknown')}")
                print(f"     Date: {article.get('seendate', 'Unknown')}")
        else:
            print("No articles found or unexpected response format")
            
    except Exception as e:
        print(f"Error in basic search: {e}")
    
    # 2. News volume timeline
    print("\n2. News Volume Timeline - 'artificial intelligence'")
    try:
        timeline = client.search_news_volume_timeline(
            query="artificial intelligence",
            timespan="1week",
            smooth=3
        )
        
        if timeline and 'timeline' in timeline:
            print(f"Timeline data points: {len(timeline['timeline'])}")
            # Show first few data points
            for point in timeline['timeline'][:3]:
                date = point.get('date', 'Unknown')
                value = point.get('value', 0)
                print(f"  {date}: {value:.4f}")
        else:
            print("No timeline data found")
            
    except Exception as e:
        print(f"Error in timeline search: {e}")
    
    # 3. Tone analysis
    print("\n3. Tone Distribution - 'donald trump'")
    try:
        tone_dist = client.get_tone_distribution(
            query="donald trump",
            timespan="1week"
        )
        
        if tone_dist and 'data' in tone_dist:
            print("Tone distribution (bins):")
            for i, bin_data in enumerate(tone_dist['data'][:5]):
                tone_range = bin_data.get('bin', 'Unknown')
                count = bin_data.get('count', 0)
                print(f"  {tone_range}: {count} articles")
        else:
            print("No tone data found")
            
    except Exception as e:
        print(f"Error in tone analysis: {e}")
    
    # 4. Country-specific search
    print("\n4. Country-specific Search - 'ukraine' from Germany")
    try:
        country_results = client.search_by_country(
            query="ukraine",
            country="germany",
            max_records=3,
            timespan="3days"
        )
        
        if country_results and 'articles' in country_results:
            print(f"Found {len(country_results['articles'])} German articles about Ukraine")
            for article in country_results['articles'][:2]:
                print(f"  - {article.get('title', 'No title')}")
        else:
            print("No country-specific articles found")
            
    except Exception as e:
        print(f"Error in country search: {e}")
    
    # 5. Image search
    print("\n5. Image Search - disaster images")
    try:
        image_results = client.search_images(
            query='(imagetag:"flood" OR imagetag:"fire" OR imagetag:"earthquake")',
            max_records=5,
            timespan="3days"
        )
        
        if image_results and 'images' in image_results:
            print(f"Found {len(image_results['images'])} disaster images")
            for i, image in enumerate(image_results['images'][:3], 1):
                print(f"  {i}. {image.get('url', 'No URL')}")
                print(f"     Context: {image.get('contextText', 'No context')[:100]}...")
        else:
            print("No disaster images found")
            
    except Exception as e:
        print(f"Error in image search: {e}")
    
    # 6. Complex query with operators
    print("\n6. Complex Query - Recent positive news about renewable energy")
    try:
        complex_results = client.search_articles(
            query='("renewable energy" OR "solar power" OR "wind energy") tone>3',
            max_records=5,
            timespan="1week",
            sort="tonedesc"
        )
        
        if complex_results and 'articles' in complex_results:
            print(f"Found {len(complex_results['articles'])} positive renewable energy articles")
            for article in complex_results['articles'][:3]:
                title = article.get('title', 'No title')
                tone = article.get('tone', 0)
                print(f"  - {title} (tone: {tone})")
        else:
            print("No positive renewable energy articles found")
            
    except Exception as e:
        print(f"Error in complex query: {e}")


def build_gdelt_query(**kwargs) -> str:
    """
    Helper function to build GDELT queries with various operators
    
    Supported operators:
    - keywords: List of keywords/phrases
    - or_keywords: List of keywords to OR together
    - exclude: Keywords to exclude (-)
    - domain: Specific domain
    - source_country: Source country
    - source_lang: Source language
    - theme: GDELT theme
    - tone_gt: Tone greater than
    - tone_lt: Tone less than
    - near: Proximity search (dict with 'distance' and 'words')
    - repeat: Word repetition (dict with 'count' and 'word')
    """
    
    query_parts = []
    
    # Basic keywords
    if 'keywords' in kwargs:
        for keyword in kwargs['keywords']:
            if ' ' in keyword:  # Phrase
                query_parts.append(f'"{keyword}"')
            else:
                query_parts.append(keyword)
    
    # OR keywords
    if 'or_keywords' in kwargs:
        or_part = " OR ".join(kwargs['or_keywords'])
        query_parts.append(f"({or_part})")
    
    # Exclude keywords
    if 'exclude' in kwargs:
        for exclude_word in kwargs['exclude']:
            query_parts.append(f"-{exclude_word}")
    
    # Domain
    if 'domain' in kwargs:
        query_parts.append(f"domain:{kwargs['domain']}")
    
    # Source country
    if 'source_country' in kwargs:
        country = kwargs['source_country'].lower().replace(' ', '')
        query_parts.append(f"sourcecountry:{country}")
    
    # Source language
    if 'source_lang' in kwargs:
        query_parts.append(f"sourcelang:{kwargs['source_lang']}")
    
    # Theme
    if 'theme' in kwargs:
        query_parts.append(f"theme:{kwargs['theme']}")
    
    # Tone filters
    if 'tone_gt' in kwargs:
        query_parts.append(f"tone>{kwargs['tone_gt']}")
    if 'tone_lt' in kwargs:
        query_parts.append(f"tone<{kwargs['tone_lt']}")
    
    # Proximity search
    if 'near' in kwargs:
        near_data = kwargs['near']
        distance = near_data['distance']
        words = near_data['words']
        query_parts.append(f'near{distance}:"{words}"')
    
    # Word repetition
    if 'repeat' in kwargs:
        repeat_data = kwargs['repeat']
        count = repeat_data['count']
        word = repeat_data['word']
        query_parts.append(f'repeat{count}:"{word}"')
    
    return " ".join(query_parts)


if __name__ == "__main__":
    # Run the demo
    demo_gdelt_api()
    
    print("\n" + "=" * 50)
    print("Query Builder Examples:")
    
    # Example 1: Complex query about climate change
    climate_query = build_gdelt_query(
        or_keywords=["climate change", "global warming", "carbon emissions"],
        source_country="united states",
        tone_gt=0,  # Positive tone only
        exclude=["hoax", "fake"]
    )
    print(f"\nClimate Query: {climate_query}")
    
    # Example 2: Technology news from specific domains
    tech_query = build_gdelt_query(
        keywords=["artificial intelligence", "machine learning"],
        or_keywords=["breakthrough", "innovation", "advancement"],
        domain="techcrunch.com"
    )
    print(f"Tech Query: {tech_query}")
    
    # Example 3: Proximity search
    proximity_query = build_gdelt_query(
        near={"distance": 10, "words": "biden putin"},
        source_lang="english",
        tone_lt=0  # Negative tone
    )
    print(f"Proximity Query: {proximity_query}")