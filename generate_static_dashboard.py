#!/usr/bin/env python3
"""
Generate Static Dashboard for Vercel Deployment

Generates all interactive Plotly charts as static HTML files
and creates an index.html for viewing.

Output: vercel_output/
  - index.html (dashboard interface)
  - charts/network.html
  - charts/trends_*.html
  - data/papers.json
  - data/trends.json
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from database import DatabaseManager, PaperModel, KeywordModel, KeywordNetworkSnapshot, TrendMetrics
from network_builder import NetworkBuilder, TrendAnalyzer
from visualization import NetworkVisualizer
from loguru import logger
import plotly.graph_objects as go
import plotly.io as pio


def generate_dashboard(db_path: str = "output/virtual_cell_papers.db", 
                      output_dir: str = "vercel_output"):
    """Generate static dashboard files"""
    
    db_path = Path(db_path)
    output_dir = Path(output_dir)
    charts_dir = output_dir / "charts"
    data_dir = output_dir / "data"
    
    # Create directories
    output_dir.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 70)
    logger.info("  GENERATING STATIC DASHBOARD")
    logger.info("=" * 70)
    
    # Check database
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        logger.error("Run: python run_virtualcell.py --days 3")
        return False
    
    # Initialize database
    db = DatabaseManager(f"sqlite:///{db_path}")
    session = db.get_session()
    
    try:
        # Get statistics
        paper_count = session.query(PaperModel).count()
        keyword_count = session.query(KeywordModel).count()
        snapshot_count = session.query(KeywordNetworkSnapshot).count()
        
        logger.info(f"\n📊 Database Statistics:")
        logger.info(f"   Papers: {paper_count}")
        logger.info(f"   Keywords: {keyword_count}")
        logger.info(f"   Snapshots: {snapshot_count}")
        
        if paper_count == 0:
            logger.error("No papers in database!")
            return False
        
        # Export papers data
        logger.info("\n📁 Exporting papers data...")
        papers = []
        for paper in session.query(PaperModel).limit(100).all():
            papers.append({
                'id': paper.id,
                'title': paper.title,
                'journal': paper.journal,
                'publication_date': paper.publication_date,
                'source': paper.source,
                'url': paper.url,
                'doi': paper.doi
            })
        
        with open(data_dir / "papers.json", 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        logger.info(f"   Exported {len(papers)} papers")
        
        # Export trends data
        logger.info("\n📈 Exporting trends data...")
        trend_analyzer = TrendAnalyzer(db)
        trends = trend_analyzer.get_trending_keywords(limit=50)
        
        with open(data_dir / "trends.json", 'w', encoding='utf-8') as f:
            json.dump(trends, f, indent=2, ensure_ascii=False)
        logger.info(f"   Exported {len(trends)} trending keywords")
        
        # Generate network visualization
        logger.info("\n🕸️  Generating network visualization...")
        latest_snapshot = session.query(KeywordNetworkSnapshot).order_by(
            KeywordNetworkSnapshot.snapshot_date.desc()
        ).first()
        
        if latest_snapshot:
            builder = NetworkBuilder(db)
            snapshot = builder._load_snapshot(latest_snapshot)
            
            visualizer = NetworkVisualizer(str(charts_dir))
            
            # Generate network graph
            network_file = visualizer.plot_network(
                snapshot.graph,
                title="Virtual Cell Keyword Network",
                top_n=min(100, snapshot.num_nodes),
                save=True
            )
            logger.info(f"   Network saved: {network_file}")
            
            # Copy to vercel_output
            import shutil
            if network_file:
                network_name = Path(network_file).name
                shutil.copy(network_file, output_dir / "network.html")
        else:
            logger.warning("No network snapshot found")
            # Create placeholder
            fig = go.Figure()
            fig.add_annotation(
                text="No network data available<br>Run: python run_virtualcell.py",
                xref="paper", yref="paper",
                showarrow=False, font_size=16
            )
            pio.write_html(fig, str(output_dir / "network.html"))
        
        # Generate trend charts
        logger.info("\n📊 Generating trend charts...")
        if trends:
            metrics = ['growth_rate', 'momentum', 'pagerank', 'degree']
            for metric in metrics:
                chart_file = visualizer.plot_trend_evolution(
                    trends, metric=metric, top_n=30, save=True
                )
                if chart_file:
                    chart_name = Path(chart_file).name
                    shutil.copy(chart_file, charts_dir / f"trends_{metric}.html")
                    logger.info(f"   Trends {metric}: saved")
        else:
            logger.warning("No trends data")
        
        # Generate index.html
        logger.info("\n📄 Generating index.html...")
        generate_index_html(output_dir, paper_count, keyword_count, len(trends))
        
        # Generate vercel.json
        generate_vercel_config(output_dir)
        
        logger.info("\n" + "=" * 70)
        logger.info("  ✅ DASHBOARD GENERATED SUCCESSFULLY")
        logger.info("=" * 70)
        logger.info(f"\n📁 Output directory: {output_dir}")
        logger.info(f"\n🌐 Files:")
        logger.info(f"   - index.html (main dashboard)")
        logger.info(f"   - network.html (keyword network)")
        logger.info(f"   - charts/trends_*.html (trend charts)")
        logger.info(f"   - data/*.json (raw data)")
        logger.info(f"\n🚀 Deploy to Vercel:")
        logger.info(f"   cd {output_dir}")
        logger.info(f"   vercel --prod")
        logger.info(f"\n📊 Or view locally:")
        logger.info(f"   python -m http.server 8000 --directory {output_dir}")
        logger.info(f"   # Open: http://localhost:8000\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def generate_index_html(output_dir: Path, paper_count: int, keyword_count: int, trend_count: int):
    """Generate main dashboard HTML"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Virtual Cell Literature Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #718096;
            font-size: 14px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .content {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}
        
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .chart-container h2 {{
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 20px;
        }}
        
        iframe {{
            width: 100%;
            height: 600px;
            border: none;
            border-radius: 8px;
        }}
        
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .tab {{
            background: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #4a5568;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .tab:hover {{
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }}
        
        .tab.active {{
            background: #667eea;
            color: white;
        }}
        
        .chart-frame {{
            display: none;
        }}
        
        .chart-frame.active {{
            display: block;
        }}
        
        footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
            opacity: 0.9;
        }}
        
        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: 1fr;
            }}
            
            iframe {{
                height: 400px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 Virtual Cell Literature Dashboard</h1>
            <p class="subtitle">AI-powered research trend analysis for Virtual Cell and AI Virtual Cell</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{paper_count}</div>
                    <div class="stat-label">Papers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{keyword_count}</div>
                    <div class="stat-label">Keywords</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{trend_count}</div>
                    <div class="stat-label">Trending</div>
                </div>
            </div>
        </header>
        
        <div class="content">
            <div class="chart-container">
                <h2>🕸️ Keyword Network</h2>
                <iframe src="network.html" title="Keyword Network"></iframe>
            </div>
            
            <div class="chart-container">
                <h2>📈 Trending Keywords</h2>
                
                <div class="tabs">
                    <button class="tab active" onclick="showChart('growth_rate')">🚀 Growth Rate</button>
                    <button class="tab" onclick="showChart('momentum')">⚡ Momentum</button>
                    <button class="tab" onclick="showChart('pagerank')">🎯 PageRank</button>
                    <button class="tab" onclick="showChart('degree')">🔗 Degree</button>
                </div>
                
                <div id="growth_rate" class="chart-frame active">
                    <iframe src="charts/trends_growth_rate.html" title="Growth Rate"></iframe>
                </div>
                <div id="momentum" class="chart-frame">
                    <iframe src="charts/trends_momentum.html" title="Momentum"></iframe>
                </div>
                <div id="pagerank" class="chart-frame">
                    <iframe src="charts/trends_pagerank.html" title="PageRank"></iframe>
                </div>
                <div id="degree" class="chart-frame">
                    <iframe src="charts/trends_degree.html" title="Degree"></iframe>
                </div>
            </div>
            
            <div class="chart-container">
                <h2>📋 Recent Papers</h2>
                <div id="papers-list" style="max-height: 400px; overflow-y: auto;">
                    Loading papers...
                </div>
            </div>
        </div>
        
        <footer>
            <p>Generated by Virtual Cell Literature Tracker</p>
            <p style="margin-top: 10px; font-size: 12px;">
                <a href="data/papers.json" style="color: white;">Download Data</a> • 
                <a href="data/trends.json" style="color: white;">Download Trends</a>
            </p>
        </footer>
    </div>
    
    <script>
        function showChart(chartId) {{
            // Hide all charts
            document.querySelectorAll('.chart-frame').forEach(frame => {{
                frame.classList.remove('active');
            }});
            
            // Remove active from all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected chart
            document.getElementById(chartId).classList.add('active');
            
            // Add active to clicked tab
            event.target.classList.add('active');
        }}
        
        // Load papers
        fetch('data/papers.json')
            .then(r => r.json())
            .then(papers => {{
                const container = document.getElementById('papers-list');
                container.innerHTML = papers.slice(0, 20).map((paper, i) => `
                    <div style="padding: 15px; border-bottom: 1px solid #e2e8f0;">
                        <div style="font-weight: 600; color: #2d3748; margin-bottom: 5px;">
                            ${{i + 1}}. ${{paper.title}}
                        </div>
                        <div style="font-size: 13px; color: #718096;">
                            <span style="margin-right: 15px;">📰 ${{paper.journal || 'N/A'}}</span>
                            <span style="margin-right: 15px;">📅 ${{paper.publication_date || 'N/A'}}</span>
                            <span>🔬 ${{paper.source}}</span>
                        </div>
                        ${{paper.url ? `<a href="${{paper.url}}" target="_blank" style="color: #667eea; font-size: 13px; margin-top: 5px; display: inline-block;">View Paper →</a>` : ''}}
                    </div>
                `).join('');
            }})
            .catch(err => {{
                document.getElementById('papers-list').innerHTML = 'Error loading papers';
                console.error(err);
            }});
    </script>
</body>
</html>
"""
    
    with open(output_dir / "index.html", 'w', encoding='utf-8') as f:
        f.write(html)


def generate_vercel_config(output_dir: Path):
    """Generate Vercel configuration"""
    
    config = {
        "version": 2,
        "name": "virtual-cell-dashboard",
        "builds": [
            {"src": "**/*", "use": "@vercel/static"}
        ],
        "routes": [
            {"src": "/", "dest": "/index.html"},
            {"src": "/(.*)", "dest": "/$1"}
        ]
    }
    
    with open(output_dir / "vercel.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also create README for Vercel
    readme = """# Virtual Cell Literature Dashboard

Static dashboard generated by Virtual Cell Tracker.

## Deploy to Vercel

```bash
cd vercel_output
vercel --prod
```

## Local Testing

```bash
python -m http.server 8000
# Open: http://localhost:8000
```

## Regenerate

```bash
python generate_static_dashboard.py
```
"""
    
    with open(output_dir / "README.md", 'w') as f:
        f.write(readme)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Static Dashboard for Vercel')
    parser.add_argument('--db', type=str, default='output/virtual_cell_papers.db',
                        help='Database path')
    parser.add_argument('--output', type=str, default='vercel_output',
                        help='Output directory')
    
    args = parser.parse_args()
    
    success = generate_dashboard(args.db, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
