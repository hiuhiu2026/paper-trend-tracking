"""
Database Schema and Operations for Paper Trend Tracking

Stores:
- Papers (with metadata)
- Keywords (extracted from papers)
- Paper-Keyword relationships
- Time-sliced keyword networks
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, Table, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import func, and_
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from dataclasses import asdict
import json
from pathlib import Path

try:
    from .data_collector import Paper
except ImportError:
    from data_collector import Paper


Base = declarative_base()


# Association table for paper-keyword many-to-many relationship
paper_keywords = Table(
    'paper_keywords',
    Base.metadata,
    Column('paper_id', String, ForeignKey('papers.id'), primary_key=True),
    Column('keyword_id', Integer, ForeignKey('keywords.id'), primary_key=True),
    Column('relevance_score', Float, nullable=True)  # Optional: keyword importance in this paper
)


class PaperModel(Base):
    """SQLAlchemy model for papers"""
    __tablename__ = 'papers'
    
    id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    abstract = Column(Text)
    publication_date = Column(String, index=True)
    journal = Column(String)
    doi = Column(String, unique=True, nullable=True, index=True)
    source = Column(String, nullable=False)  # 'pubmed' or 'semanticscholar'
    url = Column(String)
    citations_count = Column(Integer, nullable=True)
    references_count = Column(Integer, nullable=True)
    
    # Collection metadata
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    raw_data = Column(Text)  # JSON string of original API response
    
    # Relationships
    keywords = relationship(
        "KeywordModel",
        secondary=paper_keywords,
        back_populates="papers",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Paper(id='{self.id}', title='{self.title[:50]}...')>"
    
    @classmethod
    def from_paper(cls, paper: Paper) -> 'PaperModel':
        """Convert data_collector.Paper to SQLAlchemy model"""
        return cls(
            id=paper.id,
            title=paper.title,
            abstract=paper.abstract,
            publication_date=paper.publication_date,
            journal=paper.journal,
            doi=paper.doi,
            source=paper.source,
            url=paper.url,
            citations_count=paper.citations_count,
            references_count=paper.references_count,
            raw_data=json.dumps(paper.raw_data) if paper.raw_data else None
        )


class KeywordModel(Base):
    """SQLAlchemy model for keywords"""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    normalized_name = Column(String, nullable=True, index=True)  # After synonym resolution
    
    # Statistics (updated periodically)
    total_occurrences = Column(Integer, default=0)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    
    # Relationships
    papers = relationship(
        "PaperModel",
        secondary=paper_keywords,
        back_populates="keywords"
    )
    
    def __repr__(self):
        return f"<Keyword(id={self.id}, name='{self.name}')>"


class KeywordNetworkSnapshot(Base):
    """Time-sliced keyword network snapshots"""
    __tablename__ = 'keyword_network_snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)  # End date of time window
    time_window = Column(String, nullable=False)  # 'week', 'month', 'quarter'
    
    # Network stored as adjacency list in JSON format
    # Format: {"node1": {"node2": weight, "node3": weight}, ...}
    edges = Column(Text, nullable=False)
    
    # Network statistics
    num_nodes = Column(Integer)
    num_edges = Column(Integer)
    avg_degree = Column(Float)
    density = Column(Float)
    
    # Computed at snapshot creation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<KeywordNetworkSnapshot(date={self.snapshot_date}, nodes={self.num_nodes}, edges={self.num_edges})>"


class TrendMetrics(Base):
    """Computed trend metrics for keywords"""
    __tablename__ = 'trend_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=False, index=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)
    
    # Centrality metrics
    degree = Column(Float)
    betweenness = Column(Float)
    pagerank = Column(Float)
    clustering_coefficient = Column(Float)
    
    # Growth metrics
    occurrence_count = Column(Integer)  # Papers in this time window
    growth_rate = Column(Float)  # Compared to previous window
    momentum = Column(Float)  # Acceleration of growth
    
    # Computed at metric calculation
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TrendMetrics(keyword_id={self.keyword_id}, date={self.snapshot_date}, degree={self.degree})>"


class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_url: str = "sqlite:///data/papers.db"):
        # Ensure directory exists for SQLite database file
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            db_file = Path(db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        """Create all tables if they don't exist"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def add_paper(self, paper: Paper, keywords: List[str] = None) -> bool:
        """
        Add a paper to the database
        
        Args:
            paper: Paper object
            keywords: List of keyword strings
        
        Returns:
            True if added, False if already exists
        """
        session = self.get_session()
        try:
            # Check if paper already exists
            existing = session.query(PaperModel).filter(
                (PaperModel.id == paper.id) | 
                (PaperModel.doi == paper.doi)
            ).first()
            
            if existing:
                return False
            
            # Create paper model
            paper_model = PaperModel.from_paper(paper)
            
            # Add keywords
            if keywords:
                for kw_name in keywords:
                    # Get or create keyword
                    keyword = session.query(KeywordModel).filter(
                        KeywordModel.name == kw_name
                    ).first()
                    
                    if not keyword:
                        keyword = KeywordModel(
                            name=kw_name,
                            normalized_name=kw_name.lower(),
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow()
                        )
                        session.add(keyword)
                    
                    # Update statistics
                    keyword.total_occurrences = (keyword.total_occurrences or 0) + 1
                    keyword.last_seen = datetime.utcnow()
                    
                    # Link paper and keyword
                    paper_model.keywords.append(keyword)
            
            session.add(paper_model)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_papers_batch(self, papers_with_keywords: List[Tuple[Paper, List[str]]]) -> int:
        """
        Add multiple papers in a batch
        
        Args:
            papers_with_keywords: List of (Paper, [keywords]) tuples
        
        Returns:
            Number of papers successfully added
        """
        session = self.get_session()
        added_count = 0
        
        try:
            for paper, keywords in papers_with_keywords:
                # Check if exists
                existing = session.query(PaperModel).filter(
                    (PaperModel.id == paper.id) |
                    (PaperModel.doi == paper.doi)
                ).first()
                
                if existing:
                    continue
                
                # Create paper
                paper_model = PaperModel.from_paper(paper)
                
                # Add keywords
                for kw_name in keywords:
                    keyword = session.query(KeywordModel).filter(
                        KeywordModel.name == kw_name
                    ).first()
                    
                    if not keyword:
                        keyword = KeywordModel(
                            name=kw_name,
                            normalized_name=kw_name.lower(),
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow()
                        )
                        session.add(keyword)
                    
                    keyword.total_occurrences = (keyword.total_occurrences or 0) + 1
                    keyword.last_seen = datetime.utcnow()
                    paper_model.keywords.append(keyword)
                
                session.add(paper_model)
                added_count += 1
            
            session.commit()
            return added_count
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_papers_by_date_range(
        self,
        from_date: datetime,
        to_date: datetime,
        limit: int = None
    ) -> List[PaperModel]:
        """Get papers within a date range"""
        session = self.get_session()
        try:
            query = session.query(PaperModel).filter(
                and_(
                    PaperModel.collected_at >= from_date,
                    PaperModel.collected_at <= to_date
                )
            )
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        finally:
            session.close()
    
    def get_keyword_stats(self, keyword_name: str) -> Dict:
        """Get statistics for a keyword"""
        session = self.get_session()
        try:
            keyword = session.query(KeywordModel).filter(
                KeywordModel.name == keyword_name
            ).first()
            
            if not keyword:
                return None
            
            return {
                'name': keyword.name,
                'normalized_name': keyword.normalized_name,
                'total_occurrences': keyword.total_occurrences,
                'first_seen': keyword.first_seen.isoformat() if keyword.first_seen else None,
                'last_seen': keyword.last_seen.isoformat() if keyword.last_seen else None,
                'paper_count': keyword.papers.count()
            }
        finally:
            session.close()
    
    def get_trending_keywords(
        self,
        time_window_days: int = 30,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get keywords with highest growth in recent time window
        
        Args:
            time_window_days: Days to look back
            limit: Number of keywords to return
        
        Returns:
            List of keyword info with occurrence counts
        """
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            
            # Get keywords with most papers in recent window
            results = session.query(
                KeywordModel.name,
                KeywordModel.total_occurrences,
                func.count(paper_keywords.c.paper_id).label('recent_count')
            ).join(
                PaperModel,
                and_(
                    PaperModel.keywords.any(KeywordModel.id == KeywordModel.id),
                    PaperModel.collected_at >= cutoff_date
                )
            ).group_by(
                KeywordModel.id
            ).order_by(
                func.count(paper_keywords.c.paper_id).desc()
            ).limit(limit).all()
            
            return [
                {
                    'name': r.name,
                    'total_occurrences': r.total_occurrences,
                    'recent_count': r.recent_count
                }
                for r in results
            ]
        finally:
            session.close()
    
    def get_stats(self) -> Dict:
        """Get overall database statistics"""
        session = self.get_session()
        try:
            return {
                'total_papers': session.query(PaperModel).count(),
                'total_keywords': session.query(KeywordModel).count(),
                'total_snapshots': session.query(KeywordNetworkSnapshot).count(),
                'date_range': session.query(
                    func.min(PaperModel.collected_at),
                    func.max(PaperModel.collected_at)
                ).first()
            }
        finally:
            session.close()


# Import timedelta for the method above
from datetime import timedelta


if __name__ == "__main__":
    # Test database setup
    db = DatabaseManager("sqlite:///../data/test.db")
    
    print("Database initialized!")
    print(f"Stats: {db.get_stats()}")
