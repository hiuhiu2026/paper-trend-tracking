# 📊 AIVC Literature Trend Tracker

**AI Virtual Cell (AIVC) research literature tracking with automated trend analysis and interactive dashboard.**

![Last Updated](https://img.shields.io/badge/updated-daily-blue)
![Papers Collected](https://img.shields.io/badge/papers-100+-green)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 What This Does

Automatically collects, analyzes, and visualizes research trends in AI Virtual Cell literature:

- **Daily paper collection** from PubMed, arXiv, bioRxiv
- **Enhanced keyword extraction** with 90%+ specificity (filters generic terms)
- **Hot topic analysis** powered by LLM (DeepSeek/OpenAI)
- **Interactive dashboard** with network graphs and trend charts
- **Auto-deployment** to Vercel, GitHub Pages, or Netlify

**Live Demo:** https://hiuhiu2026.github.io/paper-trend-tracking/

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd paper-trend-tracking

# Option A: Conda (recommended)
conda env create -f environment.yml
conda activate paper-trends

# Option B: pip + venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configure (Optional)

Edit [`config.virtualcell.yaml`](config.virtualcell.yaml) to enable LLM features:

```yaml
llm:
  enabled: true
  provider: deepseek  # or 'openai'
  model: deepseek-chat
  api_key: YOUR_API_KEY_HERE  # Get from https://platform.deepseek.com/api-keys
```

### 3. Run Pipeline

```bash
# Collect papers from last 3 years and build trend analysis
python run_virtualcell.py --days 1095 --max 200 --network
```

### 4. Generate Dashboard

```bash
python generate_static_dashboard.py
```

### 5. Deploy

```bash
# Option A: Vercel (recommended)
cd vercel_output
vercel --prod

# Option B: GitHub Pages
./deploy.sh  # Automated script

# Option C: Local testing
python -m http.server 8000  # Open http://localhost:8000
```

---

## 📁 Project Structure

```
paper-trend-tracking/
├── src/
│   ├── enhanced_keyword_extractor.py  # 🔬 Smart keyword extraction (90%+ specificity)
│   ├── virtual_cell_tracker.py        # 📚 Paper collection & categorization
│   ├── network_builder.py             # 🕸️ Keyword co-occurrence networks
│   ├── visualization.py               # 📊 Network graphs & trend charts
│   ├── data_collector.py              # 🔍 PubMed/arXiv/bioRxiv APIs
│   └── database.py                    # 💾 SQLite storage
├── vercel_output/
│   ├── index.html                     # 📱 Main dashboard
│   ├── network.html                   # 🕸️ Interactive network graph
│   ├── charts/                        # 📈 Trend charts (4 metrics)
│   └── data/                          # 📥 Exportable JSON data
├── output/
│   ├── virtual_cell_papers.db         # SQLite database
│   ├── virtual-cell-latest.md         # Latest report
│   └── vc_visualizations/             # Static network/trend plots
├── config.virtualcell.yaml            # ⚙️ Configuration
├── requirements.txt                   # 📦 Python dependencies
├── environment.yml                    # 📦 Conda environment
├── deploy.sh                          # 🚀 Automated deployment script
└── README.md                          # 📖 This file
```

---

## 🔧 Deployment Options

### Option 1: Vercel (Recommended) ⭐

**Best for:** Production deployment with auto-HTTPS, CDN, and custom domains.

```bash
# Install Vercel CLI
npm install -g vercel

# Generate dashboard
python generate_static_dashboard.py

# Deploy
cd vercel_output
vercel --prod
```

**Result:** `https://your-project.vercel.app`

**Custom Domain:**
1. Vercel Dashboard → Project Settings → Domains
2. Add your domain
3. Configure DNS as instructed

---

### Option 2: GitHub Pages

**Best for:** Free hosting integrated with your GitHub repo.

#### Automated (Recommended)

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
1. Generate the static dashboard
2. Deploy to `gh-pages` branch
3. Provide your live URL

#### Manual

```bash
cd vercel_output

# Initialize git (if first time)
git init
git add .
git commit -m "Deploy dashboard"

# Push to gh-pages
git remote add origin https://github.com/YOUR_USERNAME/paper-trend-tracking.git
git push origin main:gh-pages --force
```

**Result:** `https://YOUR_USERNAME.github.io/paper-trend-tracking/`

**Enable GitHub Pages:**
1. Repo Settings → Pages
2. Source: Deploy from branch → `gh-pages`
3. Save

---

### Option 3: Netlify

**Best for:** Drag-and-drop deployment and form handling.

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd vercel_output
netlify deploy --prod
```

**Result:** `https://your-site.netlify.app`

---

### Option 4: Your Own Server

**Best for:** Full control, internal hosting.

```bash
# Copy static files to your web server
scp -r vercel_output/* user@your-server:/var/www/html/

# Or use Python's built-in server (testing only)
cd vercel_output
python -m http.server 8000
```

---

## 🔄 Automated Updates

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Auto Deploy Dashboard

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM UTC
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Collect papers & generate dashboard
        run: |
          python run_virtualcell.py --days 1 --max 100 --network
          python generate_static_dashboard.py
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./vercel_output
          force_orphan: true
```

### Cron Job (VPS/Server)

```bash
# Edit crontab
crontab -e

# Add daily update at 8 AM (Asia/Shanghai timezone)
0 8 * * * cd /path/to/paper-trend-tracking && \
    source venv/bin/activate && \
    python run_virtualcell.py --days 1 --max 100 && \
    python generate_static_dashboard.py && \
    cd vercel_output && \
    git add . && git commit -m "Auto-update" && git push
```

---

## 📊 Dashboard Features

### 1. Keyword Network Graph
- **Interactive force-directed layout** (zoom, pan, drag)
- **Node size** = keyword importance (degree centrality)
- **Color scale** = trending score
- **Hover** to see full keyword and metrics

### 2. Trending Keywords
- **4 metrics:** Growth Rate, Momentum, PageRank, Degree
- **Top 30 keywords** per metric
- **Interactive Plotly charts** with hover details

### 3. Recent Papers
- **Latest papers** with journal, date, source
- **Direct links** to full papers
- **Category labels** (AI Method, Modeling, Application, etc.)

### 4. Data Export
- Download `papers.json` - All collected papers
- Download `trends.json` - Trending keywords with scores

---

## ⚙️ Configuration

### Main Config: `config.virtualcell.yaml`

```yaml
# API Keys
api_keys:
  pubmed: null  # Optional: https://www.ncbi.nlm.nih.gov/account/

# LLM Configuration (for hot topic analysis & paper summaries)
llm:
  enabled: false  # Set to true to enable
  provider: deepseek  # Options: 'deepseek' or 'openai'
  model: deepseek-chat  # Options: 'deepseek-chat' or 'gpt-4o-mini'
  api_key: YOUR_API_KEY_HERE  # 🔑 Paste your key here
  base_url: https://api.deepseek.com  # Only for DeepSeek

# Collection Settings
collection:
  days_back: 1095  # 3 years
  max_per_query: 200

# Output Settings
output:
  directory: output
  save_latest: true
```

### Get API Keys

- **DeepSeek:** https://platform.deepseek.com/api-keys
- **OpenAI:** https://platform.openai.com/api-keys
- **PubMed:** https://www.ncbi.nlm.nih.gov/account/ (optional, increases rate limit)

---

## 🧪 Testing

### Verify Installation

```bash
python test_keyword_extraction.py
```

### Test Enhanced Keyword Extractor

```bash
python test_enhanced_extractor.py
```

### Test LLM Integration

```bash
# Edit config.virtualcell.yaml to enable LLM
python test_deepseek_hot_topic.py
```

### Check Dashboard Data

```bash
python check_dashboard_data.py
```

---

## 📈 Usage Examples

### Basic Run (Last 3 Days)

```bash
python run_virtualcell.py --days 3 --max 50
```

### Full Collection (3 Years)

```bash
python run_virtualcell.py --days 1095 --max 200 --network
```

### Report Only (No Network)

```bash
python run_virtualcell.py --days 7 --no-network
```

### Custom Output

```bash
python run_virtualcell.py --days 30 --output weekly-report.md
```

### Launch Interactive Dashboard

```bash
python run_dashboard.py --db output/virtual_cell_papers.db
# Open: http://localhost:8050
```

---

## 🎨 Customization

### Change Dashboard Theme

Edit `vercel_output/index.html`:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
}
```

### Add Custom Logo

```html
<!-- Add to index.html header -->
<div class="logo">
    <img src="logo.png" alt="Your Lab Logo" height="50">
</div>
```

### Modify Search Queries

Edit `src/virtual_cell_tracker.py`:

```python
VIRTUAL_CELL_QUERIES = [
    "your custom query",
    "another query",
    # Add/remove queries as needed
]
```

### Adjust Keyword Specificity

Edit `src/enhanced_keyword_extractor.py`:

```python
# Add more generic terms to filter
GENERIC_TERMS = {
    # ... existing terms ...
    'your_generic_term',
}

# Add more specific patterns
SPECIFIC_PATTERNS = [
    r'\b(your_specific_pattern)\b',
]
```

---

## 🐛 Troubleshooting

### "No papers found"

```bash
# Check API connectivity
python test_apis.py

# Try broader queries or increase days_back
python run_virtualcell.py --days 365 --max 200
```

### "Dashboard shows no data"

```bash
# Verify database has data
python check_dashboard_data.py

# Regenerate dashboard
python generate_static_dashboard.py
```

### "LLM API failed"

1. Check API key is valid and not placeholder (`YOUR_API_KEY_HERE`)
2. Verify network connectivity
3. Check provider region restrictions
4. Try switching provider (DeepSeek ↔ OpenAI)

### "Vercel deployment failed"

```bash
# Check vercel.json
cat vercel_output/vercel.json

# Try local preview
cd vercel_output
vercel dev
```

### "Charts not loading"

1. Open browser console (F12)
2. Check for 404 errors on chart files
3. Ensure all files in `vercel_output/` are deployed
4. Regenerate dashboard if needed

---

## 💰 Cost Breakdown

All deployment options are **FREE**:

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Hobby | $0 |
| GitHub Pages | Standard | $0 |
| Netlify | Basic | $0 |
| DeepSeek API | Pay-as-you-go | ~$0.14/1M tokens |
| OpenAI API | Pay-as-you-go | ~$0.15-0.60/1M tokens |

**Estimated monthly cost** (with daily updates + LLM): $1-5

---

## 📊 Performance

- **Collection speed:** ~50-100 papers/minute
- **Keyword extraction:** ~10 papers/second
- **Dashboard load time:** < 2 seconds
- **Total file size:** ~25-50MB (mostly Plotly charts)
- **Mobile friendly:** ✅ Fully responsive

---

## 🔒 Security Notes

- **Never commit API keys** to Git (use `.gitignore`)
- **Keep `config.virtualcell.yaml` local** or use environment variables
- **Dashboard is static** - no server-side code execution
- **All data is public** - don't collect sensitive/private papers

---

## 📚 Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide
- **[QUICK_DEPLOY.md](QUICK_DEPLOY.md)** - Deployment quick reference
- **[VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)** - Vercel-specific guide
- **[ENHANCED_KEYWORDS.md](ENHANCED_KEYWORDS.md)** - Keyword extraction details
- **[USAGE.md](USAGE.md)** - Advanced usage examples

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by: https://github.com/Maojianq/literature-daily-report
- Data sources: PubMed, arXiv, bioRxiv
- Visualization: Plotly, NetworkX
- LLM: DeepSeek, OpenAI

---

## 📞 Support

- **GitHub Issues:** https://github.com/hiuhiu2026/paper-trend-tracking/issues
- **Live Demo:** https://hiuhiu2026.github.io/paper-trend-tracking/
- **Documentation:** See `docs/` folder

---

**Last Updated:** 2026-04-17  
**Version:** 1.1.0  
**Maintainer:** @hiuhiu2026
