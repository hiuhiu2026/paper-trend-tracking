# 🔥 DeepSeek-Powered Analysis Guide

## What Changed (April 17, 2026)

### ⚠️  MAJOR CHANGE: DeepSeek-Only Extraction

**Removed:**
- ❌ Pattern-based keyword extraction
- ❌ Generic keyword filtering
- ❌ OpenAI support (DeepSeek only)

**Added:**
- ✅ DeepSeek LLM extracts ALL keywords
- ✅ Hot research direction analysis
- ✅ Trend stage assessment (emerging/rapid growth/mature)
- ✅ Future opportunity predictions

---

## Why DeepSeek Only?

### Before (Pattern Matching + Basic LLM)
```
Keywords extracted:
- machine learning (too generic)
- cell model (too vague)
- data analysis (meaningless)
- neural network (common)

Hot topics: Basic tagging only
```

### After (DeepSeek LLM Only)
```
Keywords extracted:
- graph neural network for molecular representation
- variational autoencoder for single-cell data integration
- spatial transcriptomics-aware foundation model
- whole-cell metabolic flux modeling with ML

Hot topics: Full research direction analysis with:
- Trend stage assessment
- Importance explanation
- Future opportunities
- Heat scores
```

---

## 🚀 Setup

### 1. Get DeepSeek API Key

Visit: https://platform.deepseek.com/api-keys

1. Sign up / Log in
2. Go to API Keys
3. Create new key
4. Copy the key (starts with `sk-`)

### 2. Configure

Edit `config.virtualcell.yaml`:

```yaml
llm:
  enabled: true  # ⚠️  MUST be true
  provider: deepseek
  model: deepseek-chat
  api_key: sk-xxxxxxxxxxxxxxxx  # 🔑 PASTE YOUR KEY HERE
  base_url: https://api.deepseek.com
```

### 3. Run Pipeline

```bash
cd paper-trend-tracking

# Full collection with DeepSeek analysis
python run_virtualcell.py --days 1095 --max 200 --network
```

---

## 📊 What You Get

### 1. Specific Keywords (per paper)

DeepSeek extracts 8-12 highly specific keywords:

**Example output:**
```json
{
  "keyword": "cross-modal alignment of scRNA-seq and proteomics",
  "category": "Data_Technology",
  "specificity": 0.95,
  "relevance": 0.92,
  "confidence": 0.89
}
```

### 2. Hot Research Directions (global analysis)

After collecting papers, DeepSeek analyzes ALL keywords to identify major research trends:

**Example report:**

```markdown
# 🔥 AIVC Hot Research Directions

## 📊 Overall Trends

The AIVC field is rapidly evolving with three major thrusts: foundation models 
for cell representation, multi-omics integration, and perturbation response 
prediction. The field is transitioning from proof-of-concept to practical applications.

---

### 1. Foundation Models for Cell Representation

**Trend Stage:** Rapid Growth

**Key Keywords:** cell foundation model, CellFM, pre-training on cell atlases, 
zero-shot cell type annotation, transfer learning

**Why It Matters:**

Foundation models trained on diverse cell atlases enable zero-shot annotation 
of new cell types and cross-species transfer. This eliminates the need for 
task-specific training data, accelerating discovery in rare cell types and 
understudied organisms.

**Future Opportunities:**

Next-generation models will incorporate spatial context and temporal dynamics, 
enabling prediction of cell state transitions and response to perturbations.

**Heat Score:** 0.94/1.0

---

### 2. Spatial Multi-Omics Integration

**Trend Stage:** Emerging

**Key Keywords:** spatial transcriptomics integration, spatial proteomics, 
multi-modal spatial analysis, tissue context modeling

...
```

### 3. Cleaner Network Visualization

Network graphs now feature:
- Smaller nodes (200-600px vs previous 150-800px)
- Professional blue color scheme
- Kamada-Kawai layout (better spacing)
- Thinner edges (0.8px vs previous 1px)
- White borders for node separation
- Reduced top_n (40 vs previous 50) for less clutter

