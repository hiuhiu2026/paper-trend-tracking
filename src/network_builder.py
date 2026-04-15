"""
Network Builder for Keyword Co-occurrence Analysis

Builds time-sliced keyword networks where:
- Nodes = keywords
- Edges = keywords co-occurring in the same paper
- Edge weights = co-occurrence frequency

Supports:
- Temporal slicing (weekly/monthly/quarterly)
- Network metrics computation
- Trend detection via metric evolution
"""

import networkx as nx
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from loguru import logger
import json

from .database import DatabaseManager, PaperModel, KeywordModel, KeywordNetworkSnapshot, TrendMetrics


@dataclass
class NetworkSnapshot:
    """Represents a time-sliced keyword network"""
    snapshot_id: int
    start_date: datetime
    end_date: datetime
    time_window: str  # 'week', 'month', 'quarter'
    
    # Network data
    graph: nx.Graph = field(default_factory=nx.Graph)
    edges: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Statistics
    num_nodes: int = 0
    num_edges: int = 0
    avg_degree: float = 0.0
    density: float = 0.0
    num_components: int = 0
    
    # Top keywords by various metrics
    top_by_degree: List[Tuple[str, float]] = field(default_factory=list)
    top_by_betweenness: List[Tuple[str, float]] = field(default_factory=list)
    top_by_pagerank: List[Tuple[str, float]] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            'snapshot_id': self.snapshot_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'time_window': self.time_window,
            'num_nodes': self.num_nodes,
            'num_edges': self.num_edges,
            'avg_degree': self.avg_degree,
            'density': self.density,
            'num_components': self.num_components,
            'top_by_degree': self.top_by_degree[:20],
            'top_by_betweenness': self.top_by_betweenness[:20],
            'top_by_pagerank': self.top_by_pagerank[:20],
            'edges': {k: dict(v) for k, v in self.edges.items()}
        }


