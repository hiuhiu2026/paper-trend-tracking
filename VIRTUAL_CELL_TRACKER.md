# Virtual Cell Literature Tracker

Automated literature collection and daily report generation for **Virtual Cell** and **AI Virtual Cell** research.

Inspired by: [literature-daily-report](https://github.com/Maojianq/literature-daily-report)

## Features

✅ **Automated Collection**
- PubMed (biomedical literature)
- arXiv (CS/Q-Bio preprints)
- bioRxiv (biology preprints)

✅ **Domain-Specific Filtering**
- Virtual Cell modeling
- AI/ML for cell simulation
- Digital twin cells
- Multi-scale modeling
- Systems biology

✅ **Smart Categorization**
- Methodology papers (AI/ML/Modeling)
- Biology focus papers
- Relevance scoring
- Top journal identification

✅ **LLM Summaries** (optional)
- Structured Chinese summaries
- Research objective/methods/conclusions
- Powered by GPT-4o-mini or DeepSeek

✅ **Daily Reports**
- Executive summary
- High priority papers
- Category distribution
- Markdown format

## Quick Start

### 1. Install Dependencies

```bash
cd paper-trend-tracking
conda activate paper-trends
```

### 2. Configure (Optional)

Edit `config.virtualcell.yaml`:

```yaml
# Enable LLM summaries
llm:
  enabled: true
  api_key: "your-openai-key"

# Customize queries
collection:
  queries:
    - "your specific topic"
```

### 3. Run Tracker

```bash
# Quick launcher (recommended)
python run_virtualcell.py

# Collect last 3 days, build network, launch dashboard
python run_virtualcell.py --days 3 --dashboard

# Custom settings
python run_virtualcell.py --days 7 --max 100 --time-window month
```

### 4. View Results

```bash
# View report
cat output/virtual-cell-latest.md

# View network visualizations
ls output/vc_visualizations/

# Launch dashboard
python run_virtualcell.py --dashboard
# Open: http://localhost:8051
```

## Search Queries

Default queries cover:

### Core Virtual Cell
- Virtual cell modeling
- Digital twin cell
- Whole cell simulation
- Computational cell model

### AI + Virtual Cell
- AI virtual cell
- Machine learning cell model
- Deep learning cell simulation
- Foundation model cell biology

### Systems Biology
- Multiscale cell model
- Integrative cell modeling
- Systems biology modeling

**Customize:** Edit `VIRTUAL_CELL_QUERIES` in `src/virtual_cell_tracker.py`

## Filtering Logic

Papers are categorized and filtered based on:

### Methodology Categories (always kept)
- **Modeling**: simulation, computational, in silico
- **AI/ML**: machine learning, deep learning, neural networks
- **Multi-scale**: multiscale, whole-cell, hierarchical

### Biology Categories (need organism keywords)
- **Cell Biology**: signaling, metabolism, gene regulation
- **Systems Biology**: networks, pathways, omics

### Organism Keywords
- human, mammalian, cell, tissue
- yeast, bacteria, E. coli
- mouse, rat, organism

### Relevance Scoring
- Methodology match: +0.5
- Organism related: +0.3
- Multiple categories: +0.2
- **Virtual Cell keywords**: +1.0 (virtual cell, digital twin, whole cell)

**Threshold:** Papers with score ≥ 0.5 are included

## Report Structure

```markdown
# Virtual Cell Literature Daily Report

**Date:** 2026-04-15
**Total Papers:** 25
**High Priority:** 5
**Methodology:** 15
**Biology Focus:** 10

---

## 📊 Executive Summary
Key highlights with top 5 papers

## 🏆 Top Journal Papers
Papers from Cell, Nature, Science, etc.

## 🤖 Methodology Papers
AI/ML/Modeling focused papers

## 🧬 Biology Focus Papers
Biology-focused research

## 📈 Trends
Category distribution and trends
```

## LLM Summaries

Enable automatic Chinese summaries:

```yaml
llm:
  enabled: true
  provider: openai
  model: gpt-4o-mini
  api_key: "sk-..."
```

**Summary format:**
```
【研究目的】: What problem does this study aim to solve?
【研究方法】: What methods/techniques were used?
【研究结论】: What are the main findings?
```

**Alternative:** Use DeepSeek

```python
# In virtual_cell_tracker.py, change to:
from deepseek import DeepSeek
```

## Output Files

```
output/
├── virtual-cell-2026-04-15.md      # Daily report with network analysis
├── virtual-cell-2026-04-16.md
├── virtual-cell-latest.md          # Latest report
├── virtual_cell_papers.db          # SQLite database for dashboard
└── vc_visualizations/
    ├── network_*.html              # Keyword network graph
    └── trends_*.html               # Trend charts
```

## Automation

### Daily Cron Job

```bash
# Run every day at 8 AM
0 8 * * * cd /path/to/paper-trend-tracking && python src/virtual_cell_tracker.py
```

### Email Notifications

```python
# Add to virtual_cell_tracker.py
import smtplib
from email.mime.text import MIMEText

def send_email(report_path, recipient):
    # Send report via email
    pass
```

## Customization

### Add New Data Sources

```python
def fetch_google_scholar():
    # Add Google Scholar search
    pass

# In collect_daily():
scholar_papers = fetch_google_scholar()
all_papers.extend(scholar_papers)
```

### Adjust Filtering

```python
# In _categorize_paper():
# Make filtering stricter
if relevance_score < 1.0:  # Was 0.5
    return None
```

### Add Categories

```python
DOMAIN_KEYWORDS = {
    "New Category": [
        "keyword1", "keyword2"
    ]
}
```

## Troubleshooting

### No papers found
- Expand search queries
- Increase `days_back`
- Check API connectivity: `python test_apis.py`

### LLM summaries not working
- Check API key is valid
- Ensure `openai` package installed: `pip install openai`
- Check network connection

### Too many papers
- Increase `min_relevance_score` in config
- Add more specific queries
- Enable stricter filtering

## Examples

### Focus on AI Methods Only

```python
# Edit VIRTUAL_CELL_QUERIES:
VIRTUAL_CELL_QUERIES = [
    "AI virtual cell",
    "machine learning cell model",
    "deep learning cell simulation",
    "foundation model biology"
]
```

### Include Only Human Cells

```python
# In _categorize_paper():
if "human" not in text and "mammalian" not in text:
    return None
```

### Generate Weekly Report

```bash
python src/virtual_cell_tracker.py --days 7 --output weekly-report.md
```

## Comparison with Original Pipeline

| Feature | Original Pipeline | Virtual Cell Tracker |
|---------|------------------|---------------------|
| Data Sources | PubMed, arXiv, bioRxiv | Same |
| Focus | General research trends | Virtual Cell specific |
| Filtering | Keyword-based | Domain-specific rules |
| Summaries | None | LLM-powered (optional) |
| Output | Dashboard + Network + Trends | Report + Network + Dashboard |
| Dashboard | General trends | Virtual Cell specific |
| Automation | Manual | Cron-ready |

**Both now include:**
- ✅ Network analysis
- ✅ Interactive dashboard
- ✅ Trend detection
- ✅ Visualization charts

## License

MIT

## Credits

Inspired by [literature-daily-report](https://github.com/Maojianq/literature-daily-report)
