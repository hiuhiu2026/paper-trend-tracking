# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
cd /home/admin/.openclaw/workspace/projects/paper-trend-tracking
pip install -r requirements.txt
```

### Step 2: Test Keyword Extraction (No API Keys Needed)

```bash
python test_keyword_extraction.py
```

You should see YAKE extracting keywords from sample abstracts.

### Step 3: Run a Small Collection

Create a minimal config:

```bash
cat > config.yaml << 'EOF'
api_keys:
  pubmed: null
  semantic_scholar: null

collection:
  tracked_queries:
    - "machine learning drug discovery"
  max_papers_per_query: 50
  from_date: "2024-01-01"

keywords:
  method: "yake"

database:
  path: "data/papers.db"
EOF
```

Run the pipeline:

```bash
python run_pipeline.py
```

### Step 4: Check Results

```bash
# Check database stats
sqlite3 data/papers.db "SELECT 'Papers:', COUNT(*) FROM papers; SELECT 'Keywords:', COUNT(*) FROM keywords;"

# View visualizations
ls -la output/visualizations/
```

## What to Expect

- **First run**: ~50 papers collected, ~300-500 keywords extracted
- **Time**: 2-5 minutes (API rate limiting)
- **Output**: 
  - `data/papers.db` - SQLite database
  - `output/visualizations/*.html` - Interactive charts
  - `logs/pipeline.log` - Execution log

## Common Issues

### "Module not found"
```bash
pip install -r requirements.txt
```

### "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

### "YAKE not installed"
```bash
pip install yake
```

### Slow collection
- Add API keys to `config.yaml` for higher rate limits
- Reduce `max_papers_per_query` for testing

## Next Steps

1. **Customize queries** - Edit `tracked_queries` in `config.yaml`
2. **Add API keys** - Get free keys for higher limits
3. **Run dashboard** - `python -c "from src.visualization import TrendDashboard; TrendDashboard().create_dashboard()"`
4. **Schedule regular runs** - Set up cron job for daily updates

## Full Pipeline Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Paper Trend Pipeline                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Collection  │   │   Extraction    │   │    Network      │
│               │   │                 │   │                 │
│ • PubMed API  │──▶│ • YAKE (default)│──▶│ • Co-occurrence │
│ • S2 API      │   │ • TF-IDF        │   │ • Time slices   │
│ • Dedup       │   │ • LLM           │   │ • Centrality    │
└───────────────┘   └─────────────────┘   └─────────────────┘
                                                   │
                    ┌──────────────────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │   Trend Analysis  │
          │                   │
          │ • Growth rates    │
          │ • Momentum        │
          │ • Clusters        │
          └───────────────────┘
                    │
                    ▼
          ┌───────────────────┐
          │  Visualizations   │
          │                   │
          │ • Network graphs  │
          │ • Trend charts    │
          │ • Dashboard       │
          └───────────────────┘
```
