#!/usr/bin/env python3
"""
Virtual Cell Literature Tracker

Automated literature collection and daily report generation for:
- Virtual Cell modeling
- AI-powered cell simulation
- Digital twin cells
- Computational cell biology
- Systems biology modeling

Inspired by: https://github.com/Maojianq/literature-daily-report
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import yaml

# Add src to path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from data_collector import DataCollector, Paper
from keyword_extractor import create_extractor


# ============================================================================
# Configuration - Virtual Cell Domain
# ============================================================================

# Search queries for Virtual Cell & AI Virtual Cell
VIRTUAL_CELL_QUERIES = [
    # Core Virtual Cell concepts
    "virtual cell modeling",
    "digital twin cell",
    "computational cell model",
    "whole cell simulation",
    "cell-scale modeling",
    
    # AI + Virtual Cell
    "AI virtual cell",
    "machine learning cell model",
    "deep learning cell simulation",
    "neural network cell modeling",
    "foundation model cell biology",
    
    # Systems Biology + Modeling
    "systems biology modeling",
    "multiscale cell model",
    "integrative cell modeling",
    "mechanistic cell model",
    
    # Specific approaches
    "agent-based cell model",
    "ODE cell modeling",
    "spatial cell simulation",
    "stochastic cell model",
]

# Domain-specific keywords for filtering
DOMAIN_KEYWORDS = {
    # [Methodology categories] - keep if matched regardless of organism
    "Modeling": [
        "modeling", "simulation", "computational", "in silico",
        "mathematical model", "mechanistic model", "dynamic model"
    ],
    "AI/ML": [
        "machine learning", "deep learning", "neural network",
        "artificial intelligence", "transformer", "foundation model",
        "language model", "CNN", "GNN", "reinforcement learning"
    ],
    "Multi-scale": [
        "multiscale", "multi-scale", "hierarchical",
        "whole-cell", "whole cell", "integrated model"
    ],
    
    # [Biology categories] - need organism keywords too
    "Cell Biology": [
        "cell signaling", "metabolic pathway", "gene regulation",
        "protein interaction", "cellular process", "organelle"
    ],
    "Systems Biology": [
        "systems biology", "network biology", "pathway analysis",
        "omics integration", "network model"
    ],
    
    # [Organism base] - for filtering
    "Organism keywords": [
        "human", "mammalian", "cell", "tissue",
        "yeast", "bacteria", "E. coli", "S. cerevisiae",
        "mouse", "rat", "organism"
    ],
}

# Top journals in the field
TOP_JOURNALS = [
    "Cell", "Nature", "Science",
    "Cell Systems", "Nature Methods", "Nature Biotechnology",
    "PLOS Computational Biology", "Bioinformatics",
    "Cell Reports", "Molecular Systems Biology",
    "Journal of Cell Biology", "Developmental Cell",
    "BioRxiv", "arXiv"
]


@dataclass
class VirtualCellPaper:
    """Extended paper metadata for Virtual Cell domain"""
    paper: Paper
    categories: List[str]
    is_methodology: bool
    is_domain_relevant: bool
    relevance_score: float
    llm_summary: Optional[str] = None


class VirtualCellTracker:
    """
    Virtual Cell Literature Tracker
    
    Features:
    - Automated collection from PubMed, arXiv, bioRxiv
    - Domain-specific filtering for Virtual Cell research
    - LLM-powered summarization (optional)
    - Daily report generation
    - Categorization by methodology/biology focus
    """
    
    def __init__(self, config_path: str = "config.yaml", output_dir: str = "output"):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = self._load_config()
        
        # Initialize components
        self.collector = DataCollector(
            pubmed_api_key=self.config.get('api_keys', {}).get('pubmed'),
            use_arxiv=True,
            use_biorxiv=True,
            use_semantic_scholar=False
        )
        
        self.extractor = create_extractor('yake', config={
            'num_keywords': 10
        })
        
        # LLM for summarization (optional)
        self.llm_enabled = False
        if self.config.get('llm', {}).get('enabled', False):
            self._init_llm()
        
        logger.info("Virtual Cell Tracker initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def _init_llm(self):
        """Initialize LLM for summarization"""
        try:
            from openai import OpenAI
            
            api_key = self.config.get('llm', {}).get('api_key')
            if api_key:
                self.llm_client = OpenAI(api_key=api_key)
                self.llm_enabled = True
                logger.info("LLM summarization enabled")
            else:
                logger.warning("LLM API key not configured")
        except ImportError:
            logger.warning("OpenAI not installed. LLM summarization disabled.")
    
    def _categorize_paper(self, paper: Paper) -> Dict:
        """
        Categorize paper for Virtual Cell domain
        
        Returns:
            Dict with categories, methodology flags, relevance score
        """
        text = f"{paper.title} {paper.abstract}".lower()
        
        categories = []
        methodology_keywords = []
        biology_keywords = []
        
        # Check methodology categories
        for category, keywords in DOMAIN_KEYWORDS.items():
            if category in ["Organism keywords"]:
                continue
            
            matches = sum(1 for kw in keywords if kw.lower() in text)
            if matches > 0:
                if category in ["Modeling", "AI/ML", "Multi-scale"]:
                    categories.append(category)
                    methodology_keywords.extend([kw for kw in keywords if kw.lower() in text])
                else:
                    biology_keywords.extend([kw for kw in keywords if kw.lower() in text])
        
        # Check organism relevance
        organism_matches = sum(1 for kw in DOMAIN_KEYWORDS["Organism keywords"] if kw.lower() in text)
        is_organism_related = organism_matches > 0
        
        # Determine if methodology-focused
        is_methodology = len(methodology_keywords) > 0
        
        # Relevance scoring
        relevance_score = 0.0
        if is_methodology:
            relevance_score += 0.5  # Methodology papers always relevant
        if is_organism_related:
            relevance_score += 0.3
        if len(categories) > 1:
            relevance_score += 0.2  # Multi-category papers
        
        # Virtual Cell specific boost
        vc_keywords = ["virtual cell", "digital twin", "whole cell", "cell model"]
        if any(kw in text for kw in vc_keywords):
            relevance_score += 1.0  # Core topic
        
        return {
            'categories': list(set(categories)),
            'is_methodology': is_methodology,
            'is_domain_relevant': relevance_score >= 0.5,
            'relevance_score': relevance_score,
            'methodology_keywords': methodology_keywords,
            'biology_keywords': biology_keywords
        }
    
    def _generate_llm_summary(self, paper: Paper) -> Optional[str]:
        """Generate structured summary using LLM"""
        if not self.llm_enabled:
            return None
        
        try:
            prompt = f"""Please read this scientific paper abstract and generate a structured Chinese summary:

