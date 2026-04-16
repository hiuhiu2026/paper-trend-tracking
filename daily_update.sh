#!/bin/bash
# AIVC Literature Daily Update Script
# Run this once per day via cron to collect new papers and update dashboard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate Python environment
PYTHON="/home/linuxbrew/.linuxbrew/bin/python3.11"

echo "======================================================================"
echo "  📚 AIVC LITERATURE DAILY UPDATE"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================================"
echo ""

# Step 1: Collect papers from last 24 hours
echo "🔍 Collecting papers from last 24 hours..."
$PYTHON run_virtualcell.py --days 1 --max 100

# Step 2: Regenerate static dashboard
echo ""
echo "📊 Regenerating dashboard..."
$PYTHON generate_static_dashboard.py

# Step 3: Commit and deploy to GitHub Pages
echo ""
echo "🚀 Deploying to GitHub Pages..."
git checkout gh-pages

# Remove old files
rm -rf charts data index.html network.html vercel.json 2>/dev/null || true

# Copy new files
mv vercel_output/* .
rm -rf vercel_output

# Commit changes
git add -A
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    git commit -m "Daily update $(date '+%Y-%m-%d')"
    git push origin gh-pages
    echo "✅ Dashboard updated and deployed!"
fi

# Return to main branch
git checkout main

echo ""
echo "======================================================================"
echo "  ✅ DAILY UPDATE COMPLETE"
echo "  🌐 Dashboard: https://hiuhiu2026.github.io/paper-trend-tracking/"
echo "======================================================================"
