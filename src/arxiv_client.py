"""
arXiv API Client for Paper Trend Tracking

Uses arXiv API v2 (REST API)
Documentation: https://arxiv.org/help/api/user-manual
"""

import requests
import time
from datetime import datetime
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from loguru import logger
import xml.etree.ElementTree as ET


@dataclass
class ArxivPaper:
    """arXiv paper representation"""
    arxiv_id: str
    title: str
    abstract: str
    authors: List[str]
    publication_date: str
    categories: List[str]  # arXiv categories
    doi: Optional[str]
    url: str
    comment: Optional[str]  # Journal reference if published
    raw_data: Optional[Dict] = None


class ArxivClient:
    """
    arXiv API v2 client
    
    API: https://export.arxiv.org/api/query
    Rate limit: 10 requests per second (recommended)
    """
    
    BASE_URL = "https://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 0.15  # ~6 requests per second to be safe
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PaperTrendTracker/1.0 (https://github.com/hiuhiu2026/paper-trend-tracking)'
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def search(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_results: int = 100,
        categories: List[str] = None
    ) -> Generator[ArxivPaper, None, None]:
        """
        Search arXiv for papers
        
        Args:
            query: Search query (supports boolean operators)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            max_results: Maximum papers to retrieve
            categories: Limit to specific arXiv categories (e.g., ['cs.LG', 'q-bio.BM'])
        
        Returns:
            Generator of ArxivPaper objects
        """
        # Build search query
        search_query = self._build_query(query, from_date, to_date, categories)
        
        # Pagination: arXiv returns max 100 per request
        start = 0
        batch_size = min(max_results, 100)
        total_fetched = 0
        
        while total_fetched < max_results:
            params = {
                'search_query': search_query,
                'start': start,
                'max_results': batch_size,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            
            response = self._request(params)
            if not response:
                break
            
            # Parse Atom XML response
            papers = self._parse_response(response)
            
            if not papers:
                break
            
            for paper in papers:
                yield paper
                total_fetched += 1
            
            # Check if more results available
            if len(papers) < batch_size:
                break
            
            start += batch_size
            
            # Small delay between requests
            time.sleep(0.5)
    
    def _build_query(
        self,
        query: str,
        from_date: Optional[str],
        to_date: Optional[str],
        categories: Optional[List[str]]
    ) -> str:
        """
        Build arXiv search query string
        
        arXiv query syntax:
        - all: Search all fields
        - ti: Title
        - au: Author
        - abs: Abstract
        - cat: Category
        - AND, OR, ANDNOT: Boolean operators
        """
        # Main query - search title and abstract
        query_parts = [f'all:{query}']
        
        # Date filter - arXiv uses submittedDate
        if from_date or to_date:
            date_filter = []
            if from_date:
                date_filter.append(f'submittedDate:[{from_date} TO *]')
            if to_date:
                date_filter.append(f'submittedDate:[* TO {to_date}]')
            if date_filter:
                query_parts.append(' AND '.join(date_filter))
        
        # Category filter
        if categories:
            cat_filter = ' OR '.join([f'cat:{cat}' for cat in categories])
            query_parts.append(f'({cat_filter})')
        
        return ' AND '.join(query_parts)
    
    def _request(self, params: Dict) -> Optional[str]:
        """Make rate-limited request to arXiv API"""
        self._rate_limit()
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"arXiv API error: {e}")
            return None
    
    def _parse_response(self, xml_string: str) -> List[ArxivPaper]:
        """Parse arXiv Atom XML response"""
        papers = []
        
        try:
            # Parse XML
            root = ET.fromstring(xml_string)
            
            # Define namespace
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Find all entries
            entries = root.findall('atom:entry', ns)
            
            for entry in entries:
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
        
        return papers
    
    def _parse_entry(self, entry: ET.Element, ns: Dict) -> Optional[ArxivPaper]:
        """Parse single arXiv entry"""
        try:
            # arXiv ID
            arxiv_id_elem = entry.find('atom:id', ns)
            arxiv_id = arxiv_id_elem.text if arxiv_id_elem is not None else ''
            
            # Extract just the ID number (remove URL prefix)
            if 'arxiv.org/abs/' in arxiv_id:
                arxiv_id = arxiv_id.split('arxiv.org/abs/')[-1]
            
            # Title
            title_elem = entry.find('atom:title', ns)
            title = title_elem.text.strip() if title_elem is not None else ''
            
            # Abstract
            abstract_elem = entry.find('atom:summary', ns)
            abstract = abstract_elem.text.strip() if abstract_elem is not None else ''
            
            # Authors
            authors = []
            for author_elem in entry.findall('atom:author', ns):
                name_elem = author_elem.find('atom:name', ns)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())
            
            # Publication date (submitted date)
            published_elem = entry.find('atom:published', ns)
            pub_date = published_elem.text if published_elem is not None else ''
            
            # Categories
            categories = []
            for category_elem in entry.findall('atom:category', ns):
                term = category_elem.get('term', '')
                if term:
                    categories.append(term)
            
            # DOI (if published in journal)
            doi_elem = entry.find('arxiv:doi', ns)
            doi = doi_elem.text if doi_elem is not None else None
            
            # Comment (journal reference)
            comment_elem = entry.find('arxiv:comment', ns)
            comment = comment_elem.text if comment_elem is not None else None
            
            # URL
            url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ''
            
            return ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date[:10] if pub_date else '',  # YYYY-MM-DD
                categories=categories,
                doi=doi,
                url=url,
                comment=comment
            )
            
        except Exception as e:
            logger.error(f"Error parsing arXiv entry: {e}")
            return None


class ArxivToPaperAdapter:
    """Adapter to convert arXiv papers to standard Paper format"""
    
    @staticmethod
    def to_standard(arxiv_paper: ArxivPaper) -> 'Paper':
        """Convert ArxivPaper to Paper format"""
        # Import here to avoid circular dependency
        from .data_collector import Paper
        
        # Map arXiv categories to keywords
        keywords = arxiv_paper.categories.copy()
        
        # Add subject area from categories
        for cat in arxiv_paper.categories:
            if '.' in cat:
                subject = cat.split('.')[0]
                if subject not in keywords:
                    keywords.append(f"{subject} research")
        
        return Paper(
            id=f"arXiv:{arxiv_paper.arxiv_id}",
            title=arxiv_paper.title,
            abstract=arxiv_paper.abstract,
            authors=arxiv_paper.authors,
            publication_date=arxiv_paper.publication_date,
            journal=arxiv_paper.comment or '',
            doi=arxiv_paper.doi,
            keywords=keywords,
            source='arxiv',
            url=arxiv_paper.url,
            raw_data={
                'arxiv_id': arxiv_paper.arxiv_id,
                'categories': arxiv_paper.categories,
                'comment': arxiv_paper.comment
            }
        )


if __name__ == "__main__":
    # Test arXiv client
    client = ArxivClient()
    
    print("Testing arXiv API...")
    
    # Search for machine learning papers
    papers = list(client.search(
        query="deep learning protein structure",
        max_results=5,
        categories=['cs.LG', 'q-bio.BM']  # Machine Learning, Biomolecules
    ))
    
    print(f"\nFound {len(papers)} papers:\n")
    
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper.title[:80]}...")
        print(f"   arXiv: {paper.arxiv_id}")
        print(f"   Categories: {', '.join(paper.categories)}")
        print(f"   Date: {paper.publication_date}")
        print(f"   Authors: {len(paper.authors)}")
        print()
