"""
Main Pipeline for Paper Trend Tracking

Orchestrates the full workflow:
1. Collect papers from APIs
2. Extract keywords
3. Build time-sliced networks
4. Compute trend metrics
5. Output trending keywords/clusters
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
import yaml

try:
    from .data_collector import DataCollector
    from .database import DatabaseManager
    from .keyword_extractor import create_extractor, BaseKeywordExtractor
    from .network_builder import NetworkBuilder, TrendAnalyzer, KeywordNetworkSnapshot
except ImportError:
    from data_collector import DataCollector
    from database import DatabaseManager
    from keyword_extractor import create_extractor, BaseKeywordExtractor
    from network_builder import NetworkBuilder, TrendAnalyzer, KeywordNetworkSnapshot


class PaperTrendPipeline:
    """
    End-to-end pipeline for paper trend tracking
    
    Usage:
        pipeline = PaperTrendPipeline.from_config('config.yaml')
        pipeline.run()
    """
    
    def __init__(
        self,
        config: Dict,
        db_path: str = "data/papers.db",
        base_dir: str = None
    ):
        """
        Args:
            config: Configuration dictionary
            db_path: Path to SQLite database (relative to base_dir)
            base_dir: Base directory for the project (defaults to current dir)
        """
        self.config = config
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # Ensure db_path is absolute
        db_path_obj = Path(db_path)
        if not db_path_obj.is_absolute():
            db_path_obj = self.base_dir / db_path_obj
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path_obj)
        
        logger.info(f"Database path: {self.db_path}")
        
        # Initialize components
        self.collector = DataCollector(
            pubmed_api_key=config.get('api_keys', {}).get('pubmed'),
            s2_api_key=config.get('api_keys', {}).get('semantic_scholar')
        )
        
        self.db = DatabaseManager(f"sqlite:///{self.db_path}")
        
        # Keyword extractor
        kw_config = config.get('keywords', {})
        method = kw_config.get('method', 'yake')
        method_config = kw_config.get(method, {})
        self.extractor = create_extractor(method, config=method_config)
        
        # Network builder
        network_config = config.get('network', {})
        self.network_builder = NetworkBuilder(
            self.db,
            min_cooccurrence=network_config.get('min_cooccurrence', 2)
        )
        
        # Trend analyzer
        self.trend_analyzer = TrendAnalyzer(self.db)
        
        logger.info("Pipeline initialized")
    
    @classmethod
    def from_config(cls, config_path: str) -> 'PaperTrendPipeline':
        """Create pipeline from YAML config file"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            config = {
                'api_keys': {'pubmed': None, 'semantic_scholar': None},
                'collection': {
                    'tracked_queries': ['machine learning'],
                    'max_papers_per_query': 100,
                    'from_date': '2024-01-01'
                },
                'keywords': {'method': 'yake'},
                'network': {'min_cooccurrence': 2},
                'database': {'path': 'data/papers.db'}
            }
        else:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        
        db_path = config.get('database', {}).get('path', 'data/papers.db')
        return cls(config, db_path)
    
    def run_collection(
        self,
        queries: List[str] = None,
        max_per_query: int = 100,
        from_date: str = None
    ) -> int:
        """
        Run paper collection phase
        
        Args:
            queries: List of search queries (uses config if None)
            max_per_query: Max papers per query
            from_date: Start date (YYYY-MM-DD)
        
        Returns:
            Number of papers collected
        """
        coll_config = self.config.get('collection', {})
        queries = queries or coll_config.get('tracked_queries', ['machine learning'])
        max_per_query = max_per_query or coll_config.get('max_papers_per_query', 100)
        from_date = from_date or coll_config.get('from_date')
        sources = coll_config.get('default_sources', ['pubmed', 'semanticscholar'])
        
        logger.info("=" * 60)
        logger.info("PHASE 1: Paper Collection")
        logger.info("=" * 60)
        
        total_collected = 0
        total_added = 0
        
        for query in queries:
            logger.info(f"\n📚 Collecting: '{query}'")
            
            papers_batch = []
            
            try:
                for paper in self.collector.collect(
                    query=query,
                    sources=sources,
                    from_date=from_date,
                    max_per_source=max_per_query
                ):
                    papers_batch.append(paper)
                    total_collected += 1
                    
                    # Progress
                    if total_collected % 20 == 0:
                        logger.info(f"   → {total_collected} papers...")
                    
                    # Batch insert every 50
                    if len(papers_batch) >= 50:
                        added = self._insert_batch(papers_batch)
                        total_added += added
                        papers_batch = []
                
                # Insert remaining
                if papers_batch:
                    added = self._insert_batch(papers_batch)
                    total_added += added
                
            except Exception as e:
                logger.error(f"Error collecting '{query}': {e}")
                continue
        
        logger.info(f"\n✅ Collection complete: {total_added} papers added")
        return total_added
    
    def _insert_batch(self, papers) -> int:
        """Insert batch of papers with extracted keywords"""
        papers_with_keywords = []
        
        for paper in papers:
            # Extract keywords from title + abstract
            text = f"{paper.title}. {paper.abstract}"
            
            # Use existing keywords if available (e.g., MeSH from PubMed)
            if paper.keywords and len(paper.keywords) > 0:
                kw_names = paper.keywords
            else:
                # Extract keywords
                extracted = self.extractor.extract(text, max_keywords=10)
                kw_names = [kw.keyword for kw in extracted]
            
            papers_with_keywords.append((paper, kw_names))
        
        return self.db.add_papers_batch(papers_with_keywords)
    
    def run_network_analysis(
        self,
        from_date: datetime = None,
        to_date: datetime = None,
        time_window: str = 'month',
        overwrite: bool = False
    ) -> int:
        """
        Run network building and trend analysis
        
        Args:
            from_date: Start date for snapshots
            to_date: End date
            time_window: 'week', 'month', or 'quarter'
            overwrite: Rebuild existing snapshots
        
        Returns:
            Number of snapshots built
        """
        logger.info("=" * 60)
        logger.info("PHASE 2: Network Analysis")
        logger.info("=" * 60)
        
        from_date = from_date or (datetime.utcnow() - timedelta(days=365))
        to_date = to_date or datetime.utcnow()
        
        # Build snapshots
        snapshots = self.network_builder.build_snapshots(
            from_date=from_date,
            to_date=to_date,
            time_window=time_window,
            overwrite=overwrite
        )
        
        if not snapshots:
            logger.warning("No snapshots built")
            return 0
        
        logger.info(f"Built {len(snapshots)} snapshots")
        
        # Compute trend metrics
        logger.info("\nComputing trend metrics...")
        self.trend_analyzer.compute_trend_metrics(snapshots)
        
        return len(snapshots)
    
    def get_trends(
        self,
        n_snapshots: int = 3,
        min_growth: float = 0.1,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get trending keywords
        
        Args:
            n_snapshots: Number of recent snapshots to consider
            min_growth: Minimum growth rate
            limit: Max results
        
        Returns:
            List of trending keyword data
        """
        logger.info("=" * 60)
        logger.info("PHASE 3: Trend Detection")
        logger.info("=" * 60)
        
        trending = self.trend_analyzer.get_trending_keywords(
            n_snapshots=n_snapshots,
            min_growth=min_growth,
            limit=limit
        )
        
        logger.info(f"\n🔥 Top {len(trending)} trending keywords:")
        for i, kw in enumerate(trending[:10], 1):
            logger.info(f"  {i:2d}. {kw['keyword']:40s} (growth: {kw['growth_rate']:.2f}, momentum: {kw['momentum']:.2f})")
        
        return trending
    
    def get_emerging_clusters(
        self,
        min_size: int = 3
    ) -> List[Dict]:
        """
        Get emerging keyword clusters
        
        Args:
            min_size: Minimum cluster size
        
        Returns:
            List of cluster data
        """
        # Get latest snapshot
        session = self.db.get_session()
        try:
            try:
                from .network_builder import NetworkBuilder
            except ImportError:
                from network_builder import NetworkBuilder
            builder = NetworkBuilder(self.db)
            
            latest_snapshot = session.query(KeywordNetworkSnapshot).order_by(
                KeywordNetworkSnapshot.snapshot_date.desc()
            ).first()
            
            if not latest_snapshot:
                return []
            
            snapshot = builder._load_snapshot(latest_snapshot)
            clusters = self.trend_analyzer.get_emerging_clusters(snapshot, min_size)
            
            logger.info(f"\n🔗 Found {len(clusters)} emerging clusters:")
            for i, cluster in enumerate(clusters[:5], 1):
                logger.info(f"  {i:2d}. Size={cluster['size']}, Growth={cluster['avg_growth_rate']:.2f}")
                logger.info(f"      Keywords: {', '.join(cluster['keywords'][:5])}...")
            
            return clusters
            
        finally:
            session.close()
    
    def run_full(
        self,
        collection_config: Dict = None,
        network_config: Dict = None
    ) -> Dict:
        """
        Run full pipeline: collection → network → trends
        
        Args:
            collection_config: Override collection settings
            network_config: Override network settings
        
        Returns:
            Summary statistics
        """
        collection_config = collection_config or {}
        network_config = network_config or {}
        
        # Phase 1: Collection
        papers_collected = self.run_collection(
            queries=collection_config.get('queries'),
            max_per_query=collection_config.get('max_papers'),
            from_date=collection_config.get('from_date')
        )
        
        # Phase 2: Network analysis
        snapshots_built = self.run_network_analysis(
            from_date=network_config.get('from_date'),
            time_window=network_config.get('time_window', 'month')
        )
        
        # Phase 3: Trends
        trends = self.get_trends(
            n_snapshots=network_config.get('n_snapshots', 3),
            limit=network_config.get('limit', 50)
        )
        
        clusters = self.get_emerging_clusters()
        
        # Summary
        summary = {
            'papers_collected': papers_collected,
            'snapshots_built': snapshots_built,
            'trending_keywords': len(trends),
            'emerging_clusters': len(clusters),
            'db_stats': self.db.get_stats()
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"  Papers: {summary['papers_collected']}")
        logger.info(f"  Snapshots: {summary['snapshots_built']}")
        logger.info(f"  Trending keywords: {summary['trending_keywords']}")
        logger.info(f"  Emerging clusters: {summary['emerging_clusters']}")
        
        return summary


def run_pipeline(config_path: str = "config.yaml"):
    """Convenience function to run full pipeline"""
    pipeline = PaperTrendPipeline.from_config(config_path)
    return pipeline.run_full()


if __name__ == "__main__":
    # Run with default config
    run_pipeline()
