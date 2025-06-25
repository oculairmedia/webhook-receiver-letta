#!/usr/bin/env python3
"""
Test arXiv integration in simulation
"""

from simulation_suite import ContextRetrievalSimulator

def test_arxiv_integration():
    print("Testing arXiv Integration in Simulation")
    print("="*60)
    
    # Create simulator
    simulator = ContextRetrievalSimulator(output_dir="arxiv_test_output")
    
    # Test queries - mix of research and non-research
    test_queries = [
        ("research", "recent advances in quantum machine learning algorithms"),
        ("research", "breakthrough neural network architectures for NLP"),
        ("non_research", "how to cook spaghetti"),
        ("non_research", "what's the weather like today"),
        ("research", "latest developments in CRISPR gene editing"),
        ("non_research", "best practices for database design")
    ]
    
    results = []
    
    for i, (expected_type, query) in enumerate(test_queries):
        query_id = f"test_{i+1:03d}"
        print(f"\n{'='*60}")
        print(f"Testing Query {i+1}: {query}")
        print(f"Expected type: {expected_type}")
        print("="*60)
        
        # Simulate single query
        result = simulator.simulate_single_query(query, "test", query_id)
        results.append(result)
        
        # Print arXiv-specific results
        print(f"\n[RESULTS]")
        print(f"  arXiv triggered: {result.arxiv_triggered}")
        if result.arxiv_triggered:
            print(f"  arXiv category: {result.arxiv_category}")
            print(f"  Papers found: {result.arxiv_papers_found}")
            print(f"  Context length: {result.arxiv_context_length}")
            print(f"  Confidence: {result.arxiv_confidence:.3f}")
            print(f"  Retrieval time: {result.arxiv_retrieval_time:.2f}s")
        
        # Verify expectation
        is_research_query = expected_type == "research"
        correctly_triggered = result.arxiv_triggered == is_research_query
        
        status = "CORRECT" if correctly_triggered else "INCORRECT"
        print(f"\n[VALIDATION] {status}")
        
        if not correctly_triggered:
            if is_research_query and not result.arxiv_triggered:
                print(f"  Expected arXiv to trigger for research query but it didn't")
            elif not is_research_query and result.arxiv_triggered:
                print(f"  arXiv triggered for non-research query (should not happen)")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print("="*60)
    
    research_queries = [r for r, (t, _) in zip(results, test_queries) if t == "research"]
    non_research_queries = [r for r, (t, _) in zip(results, test_queries) if t == "non_research"]
    
    research_triggered = sum(1 for r in research_queries if r.arxiv_triggered)
    non_research_triggered = sum(1 for r in non_research_queries if r.arxiv_triggered)
    
    print(f"Research queries: {len(research_queries)}")
    print(f"  - arXiv triggered: {research_triggered}/{len(research_queries)}")
    print(f"  - Success rate: {research_triggered/len(research_queries)*100:.1f}%")
    
    print(f"\nNon-research queries: {len(non_research_queries)}")
    print(f"  - arXiv triggered: {non_research_triggered}/{len(non_research_queries)}")
    print(f"  - Correctly avoided: {(len(non_research_queries)-non_research_triggered)/len(non_research_queries)*100:.1f}%")
    
    if research_triggered > 0:
        avg_papers = sum(r.arxiv_papers_found for r in research_queries if r.arxiv_triggered) / research_triggered
        avg_confidence = sum(r.arxiv_confidence for r in research_queries if r.arxiv_triggered) / research_triggered
        avg_time = sum(r.arxiv_retrieval_time for r in research_queries if r.arxiv_triggered) / research_triggered
        
        print(f"\nWhen arXiv was triggered:")
        print(f"  - Average papers found: {avg_papers:.1f}")
        print(f"  - Average confidence: {avg_confidence:.3f}")
        print(f"  - Average retrieval time: {avg_time:.2f}s")
    
    print("="*60)


if __name__ == "__main__":
    test_arxiv_integration()