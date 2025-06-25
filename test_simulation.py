#!/usr/bin/env python3
"""
Test script for the simulation suite
Runs a quick simulation with a few queries to demonstrate functionality
"""

import os
import sys
from simulation_suite import ContextRetrievalSimulator

def main():
    print("Running Context Retrieval Simulation Test")
    print("="*80)
    
    # Create simulator with custom output directory
    simulator = ContextRetrievalSimulator(output_dir="test_simulation_output")
    
    # Add some custom test queries with high variance
    simulator.test_queries["custom"] = [
        "What is the current state of artificial intelligence?",
        "How does machine learning work?",
        "Tell me about recent breakthroughs in quantum computing",
        "AI",
        "Can artificial intelligence become conscious?",
        "What are the ethical implications of AGI development in the next decade?",
        "ML vs DL",
        "Explain transformer architecture in LLMs with attention mechanisms",
        "AGI timeline?",
        "How might quantum supremacy impact cryptography and blockchain security?",
        "Neural networks",
        "What are the latest advances in neuromorphic computing chips?",
        "Is P=NP?",
        "Explain the intersection of quantum computing and machine learning algorithms",
        "Best AI tools",
        "How do diffusion models generate images from text prompts?",
        "Future of work with AI",
        "What are the current limitations of large language models?",
        "Quantum entanglement applications?",
        "How might brain-computer interfaces evolve in the next 5 years?",
        "AI regulation frameworks",
        "What is the role of AI in drug discovery and personalized medicine?",
        "Singularity when?",
        "How do reinforcement learning agents master complex games?",
        "AI bias solutions",
        "What are the energy consumption challenges of training large AI models?",
        "Quantum error correction",
        "How might AI transform education and personalized learning?",
        "GPT vs BERT",
        "What are the implications of AI-generated synthetic media?",
        "AI consciousness test",
        "How do federated learning systems preserve privacy?",
        "Quantum algorithms list",
        "What is the potential of AI in climate change mitigation?",
        "AI job displacement",
        "How do multi-modal AI systems process different data types?",
        "Quantum computing companies",
        "What are the challenges in achieving artificial general intelligence?",
        "AI democratization",
        "How might swarm intelligence solve complex optimization problems?",
        "Quantum vs classical",
        "What is the future of human-AI collaboration in creative fields?",
        "AI interpretability methods",
        "How do adversarial attacks challenge AI security?"
    ]
    
    # Run a larger simulation - 40 queries per category (20x the original 2)
    print("\nRunning simulation with 40 queries per category (20x volume)...")
    print("This will take several minutes...\n")
    simulator.run_simulation(
        categories=["technical", "current_events", "custom"],
        queries_per_category=40
    )
    
    # Save and analyze results
    print("\nSaving results...")
    json_path, csv_path, report_path = simulator.save_results()
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SIMULATION SUMMARY")
    print("="*80)
    
    total_queries = len(simulator.results)
    print(f"Total queries processed: {total_queries}")
    
    if total_queries > 0:
        # Calculate averages
        avg_context_length = sum(r.total_context_length for r in simulator.results) / total_queries
        avg_retrieval_time = sum(r.total_retrieval_time for r in simulator.results) / total_queries
        avg_nodes = sum(r.graphiti_nodes_retrieved for r in simulator.results) / total_queries
        avg_facts = sum(r.graphiti_facts_retrieved for r in simulator.results) / total_queries
        
        print(f"\nAverage Metrics:")
        print(f"  - Context length: {avg_context_length:.0f} chars")
        print(f"  - Retrieval time: {avg_retrieval_time:.2f} seconds")
        print(f"  - Graphiti nodes: {avg_nodes:.1f}")
        print(f"  - Graphiti facts: {avg_facts:.1f}")
        
        # Source usage
        bigquery_count = sum(1 for r in simulator.results if r.bigquery_triggered)
        gdelt_count = sum(1 for r in simulator.results if r.gdelt_triggered)
        
        print(f"\nSource Usage:")
        print(f"  - Graphiti: {total_queries}/{total_queries} (100%)")
        print(f"  - BigQuery: {bigquery_count}/{total_queries} ({bigquery_count/total_queries*100:.1f}%)")
        print(f"  - GDELT: {gdelt_count}/{total_queries} ({gdelt_count/total_queries*100:.1f}%)")
        
        # Category breakdown
        print(f"\nQueries by Category:")
        categories = {}
        for r in simulator.results:
            categories[r.query_category] = categories.get(r.query_category, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"  - {cat}: {count} queries")
        
        # Sample results
        print(f"\nSample Query Results:")
        for i, result in enumerate(simulator.results[:3]):
            print(f"\n{i+1}. Query: \"{result.query_text}\"")
            print(f"   Category: {result.query_category}")
            print(f"   Total context: {result.total_context_length} chars")
            print(f"   Total time: {result.total_retrieval_time:.2f}s")
            print(f"   Sources: {', '.join(result.sources_used)}")
    
    print(f"\n{'='*80}")
    print("Test simulation complete!")
    print(f"Full report available at: {report_path}")
    print("="*80)


if __name__ == "__main__":
    main()