class NetworkBuilder:
    """
    Builds and analyzes keyword co-occurrence networks
    
    Usage:
        builder = NetworkBuilder(db)
        snapshots = builder.build_snapshots(
            from_date=datetime(2024, 1, 1),
            time_window='month'
        )
    """
    
    def __init__(self, db: DatabaseManager, min_cooccurrence: int = 2):
        """
        Args:
            db: Database manager instance
            min_cooccurrence: Minimum co-occurrences to create an edge
        """
        self.db = db
        self.min_cooccurrence = min_cooccurrence
        logger.info(f"Network builder initialized (min_cooccurrence={min_cooccurrence})")
    
    def build_snapshots(
        self,
        from_date: datetime,
        to_date: datetime = None,
        time_window: str = 'month',
        overwrite: bool = False
    ) -> List[NetworkSnapshot]:
        """
        Build time-sliced network snapshots
        
        Args:
            from_date: Start date
            to_date: End date (default: now)
            time_window: 'week', 'month', or 'quarter'
            overwrite: Rebuild existing snapshots
        
        Returns:
            List of NetworkSnapshot objects
        """
        to_date = to_date or datetime.utcnow()
        session = self.db.get_session()
        
        try:
            # Check existing snapshots
            if not overwrite:
                existing = session.query(KeywordNetworkSnapshot).filter(
                    KeywordNetworkSnapshot.snapshot_date >= from_date,
                    KeywordNetworkSnapshot.snapshot_date <= to_date,
                    KeywordNetworkSnapshot.time_window == time_window
                ).all()
                
                if existing:
                    logger.info(f"Found {len(existing)} existing snapshots, skipping")
                    return [self._load_snapshot(s) for s in existing]
            
            # Generate time windows
            windows = self._generate_time_windows(from_date, to_date, time_window)
            logger.info(f"Building {len(windows)} {time_window} snapshots...")
            
            snapshots = []
            for i, (start, end) in enumerate(windows, 1):
                logger.info(f"  [{i}/{len(windows)}] Building snapshot: {start.date()} → {end.date()}")
                
                snapshot = self._build_single_snapshot(start, end, time_window, i)
                if snapshot and snapshot.num_nodes > 0:
                    snapshots.append(snapshot)
                    self._save_snapshot(snapshot, session)
            
            logger.info(f"Built {len(snapshots)} snapshots")
            return snapshots
            
        finally:
            session.close()
    
    def _generate_time_windows(
        self,
        from_date: datetime,
        to_date: datetime,
        time_window: str
    ) -> List[Tuple[datetime, datetime]]:
        """Generate list of (start, end) date tuples for time windows"""
        windows = []
        
        if time_window == 'week':
            delta = timedelta(weeks=1)
        elif time_window == 'month':
            delta = timedelta(days=30)
        elif time_window == 'quarter':
            delta = timedelta(days=90)
        else:
            raise ValueError(f"Unknown time_window: {time_window}")
        
        current_start = from_date
        while current_start < to_date:
            current_end = min(current_start + delta, to_date)
            windows.append((current_start, current_end))
            current_start = current_end
        
        return windows
    
    def _build_single_snapshot(
        self,
        start_date: datetime,
        end_date: datetime,
        time_window: str,
        snapshot_id: int
    ) -> Optional[NetworkSnapshot]:
        """Build a single time-sliced network"""
        session = self.db.get_session()
        
        try:
            # Get papers in this time window
            papers = session.query(PaperModel).filter(
                PaperModel.collected_at >= start_date,
                PaperModel.collected_at <= end_date
            ).all()
            
            if not papers:
                logger.debug(f"  No papers in window {start_date.date()} - {end_date.date()}")
                return None
            
            logger.debug(f"  Found {len(papers)} papers")
            
            # Build co-occurrence matrix
            cooccurrences = defaultdict(lambda: defaultdict(int))
            keyword_papers = defaultdict(set)
            
            for paper in papers:
                # Get keywords for this paper
                paper_keywords = [kw.name for kw in paper.keywords]
                
                if len(paper_keywords) < 2:
                    continue
                
                # Count co-occurrences
                for i, kw1 in enumerate(paper_keywords):
                    keyword_papers[kw1].add(paper.id)
                    for kw2 in paper_keywords[i+1:]:
                        cooccurrences[kw1][kw2] += 1
                        cooccurrences[kw2][kw1] += 1
            
            # Build graph
            G = nx.Graph()
            
            # Add nodes with attributes
            for keyword, paper_set in keyword_papers.items():
                G.add_node(
                    keyword,
                    occurrences=len(paper_set),
                    papers=paper_set
                )
            
            # Add edges (filtered by min_cooccurrence)
            for kw1, neighbors in cooccurrences.items():
                for kw2, count in neighbors.items():
                    if count >= self.min_cooccurrence and kw1 < kw2:  # Avoid duplicates
                        G.add_edge(kw1, kw2, weight=count)
            
            # Compute network statistics
            snapshot = NetworkSnapshot(
                snapshot_id=snapshot_id,
                start_date=start_date,
                end_date=end_date,
                time_window=time_window,
                graph=G
            )
            
            snapshot.num_nodes = G.number_of_nodes()
            snapshot.num_edges = G.number_of_edges()
            snapshot.avg_degree = np.mean([d for _, d in G.degree()]) if G.number_of_nodes() > 0 else 0
            snapshot.density = nx.density(G)
            snapshot.num_components = nx.number_connected_components(G)
            
            # Store edges as dict
            snapshot.edges = {u: dict(v) for u, v in G.edges(data=True)}
            
            # Compute centrality metrics
            if snapshot.num_nodes > 0:
                # Degree centrality
                degree_cent = nx.degree_centrality(G)
                snapshot.top_by_degree = sorted(
                    degree_cent.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]
                
                # Betweenness centrality (expensive for large graphs)
                if snapshot.num_nodes < 1000:
                    betweenness = nx.betweenness_centrality(G, weight='weight')
                    snapshot.top_by_betweenness = sorted(
                        betweenness.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:20]
                
                # PageRank
                pagerank = nx.pagerank(G, weight='weight')
                snapshot.top_by_pagerank = sorted(
                    pagerank.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:20]
            
            logger.debug(f"  Network: {snapshot.num_nodes} nodes, {snapshot.num_edges} edges")
            return snapshot
            
        except Exception as e:
            logger.error(f"Error building snapshot: {e}")
            return None
        finally:
            session.close()
    
    def _load_snapshot(self, db_snapshot: KeywordNetworkSnapshot) -> NetworkSnapshot:
        """Load snapshot from database"""
        snapshot = NetworkSnapshot(
            snapshot_id=db_snapshot.id,
            start_date=db_snapshot.snapshot_date - self._parse_window(db_snapshot.time_window),
            end_date=db_snapshot.snapshot_date,
            time_window=db_snapshot.time_window,
            num_nodes=db_snapshot.num_nodes,
            num_edges=db_snapshot.num_edges,
            avg_degree=db_snapshot.avg_degree,
            density=db_snapshot.density
        )
        
        # Reconstruct graph from edges
        edges_data = json.loads(db_snapshot.edges)
        G = nx.Graph()
        for u, neighbors in edges_data.items():
            for v, data in neighbors.items():
                G.add_edge(u, v, **data)
        
        snapshot.graph = G
        snapshot.edges = edges_data
        
        return snapshot
    
    def _parse_window(self, window_str: str) -> timedelta:
        """Parse time window string to timedelta"""
        if window_str == 'week':
            return timedelta(weeks=1)
        elif window_str == 'month':
            return timedelta(days=30)
        elif window_str == 'quarter':
            return timedelta(days=90)
        return timedelta(days=30)
    
    def _save_snapshot(self, snapshot: NetworkSnapshot, session):
        """Save snapshot to database"""
        db_snapshot = KeywordNetworkSnapshot(
            snapshot_date=snapshot.end_date,
            time_window=snapshot.time_window,
            edges=json.dumps(snapshot.edges),
            num_nodes=snapshot.num_nodes,
            num_edges=snapshot.num_edges,
            avg_degree=snapshot.avg_degree,
            density=snapshot.density
        )
        
        session.add(db_snapshot)
        session.commit()
        snapshot.snapshot_id = db_snapshot.id


