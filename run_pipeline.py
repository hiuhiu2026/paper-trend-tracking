#!/usr/bin/env python3
"""
Pipeline Runner

Executes the full paper trend tracking pipeline:
1. Collect papers
2. Extract keywords
3. Build networks
4. Detect trends
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pipeline import PaperTrendPipeline


def setup_logging():
    """Configure logging"""
    log_path = Path(__file__).parent / 'logs' / 'pipeline.log'
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
        format="<green>{time:HH:mm:ss}</green> | <level>{level:8s}</level> | <level>{message}</level>",
        level="INFO"
    )


def main():
    """Main entry point"""
    setup_logging()
    
    logger.info("=" * 70)
    logger.info("  PAPER TREND TRACKING PIPELINE")
    logger.info(f"  Started: {datetime.now().isoformat()}")
    logger.info("=" * 70)
    
    # Load config
    config_path = Path(__file__).parent / 'config.yaml'
    
    if config_path.exists():
        logger.info(f"Loading config: {config_path}")
    else:
        logger.warning("config.yaml not found, using defaults")
        logger.info("Tip: Copy config.example.yaml to config.yaml and customize")
    
    try:
        # Initialize and run pipeline
        pipeline = PaperTrendPipeline.from_config(str(config_path))
        
        # Run full pipeline
        results = pipeline.run_full(
            collection_config={
                # Override defaults if needed
                # 'queries': ['your custom query'],
                # 'max_papers': 200,
                # 'from_date': '2024-01-01'
            },
            network_config={
                # 'time_window': 'month',  # 'week', 'month', 'quarter'
                # 'n_snapshots': 3,
                # 'limit': 50
            }
        )
        
        logger.info("\n" + "=" * 70)
        logger.info("  ✅ PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)
        
        # Print summary
        print("\n📊 Summary:")
        print(f"   Papers collected:    {results['papers_collected']}")
        print(f"   Network snapshots:   {results['snapshots_built']}")
        print(f"   Trending keywords:   {results['trending_keywords']}")
        print(f"   Emerging clusters:   {results['emerging_clusters']}")
        
        print(f"\n   Database stats:")
        for key, value in results['db_stats'].items():
            print(f"     - {key}: {value}")
        
        print("\n📁 Output files:")
        print(f"   - Database: {Path(__file__).parent / pipeline.db_path}")
        print(f"   - Logs: {Path(__file__).parent / 'logs' / 'pipeline.log'}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
