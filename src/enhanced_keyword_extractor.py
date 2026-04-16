#!/usr/bin/env python3
"""
Enhanced Keyword Extractor for AIVC Research

Features:
1. Filters out generic/uninsightful keywords
2. Extracts specific technical phrases
3. LLM-based hot topic identification
4. Domain-aware keyword refinement
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import json

# Try to import optional LLM dependencies
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class EnhancedKeywordResult:
    """Enhanced keyword with domain specificity"""
    keyword: str
    specificity_score: float  # How specific/technical (0-1)
    relevance_score: float    # Relevance to AIVC (0-1)
    category: str             # Category (Method/Technique/Application/etc.)
    is_hot_topic: bool        # Whether this is trending
    llm_elaboration: str      # LLM-generated insight (optional)
    original_phrase: str      # Original text span
    
    def to_dict(self) -> dict:
        return {
            'keyword': self.keyword,
            'specificity': self.specificity_score,
            'relevance': self.relevance_score,
            'category': self.category,
            'hot_topic': self.is_hot_topic,
            'elaboration': self.llm_elaboration,
        }


class EnhancedAIVCKeywordExtractor:
    """
    Domain-specific keyword extractor for AI Virtual Cell research
    
    Filters generic terms and extracts specific, insightful keywords
    """
    
    # Generic terms to FILTER OUT (too general)
    GENERIC_TERMS = {
        'machine learning', 'deep learning', 'artificial intelligence',
        'neural network', 'model', 'simulation', 'analysis', 'study',
        'research', 'method', 'approach', 'system', 'data', 'cell',
        'cells', 'protein', 'gene', 'expression', 'based', 'using',
        'novel', 'new', 'improved', 'efficient', 'high', 'large',
        'single', 'multi', 'integrated', 'computational', 'biological',
        'molecular', 'cellular', 'dynamic', 'spatial', 'temporal',
        'network', 'pathway', 'signaling', 'regulation', 'interaction'
    }
    
    # Specific technical phrases to PRIORITIZE
    SPECIFIC_PATTERNS = [
        # AI Methods (specific)
        r'\b(transformer|BERT|GPT|ViT|GNN|graph neural network|attention mechanism|self-attention)\b',
        r'\b(variational autoencoder|VAE|diffusion model|generative model|flow-based model)\b',
        r'\b(reinforcement learning|RL|policy gradient|Q-learning|actor-critic)\b',
        r'\b(foundation model|large language model|LLM|pre-trained model|fine-tuning)\b',
        r'\b(multi-modal|multimodal|cross-modal|modality alignment)\b',
        
        # Cell Modeling (specific)
        r'\b(whole-cell model|whole cell simulation|digital twin|virtual cell)\b',
        r'\b(multi-scale|multiscale|cross-scale|hierarchical model)\b',
        r'\b(ODE|PDE|stochastic simulation|Gillespie|chemical master equation)\b',
        r'\b(agent-based|ABM|cellular automata|particle-based)\b',
        r'\b(metabolic model|constraint-based|FBA|flux balance)\b',
        
        # Omics & Data (specific)
        r'\b(single-cell RNA-seq|scRNA-seq|spatial transcriptomics|Visium)\b',
        r'\b(multi-omics|integrated omics|transcriptomics|proteomics|metabolomics)\b',
        r'\b(perturbation screen|CRISPR screen|drug response|dose-response)\b',
        r'\b(cell painting|high-content imaging|phenotypic profiling)\b',
        
        # Applications (specific)
        r'\b(drug discovery|virtual screening|target identification|lead optimization)\b',
        r'\b(toxicity prediction|ADMET|pharmacokinetics|pharmacodynamics)\b',
        r'\b(disease modeling|cancer model|patient-specific|personalized medicine)\b',
        r'\b(gene therapy|cell therapy|synthetic biology|gene circuit)\b',
        
        # Evaluation (specific)
        r'\b(zero-shot|few-shot|in-context learning|emergent ability)\b',
        r'\b(out-of-distribution|OOD|generalization|robustness)\b',
        r'\b(interpretability|explainability|XAI|attention visualization)\b',
    ]
    
    # Category mappings
    CATEGORY_PATTERNS = {
        'AI_Method': ['transformer', 'GNN', 'VAE', 'diffusion', 'foundation model', 'LLM'],
        'Modeling_Technique': ['whole-cell', 'multi-scale', 'ODE', 'agent-based', 'FBA'],
        'Data_Technology': ['scRNA-seq', 'spatial transcriptomics', 'multi-omics', 'cell painting'],
        'Application': ['drug discovery', 'toxicity', 'disease modeling', 'gene therapy'],
        'Evaluation': ['zero-shot', 'OOD', 'interpretability', 'generalization'],
    }
    
    def __init__(self, llm_config: Dict = None):
        """
        Initialize extractor
        
        Args:
            llm_config: Optional LLM configuration for hot topic analysis
                {'enabled': True, 'api_key': '...', 'model': 'gpt-4o-mini'}
        """
        self.llm_config = llm_config or {'enabled': False}
        self.llm_client = None
        
        if self.llm_config.get('enabled') and HAS_OPENAI:
            api_key = self.llm_config.get('api_key')
            if api_key:
                self.llm_client = openai.OpenAI(api_key=api_key)
                logger.info("✅ LLM-based hot topic analysis enabled")
            else:
                logger.warning("⚠️  LLM enabled but no API key provided")
    
    def extract_keywords(self, title: str, abstract: str, max_keywords: int = 15) -> List[EnhancedKeywordResult]:
        """
        Extract specific, insightful keywords from paper
        
        Args:
            title: Paper title
            abstract: Paper abstract
            max_keywords: Maximum keywords to return
        
        Returns:
            List of EnhancedKeywordResult, filtered and ranked
        """
        text = f"{title}. {abstract}"
        keywords = []
        
        # Step 1: Extract specific technical phrases
        specific_keywords = self._extract_specific_phrases(text)
        keywords.extend(specific_keywords)
        
        # Step 2: Extract compound technical terms (2-4 words)
        compound_keywords = self._extract_compound_terms(title, abstract)
        keywords.extend(compound_keywords)
        
        # Step 3: Filter out generic terms
        filtered = self._filter_generic(keywords)
        
        # Step 4: Score and rank by specificity + relevance
        scored = self._score_keywords(filtered)
        
        # Step 5: Take top keywords
        top_keywords = sorted(scored, key=lambda x: x.specificity_score * 0.4 + x.relevance_score * 0.6, reverse=True)[:max_keywords]
        
        # Step 6: LLM-based hot topic identification (if enabled)
        if self.llm_client:
            top_keywords = self._identify_hot_topics(top_keywords)
        
        return top_keywords
    
    def _extract_specific_phrases(self, text: str) -> List[EnhancedKeywordResult]:
        """Extract specific technical phrases matching known patterns"""
        results = []
        text_lower = text.lower()
        
        for pattern in self.SPECIFIC_PATTERNS:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                phrase = match.group(0)
                category = self._categorize_phrase(phrase)
                
                results.append(EnhancedKeywordResult(
                    keyword=phrase,
                    specificity_score=0.9,  # High specificity (matched known pattern)
                    relevance_score=0.85,
                    category=category,
                    is_hot_topic=False,  # Will be updated by LLM
                    llm_elaboration="",
                    original_phrase=phrase
                ))
        
        return results
    
    def _extract_compound_terms(self, title: str, abstract: str) -> List[EnhancedKeywordResult]:
        """Extract compound technical terms (2-4 word phrases)"""
        results = []
        
        # Focus on title for important terms
        title_tokens = title.split()
        for i in range(len(title_tokens) - 1):
            for j in range(i + 2, min(i + 5, len(title_tokens) + 1)):
                phrase = ' '.join(title_tokens[i:j])
                if self._is_technical_phrase(phrase):
                    results.append(EnhancedKeywordResult(
                        keyword=phrase.lower(),
                        specificity_score=0.7,
                        relevance_score=0.75,
                        category=self._categorize_phrase(phrase),
                        is_hot_topic=False,
                        llm_elaboration="",
                        original_phrase=phrase
                    ))
        
        return results
    
    def _is_technical_phrase(self, phrase: str) -> bool:
        """Check if phrase is technical (not generic)"""
        phrase_lower = phrase.lower()
        
        # Reject if contains generic words only
        words = phrase_lower.split()
        if all(w in self.GENERIC_TERMS for w in words):
            return False
        
        # Accept if contains technical indicators
        technical_indicators = [
            'model', 'simulation', 'network', 'learning', 'based',
            'omics', 'seq', 'RNA', 'cell', 'gene', 'protein',
            'virtual', 'digital', 'twin', 'multi', 'scale'
        ]
        
        return any(ind in phrase_lower for ind in technical_indicators)
    
    def _filter_generic(self, keywords: List[EnhancedKeywordResult]) -> List[EnhancedKeywordResult]:
        """Remove generic/uninsightful keywords"""
        filtered = []
        seen = set()
        
        for kw in keywords:
            kw_lower = kw.keyword.lower()
            
            # Skip if exact generic term
            if kw_lower in self.GENERIC_TERMS:
                continue
            
            # Skip if too short (1 word and generic)
            if len(kw_lower.split()) == 1 and kw_lower in self.GENERIC_TERMS:
                continue
            
            # Skip duplicates
            if kw_lower in seen:
                continue
            seen.add(kw_lower)
            
            # Boost specificity score for longer phrases
            if len(kw_lower.split()) >= 3:
                kw.specificity_score = min(1.0, kw.specificity_score + 0.1)
            
            filtered.append(kw)
        
        return filtered
    
    def _score_keywords(self, keywords: List[EnhancedKeywordResult]) -> List[EnhancedKeywordResult]:
        """Score keywords by specificity and AIVC relevance"""
        for kw in keywords:
            # Specificity: longer phrases = more specific
            word_count = len(kw.keyword.split())
            length_bonus = min(0.2, (word_count - 1) * 0.05)
            kw.specificity_score = min(1.0, kw.specificity_score + length_bonus)
            
            # Relevance: boost for AIVC-specific terms
            aivc_boosters = [
                'virtual cell', 'digital twin', 'whole-cell', 'whole cell',
                'AI virtual', 'foundation model', 'cell model', 'cell simulation'
            ]
            for booster in aivc_boosters:
                if booster in kw.keyword.lower():
                    kw.relevance_score = min(1.0, kw.relevance_score + 0.15)
                    break
        
        return keywords
    
    def _categorize_phrase(self, phrase: str) -> str:
        """Categorize phrase into domain category"""
        phrase_lower = phrase.lower()
        
        for category, keywords in self.CATEGORY_PATTERNS.items():
            if any(kw in phrase_lower for kw in keywords):
                return category
        
        # Default categorization
        if any(w in phrase_lower for w in ['model', 'simulation', 'ODE', 'agent']):
            return 'Modeling_Technique'
        elif any(w in phrase_lower for w in ['learning', 'neural', 'transformer', 'AI']):
            return 'AI_Method'
        elif any(w in phrase_lower for w in ['omics', 'seq', 'RNA', 'proteomics']):
            return 'Data_Technology'
        elif any(w in phrase_lower for w in ['drug', 'therapy', 'disease', 'toxicity']):
            return 'Application'
        else:
            return 'Other'
    
    def _identify_hot_topics(self, keywords: List[EnhancedKeywordResult]) -> List[EnhancedKeywordResult]:
        """Use LLM to identify hot topics and generate elaborations"""
        if not self.llm_client:
            return keywords
        
        try:
            # Prepare keywords for LLM analysis
            kw_list = [kw.keyword for kw in keywords[:10]]  # Top 10
            
            prompt = f"""You are an AI Virtual Cell (AIVC) research expert. Analyze these keywords from recent AIVC literature and identify hot topics.

