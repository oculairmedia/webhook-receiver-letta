#!/usr/bin/env python3
"""
Simulation Suite for Testing Graphiti Context Retrieval Logic
Tests the same logic as the webhook receiver but generates outputs for analysis
"""

import json
import os
import sys
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, UTC
import time
import csv
from dataclasses import dataclass, asdict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Import the core retrieval logic
try:
    from production_improved_retrieval import (
        generate_context_from_prompt,
        DEFAULT_GRAPHITI_URL,
        DEFAULT_MAX_NODES,
        DEFAULT_MAX_FACTS
    )
    USING_IMPROVED_RETRIEVAL = True
except ImportError:
    from retrieve_context import (
        generate_context_from_prompt,
        DEFAULT_GRAPHITI_URL,
        DEFAULT_MAX_NODES,
        DEFAULT_MAX_FACTS
    )
    USING_IMPROVED_RETRIEVAL = False

# Import BigQuery integration if available
# COMMENTED OUT: BigQuery is expensive, so we're disabling it for testing
# try:
#     from bigquery_gdelt_integration import (
#         generate_bigquery_context,
#         should_invoke_bigquery
#     )
#     BIGQUERY_AVAILABLE = True
# except ImportError:
#     BIGQUERY_AVAILABLE = False
#     def generate_bigquery_context(user_message: str, agent_context: Optional[str] = None) -> Optional[str]:
#         return None
#     def should_invoke_bigquery(user_message: str, agent_context: Optional[str] = None) -> bool:
#         return False

# Force BigQuery to be unavailable for testing
BIGQUERY_AVAILABLE = False
def generate_bigquery_context(user_message: str, agent_context: Optional[str] = None) -> Optional[str]:
    return None
def should_invoke_bigquery(user_message: str, agent_context: Optional[str] = None) -> bool:
    return False

# Import GDELT API integration if available
try:
    from demo_gdelt_webhook_integration import GDELTWebhookIntegration
    gdelt_integration = GDELTWebhookIntegration()
    GDELT_AVAILABLE = True
except ImportError:
    GDELT_AVAILABLE = False
    class DummyGDELTIntegration:
        def should_trigger_gdelt_search(self, message: str) -> tuple[bool, str]:
            return False, ''
        def generate_gdelt_context(self, message: str, category: str) -> dict:
            return {'success': False, 'error': 'GDELT integration not available'}
    gdelt_integration = DummyGDELTIntegration()

# Import arXiv integration if available
try:
    from arxiv_integration import ArxivIntegration
    arxiv_integration = ArxivIntegration()
    ARXIV_AVAILABLE = True
except ImportError:
    ARXIV_AVAILABLE = False
    class DummyArxivIntegration:
        def should_trigger_arxiv_search(self, message: str) -> tuple[bool, str, float]:
            return False, 'arXiv integration not available', 0.0
        def generate_arxiv_context(self, message: str) -> dict:
            return {'success': False, 'error': 'arXiv integration not available'}
    arxiv_integration = DummyArxivIntegration()

@dataclass
class SimulationResult:
    """Structure to hold simulation results"""
    query_id: str
    query_text: str
    query_category: str
    timestamp: str
    
    # Graphiti results
    graphiti_nodes_retrieved: int
    graphiti_facts_retrieved: int
    graphiti_context_length: int
    graphiti_retrieval_time: float
    graphiti_context_sample: str
    
    # BigQuery results
    bigquery_triggered: bool
    bigquery_context_length: int
    bigquery_retrieval_time: float
    bigquery_context_sample: str
    
    # GDELT results
    gdelt_triggered: bool
    gdelt_category: str
    gdelt_context_length: int
    gdelt_retrieval_time: float
    gdelt_context_sample: str
    
    # arXiv results
    arxiv_triggered: bool
    arxiv_category: str
    arxiv_papers_found: int
    arxiv_context_length: int
    arxiv_retrieval_time: float
    arxiv_confidence: float
    arxiv_context_sample: str
    
    # Combined metrics
    total_context_length: int
    total_retrieval_time: float
    sources_used: List[str]

