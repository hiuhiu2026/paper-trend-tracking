#!/usr/bin/env python3
"""
Test DeepSeek Hot Topic Analysis

Run this to debug hot topic analysis issues.
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

# Test with sample keywords
sample_keywords = [
    "foundation model",
    "single-cell RNA-seq",
    "spatial transcriptomics",
    "graph neural network",
    "variational autoencoder",
    "cell representation learning",
    "perturbation prediction",
    "multi-omics integration",
    "digital twin cell",
    "whole-cell modeling",
    "cross-modal alignment",
    "zero-shot cell type annotation",
    "drug response prediction",
    "gene regulatory network inference",
    "metabolic flux modeling",
]

print(f"\nTesting hot topic analysis with {len(sample_keywords)} keywords...\n")

# Run analysis
result = extractor.analyze_hot_topics(sample_keywords, top_n=15)

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

print(f"\nOverall Trends: {result.get('overall_trends', 'N/A')}\n")

hot_directions = result.get('hot_directions', [])
if hot_directions:
    print(f"✅ Found {len(hot_directions)} hot research directions:\n")
    for i, direction in enumerate(hot_directions[:3], 1):
        print(f"{i}. {direction.get('direction_name', 'Unknown')}")
        print(f"   Keywords: {', '.join(direction.get('keywords', [])[:5])}")
        print(f"   Trend: {direction.get('trend_stage', 'unknown')}")
        print(f"   Heat: {direction.get('heat_score', 0):.2f}")
        print()
else:
    print("❌ No hot directions identified")

# Generate report
print("\n" + "=" * 70)
print("GENERATING REPORT")
print("=" * 70)

report = extractor.generate_research_trend_report(result)
print(report[:2000] + "..." if len(report) > 2000 else report)

# Save test output
with open("test_hot_topic_output.md", "w") as f:
    f.write(report)

print(f"\n✅ Full report saved to: test_hot_topic_output.md")
