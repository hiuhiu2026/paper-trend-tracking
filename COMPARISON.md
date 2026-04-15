# Paper Tracker Comparison

## Original Pipeline vs Virtual Cell Tracker

### Purpose

| Aspect | Original Pipeline | Virtual Cell Tracker |
|--------|------------------|---------------------|
| **Goal** | Track research trends across all fields | Focus on Virtual Cell & AI Virtual Cell |
| **Output** | Network graphs, trend metrics | Daily markdown report |
| **Analysis** | Keyword co-occurrence networks | Domain-specific categorization |
| **Time Scale** | Historical trends (months/years) | Daily/weekly updates |

### Architecture

```
Original Pipeline:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Collection │ -> │  Extraction  │ -> │   Network   │ -> │   Trends +   │
│  (APIs)     │    │  (YAKE/LLM)  │    │   Building  │    │   Dashboard  │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘

Virtual Cell Tracker:
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Collection │ -> │  Filtering   │ -> │  LLM Sum    │ -> │   Daily      │
│  (APIs)     │    │  (Domain)    │    │  (Optional) │    │   Report     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

### Data Sources

| Source | Original | Virtual Cell | Notes |
|--------|----------|--------------|-------|
| PubMed | ✅ | ✅ | Biomedical literature |
| arXiv | ✅ | ✅ | CS/Q-Bio preprints |
| bioRxiv | ✅ | ✅ | Biology preprints |
| Semantic Scholar | Optional | ❌ | Requires API key |

### Filtering

**Original Pipeline:**
- General keyword extraction
- No domain-specific filtering
- All papers treated equally

**Virtual Cell Tracker:**
```python
# Domain-specific rules
if methodology_match:
    keep = True  # Always keep methods papers
elif biology_match and organism_match:
    keep = True  # Biology + organism
else:
    keep = False  # Filter out

# Relevance scoring
score = 0.0
score += 0.5 if methodology else 0
score += 0.3 if organism_related else 0
score += 1.0 if "virtual cell" in text else 0
```

### Output Format

**Original Pipeline:**
- SQLite database
- Interactive Plotly dashboard
- Network visualizations (HTML)
- Trend charts

**Virtual Cell Tracker:**
```markdown
# Virtual Cell Literature Daily Report

**Date:** 2026-04-15
**Total Papers:** 25

## 📊 Executive Summary
Top 5 high-priority papers

## 🏆 Top Journal Papers
Cell, Nature, Science, etc.

## 🤖 Methodology Papers
AI/ML/Modeling focused

## 🧬 Biology Focus Papers
Biology-focused research

## 📈 Trends
Category distribution
```

### Use Cases

**Original Pipeline - Best for:**
- Long-term trend analysis
- Discovering emerging topics
- Visual exploration
- General research monitoring

**Virtual Cell Tracker - Best for:**
- Daily literature monitoring
- Virtual Cell specific research
- Quick digest of new papers
- Automated email reports
- Lab group updates

### Configuration

**Original Pipeline:**
```yaml
collection:
  tracked_queries:
    - "machine learning"
    - "drug discovery"
  max_papers_per_query: 500

keywords:
  method: "yake"

network:
  time_window: "month"
```

**Virtual Cell Tracker:**
```yaml
collection:
  days_back: 3
  max_per_query: 50
  queries:
    - "virtual cell modeling"
    - "AI virtual cell"

llm:
  enabled: true
  api_key: "sk-..."

filtering:
  min_relevance_score: 0.5
```

### Running

**Original Pipeline:**
```bash
# Full analysis
python run_pipeline.py

# Dashboard
python run_dashboard.py
# Open http://localhost:8050
```

**Virtual Cell Tracker:**
```bash
# Daily report
python src/virtual_cell_tracker.py

# Custom
python src/virtual_cell_tracker.py --days 7 --max 100

# Output
cat output/virtual-cell-latest.md
```

### Automation

**Original Pipeline:**
```bash
# Weekly trend update
0 2 * * 0 cd /path && python run_pipeline.py
```

**Virtual Cell Tracker:**
```bash
# Daily report (every morning)
0 8 * * * cd /path && python src/virtual_cell_tracker.py --days 1
```

## Integration

You can use **both** together:

```bash
# Morning: Daily Virtual Cell report
0 8 * * * python src/virtual_cell_tracker.py --days 1

# Weekly: Full trend analysis
0 2 * * 0 python run_pipeline.py
```

## When to Use Which

### Use Original Pipeline when:
- You want to discover **new research trends**
- You need **visual network analysis**
- You're exploring **multiple research areas**
- You want **interactive dashboards**

### Use Virtual Cell Tracker when:
- You focus on **Virtual Cell research**
- You need **daily literature updates**
- You want **concise markdown reports**
- You need **email-ready summaries**
- You want **LLM-generated summaries**

## Migration

Switching from Original to Virtual Cell:

```bash
# 1. Install (same environment)
conda activate paper-trends

# 2. Configure
cp config.virtualcell.yaml config.yaml

# 3. Run
python src/virtual_cell_tracker.py
```

## Extending Virtual Cell Tracker

### Add New Domain

```python
# Copy virtual_cell_tracker.py
# Edit DOMAIN_KEYWORDS for your field
# Edit QUERIES for your topics
```

### Add Email Reports

```python
def send_email(report_path, recipient):
    import smtplib
    from email.mime.text import MIMEText
    
    with open(report_path) as f:
        content = f.read()
    
    msg = MIMEText(content)
    msg['Subject'] = 'Virtual Cell Daily Report'
    msg['From'] = 'tracker@lab.org'
    msg['To'] = recipient
    
    # Send via SMTP
    server = smtplib.SMTP('smtp.lab.org')
    server.send_message(msg)
```

### Add Slack/Discord Notifications

```python
def post_to_slack(report_path, webhook_url):
    import requests
    
    with open(report_path) as f:
        content = f.read()[:2000]  # Truncate
    
    requests.post(webhook_url, json={
        'text': f"📊 Virtual Cell Report\n{content}"
    })
```

## Summary

| Feature | Original | Virtual Cell |
|---------|----------|--------------|
| **Focus** | General | Virtual Cell specific |
| **Output** | Dashboard + DB | Markdown report |
| **Filtering** | Keywords | Domain rules |
| **Summaries** | No | LLM (optional) |
| **Frequency** | Weekly/Monthly | Daily |
| **Automation** | Cron-ready | Cron-ready |
| **Best for** | Trend discovery | Daily monitoring |

**Recommendation:** Use both! Virtual Cell for daily updates, Original Pipeline for weekly trend analysis.