class ContextRetrievalSimulator:
    """Simulates context retrieval with various query types"""
    
    def __init__(self, graphiti_url: str = None, output_dir: str = "simulation_results"):
        self.graphiti_url = graphiti_url or os.environ.get("GRAPHITI_URL", DEFAULT_GRAPHITI_URL)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configuration
        self.max_nodes = int(os.environ.get("GRAPHITI_MAX_NODES", DEFAULT_MAX_NODES))
        self.max_facts = int(os.environ.get("GRAPHITI_MAX_FACTS", DEFAULT_MAX_FACTS))
        
        # Test queries organized by category
        self.test_queries = {
            "technical": [
                "How do I implement a REST API in Python?",
                "What are the best practices for database indexing?",
                "Explain microservices architecture patterns",
                "How to optimize React performance?",
                "What is the difference between TCP and UDP?",
                "How to implement authentication in Node.js?",
                "What are Docker container best practices?",
                "How to design a scalable database schema?",
                "Explain GraphQL vs REST API differences",
                "What are Kubernetes deployment strategies?",
                "How to implement caching in web applications?",
                "What are CI/CD pipeline best practices?",
                "How to optimize SQL query performance?",
                "Explain event-driven architecture",
                "What are WebSocket implementation patterns?",
                "How to handle concurrent requests in Python?",
                "What are microservices communication patterns?",
                "How to implement rate limiting in APIs?",
                "What are NoSQL database use cases?",
                "How to secure API endpoints?",
                "What are serverless architecture patterns?",
                "How to implement message queues?",
                "What are load balancing strategies?",
                "How to handle distributed transactions?",
                "What are API versioning best practices?",
                "How to implement logging and monitoring?",
                "What are database migration strategies?",
                "How to optimize frontend bundle size?",
                "What are reactive programming patterns?",
                "How to implement OAuth 2.0?",
                "What are cloud architecture patterns?",
                "How to handle file uploads in web apps?",
                "What are unit testing best practices?",
                "How to implement search functionality?",
                "What are data validation patterns?",
                "How to optimize mobile app performance?",
                "What are API gateway patterns?",
                "How to implement real-time notifications?",
                "What are distributed system patterns?",
                "How to handle error handling in microservices?",
                "What are database connection pooling strategies?",
                "How to implement feature flags?",
                "What are container orchestration patterns?",
                "How to optimize database queries with indexes?",
                "What are event sourcing patterns?"
            ],
            "current_events": [
                "What happened in the stock market today?",
                "Latest developments in AI regulation",
                "Current geopolitical tensions in Eastern Europe",
                "Recent climate change summit outcomes",
                "Today's technology company earnings reports",
                "Breaking news about cryptocurrency markets",
                "What's happening with inflation rates globally?",
                "Latest COVID-19 variant updates and health measures",
                "Recent Supreme Court decisions impact",
                "Current state of the war in Ukraine",
                "Today's oil prices and energy market trends",
                "Latest SpaceX launch news",
                "What happened at the G20 summit?",
                "Current US-China trade relations",
                "Recent natural disasters and their impact",
                "Latest Brexit developments",
                "Today's Federal Reserve announcements",
                "Current Middle East peace talks progress",
                "Recent data breaches and cybersecurity incidents",
                "Latest climate protests and activism",
                "What's new with electric vehicle adoption?",
                "Current housing market trends",
                "Recent Nobel Prize winners announced",
                "Latest developments in renewable energy",
                "Current immigration policy changes",
                "Today's major sports events results",
                "Recent celebrity news and entertainment",
                "Latest scientific discoveries announced",
                "Current labor strikes and union activities",
                "Recent pharmaceutical breakthroughs",
                "What's happening in the gaming industry?",
                "Latest social media platform changes",
                "Current education policy debates",
                "Recent space exploration missions",
                "Today's weather extremes globally",
                "Latest art auction records",
                "Current supply chain disruptions",
                "Recent political elections worldwide",
                "Latest food security concerns",
                "What's new in quantum computing research?",
                "Current refugee crisis updates",
                "Recent corporate mergers and acquisitions",
                "Latest archaeological discoveries",
                "Current mental health awareness initiatives",
                "Recent advances in cancer research"
            ],
            "conversational": [
                "Tell me about yourself",
                "What can you help me with?",
                "How are you today?",
                "What's your opinion on this?",
                "Can you explain that in simpler terms?",
                "Hi",
                "Thanks for your help",
                "I don't understand",
                "Could you repeat that?",
                "What do you mean?",
                "That's interesting",
                "I see",
                "Go on",
                "Really?",
                "Are you sure about that?",
                "Let me think about it",
                "Can we talk about something else?",
                "I need your advice",
                "What would you do?",
                "That makes sense",
                "I disagree",
                "You're right",
                "Maybe",
                "I'm not sure",
                "Can you give me an example?",
                "How does that work?",
                "Why is that important?",
                "What's the difference?",
                "Is that really true?",
                "I've heard differently",
                "That's helpful",
                "I'm confused",
                "Can you clarify?",
                "What are the alternatives?",
                "That's a good point",
                "I hadn't thought of that",
                "Interesting perspective",
                "Tell me more",
                "What else?",
                "Is there anything else I should know?",
                "That's all I needed",
                "One more question",
                "Before we finish",
                "To summarize",
                "In conclusion"
            ],
            "scientific": [
                "Explain quantum computing principles",
                "How does CRISPR gene editing work?",
                "What causes climate change?",
                "Latest discoveries in astronomy",
                "How do vaccines work?",
                "What is dark matter?",
                "How does photosynthesis convert light to energy?",
                "Explain the theory of relativity in simple terms",
                "What are stem cells and their applications?",
                "How do black holes form?",
                "What is the human genome project?",
                "Explain nuclear fusion vs fission",
                "How does the brain process memories?",
                "What causes earthquakes?",
                "How do antibiotics work?",
                "What is machine learning at a molecular level?",
                "Explain the greenhouse effect",
                "How does DNA replication work?",
                "What are exoplanets?",
                "How does the immune system fight viruses?",
                "What is quantum entanglement?",
                "Explain evolution by natural selection",
                "How do neurons communicate?",
                "What causes aging at the cellular level?",
                "How does radiocarbon dating work?",
                "What are gravitational waves?",
                "Explain the water cycle",
                "How do solar panels generate electricity?",
                "What is the Higgs boson?",
                "How does chemotherapy target cancer cells?",
                "What causes volcanic eruptions?",
                "Explain the carbon cycle",
                "How do telescopes see distant galaxies?",
                "What is epigenetics?",
                "How does anesthesia work?",
                "What are tectonic plates?",
                "Explain bioluminescence",
                "How do batteries store energy?",
                "What is the microbiome?",
                "How does radar technology work?",
                "What causes tsunamis?",
                "Explain protein folding",
                "How do MRI machines work?",
                "What is antimatter?",
                "How does coral bleaching occur?"
            ],
            "business": [
                "How to create a business plan?",
                "What are key performance indicators?",
                "Explain supply chain management",
                "Best practices for remote team management",
                "How to analyze market competition?",
                "What is a SWOT analysis?",
                "How to calculate ROI?",
                "Explain venture capital funding rounds",
                "What are lean startup principles?",
                "How to build a sales funnel?",
                "What is customer lifetime value?",
                "Explain B2B vs B2C marketing strategies",
                "How to manage cash flow?",
                "What are OKRs?",
                "How to conduct market research?",
                "Explain the 80/20 rule in business",
                "What is a minimum viable product?",
                "How to price products competitively?",
                "What are business model canvases?",
                "How to build brand awareness?",
                "Explain equity vs debt financing",
                "What is agile project management?",
                "How to negotiate contracts?",
                "What are economies of scale?",
                "How to create a marketing budget?",
                "Explain customer acquisition cost",
                "What is a pivot in business?",
                "How to manage stakeholder expectations?",
                "What are SaaS metrics?",
                "How to build strategic partnerships?",
                "Explain blue ocean strategy",
                "What is corporate governance?",
                "How to handle business crisis?",
                "What are growth hacking techniques?",
                "How to create an exit strategy?",
                "Explain franchising business model",
                "What is intellectual property?",
                "How to scale a startup?",
                "What are merger and acquisition strategies?",
                "How to build company culture?",
                "Explain cost-benefit analysis",
                "What is disruptive innovation?",
                "How to manage inventory?",
                "What are business ethics principles?",
                "How to create a pitch deck?"
            ]
        }
        
        self.results: List[SimulationResult] = []
    
    def simulate_single_query(self, query: str, category: str, query_id: str) -> SimulationResult:
        """Simulate context retrieval for a single query"""
        print(f"\n{'='*80}")
        print(f"Simulating query {query_id}: {query}")
        print(f"Category: {category}")
        print('='*80)
        
        timestamp = datetime.now(UTC).isoformat()
        sources_used = []
        
        # 1. Graphiti Context Retrieval
        print("\n[Graphiti] Retrieving context...")
        start_time = time.time()
        try:
            graphiti_context = generate_context_from_prompt(
                messages=query,  # Single string query
                graphiti_url=self.graphiti_url,
                max_nodes=self.max_nodes,
                max_facts=self.max_facts,
                group_ids=None
            )
            graphiti_retrieval_time = time.time() - start_time
            
            # Parse context to count nodes and facts (simple heuristic)
            nodes_count = graphiti_context.count("Entity:") + graphiti_context.count("Node:")
            facts_count = graphiti_context.count("Fact:") + graphiti_context.count("Relationship:")
            
            graphiti_sample = graphiti_context[:500] + "..." if len(graphiti_context) > 500 else graphiti_context
            sources_used.append("graphiti")
            
            print(f"[Graphiti] Retrieved {nodes_count} nodes, {facts_count} facts in {graphiti_retrieval_time:.2f}s")
            print(f"[Graphiti] Context length: {len(graphiti_context)} chars")
            
        except Exception as e:
            print(f"[Graphiti] Error: {e}")
            graphiti_context = ""
            graphiti_retrieval_time = 0
            nodes_count = 0
            facts_count = 0
            graphiti_sample = f"Error: {str(e)}"
        
        # 2. BigQuery GDELT Context
        bigquery_triggered = False
        bigquery_context = ""
        bigquery_retrieval_time = 0
        bigquery_sample = ""
        
        if BIGQUERY_AVAILABLE:
            print("\n[BigQuery] Checking if query should trigger BigQuery...")
            bigquery_triggered = should_invoke_bigquery(query)
            
            if bigquery_triggered:
                print("[BigQuery] Retrieving context...")
                start_time = time.time()
                try:
                    bigquery_context = generate_bigquery_context(query) or ""
                    bigquery_retrieval_time = time.time() - start_time
                    bigquery_sample = bigquery_context[:500] + "..." if len(bigquery_context) > 500 else bigquery_context
                    if bigquery_context:
                        sources_used.append("bigquery")
                    print(f"[BigQuery] Retrieved context in {bigquery_retrieval_time:.2f}s")
                    print(f"[BigQuery] Context length: {len(bigquery_context)} chars")
                except Exception as e:
                    print(f"[BigQuery] Error: {e}")
                    bigquery_sample = f"Error: {str(e)}"
            else:
                print("[BigQuery] Query does not trigger BigQuery search")
        else:
            print("\n[BigQuery] DISABLED for testing (to avoid costs)")
        
        # 3. GDELT API Context
        gdelt_triggered = False
        gdelt_category = ""
        gdelt_context = ""
        gdelt_retrieval_time = 0
        gdelt_sample = ""
        
        if GDELT_AVAILABLE:
            print("\n[GDELT] Checking if query should trigger GDELT search...")
            gdelt_triggered, gdelt_category = gdelt_integration.should_trigger_gdelt_search(query)
            
            if gdelt_triggered:
                print(f"[GDELT] Retrieving context for category: {gdelt_category}")
                start_time = time.time()
                try:
                    gdelt_result = gdelt_integration.generate_gdelt_context(query, gdelt_category)
                    if gdelt_result.get('success'):
                        gdelt_context = gdelt_result.get('context', '')
                        gdelt_retrieval_time = time.time() - start_time
                        gdelt_sample = gdelt_context[:500] + "..." if len(gdelt_context) > 500 else gdelt_context
                        if gdelt_context:
                            sources_used.append("gdelt")
                        print(f"[GDELT] Retrieved context in {gdelt_retrieval_time:.2f}s")
                        print(f"[GDELT] Context length: {len(gdelt_context)} chars")
                    else:
                        print(f"[GDELT] Failed: {gdelt_result.get('error', 'Unknown error')}")
                        gdelt_sample = f"Error: {gdelt_result.get('error', 'Unknown error')}"
                except Exception as e:
                    print(f"[GDELT] Error: {e}")
                    gdelt_sample = f"Error: {str(e)}"
            else:
                print("[GDELT] Query does not trigger GDELT search")
        
        # 4. arXiv Research Papers Context
        arxiv_triggered = False
        arxiv_category = ""
        arxiv_papers_found = 0
        arxiv_context = ""
        arxiv_retrieval_time = 0
        arxiv_confidence = 0.0
        arxiv_sample = ""
        
        if ARXIV_AVAILABLE:
            print("\n[arXiv] Checking if query should trigger arXiv search...")
            arxiv_triggered, reason, arxiv_confidence = arxiv_integration.should_trigger_arxiv_search(query)
            
            if arxiv_triggered:
                arxiv_category = arxiv_integration.detect_research_category(query)
                print(f"[arXiv] Retrieving papers for category: {arxiv_category} (confidence: {arxiv_confidence:.2f})")
                start_time = time.time()
                try:
                    arxiv_result = arxiv_integration.generate_arxiv_context(query)
                    if arxiv_result.get('success'):
                        arxiv_context = arxiv_result.get('context', '')
                        arxiv_papers_found = arxiv_result.get('papers_found', 0)
                        arxiv_retrieval_time = time.time() - start_time
                        arxiv_sample = arxiv_context[:500] + "..." if len(arxiv_context) > 500 else arxiv_context
                        if arxiv_context:
                            sources_used.append("arxiv")
                        print(f"[arXiv] Retrieved {arxiv_papers_found} papers in {arxiv_retrieval_time:.2f}s")
                        print(f"[arXiv] Context length: {len(arxiv_context)} chars")
                    else:
                        arxiv_retrieval_time = time.time() - start_time
                        error_msg = arxiv_result.get('error', 'Unknown error')
                        print(f"[arXiv] Failed: {error_msg}")
                        arxiv_sample = f"Error: {error_msg}"
                except Exception as e:
                    print(f"[arXiv] Error: {e}")
                    arxiv_sample = f"Error: {str(e)}"
            else:
                print(f"[arXiv] Query does not trigger arXiv search - {reason}")
        else:
            print("\n[arXiv] arXiv integration not available")
        
        # Calculate combined metrics
        total_context_length = len(graphiti_context) + len(bigquery_context) + len(gdelt_context) + len(arxiv_context)
        total_retrieval_time = graphiti_retrieval_time + bigquery_retrieval_time + gdelt_retrieval_time + arxiv_retrieval_time
        
        result = SimulationResult(
            query_id=query_id,
            query_text=query,
            query_category=category,
            timestamp=timestamp,
            
            graphiti_nodes_retrieved=nodes_count,
            graphiti_facts_retrieved=facts_count,
            graphiti_context_length=len(graphiti_context),
            graphiti_retrieval_time=graphiti_retrieval_time,
            graphiti_context_sample=graphiti_sample,
            
            bigquery_triggered=bigquery_triggered,
            bigquery_context_length=len(bigquery_context),
            bigquery_retrieval_time=bigquery_retrieval_time,
            bigquery_context_sample=bigquery_sample,
            
            gdelt_triggered=gdelt_triggered,
            gdelt_category=gdelt_category,
            gdelt_context_length=len(gdelt_context),
            gdelt_retrieval_time=gdelt_retrieval_time,
            gdelt_context_sample=gdelt_sample,
            
            arxiv_triggered=arxiv_triggered,
            arxiv_category=arxiv_category,
            arxiv_papers_found=arxiv_papers_found,
            arxiv_context_length=len(arxiv_context),
            arxiv_retrieval_time=arxiv_retrieval_time,
            arxiv_confidence=arxiv_confidence,
            arxiv_context_sample=arxiv_sample,
            
            total_context_length=total_context_length,
            total_retrieval_time=total_retrieval_time,
            sources_used=sources_used
        )
        
        print(f"\n[Summary] Total context: {total_context_length} chars from {sources_used}")
        print(f"[Summary] Total time: {total_retrieval_time:.2f}s")
        
        return result
    
    def run_simulation(self, categories: Optional[List[str]] = None, queries_per_category: Optional[int] = None):
        """Run simulation for specified categories and queries"""
        if categories is None:
            categories = list(self.test_queries.keys())
        
        total_queries = 0
        for category in categories:
            if category not in self.test_queries:
                print(f"Warning: Unknown category '{category}', skipping")
                continue
            
            queries = self.test_queries[category]
            if queries_per_category is not None:
                queries = queries[:queries_per_category]
            
            for i, query in enumerate(queries):
                query_id = f"{category}_{i+1:03d}"
                result = self.simulate_single_query(query, category, query_id)
                self.results.append(result)
                total_queries += 1
                
                # Small delay to avoid overwhelming services
                time.sleep(0.5)
        
        print(f"\n{'='*80}")
        print(f"Simulation complete! Processed {total_queries} queries")
        print('='*80)
    
    def save_results(self):
        """Save simulation results to various formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Save raw results as JSON
        json_path = os.path.join(self.output_dir, f"simulation_results_{timestamp}.json")
        with open(json_path, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)
        print(f"\nSaved raw results to: {json_path}")
        
        # 2. Save summary as CSV
        csv_path = os.path.join(self.output_dir, f"simulation_summary_{timestamp}.csv")
        df = pd.DataFrame([asdict(r) for r in self.results])
        df.to_csv(csv_path, index=False)
        print(f"Saved summary CSV to: {csv_path}")
        
        # 3. Generate analysis report
        report_path = os.path.join(self.output_dir, f"simulation_report_{timestamp}.md")
        self.generate_report(report_path, df)
        print(f"Saved analysis report to: {report_path}")
        
        # 4. Generate visualizations
        self.generate_visualizations(timestamp, df)
        
        return json_path, csv_path, report_path
    
    def generate_report(self, report_path: str, df: pd.DataFrame):
        """Generate markdown analysis report"""
        with open(report_path, 'w') as f:
            f.write("# Context Retrieval Simulation Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Using improved retrieval: {USING_IMPROVED_RETRIEVAL}\n")
            f.write(f"Total queries: {len(df)}\n\n")
            
            # Overall statistics
            f.write("## Overall Statistics\n\n")
            f.write(f"- Average total context length: {df['total_context_length'].mean():.0f} chars\n")
            f.write(f"- Average total retrieval time: {df['total_retrieval_time'].mean():.2f} seconds\n")
            f.write(f"- Average Graphiti nodes: {df['graphiti_nodes_retrieved'].mean():.1f}\n")
            f.write(f"- Average Graphiti facts: {df['graphiti_facts_retrieved'].mean():.1f}\n\n")
            
            # Source usage
            f.write("## Source Usage\n\n")
            bigquery_usage = (df['bigquery_triggered'].sum() / len(df)) * 100
            gdelt_usage = (df['gdelt_triggered'].sum() / len(df)) * 100
            f.write(f"- BigQuery triggered: {bigquery_usage:.1f}% of queries\n")
            f.write(f"- GDELT triggered: {gdelt_usage:.1f}% of queries\n\n")
            
            # Category breakdown
            f.write("## Category Analysis\n\n")
            for category in df['query_category'].unique():
                cat_df = df[df['query_category'] == category]
                f.write(f"### {category.title()}\n")
                f.write(f"- Queries: {len(cat_df)}\n")
                f.write(f"- Avg context length: {cat_df['total_context_length'].mean():.0f} chars\n")
                f.write(f"- Avg retrieval time: {cat_df['total_retrieval_time'].mean():.2f}s\n")
                f.write(f"- BigQuery usage: {(cat_df['bigquery_triggered'].sum() / len(cat_df)) * 100:.1f}%\n")
                f.write(f"- GDELT usage: {(cat_df['gdelt_triggered'].sum() / len(cat_df)) * 100:.1f}%\n\n")
            
            # Performance insights
            f.write("## Performance Insights\n\n")
            
            # Slowest queries
            f.write("### Slowest Queries\n")
            slowest = df.nlargest(5, 'total_retrieval_time')[['query_text', 'total_retrieval_time', 'sources_used']]
            for _, row in slowest.iterrows():
                f.write(f"- \"{row['query_text'][:50]}...\" - {row['total_retrieval_time']:.2f}s ({', '.join(row['sources_used'])})\n")
            f.write("\n")
            
            # Largest contexts
            f.write("### Largest Contexts\n")
            largest = df.nlargest(5, 'total_context_length')[['query_text', 'total_context_length', 'sources_used']]
            for _, row in largest.iterrows():
                f.write(f"- \"{row['query_text'][:50]}...\" - {row['total_context_length']} chars ({', '.join(row['sources_used'])})\n")
    
    def generate_visualizations(self, timestamp: str, df: pd.DataFrame):
        """Generate visualization plots"""
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 1. Context length by category
        fig, ax = plt.subplots(figsize=(10, 6))
        df.boxplot(column='total_context_length', by='query_category', ax=ax)
        ax.set_title('Context Length Distribution by Category')
        ax.set_xlabel('Query Category')
        ax.set_ylabel('Context Length (chars)')
        plt.suptitle('')  # Remove automatic title
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'context_length_by_category_{timestamp}.png'))
        plt.close()
        
        # 2. Retrieval time by source
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        
        # Graphiti times
        ax1.hist(df['graphiti_retrieval_time'], bins=20, alpha=0.7, color='blue')
        ax1.set_title('Graphiti Retrieval Times')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Frequency')
        
        # BigQuery times (only for triggered queries)
        bigquery_times = df[df['bigquery_triggered']]['bigquery_retrieval_time']
        if len(bigquery_times) > 0:
            ax2.hist(bigquery_times, bins=20, alpha=0.7, color='green')
        ax2.set_title('BigQuery Retrieval Times')
        ax2.set_xlabel('Time (seconds)')
        
        # GDELT times (only for triggered queries)
        gdelt_times = df[df['gdelt_triggered']]['gdelt_retrieval_time']
        if len(gdelt_times) > 0:
            ax3.hist(gdelt_times, bins=20, alpha=0.7, color='orange')
        ax3.set_title('GDELT Retrieval Times')
        ax3.set_xlabel('Time (seconds)')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'retrieval_times_{timestamp}.png'))
        plt.close()
        
        # 3. Source usage by category
        fig, ax = plt.subplots(figsize=(10, 6))
        
        category_source_usage = []
        for category in df['query_category'].unique():
            cat_df = df[df['query_category'] == category]
            category_source_usage.append({
                'category': category,
                'graphiti': 100,  # Always used
                'bigquery': (cat_df['bigquery_triggered'].sum() / len(cat_df)) * 100,
                'gdelt': (cat_df['gdelt_triggered'].sum() / len(cat_df)) * 100
            })
        
        usage_df = pd.DataFrame(category_source_usage)
        usage_df.set_index('category')[['graphiti', 'bigquery', 'gdelt']].plot(kind='bar', ax=ax)
        ax.set_title('Source Usage by Query Category')
        ax.set_xlabel('Category')
        ax.set_ylabel('Usage (%)')
        ax.legend(title='Source')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f'source_usage_by_category_{timestamp}.png'))
        plt.close()
        
        print(f"\nGenerated visualizations in: {self.output_dir}")


def main():
    """Main simulation runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run context retrieval simulation suite")
    parser.add_argument("--graphiti-url", type=str, help="Graphiti API URL")
    parser.add_argument("--categories", nargs="+", help="Categories to test (default: all)")
    parser.add_argument("--queries-per-category", type=int, help="Max queries per category")
    parser.add_argument("--output-dir", type=str, default="simulation_results", help="Output directory")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = ContextRetrievalSimulator(
        graphiti_url=args.graphiti_url,
        output_dir=args.output_dir
    )
    
    # Print configuration
    print("Context Retrieval Simulation Suite")
    print("="*80)
    print(f"Graphiti URL: {simulator.graphiti_url}")
    print(f"Max nodes: {simulator.max_nodes}")
    print(f"Max facts: {simulator.max_facts}")
    print(f"BigQuery available: {BIGQUERY_AVAILABLE} (DISABLED to avoid costs)")
    print(f"GDELT available: {GDELT_AVAILABLE}")
    print(f"arXiv available: {ARXIV_AVAILABLE}")
    print(f"Using improved retrieval: {USING_IMPROVED_RETRIEVAL}")
    print(f"Output directory: {simulator.output_dir}")
    print("="*80)
    
    # Run simulation
    simulator.run_simulation(
        categories=args.categories,
        queries_per_category=args.queries_per_category
    )
    
    # Save results
    json_path, csv_path, report_path = simulator.save_results()
    
    print("\nSimulation complete!")
    print(f"Results saved to:")
    print(f"  - JSON: {json_path}")
    print(f"  - CSV: {csv_path}")
    print(f"  - Report: {report_path}")
    print(f"  - Visualizations: {simulator.output_dir}/*.png")


if __name__ == "__main__":
    main()