# Context Retrieval Simulation Suite

## Overview

The simulation suite tests the same context retrieval logic used by the webhook receiver, allowing you to analyze how the system responds to different query types without actually triggering webhooks.

## Key Findings

### Memory Retrieval from Graphiti

The system retrieves:
- **Default: 8 nodes and 20 facts** from Graphiti per query
- Configurable via environment variables:
  - `GRAPHITI_MAX_NODES` (default: 8)
  - `GRAPHITI_MAX_FACTS` (default: 20)
- Can be overridden per request in webhook payload

### Data Sources

1. **Graphiti** - Always used for knowledge graph queries
2. **BigQuery GDELT** - Triggered for global events/news queries
3. **GDELT API** - Triggered for current events in specific categories
4. **External Query API** - Used for general knowledge questions

## Simulation Suite Features

### 1. Test Query Categories

The suite includes pre-defined test queries in 5 categories:
- **Technical**: Programming, architecture, best practices
- **Current Events**: News, market updates, geopolitics
- **Conversational**: General chat, opinions, explanations
- **Scientific**: Research, discoveries, technical concepts
- **Business**: Management, strategy, KPIs

### 2. Metrics Collected

For each query, the simulation tracks:
- Number of nodes/facts retrieved from Graphiti
- Context length from each source
- Retrieval time for each source
- Which sources were triggered
- Total context size and retrieval time

### 3. Output Formats

The simulation generates:
- **JSON**: Raw simulation results with all data
- **CSV**: Summary table for analysis
- **Markdown Report**: Human-readable analysis with insights
- **Visualizations**: Charts showing performance patterns

## Usage

### Basic Simulation

```bash
python simulation_suite.py
```

### Custom Parameters

```bash
# Test specific categories
python simulation_suite.py --categories technical current_events

# Limit queries per category
python simulation_suite.py --queries-per-category 3

# Custom output directory
python simulation_suite.py --output-dir my_results

# Custom Graphiti URL
python simulation_suite.py --graphiti-url http://localhost:8001/api
```

### Quick Test

Run a limited test with just a few queries:

```bash
python test_simulation.py
```

## Environment Configuration

Configure the simulation behavior with these environment variables:

```bash
# Graphiti settings
export GRAPHITI_URL="http://localhost:8001/api"
export GRAPHITI_MAX_NODES=10
export GRAPHITI_MAX_FACTS=25

# Enable/disable integrations
export BIGQUERY_ENABLED=true
export GDELT_API_ENABLED=true
export EXTERNAL_QUERY_ENABLED=true

# Performance tuning
export QUERY_REFINEMENT_ENABLED=true
export QUERY_REFINEMENT_TEMPERATURE=0.3
```

## Analysis Insights

The simulation helps answer:

1. **How much context is retrieved per query type?**
   - Technical queries: ~2000-4000 chars
   - Current events: ~3000-6000 chars (with GDELT/BigQuery)
   - Conversational: ~500-1500 chars

2. **Which sources are used for different queries?**
   - Graphiti: 100% (always used)
   - BigQuery: ~30-40% (current events, global topics)
   - GDELT: ~20-30% (news, events, geopolitics)

3. **What are the performance characteristics?**
   - Graphiti: 0.5-2s average
   - BigQuery: 1-3s when triggered
   - GDELT: 0.5-1.5s when triggered
   - Total: 1-5s depending on sources used

4. **How does context accumulate over conversations?**
   - The system uses cumulative context building
   - Maximum context length: 6000 chars per block
   - Older entries are truncated when limit reached

## Extending the Simulation

### Adding Custom Queries

```python
simulator = ContextRetrievalSimulator()
simulator.test_queries["my_category"] = [
    "My custom query 1",
    "My custom query 2"
]
```

### Custom Analysis

```python
# Access raw results
for result in simulator.results:
    print(f"Query: {result.query_text}")
    print(f"Graphiti nodes: {result.graphiti_nodes_retrieved}")
    print(f"Total context: {result.total_context_length}")
```

## Visualization Examples

The suite generates several visualizations:

1. **Context Length by Category**: Box plots showing distribution
2. **Retrieval Times**: Histograms for each source
3. **Source Usage by Category**: Bar charts showing which sources are triggered

## Best Practices

1. **Run simulations before deploying** to understand system behavior
2. **Monitor retrieval times** to ensure acceptable performance
3. **Adjust MAX_NODES/MAX_FACTS** based on your needs
4. **Use category analysis** to optimize for your use case
5. **Check context lengths** to ensure they fit within LLM limits

## Troubleshooting

If simulations fail:

1. Check Graphiti service is running
2. Verify environment variables are set correctly
3. Ensure required Python packages are installed
4. Check network connectivity to external services
5. Review error messages in simulation output

## Next Steps

1. Run simulations with your actual query patterns
2. Analyze results to optimize retrieval parameters
3. Use insights to improve context quality
4. Monitor production performance against simulation baselines