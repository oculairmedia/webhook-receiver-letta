#!/usr/bin/env python3
"""
arXiv API Integration for Research Paper Context
Conservative triggering to avoid unnecessary API calls
"""

import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time

class ArxivIntegration:
    """Integrates with arXiv API for research paper context"""
    
    def __init__(self):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
        self.base_url = "http://export.arxiv.org/api/query"
        self.max_results = 5  # Conservative limit
        self.max_results_per_category = 3  # Even more conservative per category
        
        # Very specific keywords that indicate research/academic queries
        self.research_keywords = {
            'strong': [
                'arxiv', 'preprint', 'research paper', 'academic paper', 'peer review',
                'journal article', 'publication', 'study shows', 'research shows',
                'empirical study', 'systematic review', 'meta-analysis', 'literature review',
                'experimental results', 'methodology', 'hypothesis', 'theoretical framework',
                'recent advances in', 'state of the art', 'cutting edge research',
                'breakthrough in', 'scientific discovery', 'research breakthrough'
            ],
            'medium': [
                'algorithm', 'machine learning', 'deep learning', 'neural network',
                'artificial intelligence', 'computer vision', 'natural language processing',
                'quantum computing', 'cryptography', 'blockchain research',
                'physics', 'mathematics', 'statistics', 'computational',
                'optimization', 'simulation', 'modeling', 'analysis',
                'theorem', 'proof', 'mathematical', 'statistical'
            ],
            'weak': [
                'latest research', 'recent developments', 'new findings',
                'scientific', 'academic', 'technical advances',
                'innovations', 'discoveries', 'experiments'
            ]
        }
        
        # Explicit exclusions - never trigger for these
        self.exclusions = [
            'how to', 'tutorial', 'guide', 'best practices', 'tips',
            'what is', 'explain', 'definition', 'meaning',
            'stock market', 'price', 'news', 'weather', 'sports',
            'celebrity', 'entertainment', 'politics', 'election',
            'restaurant', 'recipe', 'travel', 'shopping',
            'today', 'yesterday', 'tomorrow', 'current events'
        ]
        
        # arXiv subject categories for targeted search
        self.subject_categories = {
            'cs': 'Computer Science',
            'math': 'Mathematics', 
            'physics': 'Physics',
            'stat': 'Statistics',
            'eess': 'Electrical Engineering and Systems Science',
            'econ': 'Economics',
            'q-bio': 'Quantitative Biology',
            'q-fin': 'Quantitative Finance'
        }
    
    def should_trigger_arxiv_search(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if query should trigger arXiv search.
        Returns: (should_trigger, extracted_query)
        """
        query_lower = query.lower().strip()

        # Immediate exclusions
        for exclusion in self.exclusions:
            if exclusion in query_lower:
                self.logger.info(f"ArXiv trigger excluded for query: '{query}' (reason: contains '{exclusion}')")
                return False, None

        # Calculate relevance score
        score = 0.0
        
        # Strong indicators
        for keyword in self.research_keywords['strong']:
            if keyword in query_lower:
                score += 0.4
        
        # Medium indicators
        for keyword in self.research_keywords['medium']:
            if keyword in query_lower:
                score += 0.25

        # Weak indicators
        for keyword in self.research_keywords['weak']:
            if keyword in query_lower:
                score += 0.1

        # Decision threshold
        threshold = 0.4
        should_trigger = score >= threshold
        
        if should_trigger:
            self.logger.info(f"ArXiv trigger activated for query: '{query}' (score: {score:.2f})")
            return True, query  # Return the original query
        else:
            self.logger.info(f"ArXiv trigger not activated for query: '{query}' (score: {score:.2f})")
            return False, None
    
    def detect_research_category(self, query: str) -> Optional[str]:
        """Detect which arXiv category is most relevant"""
        self.logger.debug(f"Detecting research category for query: {query}")
        query_lower = query.lower()
        
        category_keywords = {
            'cs': ['computer science', 'algorithm', 'programming', 'software', 'AI', 'ML', 
                   'machine learning', 'deep learning', 'neural network', 'NLP', 
                   'computer vision', 'robotics', 'data mining', 'cybersecurity'],
            'math': ['mathematics', 'mathematical', 'theorem', 'proof', 'algebra', 
                     'calculus', 'geometry', 'topology', 'number theory', 'analysis'],
            'physics': ['physics', 'quantum', 'particle', 'cosmology', 'relativity',
                       'thermodynamics', 'mechanics', 'optics', 'condensed matter'],
            'stat': ['statistics', 'statistical', 'probability', 'bayesian', 
                     'regression', 'hypothesis testing', 'data analysis'],
            'eess': ['signal processing', 'image processing', 'control systems',
                     'electrical engineering', 'communications'],
            'q-bio': ['biology', 'bioinformatics', 'genomics', 'neuroscience', 
                      'molecular biology', 'computational biology'],
            'q-fin': ['finance', 'financial', 'economics', 'trading', 'risk management',
                      'quantitative finance', 'portfolio optimization']
        }
        
        # Score each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])[0]
            self.logger.debug(f"Detected category: {best_category} (scores: {category_scores})")
            return best_category
        
        self.logger.debug("No category detected, defaulting to 'cs'")
        return 'cs'  # Default to computer science
    
    def search_arxiv(self, query: str, category: Optional[str] = None, max_results: int = None) -> Dict:
        """Search arXiv for relevant papers with fallback strategy"""
        try:
            if max_results is None:
                max_results = self.max_results
            
            self.logger.info(f"Starting arXiv search for query: '{query}' (category: {category}, max_results: {max_results})")
            
            # First attempt: search with category if provided
            if category:
                self.logger.debug(f"Attempting category-specific search (category: {category})")
                result = self._perform_arxiv_search(query, category, max_results)
                
                # Check if we got results
                if result['success'] and result.get('papers') and len(result['papers']) > 0:
                    self.logger.info(f"Category search successful: {len(result['papers'])} papers found")
                    return result
                else:
                    self.logger.info(f"Category search returned no papers, falling back to general search")
            
            # Fallback: search without category restriction
            self.logger.debug(f"Performing general search (no category filter)")
            return self._perform_arxiv_search(query, None, max_results)
            
        except Exception as e:
            self.logger.error(f"Exception in search_arxiv: {e}")
            return {
                'success': False,
                'error': f'arXiv search failed: {str(e)}',
                'papers': []
            }
    
    def _perform_arxiv_search(self, query: str, category: Optional[str], max_results: int) -> Dict:
        """Perform the actual arXiv API search"""
        try:
            # Build search query
            search_terms = self._build_search_terms(query, category)
            
            params = {
                'search_query': search_terms,
                'start': 0,
                'max_results': max_results,
                'sortBy': 'submittedDate',  # Most recent first
                'sortOrder': 'descending'
            }
            
            full_url = f"{self.base_url}?{requests.compat.urlencode(params)}"
            self.logger.debug(f"Searching with query: {search_terms}")
            self.logger.debug(f"Category: {category}, Max results: {max_results}")
            self.logger.debug(f"Full URL: {full_url}")
            
            # Improved network handling with longer timeout and retry logic
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            response = session.get(self.base_url, params=params, timeout=30)
            self.logger.info(f"ArXiv API response: status={response.status_code}, length={len(response.text)}")
            
            if len(response.text) < 2000:  # If response is short, log it for debugging
                self.logger.debug(f"Response content: {response.text}")
            
            response.raise_for_status()
            
            return self._parse_arxiv_response(response.text, query)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"ArXiv API request failed: {e}")
            return {
                'success': False,
                'error': f'ArXiv API request failed: {str(e)}',
                'papers': []
            }
        except Exception as e:
            self.logger.error(f"Unexpected error in _perform_arxiv_search: {e}")
            return {
                'success': False,
                'error': f'ArXiv search error: {str(e)}',
                'papers': []
            }
    
    def _build_search_terms(self, query: str, category: Optional[str] = None) -> str:
        """Build arXiv search query from user query"""
        # Extract key terms from query
        words = query.lower().split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'is', 'are', 'was', 'were', 'how', 'what', 'when',
                     'where', 'why', 'which', 'that', 'this', 'these', 'those'}
        
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Build search query
        if category:
            # Search within specific category
            search_query = f"cat:{category} AND ({' OR '.join(key_terms[:5])})"
        else:
            # General search
            search_query = ' OR '.join(key_terms[:5])
        
        return search_query
    
    def _parse_arxiv_response(self, xml_content: str, original_query: str) -> Dict:
        """Parse arXiv API XML response"""
        try:
            self.logger.debug(f"Parsing XML response of length {len(xml_content)}")
            root = ET.fromstring(xml_content)
            
            # XML namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            papers = []
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    # Extract paper data
                    title = entry.find('atom:title', namespaces)
                    title_text = title.text.strip().replace('\n', ' ') if title is not None else 'No title'
                    
                    summary = entry.find('atom:summary', namespaces)
                    summary_text = summary.text.strip().replace('\n', ' ')[:300] + '...' if summary is not None else 'No summary'
                    
                    published = entry.find('atom:published', namespaces)
                    pub_date = published.text[:10] if published is not None else 'Unknown'
                    
                    # Get arXiv ID and URL
                    arxiv_id = entry.find('atom:id', namespaces)
                    arxiv_url = arxiv_id.text if arxiv_id is not None else ''
                    
                    # Extract authors
                    authors = []
                    for author in entry.findall('atom:author', namespaces):
                        name = author.find('atom:name', namespaces)
                        if name is not None:
                            authors.append(name.text)
                    
                    author_text = ', '.join(authors[:3])  # First 3 authors
                    if len(authors) > 3:
                        author_text += ' et al.'
                    
                    # Get categories
                    categories = []
                    for category in entry.findall('atom:category', namespaces):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    
                    paper = {
                        'title': title_text,
                        'summary': summary_text,
                        'authors': author_text,
                        'published': pub_date,
                        'url': arxiv_url,
                        'categories': categories[:3]  # Limit categories
                    }
                    
                    papers.append(paper)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing entry: {e}")
                    continue
            
            self.logger.info(f"Successfully parsed {len(papers)} papers from ArXiv response")
            return {
                'success': True,
                'papers': papers,
                'total_found': len(papers),
                'query': original_query
            }
            
        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
            return {
                'success': False,
                'error': f'XML parsing error: {str(e)}',
                'papers': []
            }
    
    def generate_arxiv_context(self, query: str) -> Dict:
        """Generate context from arXiv search results"""
        # Check if we should search arXiv
        should_search, search_query = self.should_trigger_arxiv_search(query)
        
        if not should_search:
            return {
                'success': False,
                'reason': 'Not triggered',
                'context': '',
                'papers_found': 0
            }
        
        # Detect research category
        category = self.detect_research_category(query)
        
        # Initialize confidence and reason variables
        confidence = 0.8  # Default confidence score
        reason = 'arXiv search completed'
        
        # Search arXiv
        search_results = self.search_arxiv(query, category)
        
        if not search_results['success']:
            return {
                'success': False,
                'error': search_results['error'],
                'context': '',
                'papers_found': 0
            }
        
        papers = search_results['papers']
        
        if not papers:
            return {
                'success': True,  # Success but no papers found
                'reason': 'No relevant papers found',
                'context': f"**Recent Research Papers (arXiv)**\n\n*No papers found for query: {query}*\n*This may indicate the query is too specific or uses different terminology.*",
                'papers_found': 0,
                'category': category,
                'confidence': confidence
            }
        
        # Generate context text
        context_parts = [
            f"**Recent Research Papers (arXiv)**",
            f"",
            f"*Found {len(papers)} recent papers relevant to: {query}*",
            f"*Search confidence: {confidence:.2f}*",
            f""
        ]
        
        for i, paper in enumerate(papers, 1):
            context_parts.extend([
                f"**{i}. {paper['title']}**",
                f"   Authors: {paper['authors']}",
                f"   Published: {paper['published']}",
                f"   Categories: {', '.join(paper['categories'])}",
                f"   Summary: {paper['summary']}",
                f"   URL: {paper['url']}",
                f""
            ])
        
        context = "\n".join(context_parts)
        
        # Clean and validate content for API compatibility
        cleaned_context = self.clean_content_for_api(context)
        
        self.logger.info(f"ArXiv search completed: {len(papers)} papers found, context length: {len(cleaned_context)} chars")
        
        return {
            'success': True,
            'context': cleaned_context,
            'papers_found': len(papers),
            'category': category,
            'confidence': confidence,
            'reason': reason
        }

    def clean_content_for_api(self, content: str) -> str:
        """
        Clean and sanitize content for Letta API compatibility
        Removes problematic characters that might cause 400 errors
        """
        try:
            self.logger.debug(f"Cleaning content of length: {len(content)}")
            
            # Remove or replace problematic characters
            cleaned = content
            
            # Replace smart quotes and other Unicode issues
            replacements = {
                '"': '"',  # Left double quotation mark
                '"': '"',  # Right double quotation mark
                ''': "'",  # Left single quotation mark
                ''': "'",  # Right single quotation mark
                '–': '-',  # En dash
                '—': '-',  # Em dash
                '…': '...',  # Horizontal ellipsis
                '\u00a0': ' ',  # Non-breaking space
                '\u2028': '\n',  # Line separator
                '\u2029': '\n\n',  # Paragraph separator
                # Common Latin characters that might cause API issues
                'Ł': 'L',  # Latin capital letter L with stroke
                'ł': 'l',  # Latin small letter l with stroke
                'ń': 'n',  # Latin small letter n with acute
                'ó': 'o',  # Latin small letter o with acute
                'ś': 's',  # Latin small letter s with acute
                'ć': 'c',  # Latin small letter c with acute
                'ż': 'z',  # Latin small letter z with dot above
                'ź': 'z',  # Latin small letter z with acute
                'ą': 'a',  # Latin small letter a with ogonek
                'ę': 'e',  # Latin small letter e with ogonek
            }
            
            for old, new in replacements.items():
                cleaned = cleaned.replace(old, new)
            
            # Remove control characters except common whitespace
            cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
            
            # Normalize excessive whitespace
            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)  # Max 2 consecutive newlines
            cleaned = re.sub(r' {2,}', ' ', cleaned)  # Collapse multiple spaces
            cleaned = cleaned.strip()
            
            # Ensure content is valid UTF-8 and JSON-serializable
            try:
                json.dumps(cleaned)
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                self.logger.warning(f"JSON serialization issue: {e}")
                # Try to encode/decode to fix encoding issues
                cleaned = cleaned.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Limit size if too large (Letta API might have limits)
            max_length = 50000  # Conservative limit
            if len(cleaned) > max_length:
                self.logger.warning(f"Content truncated from {len(cleaned)} to {max_length} characters")
                cleaned = cleaned[:max_length] + "\n\n[Content truncated for API compatibility]"
            
            self.logger.debug(f"Content cleaned: {len(content)} -> {len(cleaned)} characters")
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning content: {e}")
            # Return safe fallback
            return "Error processing arXiv content - content sanitization failed"

    def log_api_attempt(self, content: str, error: Exception = None):
        """
        Log detailed information about API attempts for debugging
        """
        try:
            content_info = {
                'length': len(content),
                'line_count': content.count('\n'),
                'has_unicode': any(ord(c) > 127 for c in content),
                'json_serializable': True
            }
            
            # Test JSON serialization
            try:
                json.dumps(content)
            except Exception:
                content_info['json_serializable'] = False
            
            self.logger.info(f"API Content Info: {content_info}")
            
            if error:
                self.logger.error(f"API Error Details: {type(error).__name__}: {str(error)}")
                
                # Log sample of problematic content
                sample = content[:500] + "..." if len(content) > 500 else content
                self.logger.debug(f"Content sample: {repr(sample)}")
                
        except Exception as log_error:
            self.logger.error(f"Error logging API attempt: {log_error}")


def test_arxiv_integration():
    """Test the arXiv integration with various queries"""
    arxiv = ArxivIntegration()
    
    test_queries = [
        # Should trigger
        "latest research on quantum computing algorithms",
        "recent advances in machine learning optimization",
        "new deep learning architectures for computer vision",
        "breakthrough in natural language processing transformers",
        
        # Should NOT trigger
        "how to cook pasta",
        "what happened in the stock market today",
        "best practices for database design",
        "current weather in New York",
        "tell me about yourself"
    ]
    
    print("Testing arXiv Integration")
    print("=" * 50)
    
    for query in test_queries:
        should_trigger, reason, confidence = arxiv.should_trigger_arxiv_search(query)
        print(f"\nQuery: '{query}'")
        print(f"Trigger: {should_trigger}")
        print(f"Confidence: {confidence:.3f}")
        print(f"Reason: {reason}")
        
        if should_trigger:
            category = arxiv.detect_research_category(query)
            print(f"Category: {category}")


if __name__ == "__main__":
    test_arxiv_integration()