from typing import List, Dict
import re
from datetime import datetime, UTC

# Maximum context snippet length for cumulative context
# Set to 4800 to stay well under Letta's 5000 character API limit
MAX_CONTEXT_SNIPPET_LENGTH = 4800

def _build_cumulative_context(existing_context: str, new_context: str) -> str:
    """
    Build cumulative context by appending new context to existing context.
    Implements deduplication and truncation logic.
    """
    # Create timestamp separator for new entry
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    separator = f"\n\n--- CONTEXT ENTRY ({timestamp}) ---\n\n"
    
    # Handle empty existing context
    if not existing_context or existing_context.strip() == "":
        return new_context
    
    # Handle empty new context
    if not new_context or new_context.strip() == "":
        return existing_context
    
    # Simple deduplication: check if new context is substantially similar to the most recent entry
    existing_entries = _parse_context_entries(existing_context)
    if existing_entries:
        most_recent_entry = existing_entries[-1]["content"]
        if _is_content_similar_with_query_awareness(most_recent_entry, new_context):
            print("[_build_cumulative_context] New context is similar to most recent entry, skipping append.")
            return existing_context
    
    # Build new cumulative context
    cumulative_context = existing_context + separator + new_context
    
    # Truncate if exceeds maximum length
    if len(cumulative_context) > MAX_CONTEXT_SNIPPET_LENGTH:
        cumulative_context = _truncate_oldest_entries(cumulative_context, MAX_CONTEXT_SNIPPET_LENGTH)
        
        # CRITICAL FIX: Ensure new content is included even after truncation
        # If the result is just the truncation notice, append the new content
        if cumulative_context.strip() == "--- OLDER ENTRIES TRUNCATED ---":
            print("[_build_cumulative_context] TRUNCATION FIX: Adding new content after truncation notice")
            cumulative_context = "--- OLDER ENTRIES TRUNCATED ---" + separator + new_context
            
            # If still too long, truncate the new content but keep some of it
            if len(cumulative_context) > MAX_CONTEXT_SNIPPET_LENGTH:
                available_space = MAX_CONTEXT_SNIPPET_LENGTH - len("--- OLDER ENTRIES TRUNCATED ---") - len(separator) - 100  # Leave some buffer
                if available_space > 500:  # Only truncate if we have reasonable space
                    truncated_new_content = new_context[:available_space] + "\n\n[CONTENT TRUNCATED]"
                    cumulative_context = "--- OLDER ENTRIES TRUNCATED ---" + separator + truncated_new_content
                else:
                    # If no reasonable space, just return the new content
                    cumulative_context = new_context
    
    return cumulative_context

def _parse_context_entries(context: str) -> List[Dict[str, str]]:
    """
    Parse context string into individual entries with timestamps.
    Returns list of dicts with 'timestamp' and 'content' keys.
    """
    # Pattern to match context entry separators
    separator_pattern = r'\n\n--- CONTEXT ENTRY \(([^)]+)\) ---\n\n'
    
    # Split by separators
    parts = re.split(separator_pattern, context)
    
    entries = []
    if len(parts) >= 1:
        # First part might be content before any separator (legacy content)
        first_part = parts[0].strip()
        if first_part:
            entries.append({
                "timestamp": "Legacy",
                "content": first_part
            })
        
        # Process pairs of (timestamp, content)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                timestamp = parts[i]
                content = parts[i + 1].strip()
                if content:
                    entries.append({
                        "timestamp": timestamp,
                        "content": content
                    })
    
    return entries

def _is_content_similar_with_query_awareness(content1: str, content2: str) -> bool:
    """
    Check if content is similar, but with special handling for arXiv and Graphiti content
    to ensure different queries are always treated as different even if content overlaps.
    """
    if not content1 or not content2:
        return False
    
    # For arXiv content, check if the queries are different
    if "**Recent Research Papers (arXiv)**" in content1 and "**Recent Research Papers (arXiv)**" in content2:
        # Extract the query lines from both contents
        def extract_arxiv_query(content):
            lines = content.split('\n')
            for line in lines:
                if 'papers relevant to:' in line:
                    # Extract the query part after "relevant to:"
                    query_part = line.split('papers relevant to:')[-1].strip()
                    return query_part.rstrip('*').strip()
            return None
        
        query1 = extract_arxiv_query(content1)
        query2 = extract_arxiv_query(content2)
        
        if query1 and query2 and query1 != query2:
            print(f"[_is_content_similar_with_query_awareness] Different arXiv queries detected:")
            print(f"  Query 1: {query1}")
            print(f"  Query 2: {query2}")
            print(f"  Treating as different content even if papers overlap.")
            return False
        elif query1 and query2 and query1 == query2:
            print(f"[_is_content_similar_with_query_awareness] Same arXiv query detected: {query1}")
            # Fall through to regular similarity check
    
    # For Graphiti content, check if we have different context entries with timestamps
    if "Relevant Entities from Knowledge Graph:" in content1 and "Relevant Entities from Knowledge Graph:" in content2:
        # Look for timestamp patterns that indicate different search contexts
        
        # Extract timestamps from context entries
        timestamp_pattern = r'--- CONTEXT ENTRY \(([^)]+)\) ---'
        timestamps1 = re.findall(timestamp_pattern, content1)
        timestamps2 = re.findall(timestamp_pattern, content2)
        
        # If we have different timestamps, these are different searches
        if timestamps1 and timestamps2:
            latest1 = timestamps1[-1] if timestamps1 else None
            latest2 = timestamps2[-1] if timestamps2 else None
            
            if latest1 != latest2:
                print(f"[_is_content_similar_with_query_awareness] Different Graphiti search contexts detected:")
                print(f"  Latest timestamp 1: {latest1}")
                print(f"  Latest timestamp 2: {latest2}")
                print(f"  Treating as different content.")
                return False
        
        # If no timestamps found, these are likely different base contexts
        # and should be treated as different
        if not timestamps1 and not timestamps2:
            print(f"[_is_content_similar_with_query_awareness] Different Graphiti base contexts detected (no timestamps).")
            print(f"  Treating as different content.")
            return False
    
    # For non-arXiv/non-Graphiti content or same queries, use regular similarity logic
    return _is_content_similar(content1, content2)