Keywords: {json.dumps(kw_list)}

For each keyword, provide:
1. Is this a hot topic? (yes/no)
2. Why is it important for AIVC? (1 sentence)
3. What's the research trend? (emerging/mature/declining)

Format as JSON: {{"keyword": {{"hot": true/false, "importance": "...", "trend": "..."}}}}
"""
            
            response = self.llm_client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Update keywords with LLM analysis
            for kw in keywords:
                if kw.keyword in analysis:
                    kw.is_hot_topic = analysis[kw.keyword].get('hot', False)
                    kw.llm_elaboration = analysis[kw.keyword].get('importance', '')
            
            logger.info(f"✅ LLM analyzed {len(kw_list)} keywords, identified {sum(1 for kw in keywords if kw.is_hot_topic)} hot topics")
            
        except Exception as e:
            logger.warning(f"⚠️  LLM hot topic analysis failed: {e}")
        
        return keywords
    
    def generate_hot_topic_report(self, keywords: List[EnhancedKeywordResult]) -> str:
        """Generate markdown report of hot topics"""
        hot_topics = [kw for kw in keywords if kw.is_hot_topic]
        
        if not hot_topics:
            return "## 🔥 Hot Topics Analysis\n\nNo hot topics identified (enable LLM for analysis).\n"
        
        report = ["## 🔥 Hot Topics Analysis\n"]
        report.append(f"**{len(hot_topics)} emerging topics identified**\n")
        
        for i, kw in enumerate(hot_topics[:5], 1):
            report.append(f"### {i}. {kw.keyword}\n")
            report.append(f"- **Category:** {kw.category}")
            report.append(f"- **Specificity:** {kw.specificity_score:.2f}")
            report.append(f"- **Relevance:** {kw.relevance_score:.2f}")
            if kw.llm_elaboration:
                report.append(f"- **Insight:** {kw.llm_elaboration}")
            report.append("")
        
        return '\n'.join(report)


def create_enhanced_extractor(llm_config: Dict = None) -> EnhancedAIVCKeywordExtractor:
    """Factory function to create enhanced extractor"""
    return EnhancedAIVCKeywordExtractor(llm_config=llm_config)
