# Attempt to import real integrations, with fallbacks to dummy classes.

try:
    # Try importing from parent directory first (Docker structure)
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from arxiv_integration import ArxivIntegration
    arxiv_integration = ArxivIntegration()
    ARXIV_AVAILABLE = True
    print("[INIT] arXiv integration loaded successfully")
except ImportError as e:
    ARXIV_AVAILABLE = False
    print(f"[INIT] arXiv integration not available: {e}")
    class DummyArxivIntegration:
        def find_or_create_arxiv_block(self, *args, **kwargs):
            return None, False
        def should_trigger_arxiv_search(self, *args, **kwargs):
            return False, None
        def generate_arxiv_context(self, *args, **kwargs):
            return {}
    arxiv_integration = DummyArxivIntegration()

# GDELT integration removed as per user request.
class DummyGDELTIntegration:
    def should_trigger_gdelt_search(self, *args, **kwargs):
        return False, None
    def generate_gdelt_context_from_query(self, *args, **kwargs):
        return {}
gdelt_integration = DummyGDELTIntegration()