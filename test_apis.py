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


def test_semantic_scholar():
    """Test Semantic Scholar API"""
    print("\n" + "=" * 60)
    print("Testing Semantic Scholar API")
    print("=" * 60)
    
    collector = DataCollector()
    
    try:
        print("Waiting 65 seconds for rate limit reset...")
        import time
        time.sleep(65)
        
        papers = list(collector.semantic_scholar.search(
            query="machine learning",
            max_results=3
        ))
        
        print(f"✅ Retrieved {len(papers)} papers")
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n{i}. {paper.title[:80]}")
            print(f"   Authors: {len(paper.authors)}")
            print(f"   Citations: {paper.citations_count}")
            print(f"   Year: {paper.publication_date[:4] if paper.publication_date else 'N/A'}")
            print(f"   URL: {paper.url}")
        
        return len(papers) > 0
        
    except Exception as e:
        print(f"❌ Semantic Scholar API error: {e}")
        return False


def main():
    """Run API tests"""
    print("\n🧪 API Connection Tests")
    print(f"Time: {datetime.now().isoformat()}")
    
    pubmed_ok = test_pubmed()
    # ss_ok = test_semantic_scholar()  # Skip due to rate limiting
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  PubMed: {'✅ Working' if pubmed_ok else '❌ Failed'}")
    # print(f"  Semantic Scholar: {'✅ Working' if ss_ok else '❌ Failed (rate limited?)'}")
    print("=" * 60)
    
    return 0 if pubmed_ok else 1


if __name__ == "__main__":
    sys.exit(main())
