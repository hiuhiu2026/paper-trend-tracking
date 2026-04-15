"""
Data Collection Module for Paper Trend Tracking

Supports:
- PubMed (via E-utilities API)
- Semantic Scholar (via Graph API)
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass, asdict
from loguru import logger
import json


@dataclass
class Paper:
    """Standardized paper representation"""
    id: str
    title: str
    abstract: str
    authors: List[str]
    publication_date: str
    journal: str
    doi: Optional[str]
    keywords: List[str]
    source: str  # 'pubmed' or 'semanticscholar'
    url: str
    citations_count: Optional[int] = None
    references_count: Optional[int] = None
    raw_data: Optional[Dict] = None  # Keep original response for debugging


class PubMedClient:
    """NCBI PubMed E-utilities API client"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    RATE_LIMIT_DELAY = 0.34  # NCBI recommends max 3 requests per second
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce NCBI rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make rate-limited request to E-utilities"""
        self._rate_limit()
        
        if self.api_key:
            params['api_key'] = api_key
            
        try:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=30)
            response.raise_for_status()
            
            # Handle different return types
            if params.get('retmode') == 'json':
                return response.json()
            else:
                return {'text': response.text}
                
        except requests.RequestException as e:
            logger.error(f"PubMed API error: {e}")
            return None
    
    def search(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_results: int = 100
    ) -> Generator[Paper, None, None]:
        """
        Search PubMed for papers
        
        Args:
            query: Search query (supports MeSH terms, boolean operators)
            from_date: Start date (YYYY/MM/DD)
            to_date: End date (YYYY/MM/DD)
            max_results: Maximum papers to retrieve
        """
        # Build search query with date filters
        date_filter = ""
        if from_date or to_date:
            date_part = f"{from_date or '1000/01/01'}:{to_date or '3000/12/31'}[Date - Publication]"
            date_filter = f" AND {date_part}"
        
        full_query = f"{query}{date_filter}"
        
        # Step 1: Search and get PMIDs
        search_params = {
            'db': 'pubmed',
            'term': full_query,
            'retmax': min(max_results, 10000),
            'retmode': 'json'
        }
        
        search_result = self._request('esearch.fcgi', search_params)
        if not search_result or 'esearchresult' not in search_result:
            logger.error("PubMed search failed")
            return
        
        pmids = search_result['esearchresult'].get('idlist', [])
        logger.info(f"Found {len(pmids)} papers for query: {query}")
        
        # Step 2: Fetch details in batches
        for i in range(0, len(pmids), 100):  # Batch size 100
            batch_pmids = pmids[i:i+100]
            papers = self._fetch_batch(batch_pmids)
            for paper in papers:
                yield paper
    
    def _fetch_batch(self, pmids: List[str]) -> List[Paper]:
        """Fetch paper details for a batch of PMIDs"""
        if not pmids:
            return []
        
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'json',
            'rettype': 'abstract'
        }
        
        result = self._request('efetch.fcgi', fetch_params)
        if not result:
            return []
        
        papers = []
        pubmed_data = result.get('pubmedresult', [])
        
        for entry in pubmed_data:
            try:
                paper = self._parse_pubmed_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.warning(f"Failed to parse PMID {entry.get('ids', ['unknown'])[0]}: {e}")
        
        return papers
    
    def _parse_pubmed_entry(self, entry: Dict) -> Optional[Paper]:
        """Parse PubMed entry into standardized Paper object"""
        try:
            # Extract basic info
            ids = entry.get('ids', [])
            pmid = str(ids[0]) if ids else None
            
            article = entry.get('article', {})
            article_title = article.get('articleTitle', '')
            
            # Abstract
            abstract = ""
            abstract_el = article.get('abstract', {})
            if abstract_el:
                abstract_text = abstract_el.get('abstractText', [])
                if isinstance(abstract_text, list):
                    abstract = ' '.join(abstract_text)
                else:
                    abstract = str(abstract_text)
            
            # Authors
            authors = []
            author_list = article.get('authors', [])
            for author in author_list:
                name = f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                if name:
                    authors.append(name)
            
            # Journal
            journal = article.get('journal', {}).get('title', '')
            
            # Publication date
            pub_date = article.get('publicationHistory', [])
            pub_date_str = ""
            if pub_date:
                # Take first (usually print publication date)
                pub_date_str = pub_date[0].get('pubStatus', '')
            
            # DOI
            doi = None
            article_ids = article.get('articleIds', [])
            for article_id in article_ids:
                if article_id.get('idType') == 'doi':
                    doi = article_id.get('id')
                    break
            
            # Keywords (MeSH terms)
            keywords = []
            mesh_headings = entry.get('meshHeadings', [])
            for mesh in mesh_headings:
                descriptor = mesh.get('descriptorName', {})
                if descriptor:
                    keywords.append(descriptor.get('descriptor', ''))
            
            return Paper(
                id=f"PMID:{pmid}",
                title=article_title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date_str,
                journal=journal,
                doi=doi,
                keywords=keywords,
                source='pubmed',
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                raw_data=entry
            )
            
        except Exception as e:
            logger.error(f"Error parsing PubMed entry: {e}")
            return None


class SemanticScholarClient:
    """Semantic Scholar Academic Graph API client"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT_DELAY = 0.1  # 10 requests per second for free tier
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        
        if api_key:
            self.session.headers.update({'x-api-key': api_key})
    
    def _rate_limit(self):
        """Enforce rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make rate-limited request"""
        self._rate_limit()
        
        try:
            response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            if '429' in str(e):
                logger.warning(f"Semantic Scholar API rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                return self._request(endpoint, params)  # Retry once
            logger.error(f"Semantic Scholar API error: {e}")
            return None
    
    def search(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_results: int = 100
    ) -> Generator[Paper, None, None]:
        """
        Search Semantic Scholar for papers
        
        Args:
            query: Search query
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            max_results: Maximum papers to retrieve
        """
        # Build query parameters
        params = {
            'query': query,
            'limit': min(max_results, 100),
            'fields': 'title,abstract,authors,publicationDate,journal,doi,url,citationCount,referenceCount,externalIds,keywords'
        }
        
        # Date filters - Semantic Scholar expects 4-digit year only
        if from_date:
            year = from_date.split('-')[0]
            if len(year) == 4 and year.isdigit():
                params['year'] = f"{year}-"
        if to_date and not from_date:
            year = to_date.split('-')[0]
            if len(year) == 4 and year.isdigit():
                params['year'] = f"-{year}"
        
        # Pagination
        offset = 0
        total_fetched = 0
        
        while total_fetched < max_results:
            params['offset'] = offset
            
            result = self._request('paper/search', params)
            if not result or 'data' not in result:
                break
            
            papers = result['data']
            if not papers:
                break
            
            for paper_data in papers:
                paper = self._parse_paper(paper_data)
                if paper:
                    yield paper
                    total_fetched += 1
            
            # Check if more results available
            total_available = result.get('total', 0)
            if offset + len(papers) >= total_available:
                break
            
            offset += len(papers)
    
    def _parse_paper(self, data: Dict) -> Optional[Paper]:
        """Parse Semantic Scholar paper into standardized format"""
        try:
            paper_id = data.get('paperId', '')
            title = data.get('title', '')
            abstract = data.get('abstract', '') or ''
            
            # Authors
            authors = []
            for author in data.get('authors', []):
                name = author.get('name', '')
                if name:
                    authors.append(name)
            
            # Publication date
            pub_date = data.get('publicationDate', '')
            
            # Journal
            journal = ""
            journal_data = data.get('journal', {})
            if journal_data:
                journal = journal_data.get('name', '')
            
            # DOI
            doi = data.get('doi', None)
            
            # Keywords (if available)
            keywords = data.get('keywords', []) or []
            
            # Citation/reference counts
            citations = data.get('citationCount', None)
            references = data.get('referenceCount', None)
            
            # URL
            url = data.get('url', f"https://www.semanticscholar.org/paper/{paper_id}")
            
            return Paper(
                id=f"S2:{paper_id}",
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date,
                journal=journal,
                doi=doi,
                keywords=keywords,
                source='semanticscholar',
                url=url,
                citations_count=citations,
                references_count=references,
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Error parsing Semantic Scholar paper: {e}")
            return None


class DataCollector:
    """Unified data collector for multiple sources"""
    
    def __init__(self, pubmed_api_key: Optional[str] = None, s2_api_key: Optional[str] = None):
        self.pubmed = PubMedClient(api_key=pubmed_api_key)
        self.semantic_scholar = SemanticScholarClient(api_key=s2_api_key)
        logger.info("Data collector initialized")
    
    def collect(
        self,
        query: str,
        sources: List[str] = ['pubmed', 'semanticscholar'],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_per_source: int = 100
    ) -> Generator[Paper, None, None]:
        """
        Collect papers from multiple sources
        
        Args:
            query: Search query
            sources: List of sources ('pubmed', 'semanticscholar')
            from_date: Start date
            to_date: End date
            max_per_source: Max papers per source
        """
        seen_ids = set()
        
        if 'pubmed' in sources:
            logger.info(f"Collecting from PubMed: {query}")
            for paper in self.pubmed.search(query, from_date, to_date, max_per_source):
                if paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    yield paper
        
        if 'semanticscholar' in sources:
            logger.info(f"Collecting from Semantic Scholar: {query}")
            for paper in self.semantic_scholar.search(query, from_date, to_date, max_per_source):
                if paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    yield paper
        
        logger.info(f"Collection complete: {len(seen_ids)} unique papers")


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    
    # Initialize collector (add API keys if you have them)
    collector = DataCollector()
    
    # Search for recent papers on "machine learning drug discovery"
    query = "machine learning drug discovery"
    from_date = "2024-01-01"
    
    papers_collected = []
    for paper in collector.collect(
        query=query,
        from_date=from_date,
        max_per_source=50
    ):
        papers_collected.append(paper)
        print(f"✓ {paper.title[:80]}... ({paper.source})")
    
    print(f"\nTotal: {len(papers_collected)} papers")
