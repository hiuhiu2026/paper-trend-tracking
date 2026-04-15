# Dashboard Setup Guide

## Problem: "No data available"

The dashboard shows "No data available" because the database hasn't been created yet.

## Solution: Run the Pipeline First

### Quick Setup (Recommended)

```bash
cd paper-trend-tracking
source venv/bin/activate

# 1. Collect papers + Build network (default)
python run_virtualcell.py --days 3

# 2. Launch dashboard
python run_virtualcell.py --dashboard
```

### Step by Step

```bash
# Step 1: Collect papers and build network (network is built by default)
python run_virtualcell.py --days 3

# Expected output:
# ✅ Report saved: output/virtual-cell-2026-04-15.md
# 📊 Database Status:
#    - Papers: 25
#    - Keywords: 150
#    - Snapshots: 4
# ✅ Dashboard ready!

# Step 2: Launch dashboard
python run_virtualcell.py --dashboard

# Step 3: Open browser
# http://localhost:8051
```

### Verify Database

```bash
# Check if database exists and has data
python check_dashboard_data.py

# Expected output:
# ✅ Database found: output/virtual_cell_papers.db
# 📊 Database Tables:
#    - papers: 25 rows
#    - keywords: 150 rows
#    - keyword_network_snapshots: 4 rows
# ✅ Database looks good!
```

## Common Issues

### Issue 1: Database not found

```
❌ Database not found: output/virtual_cell_papers.db
```

**Solution:**
```bash
python run_virtualcell.py --days 3
# Network is built by default
```

### Issue 2: No papers in database

```
⚠️  No papers in database
```

**Solution:**
```bash
# Increase days or max papers
python run_virtualcell.py --days 7 --max 100
```

### Issue 3: No network snapshots

```
⚠️  Papers exist but no network snapshots
```

**Solution:**
```bash
# Network is built by default, just run:
python run_virtualcell.py --days 3
```

### Issue 4: Dashboard shows empty charts

**Possible causes:**
1. Database path wrong
2. No snapshots built
3. Dashboard looking at wrong database

**Solution:**
```bash
# Specify database explicitly
python run_dashboard.py --db output/virtual_cell_papers.db

# Or use the virtual cell launcher
python run_virtualcell.py --dashboard
```

## Full Workflow

```bash
# 1. Setup environment
conda activate paper-trends

# 2. Run collection and analysis (network built by default)
python run_virtualcell.py --days 3

# 3. Check database
python check_dashboard_data.py

# 4. Launch dashboard
python run_virtualcell.py --dashboard

# 5. Open http://localhost:8051
```

## Automation

```bash
# Daily update at 8 AM (network built by default)
0 8 * * * cd /path/to/paper-trend-tracking && \
    source venv/bin/activate && \
    python run_virtualcell.py --days 1

# Dashboard runs continuously (separate process)
python run_virtualcell.py --dashboard --dashboard-port 8051
```

## File Locations

```
paper-trend-tracking/
├── output/
│   ├── virtual-cell-2026-04-15.md    # Report
│   ├── virtual_cell_papers.db        # Dashboard database ⭐
│   └── vc_visualizations/            # Charts
├── run_virtualcell.py                # Main launcher
├── check_dashboard_data.py           # Diagnostic tool
└── src/
    └── virtual_cell_tracker.py       # Core logic
```

## Dashboard URL

After running `python run_virtualcell.py --dashboard`:

**Open:** http://localhost:8051

**Features:**
- 📈 Trending keywords chart
- 🕸️ Keyword network visualization
- 📋 Data table with export
- ⏱️ Time window selector
- 📊 Metric selector

## Troubleshooting

Still having issues?

```bash
# 1. Check Python path
which python
# Should show: /path/to/paper-trend-tracking/venv/bin/python

# 2. Check dependencies
pip list | grep -E "dash|plotly|sqlalchemy"

# 3. Run diagnostic
python check_dashboard_data.py

# 4. Check logs
tail -f logs/pipeline.log
```

## Need Help?

1. Check `VIRTUAL_CELL_TRACKER.md` for full documentation
2. Check `COMPARISON.md` for feature overview
3. Run `python run_virtualcell.py --help` for options
4. Check GitHub issues: https://github.com/hiuhiu2026/paper-trend-tracking/issues
