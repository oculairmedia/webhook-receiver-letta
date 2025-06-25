# GDELT API Integration for Webhook System

## Overview

This integration adds real-time global news context to your webhook system using the [GDELT Project](https://www.gdeltproject.org/) Full Text Search API. GDELT monitors news coverage from around the world in 65+ languages and provides powerful search capabilities for articles, timelines, sentiment analysis, and image search.

## Features

### 🌍 Global News Coverage
- **65+ Languages**: Search across news in 65 languages with automatic English translation
- **Real-time Data**: Access news from the last 3 months with 15-minute granularity
- **Global Perspective**: Get news from outlets worldwide, not just Western/English sources

### 🔍 Advanced Search Capabilities
- **Smart Triggering**: Automatically detects when user queries need global news context
- **Category Classification**: Organizes searches into categories (politics, conflicts, economics, etc.)
- **Complex Queries**: Support for boolean logic, proximity search, tone filtering, and more

### 📊 Rich Data Analysis
- **Sentiment Analysis**: Get tone/sentiment distribution of coverage
- **Timeline Analysis**: Track news volume and sentiment over time
- **Image Search**: Find relevant news images using AI-powered visual recognition
- **Trend Detection**: Identify increasing/decreasing coverage patterns

## File Structure

```
├── gdelt_api_client.py                    # Core GDELT API client
├── test_gdelt_api.py                      # Test suite for API functionality
├── demo_gdelt_webhook_integration.py      # Webhook integration demo
└── README_GDELT_INTEGRATION.md           # This documentation
```

## Quick Start

### 1. Test Basic GDELT API Functionality

```bash
# Test basic API calls
python test_gdelt_api.py basic

# Test advanced queries
python test_gdelt_api.py advanced

# Test image search
python test_gdelt_api.py images

# Test sentiment analysis
python test_gdelt_api.py tone

# Interactive demo
python test_gdelt_api.py interactive
```

### 2. Test Webhook Integration

```bash
# Test standalone GDELT integration
python demo_gdelt_webhook_integration.py standalone

# Test with webhook server (requires server running)
python demo_gdelt_webhook_integration.py webhook
```

### 3. Integration with Your Webhook

```python
from gdelt_api_client import GDELTAPIClient
from demo_gdelt_webhook_integration import GDELTWebhookIntegration

# Initialize integration
integration = GDELTWebhookIntegration("http://localhost:5005/webhook/letta")

# Check if message should trigger GDELT search
message = "What's happening in Ukraine today?"
should_trigger, category = integration.should_trigger_gdelt_search(message)

if should_trigger:
    # Generate GDELT context
    context = integration.generate_gdelt_context(message, category)
    print(context['context'])
```

## API Client Usage

### Basic Article Search

```python
from gdelt_api_client import GDELTAPIClient

client = GDELTAPIClient()

# Search for recent articles
results = client.search_articles(
    query="climate change",
    max_records=10,
    timespan="24h"
)

for article in results['articles']:
    print(f"Title: {article['title']}")
    print(f"Source: {article['domain']}")
    print(f"Date: {article['seendate']}")
    print(f"Tone: {article.get('tone', 'N/A')}")
```

### Advanced Query Building

```python
from gdelt_api_client import build_gdelt_query

# Build complex query
query = build_gdelt_query(
    or_keywords=["climate change", "global warming"],
    source_country="united states",
    exclude=["hoax"],
    tone_gt=2,  # Positive articles only
    domain="cnn.com"
)

results = client.search_articles(query=query, timespan="1week")
```

### Timeline Analysis

```python
# Get news volume timeline
timeline = client.search_news_volume_timeline(
    query="artificial intelligence",
    timespan="1week",
    smooth=3  # Apply smoothing
)

# Get sentiment timeline
tone_timeline = client.search_tone_timeline(
    query="donald trump",
    timespan="3days"
)
```

### Image Search

```python
# Search for protest images
images = client.search_images(
    query='imagetag:"protest"',
    max_records=20,
    timespan="1week"
)

# Search for disaster images
disaster_images = client.search_images(
    query='(imagetag:"flood" OR imagetag:"fire" OR imagetag:"earthquake")',
    timespan="3days"
)
```

### Country/Language Specific Search

```python
# German news about renewable energy
german_results = client.search_by_country(
    query="renewable energy",
    country="germany",
    timespan="1week"
)

# Spanish language coverage of technology
spanish_results = client.search_by_language(
    query="technology",
    language="spanish",
    timespan="3days"
)
```

## GDELT Query Operators

### Basic Operators
- `"exact phrase"` - Exact phrase search
- `(a OR b)` - Boolean OR
- `-keyword` - Exclude keyword
- `near10:"word1 word2"` - Proximity search (within 10 words)

### Source Filtering
- `domain:cnn.com` - Specific news domain
- `sourcecountry:france` - News from specific country
- `sourcelang:spanish` - News in specific language

### Content Filtering
- `theme:TERROR` - GDELT theme search
- `tone>5` - Articles with positive sentiment
- `tone<-5` - Articles with negative sentiment
- `repeat3:"word"` - Word must appear 3+ times

### Image Search
- `imagetag:"protest"` - Images tagged as containing protests
- `imagewebtag:"climate"` - Images with climate-related captions
- `imagenumfaces>3` - Images with more than 3 faces
- `imagefacetone<-1.5` - Images with sad facial expressions

## Webhook Integration Features

### Smart Triggering

The integration automatically detects when user queries need global news context:

```python
# These queries will trigger GDELT searches:
"What's happening in the world today?"
"Tell me about recent events in Ukraine"
"How are global markets performing?"
"Any recent AI breakthroughs in the news?"

# These won't trigger GDELT searches:
"What's the weather like?"
"How do I cook pasta?"
"What's 2 + 2?"
```

### Categories

Queries are automatically categorized for appropriate search strategies:

- **global_events**: General world news and breaking events
- **geopolitics**: Political and diplomatic news
- **conflicts**: Wars, protests, security issues
- **economics**: Markets, trade, financial news
- **disasters**: Natural disasters and emergencies
- **technology**: Tech news and innovations
- **geographic**: Country or region-specific news

### Context Generation

Generated context includes:

1. **Top Recent Articles** with titles, sources, dates, and sentiment
2. **Trend Analysis** showing increasing/decreasing coverage
3. **Sentiment Summary** of overall tone
4. **Timestamp** for data freshness

Example output:
```
**Recent Global News Context (Conflicts)**

**Top Recent Articles:**
1. **Ukraine Reports New Russian Attacks on Eastern Front**
   Source: reuters.com | Date: 2025-06-01T12:00Z | Tone: negative

2. **Diplomatic Efforts Continue Amid Ongoing Crisis**
   Source: bbc.com | Date: 2025-06-01T11:30Z | Tone: neutral

📈 **Trend**: Coverage volume is increasing significantly

**Sentiment Analysis**: Most coverage (45 articles) has negative tone

*Data from GDELT Global News Database - 2025-06-01 12:09 UTC*
```

## API Limits and Best Practices

### Rate Limits
- GDELT API is free but has reasonable use policies
- No explicit rate limits published, but avoid excessive requests
- Use timespan parameters to limit data volume

### Best Practices
1. **Cache Results**: Store recent results to avoid repeated queries
2. **Reasonable Timespans**: Use 24h-1week for most queries
3. **Smart Triggering**: Only query when relevant to user intent
4. **Error Handling**: Always handle API timeouts and failures gracefully

### Performance Tips
```python
# Good: Specific, focused query
query = "ukraine conflict" 
timespan = "24h"
max_records = 10

# Avoid: Too broad, too much data
query = "news"
timespan = "3months" 
max_records = 250
```

## Error Handling

```python
try:
    results = client.search_articles(query="test", timespan="24h")
    if results and 'articles' in results:
        # Process results
        pass
    else:
        print("No articles found or unexpected format")
except Exception as e:
    print(f"GDELT API error: {e}")
    # Fallback to other data sources or cached results
```

## Integration with Existing Webhook

To add GDELT to your existing webhook receiver:

1. **Import the integration**:
```python
from demo_gdelt_webhook_integration import GDELTWebhookIntegration
```

2. **Initialize in your webhook handler**:
```python
gdelt_integration = GDELTWebhookIntegration()
```

3. **Check for trigger and generate context**:
```python
should_trigger, category = gdelt_integration.should_trigger_gdelt_search(user_message)
if should_trigger:
    gdelt_context = gdelt_integration.generate_gdelt_context(user_message, category)
    # Add to your response context
```

4. **Include in LLM prompt**:
```python
if gdelt_context and gdelt_context['success']:
    enhanced_prompt = f"{user_message}\n\nRecent Global News Context:\n{gdelt_context['context']}"
```

## Troubleshooting

### Common Issues

1. **No Results Returned**
   - Check if query is too specific
   - Try broader timespan (3days instead of 24h)
   - Verify internet connection

2. **API Timeout**
   - Reduce max_records parameter
   - Use shorter timespan
   - Add retry logic with exponential backoff

3. **Unexpected Response Format**
   - GDELT API responses can vary by query type
   - Always check for expected keys before accessing
   - Log unexpected responses for debugging

### Debug Mode

Enable debug output:
```python
client = GDELTAPIClient(timeout=30)
# Add logging to see request URLs and responses
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples and Use Cases

### Crisis Monitoring
```python
# Monitor breaking news globally
crisis_query = build_gdelt_query(
    or_keywords=["breaking news", "emergency", "crisis"],
    tone_lt=-3,  # Very negative events
    timespan="1h"  # Very recent
)
```

### Sentiment Tracking
```python
# Track sentiment about a political figure
sentiment_timeline = client.search_tone_timeline(
    query="president biden",
    timespan="1week",
    smooth=5
)
```

### Regional Analysis
```python
# Compare coverage between countries
us_coverage = client.search_by_country("trade war", "usa", "3days")
china_coverage = client.search_by_country("trade war", "china", "3days")
```

### Visual News Analysis
```python
# Find images of climate protests
protest_images = client.search_images(
    query='(imagetag:"protest" AND imagewebtag:"climate")',
    timespan="1week"
)
```

## Contributing

To extend the GDELT integration:

1. **Add new trigger keywords** in `GDELTWebhookIntegration.trigger_keywords`
2. **Create new query builders** in `_build_search_query` method
3. **Add new response formatters** in `_format_gdelt_context` method
4. **Test thoroughly** with `test_gdelt_api.py`

## Resources

- [GDELT Project Homepage](https://www.gdeltproject.org/)
- [GDELT DOC 2.0 API Documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)
- [GDELT Query Examples](https://blog.gdeltproject.org/gdelt-global-knowledge-graph-codebook/)
- [GDELT Theme List](http://data.gdeltproject.org/api/v2/guides/LOOKUP-GKGTHEMES.TXT)
- [GDELT Country Codes](http://data.gdeltproject.org/api/v2/guides/LOOKUP-COUNTRIES.TXT)