#!/usr/bin/env python3
"""
Run large-scale simulation with progress tracking
"""

import os
import sys
import time
import json
from datetime import datetime
from simulation_suite import ContextRetrievalSimulator

def run_with_progress():
    print("Starting Large-Scale Context Retrieval Simulation")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create simulator
    simulator = ContextRetrievalSimulator(output_dir="large_simulation_output")
    
    # Configure categories and queries
    categories = ["technical", "current_events", "conversational", "scientific", "business"]
    queries_per_category = 40  # 20x the original 2
    
    total_queries = len(categories) * queries_per_category
    print(f"\nTotal queries to process: {total_queries}")
    print(f"Categories: {', '.join(categories)}")
    print(f"Queries per category: {queries_per_category}")
    
    # Estimate time
    avg_time_per_query = 2.0  # seconds (conservative estimate)
    estimated_minutes = (total_queries * avg_time_per_query) / 60
    print(f"\nEstimated time: {estimated_minutes:.1f} minutes")
    print("="*80)
    
    # Track progress
    start_time = time.time()
    processed = 0
    
    # Process each category separately to track progress
    for category in categories:
        print(f"\n\nProcessing category: {category.upper()}")
        print("-"*60)
        
        queries = simulator.test_queries.get(category, [])[:queries_per_category]
        
        for i, query in enumerate(queries):
            query_id = f"{category}_{i+1:03d}"
            
            # Show progress every 5 queries
            if (processed + 1) % 5 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / (processed + 1)
                remaining = (total_queries - processed - 1) * avg_time
                
                print(f"\n[PROGRESS] {processed + 1}/{total_queries} queries completed")
                print(f"[PROGRESS] Elapsed: {elapsed/60:.1f} min, Remaining: {remaining/60:.1f} min")
                print(f"[PROGRESS] Average time per query: {avg_time:.2f}s\n")
            
            try:
                result = simulator.simulate_single_query(query, category, query_id)
                simulator.results.append(result)
                processed += 1
                
                # Save intermediate results every 20 queries
                if processed % 20 == 0:
                    intermediate_file = os.path.join(
                        simulator.output_dir, 
                        f"intermediate_results_{processed}.json"
                    )
                    with open(intermediate_file, 'w') as f:
                        json.dump([r.__dict__ for r in simulator.results], f, indent=2)
                    print(f"\n[CHECKPOINT] Saved intermediate results to {intermediate_file}")
                    
            except Exception as e:
                print(f"\n[ERROR] Failed to process query {query_id}: {e}")
                processed += 1
                continue
            
            # Small delay between queries
            time.sleep(0.5)
    
    # Final statistics
    total_time = time.time() - start_time
    print("\n" + "="*80)
    print("SIMULATION COMPLETE!")
    print("="*80)
    print(f"Total queries processed: {processed}")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average time per query: {total_time/processed:.2f} seconds")
    
    # Save final results
    print("\nSaving final results...")
    json_path, csv_path, report_path = simulator.save_results()
    
    print(f"\nResults saved:")
    print(f"  - JSON: {json_path}")
    print(f"  - CSV: {csv_path}")
    print(f"  - Report: {report_path}")
    
    # Summary statistics
    if simulator.results:
        avg_context = sum(r.total_context_length for r in simulator.results) / len(simulator.results)
        avg_time = sum(r.total_retrieval_time for r in simulator.results) / len(simulator.results)
        gdelt_count = sum(1 for r in simulator.results if r.gdelt_triggered)
        
        print(f"\nSummary Statistics:")
        print(f"  - Average context length: {avg_context:.0f} chars")
        print(f"  - Average retrieval time: {avg_time:.2f}s")
        print(f"  - GDELT triggered: {gdelt_count}/{len(simulator.results)} ({gdelt_count/len(simulator.results)*100:.1f}%)")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    try:
        run_with_progress()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        print("Partial results have been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nSimulation failed with error: {e}")
        sys.exit(1)