class TrendAnalyzer:
    """
    Analyzes keyword trends across network snapshots
    
    Identifies:
    - Emerging keywords (rapidly growing centrality)
    - Declining keywords (losing importance)
    - Stable keywords (consistent presence)
    - Trending clusters (groups of related emerging keywords)
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        logger.info("Trend analyzer initialized")
    
    def compute_trend_metrics(self, snapshots: List[NetworkSnapshot]):
        """
        Compute trend metrics for all keywords across snapshots
        
        Args:
            snapshots: List of NetworkSnapshot objects (chronological order)
        """
        session = self.db.get_session()
        
        try:
            for snapshot in snapshots:
                logger.debug(f"Computing metrics for snapshot {snapshot.snapshot_id}")
                
                # Get keyword IDs
                keyword_map = {}
                for keyword, _ in snapshot.top_by_degree:
                    kw_model = session.query(KeywordModel).filter(
                        KeywordModel.name == keyword
                    ).first()
                    if kw_model:
                        keyword_map[keyword] = kw_model.id
                
                # Compute metrics for each keyword
                for keyword, score in snapshot.top_by_degree:
                    if keyword not in keyword_map:
                        continue
                    
                    kw_id = keyword_map[keyword]
                    
                    # Get scores from different centrality measures
                    degree_score = dict(snapshot.top_by_degree).get(keyword, 0)
                    betweenness_score = dict(snapshot.top_by_betweenness).get(keyword, 0)
                    pagerank_score = dict(snapshot.top_by_pagerank).get(keyword, 0)
                    
                    # Get occurrence count
                    node_data = snapshot.graph.nodes.get(keyword, {})
                    occurrence_count = node_data.get('occurrences', 0)
                    
                    # Calculate growth rate (compare to previous snapshot)
                    growth_rate = self._calculate_growth_rate(
                        session, kw_id, snapshot.snapshot_date, occurrence_count
                    )
                    
                    # Calculate momentum (acceleration)
                    momentum = self._calculate_momentum(
                        session, kw_id, snapshot.snapshot_date, growth_rate
                    )
                    
                    # Save metrics
                    metric = TrendMetrics(
                        keyword_id=kw_id,
                        snapshot_date=snapshot.end_date,
                        degree=degree_score,
                        betweenness=betweenness_score,
                        pagerank=pagerank_score,
                        clustering_coefficient=0.0,  # Could compute per-node
                        occurrence_count=occurrence_count,
                        growth_rate=growth_rate,
                        momentum=momentum
                    )
                    
                    session.add(metric)
                
                session.commit()
            
            logger.info(f"Computed metrics for {len(snapshots)} snapshots")
            
        finally:
            session.close()
    
    def _calculate_growth_rate(
        self,
        session,
        keyword_id: int,
        current_date: datetime,
        current_count: int
    ) -> float:
        """Calculate growth rate compared to previous snapshot"""
        previous = session.query(TrendMetrics).filter(
            TrendMetrics.keyword_id == keyword_id,
            TrendMetrics.snapshot_date < current_date
        ).order_by(TrendMetrics.snapshot_date.desc()).first()
        
        if not previous or previous.occurrence_count == 0:
            return float('inf') if current_count > 0 else 0.0
        
        return (current_count - previous.occurrence_count) / previous.occurrence_count
    
    def _calculate_momentum(
        self,
        session,
        keyword_id: int,
        current_date: datetime,
        current_growth: float
    ) -> float:
        """Calculate momentum (change in growth rate)"""
        previous = session.query(TrendMetrics).filter(
            TrendMetrics.keyword_id == keyword_id,
            TrendMetrics.snapshot_date < current_date
        ).order_by(TrendMetrics.snapshot_date.desc()).first()
        
        if not previous:
            return 0.0
        
        return current_growth - (previous.growth_rate if previous.growth_rate != float('inf') else 0)
    
    def get_trending_keywords(
        self,
        n_snapshots: int = 3,
        min_growth: float = 0.1,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get keywords with highest growth momentum
        
        Args:
            n_snapshots: Number of recent snapshots to consider
            min_growth: Minimum growth rate threshold
            limit: Maximum keywords to return
        
        Returns:
            List of keyword trend data
        """
        session = self.db.get_session()
        
        try:
            # Get most recent snapshots
            recent_snapshots = session.query(TrendMetrics.snapshot_date).distinct().order_by(
                TrendMetrics.snapshot_date.desc()
            ).limit(n_snapshots).all()
            
            if not recent_snapshots:
                return []
            
            # Get latest snapshot date
            latest_date = recent_snapshots[0][0]
            
            # Get metrics from latest snapshot
            latest_metrics = session.query(TrendMetrics).filter(
                TrendMetrics.snapshot_date == latest_date,
                TrendMetrics.growth_rate >= min_growth
            ).order_by(
                TrendMetrics.momentum.desc(),
                TrendMetrics.growth_rate.desc()
            ).limit(limit).all()
            
            results = []
            for metric in latest_metrics:
                keyword = session.query(KeywordModel).filter(
                    KeywordModel.id == metric.keyword_id
                ).first()
                
                results.append({
                    'keyword': keyword.name if keyword else f'ID:{metric.keyword_id}',
                    'normalized_keyword': keyword.normalized_name if keyword else None,
                    'growth_rate': metric.growth_rate,
                    'momentum': metric.momentum,
                    'degree': metric.degree,
                    'betweenness': metric.betweenness,
                    'pagerank': metric.pagerank,
                    'occurrence_count': metric.occurrence_count,
                    'snapshot_date': metric.snapshot_date.isoformat()
                })
            
            return results
            
        finally:
            session.close()
    
    def get_emerging_clusters(
        self,
        snapshot: NetworkSnapshot,
        min_size: int = 3
    ) -> List[Dict]:
        """
        Detect emerging keyword clusters
        
        Args:
            snapshot: Network snapshot
            min_size: Minimum cluster size
        
        Returns:
            List of cluster info
        """
        G = snapshot.graph
        
        # Find connected components (simple clustering)
        components = list(nx.connected_components(G))
        
        # Filter by size and compute cluster stats
        clusters = []
        for i, component in enumerate(components):
            if len(component) < min_size:
                continue
            
            # Check if cluster is "emerging" (high average growth)
            session = self.db.get_session()
            try:
                avg_growth = 0
                for keyword in component:
                    kw_model = session.query(KeywordModel).filter(
                        KeywordModel.name == keyword
                    ).first()
                    if kw_model:
                        latest_metric = session.query(TrendMetrics).filter(
                            TrendMetrics.keyword_id == kw_model.id
                        ).order_by(TrendMetrics.snapshot_date.desc()).first()
                        if latest_metric and latest_metric.growth_rate != float('inf'):
                            avg_growth += latest_metric.growth_rate
                
                avg_growth = avg_growth / len(component) if component else 0
                
                clusters.append({
                    'cluster_id': i,
                    'size': len(component),
                    'keywords': list(component),
                    'avg_growth_rate': avg_growth,
                    'density': nx.density(G.subgraph(component))
                })
            finally:
                session.close()
        
        # Sort by growth rate
        clusters.sort(key=lambda x: x['avg_growth_rate'], reverse=True)
        return clusters


if __name__ == "__main__":
    # Test network building
    from database import DatabaseManager
    
    db = DatabaseManager("sqlite:///../data/papers.db")
    
    builder = NetworkBuilder(db, min_cooccurrence=2)
    
    # Build monthly snapshots for last year
    from datetime import datetime, timedelta
    snapshots = builder.build_snapshots(
        from_date=datetime.utcnow() - timedelta(days=365),
        time_window='month'
    )
    
    print(f"Built {len(snapshots)} snapshots")
    for s in snapshots[:5]:
        print(f"  {s.start_date.date()}: {s.num_nodes} nodes, {s.num_edges} edges")
    
    # Analyze trends
    analyzer = TrendAnalyzer(db)
    trending = analyzer.get_trending_keywords(n_snapshots=3, limit=20)
    
    print("\nTop trending keywords:")
    for kw in trending[:10]:
        print(f"  {kw['keyword']}: growth={kw['growth_rate']:.2f}, momentum={kw['momentum']:.2f}")
