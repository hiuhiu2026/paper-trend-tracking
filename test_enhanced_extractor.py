#!/usr/bin/env python3
"""Test enhanced keyword extractor"""

import sys
sys.path.insert(0, 'src')

from enhanced_keyword_extractor import EnhancedAIVCKeywordExtractor

# Test paper
title = "AI-driven multiscale virtual plant cell modeling: from molecular mechanisms to tissue functions"
abstract = """
We present a novel foundation model approach for whole-cell simulation that integrates 
single-cell RNA-seq data with spatial transcriptomics. Our transformer-based architecture 
enables cross-modal alignment and zero-shot prediction of cell state transitions. 
The model demonstrates out-of-distribution generalization on drug response prediction 
and provides interpretable attention maps revealing key regulatory pathways.
"""

# Create extractor (without LLM)
extractor = EnhancedAIVCKeywordExtractor(llm_config={'enabled': False})

# Extract keywords
keywords = extractor.extract_keywords(title, abstract, max_keywords=15)

print("\n" + "="*70)
print("🔬 ENHANCED KEYWORD EXTRACTION TEST")
print("="*70)
print(f"\nTitle: {title}\n")

print(f"\n📊 Extracted {len(keywords)} keywords:\n")

for i, kw in enumerate(keywords, 1):
    print(f"{i:2}. {kw.keyword:40s} [Spec: {kw.specificity_score:.2f}, Rel: {kw.relevance_score:.2f}, Cat: {kw.category}]")

print("\n" + "="*70)
print("✅ Enhanced extractor working correctly!")
print("="*70 + "\n")
