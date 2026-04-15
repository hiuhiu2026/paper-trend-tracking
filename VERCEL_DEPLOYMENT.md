# Vercel Deployment Guide

## Quick Deploy

### 1. Generate Static Dashboard

```bash
cd paper-trend-tracking
source venv/bin/activate

# First, collect data
python run_virtualcell.py --days 3

# Generate static dashboard
python generate_static_dashboard.py
```

### 2. Deploy to Vercel

#### Option A: Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to output directory
cd vercel_output

# Deploy
vercel --prod
```

#### Option B: Vercel Web UI

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Set **Root Directory** to `vercel_output`
4. Click **Deploy**

#### Option C: GitHub Pages

```bash
cd vercel_output

# Initialize git
git init
git add .
git commit -m "Dashboard deployment"

# Push to gh-pages branch
git push origin main:gh-pages
```

Then access at: `https://yourusername.github.io/paper-trend-tracking/`

## Output Structure

```
vercel_output/
├── index.html              # Main dashboard
├── network.html            # Keyword network (interactive)
├── vercel.json             # Vercel config
├── README.md               # Deployment guide
├── charts/
│   ├── trends_growth_rate.html
│   ├── trends_momentum.html
│   ├── trends_pagerank.html
│   └── trends_degree.html
└── data/
    ├── papers.json         # Paper data
    └── trends.json         # Trend data
```

## Features

✅ **Fully Static** - No server required
✅ **Interactive Charts** - Plotly interactive visualizations
✅ **Responsive Design** - Works on mobile and desktop
✅ **Fast Loading** - Pre-generated HTML files
✅ **Data Export** - Download JSON data

## Dashboard Views

### 1. Keyword Network
- Interactive force-directed graph
- Zoom and pan
- Hover to see keywords
- Node size = degree centrality

### 2. Trending Keywords
- 4 metrics: Growth Rate, Momentum, PageRank, Degree
- Tab-based navigation
- Top 30 keywords per metric

### 3. Recent Papers
- List of latest papers
- Journal, date, source info
- Direct links to papers

## Custom Domain

After deploying to Vercel:

1. Go to Vercel Dashboard
2. Select your project
3. Go to **Settings** → **Domains**
4. Add your custom domain

## Automatic Updates

### GitHub Actions (Recommended)

Create `.github/workflows/deploy-dashboard.yml`:

```yaml
name: Deploy Dashboard

on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Generate dashboard
        run: |
          python run_virtualcell.py --days 1
          python generate_static_dashboard.py
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./vercel_output
```

### Manual Updates

```bash
# Regenerate and deploy
python run_virtualcell.py --days 3
python generate_static_dashboard.py
cd vercel_output
vercel --prod
```

## Environment Variables

No environment variables needed for static dashboard!

All data is pre-generated and stored in static files.

## Troubleshooting

### Dashboard shows "No data"

1. Check database exists:
   ```bash
   python check_dashboard_data.py
   ```

2. Regenerate:
   ```bash
   python generate_static_dashboard.py
   ```

### Vercel deployment fails

1. Check `vercel.json` is valid:
   ```bash
   cat vercel.json
   ```

2. Try local preview:
   ```bash
   vercel dev
   ```

### Charts not loading

1. Check file paths in `index.html`
2. Ensure all HTML files are in correct directories
3. Check browser console for errors

## Performance

- **Load time**: < 2 seconds
- **File size**: ~25MB (mostly Plotly charts)
- **Mobile friendly**: Yes
- **Browser support**: All modern browsers

## Cost

- **Vercel Hobby**: Free (unlimited deployments)
- **GitHub Pages**: Free
- **Netlify**: Free

## Examples

### Local Testing

```bash
cd vercel_output
python -m http.server 8000
# Open: http://localhost:8000
```

### Production URL

After deployment:
```
https://your-project.vercel.app
```

## Support

- Vercel Docs: https://vercel.com/docs
- Plotly Docs: https://plotly.com/python/
- GitHub Issues: https://github.com/hiuhiu2026/paper-trend-tracking/issues
