#!/usr/bin/env python3

def _is_content_similar(content1: str, content2: str) -> bool:
    if not content1 or not content2:
        return False
    
    content1_clean = content1.strip().lower()
    content2_clean = content2.strip().lower()
    
    # Exact match
    if content1_clean == content2_clean:
        print('Exact match detected')
        return True
    
    # Check if one is contained within the other (80% threshold)
    shorter_len = min(len(content1_clean), len(content2_clean))
    longer_len = max(len(content1_clean), len(content2_clean))
    
    print(f'Content 1 length: {len(content1_clean)}')
    print(f'Content 2 length: {len(content2_clean)}')
    print(f'Length ratio: {shorter_len / longer_len if longer_len > 0 else 0:.3f}')
    
    if shorter_len > 0 and longer_len > 0:
        # If one is much shorter, check containment
        if shorter_len / longer_len < 0.8:
            containment = content1_clean in content2_clean or content2_clean in content1_clean
            print(f'Containment check: {containment}')
            return containment
        
        # For similar length strings, check character overlap
        common_chars = len(set(content1_clean) & set(content2_clean))
        total_unique_chars = len(set(content1_clean) | set(content2_clean))
        
        if total_unique_chars > 0:
            similarity_ratio = common_chars / total_unique_chars
            print(f'Character similarity ratio: {similarity_ratio:.3f}')
            is_similar = similarity_ratio > 0.9
            print(f'Is similar (>0.9): {is_similar}')
            return is_similar
    
    return False

# Test with likely arXiv content that would be similar
old_content = """**Recent Research Papers (arXiv)**

*Found 5 recent papers relevant to: recent advances in machine learning optimization*
*Search confidence: 1.00*

**1. VideoMathQA: Benchmarking Mathematical Reasoning via Multimodal Understanding in Videos**
   Authors: Hanoona Rasheed, Abdelrahman Shaker, Anqi Tang et al.
   Published: 2025-06-05
   Categories: cs.CV"""

new_content = """**Recent Research Papers (arXiv)**

*Found 5 recent papers relevant to: Show me latest arxiv papers on neural network architectures*
*Search confidence: 0.75*

**1. FreeTimeGS: Free Gaussians at Anytime and Anywhere for Dynamic Scene Reconstruction**
   Authors: Yifan Wang, Peishan Yang, Zhen Xu et al.
   Published: 2025-06-05
   Categories: cs.CV"""

print('=== Testing Similarity Detection ===')
print('This will show why your neural network query was skipped...')
print()

is_similar = _is_content_similar(old_content, new_content)
print(f'\nFinal result: Content considered similar = {is_similar}')

if is_similar:
    print('\n🔍 DIAGNOSIS: Your query was skipped because the content was deemed "similar"')
    print('   The similarity detection is too aggressive for arXiv content.')
    print('   Different papers but same format = false positive similarity')
else:
    print('\n✅ Content would be considered different and should update')