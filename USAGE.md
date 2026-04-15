# Paper Trend Tracking - Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
cd paper-trend-tracking
conda env create -f environment.yml
conda activate paper-trends
python -m spacy download en_core_web_sm
```

### 2. Configure (Optional)

Edit `config.yaml` to customize:

```yaml
collection:
  tracked_queries:
    - "machine learning drug discovery"
    - "deep learning protein structure"
    - "AI clinical trials"
  max_papers_per_query: 500

keywords:
  method: "yake"  # or tfidf, llm, hybrid
```

### 3. Run Pipeline

```bash
python run_pipeline.py
```

This will:
1. Collect papers from PubMed, arXiv, and bioRxiv
2. Extract keywords using YAKE
3. Build keyword co-occurrence networks
4. Compute trend metrics
5. Generate visualizations

### 4. View Dashboard

```bash
python run_dashboard.py
```

Open http://localhost:8050 in your browser.

## Data Sources

| Source | Content | API Key | Status |
|--------|---------|---------|--------|
| **PubMed** | Biomedical literature | Optional | ✅ Working |
| **arXiv** | CS, Physics, Math, Quant Bio | No | ✅ Working |
| **bioRxiv** | Biology preprints | No | ⚠️ Unstable |
| Semantic Scholar | All fields | Required | Optional |

### Configure Sources

Edit `config.yaml`:

```yaml
collection:
  default_sources:
    - pubmed
    - arxiv
    - biorxiv  # Remove if causing issues
```

## Output Files

After running the pipeline:

```
paper-trend-tracking/
├── data/
│   └── papers.db           # SQLite database
├── output/
│   └── visualizations/     # HTML charts
│       ├── network_*.html
│       └── trends_*.html
├── logs/
│   └── pipeline.log
└── config.yaml
```

## Dashboard Features

### 📈 Trends Tab
- Bar chart of trending keywords
- Filter by metric (growth rate, momentum, PageRank, etc.)
- Adjustable top-N slider

### 🕸️ Network Tab
- Interactive keyword co-occurrence network
- Zoom and pan
- Hover to see keyword names
- Node size = degree centrality

### 📋 Table Tab
- Exportable data table
- All trend metrics
- Sortable columns

## Advanced Usage

### Custom Date Range

```python
from src.pipeline import PaperTrendPipeline

pipeline = PaperTrendPipeline.from_config('config.yaml')

pipeline.run_collection(
    from_date='2025-01-01',
    to_date='2025-12-31'
)
```

### Different Time Windows

```python
pipeline.run_network_analysis(
    time_window='week'  # or 'day', 'month', 'quarter'
)
```

### Export Trends

```python
trends = pipeline.get_trends(limit=100)

import pandas as pd
df = pd.DataFrame(trends)
df.to_csv('trending_keywords.csv', index=False)
```

## Troubleshooting

### No papers collected

1. Check API connectivity:
   ```bash
   python test_apis.py
   ```

2. Try smaller query:
   ```yaml
   tracked_queries:
     - "machine learning"  # Simpler query
   ```

3. Check logs:
   ```bash
   tail -f logs/pipeline.log
   ```

### Dashboard not loading

1. Make sure pipeline has run:
   ```bash
   python run_pipeline.py
   ```

2. Check database exists:
   ```bash
   ls -lh data/papers.db
   ```

3. Install dash:
   ```bash
   pip install dash plotly
   ```

### Network analysis fails

Error: `too many values to unpack`

✅ **Fixed!** Update to latest version:
```bash
git pull origin main
```

### bioRxiv errors

bioRxiv API can be unstable. To disable:

```yaml
collection:
  default_sources:
    - pubmed
    - arxiv
    # - biorxiv  # Comment out
```

## API Keys (Optional)

### PubMed

Get free API key: https://www.ncbi.nlm.nih.gov/account/

```yaml
api_keys:
  pubmed: "your_ncbi_key"
```

### Semantic Scholar

Get free API key: https://www.semanticscholar.org/product/api

```yaml
api_keys:
  semantic_scholar: "your_s2_key"
```

## Performance Tips

1. **Start small**: Test with 50 papers first
2. **Use API keys**: Higher rate limits
3. **Run overnight**: Large collections take time
4. **Schedule runs**: Use cron for daily updates

```bash
# Daily update at 2 AM
0 2 * * * cd /path/to/paper-trend-tracking && python run_pipeline.py
```

## Support

- GitHub: https://github.com/hiuhiu2026/paper-trend-tracking
- Issues: https://github.com/hiuhiu2026/paper-trend-tracking/issues
