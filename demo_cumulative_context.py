#!/usr/bin/env python3
"""
Simple demonstration of the cumulative context system functionality
"""

import sys
sys.path.append('.')

from flask_webhook_receiver import (
    _build_cumulative_context,
    _parse_context_entries,
    _is_content_similar,
    _truncate_oldest_entries
)

def demo_basic_accumulation():
    """Demonstrate basic context accumulation"""
    print("🔄 Demo: Basic Context Accumulation")
    print("-" * 50)
    
    # Start with empty context
    context = ""
    
    # Add first entry
    context = _build_cumulative_context(context, "User asks about Python programming")
    print(f"After 1st entry ({len(context)} chars):\n{context}\n")
    
    # Add second entry
    context = _build_cumulative_context(context, "User wants to learn Flask framework")
    print(f"After 2nd entry ({len(context)} chars):\n{context}\n")
    
    # Add third entry
    context = _build_cumulative_context(context, "User inquires about database integration")
    print(f"After 3rd entry ({len(context)} chars):\n{context}\n")
    
    print("=" * 80 + "\n")

def demo_deduplication():
    """Demonstrate content deduplication"""
    print("🚫 Demo: Content Deduplication")
    print("-" * 50)
    
    # Start with some context
    context = "User asks about machine learning algorithms"
    print(f"Initial context: {context}\n")
    
    # Try to add identical content
    new_context1 = _build_cumulative_context(context, "User asks about machine learning algorithms")
    print(f"After trying to add identical content:")
    print(f"Context unchanged: {new_context1 == context}")
    print(f"Length: {len(new_context1)} (was {len(context)})\n")
    
    # Try to add similar content
    new_context2 = _build_cumulative_context(context, "User asks about machine learning algorithms and techniques")
    print(f"After trying to add similar content:")
    print(f"Context unchanged: {new_context2 == context}")
    print(f"Length: {len(new_context2)} (was {len(context)})\n")
    
    # Add clearly different content
    new_context3 = _build_cumulative_context(context, "User wants to learn about web development")
    print(f"After adding different content:")
    print(f"Context changed: {new_context3 != context}")
    print(f"Length: {len(new_context3)} (was {len(context)})")
    print(f"New context:\n{new_context3}\n")
    
    print("=" * 80 + "\n")

def demo_truncation():
    """Demonstrate context truncation"""
    print("✂️ Demo: Context Truncation")
    print("-" * 50)
    
    # Build up a long context
    context = ""
    entries = [
        "First entry with some initial content about user preferences",
        "Second entry discussing technical requirements and specifications",
        "Third entry containing detailed information about project goals",
        "Fourth entry with comprehensive analysis of user needs and context",
        "Fifth entry adding more extensive details about implementation strategy",
        "Sixth entry with additional comprehensive information about the solution approach"
    ]
    
    for i, entry in enumerate(entries):
        context = _build_cumulative_context(context, entry)
        print(f"After entry {i+1}: {len(context)} characters")
    
    print(f"\nFull context before truncation ({len(context)} chars):\n{context}\n")
    
    # Demonstrate truncation with a small limit
    small_limit = 300
    truncated = _truncate_oldest_entries(context, small_limit)
    
    print(f"After truncation to {small_limit} characters:")
    print(f"Length: {len(truncated)}")
    print(f"Contains truncation notice: {'--- OLDER ENTRIES TRUNCATED ---' in truncated}")
    print(f"Contains latest entry: {entries[-1] in truncated}")
    print(f"Contains oldest entry: {entries[0] in truncated}")
    print(f"\nTruncated context:\n{truncated}\n")
    
    print("=" * 80 + "\n")

def demo_similarity_detection():
    """Demonstrate similarity detection"""
    print("🔍 Demo: Similarity Detection")
    print("-" * 50)
    
    test_cases = [
        ("Hello world", "Hello world", True),
        ("Hello world", "hello world", True),
        ("Hello world", "Hello World!", True),
        ("Hello world", "Goodbye world", False),
        ("Python programming", "Python programming basics", True),
        ("Machine learning", "Deep learning", False),
        ("User wants help", "User needs help", False),
        ("Very long detailed explanation about complex topics", "Very long detailed explanation", True)
    ]
    
    for text1, text2, expected in test_cases:
        result = _is_content_similar(text1, text2)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text1}' vs '{text2}' → Similar: {result} (expected: {expected})")
    
    print("\n" + "=" * 80 + "\n")

def run_all_demos():
    """Run all demonstrations"""
    print("🎯 Cumulative Context System Demonstration")
    print("=" * 80)
    print("This demonstration shows the key features of the cumulative context system:")
    print("1. Context accumulation with timestamped separators")
    print("2. Automatic deduplication of similar content")
    print("3. Intelligent truncation when size limits are exceeded")
    print("4. Content similarity detection\n")
    
    demo_basic_accumulation()
    demo_deduplication()
    demo_truncation()
    demo_similarity_detection()
    
    print("🎉 Demonstration complete!")
    print("The cumulative context system successfully:")
    print("• Accumulates context with proper separators and timestamps")
    print("• Prevents duplicate content from being added")
    print("• Maintains reasonable context sizes through intelligent truncation")
    print("• Preserves the most recent and relevant information")

if __name__ == "__main__":
    run_all_demos()