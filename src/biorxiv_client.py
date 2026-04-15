"""
bioRxiv API Client for Paper Trend Tracking

Uses bioRxiv API v2
Documentation: https://api.biorxiv.org/
"""

import requests
import time
from datetime import datetime
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from loguru import logger


@dataclass
class BiorxivPaper:
    """bioRxiv paper representation"""
    doi: str
    title: str
    abstract: str
    authors: List[str]
    publication_date: str
    category: str  # bioRxiv category
    url: str
    published_date: str  # When published on bioRxiv
    raw_data: Optional[Dict] = None


class BiorxivClient:
    """
    bioRxiv API v2 client
    
    API: https://api.biorxiv.org/
    Rate limit: No documented limit, be conservative
    """
    
    BASE_URL = "https://api.biorxiv.org/details/biorxiv"
    RATE_LIMIT_DELAY = 0.5  # 2 requests per second to be safe
    
    # bioRxiv categories
    CATEGORIES = [
        'bioinformatics', 'bioengineering', 'biophysics', 'cancer_biology',
        'cell_biology', 'clinical_trials', 'developmental_biology', 'ecology',
        'epidemiology', 'genetics', 'genomics', 'immunology', 'microbiology',
        'molecular_biology', 'neuroscience', 'pharmacology', 'physiology',
        'synthetic_biology', 'systems_biology', 'zoology'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PaperTrendTracker/1.0 (https://github.com/hiuhiu2026/paper-trend-tracking)',
            'Accept': 'application/json'
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
    ) -> Generator[BiorxivPaper, None, None]:
        """
        Search bioRxiv for papers
        
        Args:
            query: Search query
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            max_results: Maximum papers to retrieve
            categories: Limit to specific bioRxiv categories
        
        Returns:
            Generator of BiorxivPaper objects
        """
        # bioRxiv API returns 100 results per request, uses cursor for pagination
        cursor = 0
        total_fetched = 0
        
        while total_fetched < max_results:
            # Build URL with cursor
            url = f"{self.BASE_URL}/{cursor}"
            
            params = {
                'keywords': query,
            }
            
            # Note: bioRxiv API doesn't support date filtering in API
            # We'll filter after retrieval
            
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # bioRxiv API returns either:
                # 1. {'messages': {...}, 'collection': [...]}
                # 2. {'collection': [...]} directly
                if isinstance(data, dict):
                    if 'messages' in data and data['messages'].get('error'):
                        logger.error(f"bioRxiv API error: {data['messages']['error']}")
                        break
                    
                    collection = data.get('collection', [])
                elif isinstance(data, list):
                    # Sometimes returns list directly
                    collection = data
                else:
                    logger.error(f"Unexpected bioRxiv response format: {type(data)}")
                    break
                
                if not collection:
                    break
                
                for paper_data in collection:
                    # Filter by date if specified
                    pub_date = paper_data.get('date', '')
                    if from_date and pub_date < from_date.replace('-', ''):
                        continue
                    if to_date and pub_date > to_date.replace('-', ''):
                        continue
                    
                    # Filter by category if specified
                    if categories:
                        category = paper_data.get('category', '')
                        if category not in categories:
                            continue
                    
                    paper = self._parse_paper(paper_data)
                    if paper:
                        yield paper
                        total_fetched += 1
                    
                    if total_fetched >= max_results:
                        break
                
                # Check if more results available
                if len(collection) < 100:
                    break
                
                cursor += 100
                
            except requests.RequestException as e:
                logger.error(f"bioRxiv API error: {e}")
                break
            except Exception as e:
                logger.error(f"Error parsing bioRxiv response: {e}")
                break
    
    def _parse_paper(self, data: Dict) -> Optional[BiorxivPaper]:
        """Parse bioRxiv paper data"""
        try:
            doi = data.get('doi', '')
            title = data.get('title', '') or ''
            abstract = data.get('abstract', '') or ''
            
            # Authors - bioRxiv provides as "authors" string with semicolon separation
            authors_str = data.get('authors', '')
            authors = [a.strip() for a in authors_str.split(';') if a.strip()] if authors_str else []
            
            # Publication date
            pub_date = data.get('date', '')  # Format: YYYY-MM-DD
            published_date = data.get('published_date', '')  # When posted to bioRxiv
            
            # Category
            category = data.get('category', '')
            
            # URL
            url = f"https://www.biorxiv.org/content/{doi}" if doi else ''
            
            return BiorxivPaper(
                doi=doi,
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date,
                category=category,
                url=url,
                published_date=published_date,
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Error parsing bioRxiv paper: {e}")
            return None


class BiorxivToPaperAdapter:
    """Adapter to convert bioRxiv papers to standard Paper format"""
    
    @staticmethod
    def to_standard(biorxiv_paper: BiorxivPaper) -> 'Paper':
        """Convert bioRxivPaper to Paper format"""
        from .data_collector import Paper
        
        # Map bioRxiv category to keywords
        keywords = [biorxiv_paper.category] if biorxiv_paper.category else []
        
        # Add broader category
        if biorxiv_paper.category:
            if 'bio' in biorxiv_paper.category.lower():
                keywords.append('biology')
            if 'molecular' in biorxiv_paper.category.lower():
                keywords.append('molecular biology')
            if 'gen' in biorxiv_paper.category.lower():  # genetics, genomics
                keywords.append('genetics')
        
        return Paper(
            id=f"biorxiv:{biorxiv_paper.doi}",
            title=biorxiv_paper.title,
            abstract=biorxiv_paper.abstract,
            authors=biorxiv_paper.authors,
            publication_date=biorxiv_paper.publication_date,
            journal=f"bioRxiv ({biorxiv_paper.category})" if biorxiv_paper.category else 'bioRxiv',
            doi=biorxiv_paper.doi,
            keywords=keywords,
            source='biorxiv',
            url=biorxiv_paper.url,
            raw_data=biorxiv_paper.raw_data
        )


if __name__ == "__main__":
    # Test bioRxiv client
    client = BiorxivClient()
    
    print("Testing bioRxiv API...")
    
    papers = list(client.search(
        query="CRISPR gene editing",
        max_results=5,
        categories=['genetics', 'molecular_biology']
    ))
    
    print(f"\nFound {len(papers)} papers:\n")
    
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper.title[:70]}...")
        print(f"   DOI: {paper.doi}")
        print(f"   Category: {paper.category}")
        print(f"   Date: {paper.publication_date}")
        print(f"   URL: {paper.url}")
        print()