Title: {paper.title}

Abstract: {paper.abstract}

Please output in the following format (in Chinese):
【研究目的】: What problem does this study aim to solve?
【研究方法】: What methods/techniques were used?
【研究结论】: What are the main findings?

Keep it concise and professional."""

            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a research assistant specializing in computational biology and virtual cell modeling."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.debug(f"LLM summary failed: {e}")
            return None
    
    def collect_daily(self, days_back: int = 3, max_per_query: int = 50) -> List[VirtualCellPaper]:
        """
        Collect papers from the past N days
        
        Args:
            days_back: Number of days to look back
            max_per_query: Max papers per query
        
        Returns:
            List of categorized VirtualCellPaper objects
        """
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        logger.info(f"Collecting Virtual Cell literature from {from_date} to today")
        logger.info(f"Queries: {len(VIRTUAL_CELL_QUERIES)}")
        
        all_papers = []
        
        for query in VIRTUAL_CELL_QUERIES:
            logger.info(f"Searching: {query}")
            
            try:
                papers = list(self.collector.collect(
                    query=query,
                    from_date=from_date,
                    max_per_source=max_per_query
                ))
                
                logger.info(f"  Found {len(papers)} papers")
                
                for paper in papers:
                    # Categorize
                    cat_info = self._categorize_paper(paper)
                    
                    # Filter by relevance
                    if not cat_info['is_domain_relevant']:
                        continue
                    
                    # Create VirtualCellPaper
                    vc_paper = VirtualCellPaper(
                        paper=paper,
                        categories=cat_info['categories'],
                        is_methodology=cat_info['is_methodology'],
                        is_domain_relevant=cat_info['is_domain_relevant'],
                        relevance_score=cat_info['relevance_score']
                    )
                    
                    # Generate LLM summary for high-relevance papers
                    if vc_paper.relevance_score >= 1.0 and self.llm_enabled:
                        vc_paper.llm_summary = self._generate_llm_summary(paper)
                    
                    all_papers.append(vc_paper)
                
            except Exception as e:
                logger.error(f"Error collecting '{query}': {e}")
                continue
        
        # Remove duplicates by DOI/title
        seen = set()
        unique_papers = []
        for p in all_papers:
            key = p.paper.doi or p.paper.title
            if key not in seen:
                seen.add(key)
                unique_papers.append(p)
        
        # Sort by relevance
        unique_papers.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Total unique papers: {len(unique_papers)}")
        
        return unique_papers
    
    def generate_report(self, papers: List[VirtualCellPaper], date: str = None) -> str:
        """
        Generate daily report in markdown format
        
        Args:
            papers: List of VirtualCellPaper objects
            date: Report date (YYYY-MM-DD)
        
        Returns:
            Markdown report content
        """
        if date is None:
            date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Categorize papers
        high_priority = [p for p in papers if p.relevance_score >= 1.5]
        methodology = [p for p in papers if p.is_methodology]
        biology = [p for p in papers if not p.is_methodology]
        
        # Build report
        report = []
        report.append("# Virtual Cell Literature Daily Report\n")
        report.append(f"**Date:** {date}\n")
        report.append(f"**Total Papers:** {len(papers)}\n")
        report.append(f"**High Priority:** {len(high_priority)}\n")
        report.append(f"**Methodology:** {len(methodology)}\n")
        report.append(f"**Biology Focus:** {len(biology)}\n")
        report.append("\n---\n")
        
        # Executive Summary
        report.append("## 📊 Executive Summary\n")
        if high_priority:
            report.append("**Key Highlights:**\n")
            for i, p in enumerate(high_priority[:5], 1):
                report.append(f"{i}. **{p.paper.title}**")
                if p.llm_summary:
                    report.append(f"   - {p.llm_summary[:200]}...\n")
                else:
                    report.append(f"   - {', '.join(p.categories)}\n")
        report.append("\n---\n")
        
        # Top Journals
        top_journal_papers = [p for p in papers if any(j.lower() in p.paper.journal.lower() for j in TOP_JOURNALS)]
        if top_journal_papers:
            report.append("## 🏆 Top Journal Papers\n")
            for p in top_journal_papers[:10]:
                report.append(f"- **{p.paper.title}**")
                report.append(f"  - *{p.paper.journal}* | {p.paper.publication_date[:10] if p.paper.publication_date else 'N/A'}")
                report.append(f"  - Categories: {', '.join(p.categories)}\n")
            report.append("\n---\n")
        
        # Methodology Papers
        report.append("## 🤖 Methodology Papers (AI/ML/Modeling)\n")
        for p in methodology[:20]:
            report.append(f"- **{p.paper.title}**")
            report.append(f"  - Source: {p.paper.source} | {p.paper.publication_date[:10] if p.paper.publication_date else 'N/A'}")
            report.append(f"  - Categories: {', '.join(p.categories)}")
            if p.llm_summary:
                report.append(f"  - Summary: {p.llm_summary}\n")
            else:
                report.append(f"  - Relevance: {p.relevance_score:.1f}\n")
        report.append("\n---\n")
        
        # Biology Focus Papers
        report.append("## 🧬 Biology Focus Papers\n")
        for p in biology[:20]:
            report.append(f"- **{p.paper.title}**")
            report.append(f"  - Source: {p.paper.source} | {p.paper.publication_date[:10] if p.paper.publication_date else 'N/A'}")
            report.append(f"  - Relevance: {p.relevance_score:.1f}\n")
        report.append("\n---\n")
        
        # Trends
        report.append("## 📈 Trends\n")
        if papers:
            categories_count = {}
            for p in papers:
                for cat in p.categories:
                    categories_count[cat] = categories_count.get(cat, 0) + 1
            
            report.append("**Category Distribution:**\n")
            for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
                report.append(f"- {cat}: {count} papers")
        
        # Footer
        report.append("\n---\n")
        report.append(f"*Generated by Virtual Cell Tracker on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        return '\n'.join(report)
    
    def run(self, days_back: int = 3, max_per_query: int = 50, output_file: str = None):
        """
        Run full pipeline: collect → categorize → generate report
        
        Args:
            days_back: Days to look back
            max_per_query: Max papers per query
            output_file: Output file path (default: output/virtual-cell-{date}.md)
        """
        logger.info("=" * 70)
        logger.info("  VIRTUAL CELL LITERATURE TRACKER")
        logger.info("=" * 70)
        
        # Collect
        papers = self.collect_daily(days_back=days_back, max_per_query=max_per_query)
        
        if not papers:
            logger.warning("No papers found. Try expanding search queries.")
            return
        
        # Generate report
        date = datetime.utcnow().strftime('%Y-%m-%d')
        report = self.generate_report(papers, date)
        
        # Save report
        if output_file is None:
            output_file = self.output_dir / f"virtual-cell-{date}.md"
        else:
            output_file = Path(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n✅ Report saved: {output_file}")
        logger.info(f"📊 Total papers: {len(papers)}")
        logger.info(f"🎯 High priority: {len([p for p in papers if p.relevance_score >= 1.5])}")
        
        # Also save as latest
        latest_file = self.output_dir / "virtual-cell-latest.md"
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📌 Latest report: {latest_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Virtual Cell Literature Tracker')
    parser.add_argument('--days', type=int, default=3, help='Days to look back')
    parser.add_argument('--max', type=int, default=50, help='Max papers per query')
    parser.add_argument('--output', type=str, default=None, help='Output file')
    parser.add_argument('--config', type=str, default='config.yaml', help='Config file')
    
    args = parser.parse_args()
    
    tracker = VirtualCellTracker(config_path=args.config)
    tracker.run(days_back=args.days, max_per_query=args.max, output_file=args.output)


if __name__ == "__main__":
    main()
