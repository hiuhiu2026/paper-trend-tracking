#!/usr/bin/env python3
"""
DeepSeek-Powered Keyword Extractor for AIVC Research

This extractor uses DeepSeek LLM exclusively for:
1. Extracting specific, technical keywords from papers
2. Identifying hot research directions and trends
3. Categorizing keywords by domain
4. Filtering out generic terms

NO pattern matching - all extraction is LLM-driven for maximum specificity.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import json
import re

# Try to import OpenAI client (DeepSeek uses OpenAI-compatible API)
try:
    from openai import OpenAI
    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False
    logger.warning("⚠️  OpenAI package not installed. Install with: pip install openai")


@dataclass
class EnhancedKeywordResult:
    """Keyword result with DeepSeek analysis"""
    keyword: str
    specificity_score: float  # How specific/technical (0-1)
    relevance_score: float    # Relevance to AIVC (0-1)
    category: str             # AI_Method / Modeling_Technique / Data_Technology / Application / Evaluation
    is_hot_topic: bool        # Whether this is a trending research direction
    llm_elaboration: str      # DeepSeek-generated insight about why this matters
    confidence: float         # LLM confidence in this keyword (0-1)
    
    def to_dict(self) -> dict:
        return {
            'keyword': self.keyword,
            'specificity': self.specificity_score,
            'relevance': self.relevance_score,
            'category': self.category,
            'hot_topic': self.is_hot_topic,
            'elaboration': self.llm_elaboration,
            'confidence': self.confidence,
        }


class DeepSeekAIVCExtractor:
    """
    DeepSeek-powered keyword extractor for AI Virtual Cell research
    
    Uses LLM to extract specific technical keywords and identify hot research directions.
    NO pattern matching - everything is LLM-driven for maximum quality.
    """
    
    # System prompt for keyword extraction
    EXTRACTION_PROMPT = """You are an expert in AI Virtual Cell (AIVC) research. Your task is to extract specific, technical keywords from scientific paper titles and abstracts.

**CRITICAL RULES:**
1. Extract ONLY specific technical terms - NO generic words like "machine learning", "model", "analysis", "cell", "protein"
2. Focus on cutting-edge techniques and methods specific to AIVC
3. Prefer multi-word phrases (2-5 words) over single words
4. Extract 8-12 keywords maximum
5. Each keyword must be actionable and insightful for tracking research trends

**GOOD examples:**
- "graph neural network for molecular representation"
- "variational autoencoder for single-cell data"
- "spatial transcriptomics integration"
- "whole-cell metabolic modeling"
- "foundation model pre-training on cell atlases"
- "perturbation response prediction"
- "cross-modal alignment of scRNA-seq and proteomics"

**BAD examples (DO NOT extract):**
- "machine learning" (too generic)
- "cell model" (too vague)
- "data analysis" (meaningless)
- "novel approach" (not technical)
- "protein expression" (too common)

**Output format (JSON only, no explanation):**
{
  "keywords": [
    {
      "keyword": "specific technical phrase",
      "category": "AI_Method|Modeling_Technique|Data_Technology|Application|Evaluation",
      "specificity": 0.95,
      "relevance": 0.90,
      "confidence": 0.92
    }
  ]
}

**Categories:**
- AI_Method: Specific AI/ML techniques (transformer, GNN, VAE, diffusion, etc.)
- Modeling_Technique: Cell modeling approaches (whole-cell, multi-scale, ODE, agent-based, etc.)
- Data_Technology: Omics and data technologies (scRNA-seq, spatial transcriptomics, multi-omics, etc.)
- Application: Research applications (drug discovery, disease modeling, toxicity prediction, etc.)
- Evaluation: Evaluation methods (zero-shot, out-of-distribution, interpretability, etc.)

---

Title: {title}

Abstract: {abstract}

---

