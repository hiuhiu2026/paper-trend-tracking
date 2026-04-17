#!/usr/bin/env python3
"""
Test DeepSeek Keyword Extraction

Run this to debug keyword extraction issues.
"""

import yaml
from pathlib import Path
from src.enhanced_keyword_extractor import create_deepseek_extractor

# Load config
config_path = Path("config.virtualcell.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

llm_config = config.get('llm', {})

if not llm_config.get('enabled'):
    print("❌ LLM not enabled in config.virtualcell.yaml")
    print("Set llm.enabled: true and add your API key")
    exit(1)

api_key = llm_config.get('api_key')
if not api_key or api_key == 'YOUR_API_KEY_HERE':
    print("❌ API key not configured")
    print("Edit config.virtualcell.yaml and paste your DeepSeek API key")
    exit(1)

# Initialize extractor
print(f"Initializing DeepSeek extractor with model: {llm_config.get('model', 'deepseek-chat')}")
extractor = create_deepseek_extractor(
    api_key=api_key,
    model=llm_config.get('model', 'deepseek-chat'),
    base_url=llm_config.get('base_url', 'https://api.deepseek.com')
)

# Test with a real paper
test_title = "AI-driven multiscale virtual plant cell modeling: from molecular mechanisms to tissue functions"
test_abstract = """
We present a novel foundation model approach for whole-cell simulation that integrates 
single-cell RNA-seq data with spatial transcriptomics. Our transformer-based architecture 
enables cross-modal alignment and zero-shot prediction of cell state transitions. The 
model was trained on 10 million cells from 50 tissues and achieves state-of-the-art 
performance on perturbation response prediction. Our approach combines graph neural 
networks for molecular representation with variational autoencoders for dimensionality 
reduction, enabling interpretable cell embeddings.
"""

print("\n" + "=" * 70)
print("TEST PAPER")
print("=" * 70)
print(f"Title: {test_title}")
print(f"Abstract: {test_abstract[:200]}...")

print("\n" + "=" * 70)
print("EXTRACTING KEYWORDS")
print("=" * 70)

# Run extraction
keywords = extractor.extract_keywords(test_title, test_abstract, max_keywords=10)

print(f"\n✅ Extracted {len(keywords)} keywords:\n")

for i, kw in enumerate(keywords, 1):
    print(f"{i}. {kw.keyword}")
    print(f"   Category: {kw.category}")
    print(f"   Specificity: {kw.specificity_score:.2f}")
    print(f"   Relevance: {kw.relevance_score:.2f}")
    print(f"   Confidence: {kw.confidence:.2f}")
    print()

if not keywords:
    print("❌ No keywords extracted! Check the error logs above.")
    print("\n💡 Tips:")
    print("   1. Check your API key is valid")
    print("   2. Check network connectivity")
    print("   3. Try a shorter abstract")
    print("   4. Check DeepSeek API status")

# Save test output
with open("test_keyword_extraction_output.md", "w") as f:
    f.write("# DeepSeek Keyword Extraction Test\n\n")
    f.write(f"**Title:** {test_title}\n\n")
    f.write(f"**Abstract:** {test_abstract}\n\n")
    f.write("## Extracted Keywords\n\n")
    for i, kw in enumerate(keywords, 1):
        f.write(f"{i}. **{kw.keyword}** (Category: {kw.category}, Specificity: {kw.specificity_score:.2f})\n")

print(f"\n✅ Test output saved to: test_keyword_extraction_output.md")
