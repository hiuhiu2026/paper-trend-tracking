#!/usr/bin/env python3
"""
Test API Connections

Tests PubMed and Semantic Scholar API connectivity.
Run this to verify your API keys work.
"""

import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from data_collector import DataCollector
from datetime import datetime


def test_pubmed():
    """Test PubMed API"""
    print("\n" + "=" * 60)
    print("Testing PubMed API")
    print("=" * 60)
    
    collector = DataCollector()
    
    try:
        papers = list(collector.pubmed.search(
            query="deep learning protein structure",
            max_results=5
        ))
        
        print(f"✅ Retrieved {len(papers)} papers")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper.title[:80]}")
            print(f"   Authors: {len(paper.authors)}")
            print(f"   Journal: {paper.journal[:50] if paper.journal else 'N/A'}")
            print(f"   URL: {paper.url}")
        
        return len(papers) > 0
        
    except Exception as e:
        print(f"❌ PubMed API error: {e}")
        return False


def test_arxiv():
    """Test arXiv API"""
    print("\n" + "=" * 60)
    print("Testing arXiv API")
    print("=" * 60)
    
    collector = DataCollector(use_arxiv=True, use_semantic_scholar=False)
    
    try:
        papers = list(collector.arxiv.search(
            query="deep learning",
            max_results=5,
            categories=['cs.LG', 'cs.AI']
        ))
        
        print(f"✅ Retrieved {len(papers)} papers")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper.title[:80]}")
            print(f"   arXiv: {paper.arxiv_id}")
            print(f"   Categories: {', '.join(paper.categories)}")
            print(f"   Date: {paper.publication_date}")
            print(f"   URL: {paper.url}")
        
        return len(papers) > 0
        
    except Exception as e:
        print(f"❌ arXiv API error: {e}")
        return False


def main():
    """Run API tests"""
    print("\n🧪 API Connection Tests")
    print(f"Time: {datetime.now().isoformat()}")
    
    pubmed_ok = test_pubmed()
    arxiv_ok = test_arxiv()
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  PubMed: {'✅ Working' if pubmed_ok else '❌ Failed'}")
    print(f"  arXiv:  {'✅ Working' if arxiv_ok else '❌ Failed'}")
    print("\n💡 Default config uses PubMed + arXiv (no API keys needed)")
    print("=" * 60)
    
    return 0 if (pubmed_ok and arxiv_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