Extract keywords (JSON only):"""

    # Prompt for hot topic analysis across multiple papers
    HOT_TOPIC_PROMPT = """You are an AI Virtual Cell (AIVC) research trend analyst. Analyze these keywords collected from recent AIVC literature and identify the hottest research directions.

**Your task:**
1. Identify 5-8 hot research directions (emerging trends)
2. For each direction, list 3-5 related keywords
3. Explain why this direction is important for AIVC
4. Assess the trend stage (emerging/rapid growth/mature)
5. Predict future research opportunities

**Output format (JSON only):**
{
  "hot_directions": [
    {
      "direction_name": "Clear name for this research direction",
      "keywords": ["keyword1", "keyword2", "keyword3"],
      "importance": "Why this matters for AIVC (2-3 sentences)",
      "trend_stage": "emerging|rapid growth|mature",
      "future_opportunities": "What's next in this area (1-2 sentences)",
      "heat_score": 0.95
    }
  ],
  "overall_trends": "Brief summary of the overall AIVC research landscape (2-3 sentences)"
}

**Keywords from recent papers:**
{keywords}

---

Analyze and identify hot research directions (JSON only):"""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com"):
        """
        Initialize DeepSeek extractor
        
        Args:
            api_key: DeepSeek API key (required)
            model: Model name (default: deepseek-chat)
            base_url: API base URL (default: https://api.deepseek.com)
        """
        if not HAS_CLIENT:
            raise ImportError("OpenAI package required. Install: pip install openai")
        
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise ValueError("DeepSeek API key required. Get one from https://platform.deepseek.com/api-keys")
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        logger.info(f"✅ DeepSeek AIVC extractor initialized (model: {model})")
    
    def extract_keywords(self, title: str, abstract: str, max_keywords: int = 12) -> List[EnhancedKeywordResult]:
        """
        Extract keywords using DeepSeek LLM
        
        Args:
            title: Paper title
            abstract: Paper abstract
            max_keywords: Maximum keywords to return
        
        Returns:
            List of EnhancedKeywordResult objects
        """
        try:
            # Prepare prompt
            prompt = self.EXTRACTION_PROMPT.format(title=title, abstract=abstract)
            
            # Call DeepSeek
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AIVC research expert. Output JSON only, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)
            
            result = json.loads(content)
            
            # Convert to EnhancedKeywordResult objects
            keywords = []
            for kw_data in result.get('keywords', [])[:max_keywords]:
                keywords.append(EnhancedKeywordResult(
                    keyword=kw_data.get('keyword', ''),
                    specificity_score=kw_data.get('specificity', 0.8),
                    relevance_score=kw_data.get('relevance', 0.8),
                    category=kw_data.get('category', 'Other'),
                    is_hot_topic=False,  # Will be set by hot topic analysis
                    llm_elaboration="",  # Will be filled by hot topic analysis
                    confidence=kw_data.get('confidence', 0.85)
                ))
            
            logger.info(f"✅ Extracted {len(keywords)} keywords via DeepSeek")
            return keywords
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse DeepSeek response: {e}")
            logger.debug(f"Raw response: {content[:500]}...")
            return []
        except Exception as e:
            logger.error(f"❌ DeepSeek extraction failed: {e}")
            return []
    
    def analyze_hot_topics(self, all_keywords: List[str], top_n: int = 50) -> Dict:
        """
        Analyze hot research directions across all collected keywords
        
        Args:
            all_keywords: List of all keywords from collected papers
            top_n: Use top N most frequent keywords
        
        Returns:
            Dict with hot directions analysis
        """
        try:
            # Get most frequent keywords
            from collections import Counter
            keyword_counts = Counter(all_keywords)
            top_keywords = [kw for kw, count in keyword_counts.most_common(top_n)]
            
            if not top_keywords:
                logger.warning("⚠️  No keywords available for hot topic analysis")
                return {"hot_directions": [], "overall_trends": "No keywords collected yet"}
            
            # Prepare prompt
            prompt = self.HOT_TOPIC_PROMPT.format(keywords=", ".join(top_keywords))
            
            # Call DeepSeek
            logger.debug(f"Sending {len(top_keywords)} keywords to DeepSeek for hot topic analysis...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AIVC research trend analyst. Output JSON only, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            logger.debug(f"DeepSeek response length: {len(content)} chars")
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)
            
            result = json.loads(content)
            
            # Validate structure
            if not isinstance(result, dict):
                logger.error(f"❌ Expected dict, got {type(result)}")
                return {"hot_directions": [], "overall_trends": "Invalid response format"}
            
            # Handle different possible key names
            hot_directions = result.get('hot_directions') or result.get('hot_topics') or result.get('directions') or []
            overall_trends = result.get('overall_trends') or result.get('summary') or result.get('overview') or "Analysis completed"
            
            logger.info(f"✅ DeepSeek identified {len(hot_directions)} hot research directions")
            
            return {
                "hot_directions": hot_directions,
                "overall_trends": overall_trends
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse hot topic analysis: {e}")
            logger.debug(f"Raw response: {content[:1000] if 'content' in dir() else 'N/A'}...")
            return {"hot_directions": [], "overall_trends": f"JSON parsing failed: {e}"}
        except KeyError as e:
            logger.error(f"❌ Missing expected key in response: {e}")
            logger.debug(f"Raw response: {content[:1000] if 'content' in dir() else 'N/A'}...")
            return {"hot_directions": [], "overall_trends": f"Missing key: {e}"}
        except Exception as e:
            logger.error(f"❌ Hot topic analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {"hot_directions": [], "overall_trends": f"Analysis failed: {e}"}
    
    def generate_research_trend_report(self, hot_topics: Dict) -> str:
        """
        Generate markdown report from hot topic analysis
        
        Args:
            hot_topics: Result from analyze_hot_topics()
        
        Returns:
            Markdown report string
        """
        lines = [
            "# 🔥 AIVC Hot Research Directions",
            "",
            "*Analysis powered by DeepSeek LLM*",
            "",
            "## 📊 Overall Trends",
            "",
            hot_topics.get('overall_trends', 'No analysis available'),
            "",
            "---",
            "",
        ]
        
        directions = hot_topics.get('hot_directions', [])
        if not directions:
            lines.append("*No hot directions identified yet. Collect more papers and re-run analysis.*")
        else:
            lines.append(f"**{len(directions)} major research directions identified**")
            lines.append("")
            
            for i, direction in enumerate(sorted(directions, key=lambda x: x.get('heat_score', 0), reverse=True), 1):
                lines.extend([
                    f"### {i}. {direction.get('direction_name', 'Unknown Direction')}",
                    "",
                    f"**Trend Stage:** {direction.get('trend_stage', 'unknown').replace('_', ' ').title()}",
                    "",
                    f"**Key Keywords:** {', '.join(direction.get('keywords', [])[:5])}",
                    "",
                    f"**Why It Matters:**",
                    "",
                    f"{direction.get('importance', 'N/A')}",
                    "",
                    f"**Future Opportunities:**",
                    "",
                    f"{direction.get('future_opportunities', 'N/A')}",
                    "",
                    f"**Heat Score:** {direction.get('heat_score', 0):.2f}/1.0",
                    "",
                    "---",
                    "",
                ])
        
        return "\n".join(lines)


def create_deepseek_extractor(api_key: str, model: str = "deepseek-chat", base_url: str = "https://api.deepseek.com") -> DeepSeekAIVCExtractor:
    """
    Factory function to create DeepSeek extractor
    
    Args:
        api_key: DeepSeek API key
        model: Model name
        base_url: API base URL
    
    Returns:
        DeepSeekAIVCExtractor instance
    """
    return DeepSeekAIVCExtractor(api_key=api_key, model=model, base_url=base_url)
