#!/usr/bin/env python3
"""
Paper Collection Runner

Collects papers from configured sources and stores them in the database.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_collector import DataCollector, Paper
from database import DatabaseManager


def setup_logging(log_file: str = "logs/collector.log"):
    """Configure logging"""
    log_path = Path(__file__).parent / log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.remove()
    logger.add(
        str(log_path),
        rotation="10 MB",
        retention="7 days",
        level="INFO"
    )
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
        level="INFO"
    )


def load_config():
    """Load configuration from YAML file"""
    import yaml
    
    config_path = Path(__file__).parent / 'config.yaml'
    if not config_path.exists():
        logger.warning("config.yaml not found, using defaults")
        return {
            'api_keys': {'pubmed': None, 'semantic_scholar': None},
            'collection': {
                'default_sources': ['pubmed', 'semanticscholar'],
                'max_papers_per_query': 100,
                'tracked_queries': ['machine learning'],
                'from_date': '2024-01-01'
            },
            'database': {'path': 'data/papers.db'}
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main collection runner"""
    setup_logging()
    logger.info("=" * 60)
    logger.info("Starting paper collection")
    logger.info("=" * 60)
    
    # Load config
    config = load_config()
    
    # Initialize components
    collector = DataCollector(
        pubmed_api_key=config['api_keys'].get('pubmed'),
        s2_api_key=config['api_keys'].get('semantic_scholar')
    )
    
    db_path = Path(__file__).parent / config['database']['path']
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    db = DatabaseManager(f"sqlite:///{db_path}")
    
    # Collection settings
    queries = config['collection']['tracked_queries']
    max_papers = config['collection']['max_papers_per_query']
    from_date = config['collection']['from_date']
    sources = config['collection']['default_sources']
    
    total_collected = 0
    total_added = 0
    
    for query in queries:
        logger.info(f"\n📚 Collecting: '{query}'")
        logger.info(f"   From: {from_date or 'beginning'} | Max: {max_papers} papers")
        
        papers_batch = []
        
        try:
            for paper in collector.collect(
                query=query,
                sources=sources,
                from_date=from_date,
                max_per_source=max_papers
            ):
                papers_batch.append(paper)
                total_collected += 1
                
                # Progress indicator
                if total_collected % 10 == 0:
                    logger.info(f"   → {total_collected} papers collected...")
                
                # Batch insert every 50 papers
                if len(papers_batch) >= 50:
                    added = db.add_papers_batch([(p, p.keywords) for p in papers_batch])
                    total_added += added
                    logger.info(f"   ✓ Added {added} papers to database")
                    papers_batch = []
            
            # Insert remaining papers
            if papers_batch:
                added = db.add_papers_batch([(p, p.keywords) for p in papers_batch])
                total_added += added
                logger.info(f"   ✓ Added {added} papers to database")
        
        except Exception as e:
            logger.error(f"Error collecting '{query}': {e}")
            continue
    
    # Final stats
    logger.info("\n" + "=" * 60)
    logger.info("Collection complete!")
    logger.info(f"   Total collected: {total_collected}")
    logger.info(f"   Total added to DB: {total_added}")
    logger.info(f"   Database stats: {db.get_stats()}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
