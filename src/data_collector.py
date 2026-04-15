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

try:
    from .arxiv_client import ArxivClient, ArxivToPaperAdapter
except ImportError:
    from arxiv_client import ArxivClient, ArxivToPaperAdapter


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
        """
        Fetch paper details for a batch of PMIDs using PubMed Central API
        Uses /pmc/articles/ endpoint which returns proper JSON
        """
        if not pmids:
            return []
        
        papers = []
        
        # Fetch each PMID individually using the newer PMC API
        # This returns proper JSON format
        for pmid in pmids[:20]:  # Limit to avoid rate limits
            try:
                paper = self._fetch_single_pmid(pmid)
                if paper:
                    papers.append(paper)
            except Exception as e:
                logger.debug(f"Failed to fetch PMID {pmid}: {e}")
        
        return papers
    
    def _fetch_single_pmid(self, pmid: str) -> Optional[Paper]:
        """Fetch single paper using E-utilities summary + fetch"""
        try:
            # Use esummary which returns JSON reliably
            summary_params = {
                'db': 'pubmed',
                'id': pmid,
                'retmode': 'json'
            }
            
            summary = self._request('esummary.fcgi', summary_params)
            if not summary or 'result' not in summary:
                return None
            
            paper_data = summary['result'].get(pmid)
            if not paper_data:
                return None
            
            # Parse summary data
            title = paper_data.get('title', '')
            
            # Authors
            authors = []
            for author in paper_data.get('authors', []):
                name = author.get('name', '')
                if name:
                    authors.append(name)
            
            # Journal
            journal = paper_data.get('fulljournalname', '') or paper_data.get('journal', '')
            
            # Publication date
            pub_date = paper_data.get('pubdate', '')
            if not pub_date:
                pub_date = paper_data.get('epubdate', '')
            
            # DOI
            doi = None
            article_ids = paper_data.get('articleids', [])
            for article_id in article_ids:
                if article_id.get('idtype') == 'doi':
                    doi = article_id.get('value')
                    break
            
            # URL
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            
            # Get abstract separately if available
            abstract = ""
            if paper_data.get('hasabstract', False):
                abstract_params = {
                    'db': 'pubmed',
                    'id': pmid,
                    'rettype': 'abstract',
                    'retmode': 'text'
                }
                try:
                    abstract_result = self._request('efetch.fcgi', abstract_params)
                    if abstract_result and 'text' in abstract_result:
                        abstract_text = abstract_result.get('text', '')
                        # Extract abstract from text format
                        if 'ABSTRACT' in abstract_text:
                            abstract = abstract_text.split('ABSTRACT')[-1].strip()[:2000]
                except:
                    pass
            
            return Paper(
                id=f"PMID:{pmid}",
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=pub_date,
                journal=journal,
                doi=doi,
                keywords=[],  # Will be extracted
                source='pubmed',
                url=url,
                raw_data=paper_data
            )
            
        except Exception as e:
            logger.error(f"Error fetching PMID {pmid}: {e}")
            return None
        
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
    """
    Semantic Scholar Academic Graph API v1 client
    
    API Documentation: https://api.semanticscholar.org/api-docs/graph
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RATE_LIMIT_DELAY = 1.0  # Conservative: 1 request per second to avoid 429
    
    # Valid fields according to S2AG API
    VALID_FIELDS = [
        'title', 'abstract', 'authors', 'year', 'publicationDate', 'publicationTypes',
        'journal', 'venue', 'doi', 'url', 'citationCount', 'referenceCount',
        'influentialCitationCount', 'isOpenAccess', 'externalIds', 'fieldsOfStudy',
        's2FieldsOfStudy', 'tldr', 'embedding', 'openAccessPdf', 'citationStyles'
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        self.last_request_time = 0
        
        # Add user agent header (required by some APIs)
        self.session.headers.update({
            'User-Agent': 'PaperTrendTracker/1.0',
        })
        
        if api_key:
            self.session.headers.update({'x-api-key': api_key})
        else:
            logger.info("Semantic Scholar client initialized without API key (rate limited)")
    
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
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            
            if status_code == 429:
                logger.warning(f"Semantic Scholar API rate limit hit. Waiting 60 seconds...")
                time.sleep(60)
                return self._request(endpoint, params)  # Retry once
            elif status_code == 400:
                logger.error(f"Semantic Scholar API bad request: {e}. Check parameters.")
            else:
                logger.error(f"Semantic Scholar API error (status {status_code}): {e}")
            return None
    
    def search(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_results: int = 100
    ) -> Generator[Paper, None, None]:
        """
        Search Semantic Scholar for papers using /graph/v1/paper/search
        
        Args:
            query: Search query
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            max_results: Maximum papers to retrieve
        
        Returns:
            Generator of Paper objects
        """
        # Build query parameters according to S2AG API spec
        # Core fields only to avoid 400 errors
        params = {
            'query': query,
            'limit': min(max_results, 100),  # Max 100 per request
            'fields': 'title,abstract,authors,year,publicationDate,venue,journal,doi,url,citationCount,referenceCount,externalIds,fieldsOfStudy'
        }
        
        # Date filters - Semantic Scholar year parameter
        # Format: year=2020 (single year) or omit for all years
        # Note: S2AG API doesn't support year ranges in search, filter after retrieval
        if from_date:
            from_year = from_date.split('-')[0]
            if len(from_year) == 4 and from_year.isdigit():
                # Store for post-filtering (API doesn't support ranges well)
                params['min_year'] = int(from_year)
        
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
                    # Apply year filter if specified
                    if params.get('min_year'):
                        pub_year = paper.publication_date[:4] if paper.publication_date else None
                        if pub_year and pub_year.isdigit() and int(pub_year) < params['min_year']:
                            continue
                    
                    yield paper
                    total_fetched += 1
            
            # Check if more results available
            total_available = result.get('total', 0)
            if offset + len(papers) >= total_available:
                break
            
            offset += len(papers)
    
    def _parse_paper(self, data: Dict) -> Optional[Paper]:
        """
        Parse Semantic Scholar paper into standardized format
        
        S2AG API Response Fields:
        https://semanticscholar.readthedocs.io/en/stable/s2objects/Paper.html
        """
        try:
            # Paper ID - primary identifier
            paper_id = data.get('paperId', '')
            if not paper_id:
                return None
            
            # Basic info
            title = data.get('title', '') or ''
            abstract = data.get('abstract', '') or ''
            
            # Authors - array of {authorId, name}
            authors = []
            for author in data.get('authors', []):
                if isinstance(author, dict):
                    name = author.get('name', '')
                else:
                    name = str(author)
                if name:
                    authors.append(name)
            
            # Publication date - can be string or null
            pub_date = data.get('publicationDate', '') or ''
            
            # Year (fallback if publicationDate missing)
            if not pub_date:
                year = data.get('year', None)
                if year:
                    pub_date = str(year)
            
            # Journal/Venue - prefer venue, fallback to journal.name
            venue = data.get('venue', '') or ''
            journal = venue
            journal_data = data.get('journal', {})
            if journal_data and isinstance(journal_data, dict):
                journal_name = journal_data.get('name', '')
                if journal_name:
                    journal = journal_name
            
            # DOI from externalIds or direct doi field
            doi = data.get('doi', None)
            if not doi:
                external_ids = data.get('externalIds', {})
                if external_ids and isinstance(external_ids, dict):
                    doi = external_ids.get('DOI', None)
            
            # Fields of study (use as keywords if no explicit keywords)
            keywords = []
            fields_of_study = data.get('fieldsOfStudy', [])
            if fields_of_study and isinstance(fields_of_study, list):
                keywords.extend(fields_of_study)
            
            s2_fields = data.get('s2FieldsOfStudy', [])
            if s2_fields and isinstance(s2_fields, list):
                for field in s2_fields:
                    if isinstance(field, dict):
                        category = field.get('category', '')
                        if category and category not in keywords:
                            keywords.append(category)
            
            # Citation/reference counts
            citations = data.get('citationCount', None)
            references = data.get('referenceCount', None)
            
            # URL - construct if not provided
            url = data.get('url', None)
            if not url and paper_id:
                url = f"https://www.semanticscholar.org/paper/{paper_id}"
            
            return Paper(
                id=f"S2:{paper_id}",
                title=title,
                abstract=abstract,
                authors=authors,
                publication_date=str(pub_date) if pub_date else '',
                journal=journal or '',
                doi=doi,
                keywords=keywords,
                source='semanticscholar',
                url=url or '',
                citations_count=citations,
                references_count=references,
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Error parsing Semantic Scholar paper: {e}")
            return None


class DataCollector:
    """Unified data collector for multiple sources
    
    Supported sources:
    - PubMed (biomedical literature)
    - arXiv (preprints, especially CS, Physics, Quant Bio)
    - Semantic Scholar (optional, requires API key for good rate limits)
    """
    
    def __init__(
        self,
        pubmed_api_key: Optional[str] = None,
        s2_api_key: Optional[str] = None,
        use_arxiv: bool = True,
        use_semantic_scholar: bool = False
    ):
        self.pubmed = PubMedClient(api_key=pubmed_api_key)
        self.arxiv = ArxivClient() if use_arxiv else None
        self.semantic_scholar = SemanticScholarClient(api_key=s2_api_key) if use_semantic_scholar else None
        
        self.use_arxiv = use_arxiv
        self.use_semantic_scholar = use_semantic_scholar
        
        sources = ['PubMed']
        if use_arxiv:
            sources.append('arXiv')
        if use_semantic_scholar:
            sources.append('Semantic Scholar')
        
        logger.info(f"Data collector initialized (sources: {', '.join(sources)})")
    
    def collect(
        self,
        query: str,
        sources: List[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_per_source: int = 100
    ) -> Generator[Paper, None, None]:
        """
        Collect papers from multiple sources
        
        Args:
            query: Search query
            sources: List of sources ('pubmed', 'arxiv', 'semanticscholar')
                     Defaults to ['pubmed', 'arxiv'] if None
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            max_per_source: Max papers per source
        """
        # Default sources: PubMed + arXiv (no API key needed)
        if sources is None:
            sources = ['pubmed', 'arxiv']
            if self.use_semantic_scholar:
                sources.append('semanticscholar')
        
        seen_ids = set()
        
        # PubMed
        if 'pubmed' in sources and self.pubmed:
            logger.info(f"Collecting from PubMed: {query}")
            for paper in self.pubmed.search(query, from_date, to_date, max_per_source):
                if paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    yield paper
        
        # arXiv
        if 'arxiv' in sources and self.arxiv:
            logger.info(f"Collecting from arXiv: {query}")
            
            # Map query to arXiv categories for better results
            categories = self._infer_arxiv_categories(query)
            
            for paper in self.arxiv.search(query, from_date, to_date, max_per_source, categories):
                # Convert to standard format
                std_paper = ArxivToPaperAdapter.to_standard(paper)
                if std_paper.id not in seen_ids:
                    seen_ids.add(std_paper.id)
                    yield std_paper
        
        # Semantic Scholar (optional, requires API key)
        if 'semanticscholar' in sources and self.semantic_scholar:
            logger.info(f"Collecting from Semantic Scholar: {query}")
            for paper in self.semantic_scholar.search(query, from_date, to_date, max_per_source):
                if paper.id not in seen_ids:
                    seen_ids.add(paper.id)
                    yield paper
        
        logger.info(f"Collection complete: {len(seen_ids)} unique papers")
    
    def _infer_arxiv_categories(self, query: str) -> List[str]:
        """
        Infer relevant arXiv categories from query
        
        Common categories:
        - cs.LG: Machine Learning
        - cs.AI: Artificial Intelligence
        - cs.CL: Computation and Language (NLP)
        - cs.CV: Computer Vision
        - q-bio.BM: Biomolecules
        - q-bio.GN: Genomics
        - q-bio.QM: Quantitative Methods
        - physics.bio-ph: Biological Physics
        - stat.ML: Machine Learning (Statistics)
        """
        query_lower = query.lower()
        
        categories = []
        
        # Machine Learning / AI
        if any(word in query_lower for word in ['machine learning', 'deep learning', 'neural', 'ai', 'artificial intelligence']):
            categories.extend(['cs.LG', 'cs.AI', 'stat.ML'])
        
        # NLP / Language
        if any(word in query_lower for word in ['language', 'text', 'nlp', 'translation']):
            categories.append('cs.CL')
        
        # Computer Vision
        if any(word in query_lower for word in ['vision', 'image', 'classification', 'detection']):
            categories.append('cs.CV')
        
        # Biology / Bioinformatics
        if any(word in query_lower for word in ['protein', 'drug', 'molecule', 'gene', 'genomics', 'bio']):
            categories.extend(['q-bio.BM', 'q-bio.GN', 'physics.bio-ph'])
        
        # Clinical / Medical
        if any(word in query_lower for word in ['clinical', 'medical', 'patient', 'trial']):
            categories.extend(['q-bio.QM'])
        
        # Default to ML + Bio if nothing specific
        if not categories:
            categories = ['cs.LG', 'q-bio.BM']
        
        return list(set(categories))  # Remove duplicates


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
