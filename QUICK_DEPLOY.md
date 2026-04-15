# Quick Deploy Guide

## 🚀 One-Click Deployment

### Option 1: Automated Script

```bash
cd paper-trend-tracking
chmod +x deploy.sh
./deploy.sh
```

This will:
1. Collect latest papers (if needed)
2. Generate static dashboard
3. Let you choose deployment method

### Option 2: Manual Steps

```bash
# 1. Collect data
python run_virtualcell.py --days 3

# 2. Generate dashboard
python generate_static_dashboard.py

# 3. Deploy
cd vercel_output
vercel --prod
```

## 📊 Deployment Options

### Vercel (Recommended)

**Pros:**
- ✅ Free hosting
- ✅ Automatic HTTPS
- ✅ Custom domain support
- ✅ Auto-deploy on git push
- ✅ Fast CDN

**Steps:**
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd vercel_output
vercel --prod
```

**URL:** `https://your-project.vercel.app`

### GitHub Pages

**Pros:**
- ✅ Free hosting
- ✅ Integrated with GitHub
- ✅ Easy updates

**Steps:**
```bash
cd vercel_output
git init
git add .
git commit -m "Deploy dashboard"
git push origin main:gh-pages --force
```

**URL:** `https://yourusername.github.io/paper-trend-tracking/`

### Netlify

**Pros:**
- ✅ Free hosting
- ✅ Drag-and-drop deployment
- ✅ Form handling

**Steps:**
```bash
# Via Netlify CLI
npm install -g netlify-cli
cd vercel_output
netlify deploy --prod
```

**URL:** `https://your-site.netlify.app`

### Local Testing

```bash
cd vercel_output
python -m http.server 8000
# Open: http://localhost:8000
```

## 🔄 Automatic Updates

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Auto Deploy Dashboard

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
        run: pip install -r requirements.txt
      
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

### Cron Job (VPS)

```bash
# Edit crontab
crontab -e

# Add daily update at 8 AM
0 8 * * * cd /path/to/paper-trend-tracking && \
    source venv/bin/activate && \
    python run_virtualcell.py --days 1 && \
    python generate_static_dashboard.py && \
    cd vercel_output && \
    vercel --prod --confirm
```

## 📈 Dashboard Features

### Interactive Network
- Force-directed graph
- Zoom and pan
- Hover to see keywords
- Node size = importance

### Trend Charts
- 4 metrics (tabs)
- Top 30 keywords
- Interactive Plotly charts

### Paper List
- Recent papers
- Journal info
- Direct links

## 🎨 Customization

### Change Colors

Edit `vercel_output/index.html`:

```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Change to your colors */
}
```

### Add Logo

Add to `index.html` header:

```html
<img src="logo.png" alt="Logo" style="height: 50px;">
```

### Custom Domain

**Vercel:**
1. Go to Vercel Dashboard
2. Project Settings → Domains
3. Add your domain

**GitHub Pages:**
1. Add `CNAME` file to `vercel_output/`
2. Add your domain: `yourdomain.com`
3. Configure DNS

## 📊 Data Export

Dashboard includes download links for:
- `data/papers.json` - All papers
- `data/trends.json` - Trending keywords

## 🔧 Troubleshooting

### Dashboard shows "No data"

```bash
# Regenerate
python run_virtualcell.py --days 3
python generate_static_dashboard.py
```

### Vercel deployment fails

```bash
# Check vercel.json
cat vercel_output/vercel.json

# Try local preview
cd vercel_output
vercel dev
```

### Charts not loading

1. Check browser console (F12)
2. Verify file paths
3. Regenerate dashboard

## 💰 Cost

All options are **FREE**:
- Vercel Hobby: $0
- GitHub Pages: $0
- Netlify: $0

## 📱 Mobile Support

Dashboard is fully responsive:
- ✅ Mobile friendly
- ✅ Touch gestures
- ✅ Adaptive layout

## 🌐 Performance

- Load time: < 2 seconds
- File size: ~50MB total
- CDN delivery (Vercel)
- Optimized Plotly charts

## 📞 Support

- **Vercel Docs:** https://vercel.com/docs
- **Plotly Docs:** https://plotly.com
- **GitHub Issues:** https://github.com/hiuhiu2026/paper-trend-tracking/issues

## 🎉 Success!

After deployment, you'll have:
- ✅ Live dashboard URL
- ✅ Interactive charts
- ✅ Auto-updates (if configured)
- ✅ Shareable link

**Example:** https://virtual-cell-dashboard.vercel.app
