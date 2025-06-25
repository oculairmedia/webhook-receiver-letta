#!/usr/bin/env python3
"""
Monitor simulation progress by analyzing the log file
"""

import re
import time
import os
from datetime import datetime

def monitor_progress(log_file="large_simulation.log", update_interval=5):
    """Monitor simulation progress from log file"""
    
    print("Monitoring Simulation Progress")
    print("="*60)
    print(f"Log file: {log_file}")
    print(f"Update interval: {update_interval} seconds")
    print("Press Ctrl+C to stop monitoring")
    print("="*60)
    
    last_position = 0
    
    while True:
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    f.seek(last_position)
                    new_content = f.read()
                    last_position = f.tell()
                    
                    # Extract progress updates
                    progress_matches = re.findall(
                        r'\[PROGRESS\] (\d+)/(\d+) queries completed.*?'
                        r'Elapsed: ([\d.]+) min.*?Remaining: ([\d.]+) min.*?'
                        r'Average time per query: ([\d.]+)s',
                        new_content,
                        re.DOTALL
                    )
                    
                    for match in progress_matches:
                        completed, total, elapsed, remaining, avg_time = match
                        percentage = (int(completed) / int(total)) * 100
                        
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Progress Update:")
                        print(f"  Completed: {completed}/{total} ({percentage:.1f}%)")
                        print(f"  Elapsed: {elapsed} minutes")
                        print(f"  Remaining: {remaining} minutes")
                        print(f"  Avg time/query: {avg_time} seconds")
                    
                    # Extract checkpoint saves
                    checkpoint_matches = re.findall(
                        r'\[CHECKPOINT\] Saved intermediate results to (.+)',
                        new_content
                    )
                    
                    for checkpoint in checkpoint_matches:
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checkpoint saved: {checkpoint}")
                    
                    # Check for completion
                    if "SIMULATION COMPLETE!" in new_content:
                        print("\n" + "="*60)
                        print("SIMULATION COMPLETE!")
                        
                        # Extract final statistics
                        stats_match = re.search(
                            r'Total queries processed: (\d+).*?'
                            r'Total time: ([\d.]+) minutes.*?'
                            r'Average time per query: ([\d.]+) seconds',
                            new_content,
                            re.DOTALL
                        )
                        
                        if stats_match:
                            total_processed, total_time, avg_time_final = stats_match.groups()
                            print(f"\nFinal Statistics:")
                            print(f"  Total queries: {total_processed}")
                            print(f"  Total time: {total_time} minutes")
                            print(f"  Avg time/query: {avg_time_final} seconds")
                        
                        # Extract summary statistics
                        summary_match = re.search(
                            r'Average context length: ([\d.]+) chars.*?'
                            r'Average retrieval time: ([\d.]+)s.*?'
                            r'GDELT triggered: (\d+)/(\d+)',
                            new_content,
                            re.DOTALL
                        )
                        
                        if summary_match:
                            avg_context, avg_retrieval, gdelt_count, total_count = summary_match.groups()
                            gdelt_percentage = (int(gdelt_count) / int(total_count)) * 100
                            print(f"\nContent Statistics:")
                            print(f"  Avg context length: {avg_context} chars")
                            print(f"  Avg retrieval time: {avg_retrieval}s")
                            print(f"  GDELT usage: {gdelt_percentage:.1f}%")
                        
                        print("="*60)
                        break
            else:
                print(f"Waiting for log file {log_file} to be created...")
            
            time.sleep(update_interval)
            
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"\nError reading log: {e}")
            time.sleep(update_interval)


if __name__ == "__main__":
    monitor_progress()