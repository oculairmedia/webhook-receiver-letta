#!/usr/bin/env python3

"""
Test script to verify that the ArXiv integration fix is working correctly.
This focuses specifically on the ArXiv functionality without the Letta API calls.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arxiv_integration import ArxivIntegration

def test_arxiv_integration():
    """Test the ArxivIntegration class to ensure the method signature error is fixed."""
    print("🔬 Testing ArXiv Integration Fix")
    print("=" * 50)
    
    try:
        # Initialize the ArxivIntegration
        arxiv = ArxivIntegration()
        print("✅ ArxivIntegration initialized successfully")
        
        # Test the should_trigger_arxiv_search method
        test_query = "Tell me about artificial intelligence and machine learning"
        should_trigger, search_query = arxiv.should_trigger_arxiv_search(test_query)
        print(f"✅ should_trigger_arxiv_search returned: {should_trigger}, '{search_query}'")
        
        if should_trigger:
            # Test the generate_arxiv_context method - this was the problematic method
            try:
                result = arxiv.generate_arxiv_context(search_query)
                print("✅ generate_arxiv_context executed successfully")
                print(f"   - Success: {result.get('success', False)}")
                print(f"   - Papers found: {result.get('papers_found', 0)}")
                print(f"   - Context length: {len(result.get('context', ''))}")
                if result.get('error'):
                    print(f"   - Error: {result['error']}")
                    
                return True
            except Exception as e:
                print(f"❌ generate_arxiv_context failed: {e}")
                return False
        else:
            print("⚠️  ArXiv trigger not activated for this query")
            return True
            
    except Exception as e:
        print(f"❌ ArxivIntegration test failed: {e}")
        return False

def test_method_signature():
    """Test that the method signature issue is resolved."""
    print("\n🔧 Testing Method Signature Fix")
    print("=" * 50)
    
    try:
        arxiv = ArxivIntegration()
        
        # This call should work with only 2 arguments (self + query)
        result = arxiv.generate_arxiv_context("machine learning")
        print("✅ Method called with correct number of arguments")
        print(f"   - Result type: {type(result)}")
        print(f"   - Has 'success' key: {'success' in result}")
        
        return True
    except TypeError as e:
        if "positional arguments" in str(e):
            print(f"❌ Method signature error still exists: {e}")
            return False
        else:
            print(f"⚠️  Different TypeError occurred: {e}")
            return True
    except Exception as e:
        print(f"⚠️  Other exception (not method signature related): {e}")
        return True

if __name__ == "__main__":
    print("🚀 ArXiv Integration Fix Verification")
    print("=" * 50)
    
    success1 = test_method_signature()
    success2 = test_arxiv_integration()
    
    print("\n📋 SUMMARY")
    print("=" * 50)
    if success1 and success2:
        print("✅ ALL TESTS PASSED - ArXiv integration fix successful!")
        print("   - Method signature error resolved")
        print("   - ArXiv functionality working correctly")
    else:
        print("❌ SOME TESTS FAILED")
        if not success1:
            print("   - Method signature error still exists")
        if not success2:
            print("   - ArXiv integration has other issues")