#!/usr/bin/env python3
"""
Simple test of cumulative context functionality focusing on core logic
"""

import sys
sys.path.append('.')

from flask_webhook_receiver import (
    _build_cumulative_context,
    _parse_context_entries,
    _is_content_similar,
    _truncate_oldest_entries,
    MAX_CONTEXT_SNIPPET_LENGTH
)

def test_basic_accumulation():
    """Test basic context accumulation"""
    print("🧪 Testing Basic Context Accumulation")
    print("-" * 50)
    
    # Start with empty context
    context = ""
    
    # Add first entry
    context = _build_cumulative_context(context, "User asks about Python programming")
    print(f"✅ After 1st entry: {len(context)} chars")
    assert "User asks about Python programming" in context
    
    # Add second entry
    context = _build_cumulative_context(context, "User wants to learn Flask framework")
    print(f"✅ After 2nd entry: {len(context)} chars")
    assert "User asks about Python programming" in context
    assert "User wants to learn Flask framework" in context
    assert "--- CONTEXT ENTRY (" in context
    
    # Add third entry
    context = _build_cumulative_context(context, "User inquires about database integration")
    print(f"✅ After 3rd entry: {len(context)} chars")
    assert "User asks about Python programming" in context
    assert "User wants to learn Flask framework" in context
    assert "User inquires about database integration" in context
    
    # Should have 2 separators (between 3 entries)
    separator_count = context.count("--- CONTEXT ENTRY (")
    assert separator_count == 2, f"Expected 2 separators, got {separator_count}"
    
    print(f"✅ All assertions passed! Final context:\n{context}\n")
    return True

def test_deduplication():
    """Test content deduplication"""
    print("🧪 Testing Content Deduplication")
    print("-" * 50)
    
    # Test similarity detection
    assert _is_content_similar("Hello world", "Hello world"), "Identical strings should be similar"
    assert _is_content_similar("Hello world", "hello world"), "Case differences should be ignored"
    assert not _is_content_similar("Hello world", "Goodbye world"), "Different strings should not be similar"
    print("✅ Similarity detection working correctly")
    
    # Test deduplication in context building
    context = "User asks about machine learning algorithms"
    original_length = len(context)
    
    # Try to add identical content
    new_context = _build_cumulative_context(context, "User asks about machine learning algorithms")
    assert len(new_context) == original_length, "Identical content should be deduplicated"
    print("✅ Identical content deduplicated")
    
    # Add different content
    different_context = _build_cumulative_context(context, "User wants to learn about web development")
    assert len(different_context) > original_length, "Different content should be added"
    print("✅ Different content added successfully")
    
    return True

def test_truncation():
    """Test context truncation"""
    print("🧪 Testing Context Truncation")
    print("-" * 50)
    
    # Build a long context by adding many entries
    context = ""
    entries = [
        "First entry with some content about user preferences and requirements",
        "Second entry discussing technical specifications and implementation details",
        "Third entry containing comprehensive information about project goals and objectives",
        "Fourth entry with extensive analysis of user needs and contextual requirements",
        "Fifth entry adding detailed information about implementation strategy and approach",
        "Sixth entry with additional comprehensive details about the solution methodology"
    ]
    
    for i, entry in enumerate(entries):
        context = _build_cumulative_context(context, entry)
        print(f"After entry {i+1}: {len(context)} characters")
    
    # Test truncation with a small limit
    small_limit = 400
    truncated = _truncate_oldest_entries(context, small_limit)
    
    print(f"Original length: {len(context)}, Truncated length: {len(truncated)}")
    assert len(truncated) <= small_limit, f"Truncated context should not exceed {small_limit} chars"
    
    # Should contain truncation notice
    assert "--- OLDER ENTRIES TRUNCATED ---" in truncated, "Should contain truncation notice"
    
    # Should contain the most recent entries
    assert entries[-1] in truncated, "Should contain the most recent entry"
    
    # Should NOT contain the earliest entries (they should be truncated)
    assert entries[0] not in truncated, "Should NOT contain the oldest entry"
    
    print("✅ Truncation working correctly")
    print(f"✅ Truncated context:\n{truncated}\n")
    
    return True

def test_context_parsing():
    """Test context entry parsing"""
    print("🧪 Testing Context Entry Parsing")
    print("-" * 50)
    
    test_context = """First entry without separator

--- CONTEXT ENTRY (2024-01-01 12:00:00 UTC) ---

Second entry with separator

--- CONTEXT ENTRY (2024-01-01 13:00:00 UTC) ---

Third entry with separator"""
    
    entries = _parse_context_entries(test_context)
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"
    assert entries[0]["timestamp"] == "Legacy", "First entry should have Legacy timestamp"
    assert entries[1]["timestamp"] == "2024-01-01 12:00:00 UTC", "Second entry timestamp incorrect"
    assert entries[2]["timestamp"] == "2024-01-01 13:00:00 UTC", "Third entry timestamp incorrect"
    
    print("✅ Context parsing working correctly")
    return True

def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting Cumulative Context Core Logic Tests")
    print("=" * 80)
    
    tests = [
        ("Basic Accumulation", test_basic_accumulation),
        ("Deduplication", test_deduplication),
        ("Truncation", test_truncation),
        ("Context Parsing", test_context_parsing)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED\n")
            else:
                failed += 1
                print(f"❌ {test_name}: FAILED\n")
        except Exception as e:
            failed += 1
            print(f"💥 {test_name}: ERROR - {e}\n")
    
    print("=" * 80)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The cumulative context system core logic is working correctly.")
        return True
    else:
        print("⚠️  SOME TESTS FAILED. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)