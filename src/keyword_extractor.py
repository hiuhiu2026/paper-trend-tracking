"""
Keyword Extraction Module for Paper Trend Tracking

Supports multiple extraction methods with a unified interface:
- YAKE (default) - Fast, unsupervised, no training needed
- TF-IDF - Corpus-based statistical approach
- LLM-based - High quality, uses LLM APIs
- MeSH-only - PubMed MeSH terms only (no extraction)

All methods implement the BaseKeywordExtractor interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path
from loguru import logger


@dataclass
class KeywordResult:
    """Extracted keyword with metadata"""
    keyword: str
    score: float  # Relevance score (higher = more relevant)
    occurrences: int  # Number of times it appears in text
    positions: List[int]  # Character positions (optional)
    method: str  # Extraction method used
    
    def __repr__(self):
        return f"<Keyword(keyword='{self.keyword}', score={self.score:.4f})>"


class BaseKeywordExtractor(ABC):
    """Abstract base class for keyword extractors"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def extract(self, text: str, max_keywords: int = 10) -> List[KeywordResult]:
        """
        Extract keywords from text
        
        Args:
            text: Input text (typically title + abstract)
            max_keywords: Maximum number of keywords to return
        
        Returns:
            List of KeywordResult objects, sorted by score (descending)
        """
        pass
    
    @abstractmethod
    def batch_extract(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> List[List[KeywordResult]]:
        """
        Extract keywords from multiple texts
        
        Args:
            texts: List of input texts
            max_keywords: Maximum keywords per text
        
        Returns:
            List of keyword lists (one per input text)
        """
        pass
    
    def normalize_keyword(self, keyword: str) -> str:
        """
        Normalize a keyword for consistent matching
        
        Default implementation: lowercase and strip
        Override for more sophisticated normalization
        """
        return keyword.lower().strip()
    
    def filter_keywords(
        self,
        keywords: List[KeywordResult],
        min_score: float = 0.0,
        exclude_patterns: List[str] = None
    ) -> List[KeywordResult]:
        """
        Filter keywords by score and patterns
        
        Args:
            keywords: Input keywords
            min_score: Minimum score threshold
            exclude_patterns: Regex patterns to exclude
        
        Returns:
            Filtered keywords
        """
        import re
        
        filtered = []
        for kw in keywords:
            # Score filter
            if kw.score < min_score:
                continue
            
            # Pattern exclusion
            if exclude_patterns:
                excluded = False
                for pattern in exclude_patterns:
                    if re.search(pattern, kw.keyword, re.IGNORECASE):
                        excluded = True
                        break
                if excluded:
                    continue
            
            filtered.append(kw)
        
        return filtered


class YakeExtractor(BaseKeywordExtractor):
    """
    YAKE (Yet Another Keyword Extractor)
    
    Fast, unsupervised keyword extraction.
    Good for single documents, no training needed.
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.name = "YAKE"
        
        # Default YAKE parameters
        self.language = self.config.get('language', 'en')
        self.max_ngram_size = self.config.get('max_ngram_size', 3)
        self.num_keywords = self.config.get('num_keywords', 10)
        self.dedup_threshold = self.config.get('dedup_threshold', 0.9)
        
        # Lazy load yake
        self._extractor = None
    
    @property
    def extractor(self):
        """Lazy load YAKE extractor"""
        if self._extractor is None:
            try:
                import yake
                self._extractor = yake.KeywordExtractor(
                    lan=self.language,
                    n=self.max_ngram_size,
                    k=self.num_keywords,
                    dedupLim=self.dedup_threshold,
                    dedupFunc=self._dedup
                )
            except ImportError:
                logger.error("YAKE not installed. Run: pip install yake")
                raise
        return self._extractor
    
    def _dedup(self, candidate1, candidate2):
        """Simple deduplication function"""
        return candidate1.lower() == candidate2.lower()
    
    def extract(self, text: str, max_keywords: int = 10) -> List[KeywordResult]:
        """Extract keywords using YAKE"""
        if not text or len(text.strip()) < 10:
            return []
        
        try:
            # YAKE returns list of (keyword, score) tuples
            # Lower score = more relevant in YAKE
            candidates = self.extractor.extract_keywords(text)
            
            results = []
            for keyword, score in candidates[:max_keywords]:
                # Invert score so higher = more relevant (for consistency)
                normalized_score = 1.0 / (score + 1.0)
                
                results.append(KeywordResult(
                    keyword=keyword.strip(),
                    score=normalized_score,
                    occurrences=1,  # YAKE doesn't provide this directly
                    positions=[],
                    method='YAKE'
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"YAKE extraction error: {e}")
            return []
    
    def batch_extract(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> List[List[KeywordResult]]:
        """Batch extract keywords"""
        return [self.extract(text, max_keywords) for text in texts]


class TFIDFExtractor(BaseKeywordExtractor):
    """
    TF-IDF based keyword extraction
    
    Requires a corpus to build IDF weights.
    Good for large collections, captures corpus-specific importance.
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.name = "TF-IDF"
        
        self.max_features = self.config.get('max_features', 10000)
        self.min_df = self.config.get('min_df', 2)
        self.max_df = self.config.get('max_df', 0.8)
        self.ngram_range = tuple(self.config.get('ngram_range', [1, 3]))
        
        # TF-IDF vectorizer (fitted on corpus)
        self._vectorizer = None
        self._is_fitted = False
        
        # NLP preprocessing
        self._nlp = None
    
    def _load_nlp(self):
        """Load spaCy for preprocessing"""
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load('en_core_web_sm')
            except OSError:
                logger.error("spaCy model not found. Run: python -m spacy download en_core_web_sm")
                raise
    
    def fit(self, documents: List[str]):
        """
        Fit TF-IDF vectorizer on corpus
        
        Args:
            documents: List of document texts for training
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        logger.info(f"Fitting TF-IDF on {len(documents)} documents...")
        
        self._vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            min_df=self.min_df,
            max_df=self.max_df,
            ngram_range=self.ngram_range,
            stop_words='english'
        )
        
        self._vectorizer.fit(documents)
        self._is_fitted = True
        
        logger.info(f"TF-IDF fitted with {len(self._vectorizer.vocabulary_)} features")
    
    def extract(self, text: str, max_keywords: int = 10) -> List[KeywordResult]:
        """Extract keywords using TF-IDF scores"""
        if not self._is_fitted:
            logger.warning("TF-IDF extractor not fitted. Call fit() first or use batch_extract.")
            return []
        
        if not text or len(text.strip()) < 10:
            return []
        
        try:
            # Transform document to TF-IDF vector
            tfidf_matrix = self._vectorizer.transform([text])
            
            # Get feature names
            feature_names = self._vectorizer.get_feature_names_out()
            
            # Get top keywords by TF-IDF score
            row = tfidf_matrix.getrow(0)
            indices = row.indices
            data = row.data
            
            # Sort by score
            sorted_indices = sorted(
                zip(indices, data),
                key=lambda x: x[1],
                reverse=True
            )[:max_keywords]
            
            results = []
            for idx, score in sorted_indices:
                results.append(KeywordResult(
                    keyword=feature_names[idx],
                    score=float(score),
                    occurrences=1,
                    positions=[],
                    method='TF-IDF'
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"TF-IDF extraction error: {e}")
            return []
    
    def batch_extract(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> List[List[KeywordResult]]:
        """Batch extract and optionally fit on the corpus"""
        # Fit if not already fitted
        if not self._is_fitted and len(texts) >= 10:
            self.fit(texts)
        
        return [self.extract(text, max_keywords) for text in texts]


class LLMKeywordExtractor(BaseKeywordExtractor):
    """
    LLM-based keyword extraction
    
    Uses an LLM API to extract keywords.
    Highest quality but slower and costs money.
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.name = "LLM"
        
        self.provider = self.config.get('provider', 'openai')
        self.model = self.config.get('model', 'gpt-4o-mini')
        self.api_key = self.config.get('api_key')
        self.max_keywords = self.config.get('max_keywords', 10)
        
        # Prompt template
        self.prompt_template = self.config.get('prompt', """
Extract {max_keywords} key topics/concepts from the following scientific abstract.
Return ONLY a JSON array of keyword objects with "keyword" and "relevance" (1-10) fields.

Abstract:
{text}

Keywords (JSON array):
""")
    
    def extract(self, text: str, max_keywords: int = 10) -> List[KeywordResult]:
        """Extract keywords using LLM"""
        if not text or len(text.strip()) < 10:
            return []
        
        try:
            # Build prompt
            prompt = self.prompt_template.format(
                max_keywords=max_keywords,
                text=text
            )
            
            # Call LLM API
            if self.provider == 'openai':
                response = self._call_openai(prompt, max_keywords)
            elif self.provider == 'anthropic':
                response = self._call_anthropic(prompt, max_keywords)
            else:
                logger.error(f"Unknown LLM provider: {self.provider}")
                return []
            
            # Parse response
            keywords = self._parse_llm_response(response)
            
            results = []
            for kw_data in keywords:
                results.append(KeywordResult(
                    keyword=kw_data.get('keyword', ''),
                    score=kw_data.get('relevance', 5.0) / 10.0,
                    occurrences=1,
                    positions=[],
                    method='LLM'
                ))
            
            return results[:max_keywords]
            
        except Exception as e:
            logger.error(f"LLM extraction error: {e}")
            return []
    
    def _call_openai(self, prompt: str, max_keywords: int) -> str:
        """Call OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research assistant. Extract keywords from scientific abstracts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.error("OpenAI not installed. Run: pip install openai")
            raise
    
    def _call_anthropic(self, prompt: str, max_keywords: int) -> str:
        """Call Anthropic API"""
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except ImportError:
            logger.error("Anthropic not installed. Run: pip install anthropic")
            raise
    
    def _parse_llm_response(self, response: str) -> List[Dict]:
        """Parse LLM response as JSON"""
        import re
        import json
        
        # Try to extract JSON from response
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: parse as simple list
        keywords = []
        for line in response.strip().split('\n'):
            line = line.strip(' -,•')
            if line:
                keywords.append({'keyword': line, 'relevance': 5.0})
        
        return keywords
    
    def batch_extract(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> List[List[KeywordResult]]:
        """Batch extract (note: rate limits apply)"""
        import time
        
        results = []
        for i, text in enumerate(texts):
            kw = self.extract(text, max_keywords)
            results.append(kw)
            
            # Rate limiting
            if (i + 1) % 10 == 0:
                time.sleep(1.0)
        
        return results


class MeshOnlyExtractor(BaseKeywordExtractor):
    """
    MeSH-only extractor for PubMed papers
    
    Uses existing MeSH terms from PubMed, no extraction needed.
    Fastest option but only works for PubMed papers.
    """
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.name = "MeSH"
    
    def extract(self, text: str, max_keywords: int = 10) -> List[KeywordResult]:
        """
        MeSH extractor doesn't work on raw text.
        Use extract_from_pubmed_entry instead.
        """
        logger.warning("MeSH extractor requires structured PubMed data, not raw text")
        return []
    
    def extract_from_pubmed_entry(self, pubmed_entry: Dict) -> List[KeywordResult]:
        """
        Extract MeSH terms from PubMed API response
        
        Args:
            pubmed_entry: Raw PubMed API response dict
        
        Returns:
            List of KeywordResult objects
        """
        results = []
        
        mesh_headings = pubmed_entry.get('meshHeadings', [])
        for mesh in mesh_headings:
            descriptor = mesh.get('descriptorName', {})
            if descriptor:
                results.append(KeywordResult(
                    keyword=descriptor.get('descriptor', ''),
                    score=1.0,  # All MeSH terms equally relevant
                    occurrences=1,
                    positions=[],
                    method='MeSH'
                ))
        
        return results
    
    def batch_extract(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> List[List[KeywordResult]]:
        """Not applicable for MeSH"""
        logger.warning("MeSH batch_extract not applicable for raw text")
        return [[] for _ in texts]


class KeywordExtractorFactory:
    """
    Factory for creating keyword extractors
    
    Usage:
        factory = KeywordExtractorFactory()
        extractor = factory.create('yake', config={...})
    """
    
    _extractors = {
        'yake': YakeExtractor,
        'tfidf': TFIDFExtractor,
        'llm': LLMKeywordExtractor,
        'mesh': MeshOnlyExtractor
    }
    
    @classmethod
    def create(cls, method: str, config: Dict = None) -> BaseKeywordExtractor:
        """
        Create keyword extractor by method name
        
        Args:
            method: Extraction method ('yake', 'tfidf', 'llm', 'mesh')
            config: Method-specific configuration
        
        Returns:
            Configured extractor instance
        """
        if method not in cls._extractors:
            logger.error(f"Unknown extraction method: {method}")
            logger.info(f"Available methods: {list(cls._extractors.keys())}")
            raise ValueError(f"Unknown extraction method: {method}")
        
        extractor_class = cls._extractors[method]
        return extractor_class(config)
    
    @classmethod
    def register_extractor(cls, name: str, extractor_class: type):
        """Register a custom extractor"""
        if not issubclass(extractor_class, BaseKeywordExtractor):
            raise ValueError("Extractor must inherit from BaseKeywordExtractor")
        
        cls._extractors[name] = extractor_class
        logger.info(f"Registered custom extractor: {name}")


class HybridExtractor(BaseKeywordExtractor):
    """
    Hybrid extractor combining multiple methods
    
    Useful for:
    - YAKE + MeSH (PubMed papers)
    - TF-IDF + LLM (high accuracy)
    """
    
    def __init__(self, extractors: List[Tuple[BaseKeywordExtractor, float]]):
        """
        Args:
            extractors: List of (extractor, weight) tuples
        """
        super().__init__()
        self.name = "Hybrid"
        self.extractors = extractors
    
    def extract(self, text: str, max_keywords: int = 10) -> List[KeywordResult]:
        """Extract using all methods and combine scores"""
        all_keywords = {}
        
        for extractor, weight in self.extractors:
            keywords = extractor.extract(text, max_keywords)
            
            for kw in keywords:
                if kw.keyword in all_keywords:
                    # Combine scores (weighted average)
                    existing = all_keywords[kw.keyword]
                    existing.score = (existing.score + kw.score * weight) / 2
                    existing.methods.append(kw.method)
                else:
                    kw.score = kw.score * weight
                    kw.methods = [kw.method]
                    all_keywords[kw.keyword] = kw
        
        # Sort by combined score
        sorted_keywords = sorted(
            all_keywords.values(),
            key=lambda x: x.score,
            reverse=True
        )
        
        return sorted_keywords[:max_keywords]
    
    def batch_extract(
        self,
        texts: List[str],
        max_keywords: int = 10
    ) -> List[List[KeywordResult]]:
        """Batch extract"""
        return [self.extract(text, max_keywords) for text in texts]


# Convenience function
def create_extractor(method: str = 'yake', config: Dict = None) -> BaseKeywordExtractor:
    """
    Create keyword extractor
    
    Args:
        method: Extraction method ('yake', 'tfidf', 'llm', 'mesh')
        config: Method-specific configuration
    
    Returns:
        Configured extractor
    """
    return KeywordExtractorFactory.create(method, config)


if __name__ == "__main__":
    # Test extractors
    sample_text = """
    Machine learning approaches for drug discovery have shown promising results 
    in recent years. Deep learning models can predict molecular properties and 
    identify potential drug candidates from large chemical libraries. This study 
    presents a novel graph neural network architecture for molecular property 
    prediction with applications in pharmaceutical research.
    """
    
    print("Testing YAKE extractor:")
    yake = create_extractor('yake')
    keywords = yake.extract(sample_text, max_keywords=5)
    for kw in keywords:
        print(f"  {kw.keyword}: {kw.score:.4f}")
    
    print("\nTesting TF-IDF extractor (needs fitting):")
    tfidf = create_extractor('tfidf')
    # Would need to call tfidf.fit([sample_text, ...]) first
