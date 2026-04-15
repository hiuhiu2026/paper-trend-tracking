#!/usr/bin/env python3
"""
Test Keyword Extraction

Demonstrates different extraction methods on sample papers.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from keyword_extractor import (
    create_extractor,
    YakeExtractor,
    TFIDFExtractor,
    HybridExtractor,
    KeywordExtractorFactory
)


def test_yake():
    """Test YAKE extraction"""
    print("\n" + "=" * 60)
    print("Testing YAKE Extractor")
    print("=" * 60)
    
    sample_abstract = """
    Background: Machine learning (ML) has emerged as a transformative technology 
    in drug discovery and development. Traditional drug discovery processes are 
    time-consuming and expensive, often taking over 10 years and billions of 
    dollars to bring a new drug to market.
    
    Methods: We developed a deep learning framework using graph neural networks 
    (GNNs) to predict molecular properties including solubility, toxicity, and 
    binding affinity. Our model was trained on ChEMBL and PubChem databases 
    containing over 2 million compounds.
    
    Results: The GNN model achieved 94% accuracy in predicting drug-target 
    interactions and identified 15 novel drug candidates for Alzheimer's disease. 
    Virtual screening of 500,000 compounds took only 48 hours compared to 
    months using traditional methods.
    
    Conclusions: Deep learning approaches can significantly accelerate early-stage 
    drug discovery and reduce costs. Our open-source framework is available at 
    github.com/example/drug-ml.
    """
    
    extractor = create_extractor('yake', config={
        'max_ngram_size': 3,
        'num_keywords': 10
    })
    
    keywords = extractor.extract(sample_abstract, max_keywords=10)
    
    print(f"\nExtracted {len(keywords)} keywords:\n")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:2d}. {kw.keyword:40s} (score: {kw.score:.4f})")
    
    return keywords


def test_tfidf():
    """Test TF-IDF extraction"""
    print("\n" + "=" * 60)
    print("Testing TF-IDF Extractor")
    print("=" * 60)
    
    # Need multiple documents to fit TF-IDF
    documents = [
        """
        Machine learning for drug discovery: predicting molecular properties 
        using deep neural networks. We present methods for virtual screening 
        and drug-target interaction prediction.
        """,
        """
        Clinical trial design using artificial intelligence. AI-powered 
        patient recruitment and outcome prediction for pharmaceutical research.
        """,
        """
        Natural language processing in biomedical literature. Mining PubMed 
        for drug-drug interactions and adverse event detection.
        """,
        """
        Graph neural networks for molecular property prediction. Deep learning 
        on chemical structures for drug discovery applications.
        """,
        """
        Reinforcement learning for de novo drug design. Generative models 
        creating novel molecular structures with desired properties.
        """
    ]
    
    extractor = create_extractor('tfidf', config={
        'max_features': 5000,
        'min_df': 1,
        'max_df': 0.9,
        'ngram_range': [1, 2]
    })
    
    print("\nFitting TF-IDF on corpus...")
    extractor.fit(documents)
    
    test_text = """
    Our machine learning model predicts drug-target interactions using 
    deep neural networks trained on molecular structures. The system 
    enables rapid virtual screening of compound libraries.
    """
    
    keywords = extractor.extract(test_text, max_keywords=8)
    
    print(f"\nExtracted {len(keywords)} keywords:\n")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:2d}. {kw.keyword:40s} (score: {kw.score:.4f})")
    
    return keywords


def test_custom_extractor():
    """Test registering and using a custom extractor"""
    print("\n" + "=" * 60)
    print("Testing Custom Extractor Registration")
    print("=" * 60)
    
    from keyword_extractor import BaseKeywordExtractor, KeywordResult
    
    class SimpleWordExtractor(BaseKeywordExtractor):
        """Simple extractor that just returns most frequent words"""
        
        def extract(self, text: str, max_keywords: int = 10):
            from collections import Counter
            import re
            
            # Simple word frequency
            words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
            word_counts = Counter(words)
            
            # Filter common words
            stop_words = {'using', 'present', 'methods', 'results', 'conclusions'}
            filtered = [(w, c) for w, c in word_counts.most_common(20) if w not in stop_words]
            
            return [
                KeywordResult(
                    keyword=word,
                    score=count / len(words),
                    occurrences=count,
                    positions=[],
                    method='SimpleWord'
                )
                for word, count in filtered[:max_keywords]
            ]
        
        def batch_extract(self, texts: list, max_keywords: int = 10):
            return [self.extract(text, max_keywords) for text in texts]
    
    # Register custom extractor
    KeywordExtractorFactory.register_extractor('simple', SimpleWordExtractor)
    
    # Use it
    extractor = create_extractor('simple')
    keywords = extractor.extract("Machine learning drug discovery using deep learning methods", max_keywords=5)
    
    print(f"\nCustom extractor keywords:\n")
    for kw in keywords:
        print(f"  - {kw.keyword} (score: {kw.score:.4f})")


def test_batch_extraction():
    """Test batch extraction performance"""
    import time
    
    print("\n" + "=" * 60)
    print("Testing Batch Extraction Performance")
    print("=" * 60)
    
    # Sample abstracts
    abstracts = [
        "Deep learning for protein structure prediction using AlphaFold and neural networks.",
        "Machine learning in clinical trials: patient selection and outcome prediction.",
        "Natural language processing for mining biomedical literature and electronic health records.",
        "Graph neural networks for molecular property prediction and drug discovery.",
        "Reinforcement learning approaches for automated synthesis planning in chemistry."
    ] * 10  # 50 abstracts
    
    extractor = create_extractor('yake')
    
    print(f"\nProcessing {len(abstracts)} abstracts...")
    start = time.time()
    
    results = extractor.batch_extract(abstracts, max_keywords=5)
    
    elapsed = time.time() - start
    rate = len(abstracts) / elapsed
    
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Rate: {rate:.1f} abstracts/second")
    print(f"  Total keywords extracted: {sum(len(r) for r in results)}")


def main():
    """Run all tests"""
    print("\n🧪 Keyword Extraction Tests\n")
    
    test_yake()
    test_tfidf()
    test_custom_extractor()
    test_batch_extraction()
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