---

## 💰 Cost Estimate

DeepSeek is significantly cheaper than OpenAI:

| Operation | Tokens | Cost (DeepSeek) | Cost (GPT-4o-mini) |
|-----------|--------|-----------------|-------------------|
| Keyword extraction (per paper) | ~500 | $0.00007 | $0.000075 |
| Hot topic analysis (per run) | ~2000 | $0.00028 | $0.0003 |
| **Daily (100 papers)** | ~52,000 | **$0.007** | **$0.008** |
| **Monthly** | ~1.5M | **$0.21** | **$0.23** |

**Estimated monthly cost: $0.20-0.50** (very affordable!)

---

## 🔧 Troubleshooting

### "DeepSeek API key required"

Edit `config.virtualcell.yaml` and paste your API key:
```yaml
api_key: sk-xxxxxxxxxxxxxxxx  # Replace with your actual key
```

### "Failed to parse DeepSeek response"

This can happen if the API returns malformed JSON. Try:
1. Check your API key is valid
2. Check network connectivity
3. Reduce `max_keywords` in the extractor (default: 12)

### "Hot topic analysis failed"

Ensure you have collected enough papers (minimum 20-30) before running hot topic analysis.

### Keywords still too generic

DeepSeek's extraction quality depends on the paper abstract quality. If abstracts are too short or generic, keywords will be too. Try:
1. Increase `days_back` to collect more papers
2. Increase `max_per_query` for more results
3. Check if your search queries are specific enough

---

## 📈 Comparing Results

### Before (Pattern Matching)

```
Top keywords:
1. machine learning (generic)
2. deep learning (generic)
3. cell model (vague)
4. neural network (common)
5. data analysis (meaningless)
```

### After (DeepSeek LLM)

```
Top keywords:
1. graph neural network for molecular representation
2. variational autoencoder for single-cell data
3. spatial transcriptomics-aware foundation model
4. whole-cell metabolic flux modeling
5. cross-modal alignment of scRNA-seq and proteomics
```

---

## 🎯 Best Practices

### 1. Run Full Collection First

```bash
# Collect 3 years of data
python run_virtualcell.py --days 1095 --max 200 --network
```

### 2. Check Hot Topic Report

After running, check `output/hot_topics.md` for DeepSeek's analysis of research directions.

### 3. Re-run Hot Topic Analysis Only

If you want to re-analyze without re-collecting:

```bash
python -c "
from src.virtual_cell_tracker import VirtualCellTracker
tracker = VirtualCellTracker()
# Load existing database and re-run analysis
"
```

### 4. Customize Search Queries

Edit `config.virtualcell.yaml` to focus on your specific research interests:

```yaml
collection:
  queries:
    - "your specific query"
    - "another focused query"
```

---

## 📝 API Reference

### DeepSeekAIVCExtractor

```python
from src.enhanced_keyword_extractor import create_deepseek_extractor

# Initialize
extractor = create_deepseek_extractor(
    api_key="sk-xxx",
    model="deepseek-chat",
    base_url="https://api.deepseek.com"
)

# Extract keywords from single paper
keywords = extractor.extract_keywords(
    title="Paper Title",
    abstract="Paper abstract text...",
    max_keywords=12
)

# Analyze hot topics across all keywords
hot_topics = extractor.analyze_hot_topics(
    all_keywords=["keyword1", "keyword2", ...],
    top_n=50
)

# Generate markdown report
report = extractor.generate_research_trend_report(hot_topics)
```

---

## 🔒 Security

- **Never commit API keys** to Git
- Use `.gitignore` for `config.virtualcell.yaml` if it contains your key
- Or use environment variables:
  ```bash
  export DEEPSEEK_API_KEY="sk-xxx"
  ```

---

## 📞 Support

- DeepSeek API Docs: https://platform.deepseek.com/api-docs
- GitHub Issues: https://github.com/hiuhiu2026/paper-trend-tracking/issues

---

**Updated:** 2026-04-17  
**Version:** 2.0 (DeepSeek-only extraction)
