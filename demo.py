#!/usr/bin/env python3
"""
Demo: Paper Trend Tracking System

Shows the system working with sample data (no API calls needed).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from data_collector import Paper
from database import DatabaseManager
from keyword_extractor import create_extractor
from network_builder import NetworkBuilder, TrendAnalyzer
from visualization import NetworkVisualizer, create_visualizations


def create_sample_papers():
    """Create sample papers for demonstration"""
    
    sample_data = [
        {
            'title': "Deep learning for drug discovery: A comprehensive review",
            'abstract': "Machine learning and deep learning approaches have revolutionized drug discovery. Graph neural networks predict molecular properties while transformer models analyze biomedical literature. This review covers recent advances in AI-driven pharmaceutical research.",
            'authors': ["Smith, J.", "Chen, L."],
            'journal': "Nature Machine Intelligence",
            'date': "2026-03-15"
        },
        {
            'title': "Graph neural networks for molecular property prediction",
            'abstract': "We present a novel graph neural network architecture for predicting drug-target interactions. Our model achieves 94% accuracy on benchmark datasets and identifies promising drug candidates for Alzheimer's disease.",
            'authors': ["Johnson, A.", "Williams, R."],
            'journal': "Journal of Chemical Information and Modeling",
            'date': "2026-03-18"
        },
        {
            'title': "Transformer models in biomedical text mining",
            'abstract': "Large language models and transformer architectures enable automated extraction of drug-drug interactions from PubMed literature. Our BERT-based system outperforms traditional NLP methods.",
            'authors': ["Brown, K.", "Davis, M."],
            'journal': "Bioinformatics",
            'date': "2026-03-20"
        },
        {
            'title': "AI-powered clinical trial design and patient recruitment",
            'abstract': "Machine learning optimizes clinical trial protocols and identifies eligible patients from electronic health records. Deep learning models predict trial outcomes and reduce recruitment time by 40%.",
            'authors': ["Lee, S.", "Garcia, P."],
            'journal': "Nature Medicine",
            'date': "2026-03-22"
        },
        {
            'title': "Reinforcement learning for de novo drug design",
            'abstract': "Generative models and reinforcement learning create novel molecular structures with desired properties. Our approach discovers drug-like compounds optimized for binding affinity and solubility.",
            'authors': ["Wilson, T.", "Martinez, A."],
            'journal': "Science",
            'date': "2026-03-25"
        },
        {
            'title': "Federated learning for privacy-preserving medical AI",
            'abstract': "Federated learning enables collaborative model training across hospitals without sharing patient data. We demonstrate improved drug response prediction while maintaining privacy.",
            'authors': ["Anderson, B.", "Taylor, C."],
            'journal': "Nature Biotechnology",
            'date': "2026-03-28"
        },
        {
            'title': "Multi-omics integration with deep learning for precision medicine",
            'abstract': "Deep learning models integrate genomics, proteomics, and metabolomics data for personalized treatment recommendations. Our framework identifies biomarkers for cancer drug response.",
            'authors': ["Thomas, E.", "White, D."],
            'journal': "Cell",
            'date': "2026-04-01"
        },
        {
            'title': "Explainable AI for drug discovery: Interpretable deep learning models",
            'abstract': "We develop interpretable machine learning models that provide insights into drug-target binding mechanisms. Attention mechanisms highlight key molecular features driving predictions.",
            'authors': ["Harris, N.", "Clark, F."],
            'journal': "Nature Communications",
            'date': "2026-04-05"
        }
    ]
    
    papers = []
    for i, data in enumerate(sample_data):
        paper = Paper(
            id=f"DEMO:{i:03d}",
            title=data['title'],
            abstract=data['abstract'],
            authors=data['authors'],
            publication_date=data['date'],
            journal=data['journal'],
            doi=None,
            keywords=[],  # Will be extracted
            source='demo',
            url='https://example.com'
        )
        papers.append(paper)
    
    return papers


def main():
    """Run demo pipeline"""
    print("=" * 70)
    print("  PAPER TREND TRACKING - DEMO")
    print("  Using sample data (no API calls)")
    print("=" * 70)
    print()
    
    # Initialize components
    db = DatabaseManager("sqlite:///data/demo.db")
    extractor = create_extractor('yake', config={'num_keywords': 8})
    
    # Create and insert sample papers
    print("📚 Creating sample papers...")
    papers = create_sample_papers()
    
    papers_with_keywords = []
    for paper in papers:
        text = f"{paper.title}. {paper.abstract}"
        keywords = extractor.extract(text, max_keywords=8)
        kw_names = [kw.keyword for kw in keywords]
        papers_with_keywords.append((paper, kw_names))
        print(f"   ✓ {paper.title[:60]}...")
        print(f"     Keywords: {', '.join(kw_names[:5])}")
    
    print(f"\n💾 Inserting into database...")
    added = db.add_papers_batch(papers_with_keywords)
    print(f"   Added {added} papers with {sum(len(pw[1]) for pw in papers_with_keywords)} keywords")
    
    # Build network
    print(f"\n🔗 Building keyword network...")
    builder = NetworkBuilder(db, min_cooccurrence=2)
    
    from_date = datetime.utcnow() - timedelta(days=90)
    snapshots = builder.build_snapshots(
        from_date=from_date,
        time_window='month',
        overwrite=True
    )
    
    if snapshots:
        print(f"   Built {len(snapshots)} snapshot(s)")
        for s in snapshots:
            print(f"   - {s.start_date.date()}: {s.num_nodes} nodes, {s.num_edges} edges")
    
    # Analyze trends
    print(f"\n📈 Analyzing trends...")
    analyzer = TrendAnalyzer(db)
    analyzer.compute_trend_metrics(snapshots)
    
    trends = analyzer.get_trending_keywords(limit=10)
    print(f"\n🔥 Top trending keywords:")
    for i, kw in enumerate(trends[:10], 1):
        print(f"   {i:2d}. {kw['keyword']:35s} (growth: {kw.get('growth_rate', 0):.2f})")
    
    # Create visualizations
    print(f"\n📊 Creating visualizations...")
    create_visualizations("data/demo.db")
    
    # Stats
    stats = db.get_stats()
    print(f"\n📁 Database stats:")
    for key, value in stats.items():
        print(f"   - {key}: {value}")
    
    print("\n" + "=" * 70)
    print("  ✅ DEMO COMPLETE!")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  - Database: data/demo.db")
    print(f"  - Visualizations: output/visualizations/")
    print(f"  - Logs: logs/")
    print()


if __name__ == "__main__":
    main()
