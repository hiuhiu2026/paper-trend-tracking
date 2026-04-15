#!/bin/bash
# One-click deployment script for Virtual Cell Dashboard

set -e

echo "========================================"
echo "  Virtual Cell Dashboard Deployment"
echo "========================================"
echo ""

# Check if database exists
if [ ! -f "output/virtual_cell_papers.db" ]; then
    echo "❌ Database not found!"
    echo ""
    echo "Running data collection first..."
    python run_virtualcell.py --days 3
fi

# Generate static dashboard
echo "📊 Generating static dashboard..."
python generate_static_dashboard.py

echo ""
echo "========================================"
echo "  Dashboard Generated Successfully!"
echo "========================================"
echo ""
echo "📁 Output: vercel_output/"
echo ""
echo "Choose deployment method:"
echo ""
echo "1. Deploy to Vercel (recommended)"
echo "2. Deploy to GitHub Pages"
echo "3. Test locally"
echo "4. Exit"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Deploying to Vercel..."
        echo ""
        
        # Check if vercel CLI is installed
        if ! command -v vercel &> /dev/null; then
            echo "Installing Vercel CLI..."
            npm install -g vercel
        fi
        
        cd vercel_output
        vercel --prod
        ;;
    2)
        echo ""
        echo "📦 Deploying to GitHub Pages..."
        echo ""
        
        cd vercel_output
        git init
        git add .
        git commit -m "Dashboard deployment"
        git push origin main:gh-pages --force
        
        echo ""
        echo "✅ Deployed to GitHub Pages!"
        echo "Access at: https://YOUR_USERNAME.github.io/paper-trend-tracking/"
        ;;
    3)
        echo ""
        echo "🧪 Starting local server..."
        echo ""
        echo "Access at: http://localhost:8000"
        echo "Press Ctrl+C to stop"
        echo ""
        
        cd vercel_output
        python -m http.server 8000
        ;;
    4)
        echo ""
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