def _is_content_similar(content1: str, content2: str) -> bool:
    """
    Simple similarity check to detect duplicate or highly similar content.
    Returns True if contents are substantially similar.
    """
    if not content1 or not content2:
        return False
    
    # Simple checks for exact or near-exact duplicates
    content1_clean = content1.strip().lower()
    content2_clean = content2.strip().lower()
    
    # Exact match
    if content1_clean == content2_clean:
        return True
    
    # Check if one is contained within the other (80% threshold)
    shorter_len = min(len(content1_clean), len(content2_clean))
    longer_len = max(len(content1_clean), len(content2_clean))
    
    if shorter_len > 0 and longer_len > 0:
        # If one is much shorter, check containment
        if shorter_len / longer_len < 0.8:
            return content1_clean in content2_clean or content2_clean in content1_clean
        
        # For similar length strings, check character overlap
        common_chars = len(set(content1_clean) & set(content2_clean))
        total_unique_chars = len(set(content1_clean) | set(content2_clean))
        
        if total_unique_chars > 0:
            similarity_ratio = common_chars / total_unique_chars
            return similarity_ratio > 0.9
    
    return False

def _truncate_oldest_entries(context: str, max_length: int) -> str:
    """
    Truncate oldest context entries to fit within max_length.
    Preserves the most recent entries and ensures new content is always included.
    """
    if len(context) <= max_length:
        return context
    
    entries = _parse_context_entries(context)
    if not entries:
        # If we can't parse entries, just truncate from the beginning
        return context[-max_length:]
    
    # Always try to preserve the most recent entry (which should be the new content)
    if len(entries) > 0:
        most_recent_entry = entries[-1]
        
        # Format the most recent entry
        if most_recent_entry["timestamp"] == "Legacy":
            recent_formatted = most_recent_entry["content"]
        else:
            recent_formatted = f"\n\n--- CONTEXT ENTRY ({most_recent_entry['timestamp']}) ---\n\n{most_recent_entry['content']}"
        
        # If the most recent entry alone fits in the limit, start with it
        truncation_notice = "--- OLDER ENTRIES TRUNCATED ---\n\n"
        
        if len(recent_formatted) + len(truncation_notice) <= max_length:
            # We can fit the most recent entry plus truncation notice
            result_entries = [recent_formatted]
            current_length = len(recent_formatted)
            
            # Try to add older entries working backwards (excluding the most recent we already added)
            for entry in reversed(entries[:-1]):
                if entry["timestamp"] == "Legacy":
                    formatted_entry = entry["content"]
                else:
                    formatted_entry = f"\n\n--- CONTEXT ENTRY ({entry['timestamp']}) ---\n\n{entry['content']}"
                
                proposed_length = current_length + len(formatted_entry) + len(truncation_notice)
                
                if proposed_length <= max_length:
                    result_entries.insert(0, formatted_entry)
                    current_length += len(formatted_entry)
                else:
                    break
            
            # Add truncation notice if we have multiple entries
            if len(result_entries) > 1 or len(entries) > 1:
                result_entries.insert(0, truncation_notice.rstrip())
            
            return "".join(result_entries)
        else:
            # Most recent entry is too long by itself, truncate it but keep it
            available_space = max_length - len(truncation_notice) - 100  # Leave buffer
            if available_space > 500:
                # Truncate the recent content but preserve it
                if most_recent_entry["timestamp"] == "Legacy":
                    truncated_content = most_recent_entry["content"][:available_space] + "\n\n[CONTENT TRUNCATED]"
                    return truncation_notice + truncated_content
                else:
                    truncated_content = most_recent_entry["content"][:available_space] + "\n\n[CONTENT TRUNCATED]"
                    return truncation_notice + f"\n\n--- CONTEXT ENTRY ({most_recent_entry['timestamp']}) ---\n\n" + truncated_content
            else:
                # Very little space, just return recent content without truncation notice
                return recent_formatted[-max_length:]
    
    # Fallback: just return the end of the context
    return context[-max_length:]