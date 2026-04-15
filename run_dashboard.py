#!/usr/bin/env python3
"""
Launch Paper Trend Tracking Dashboard

Usage:
    python run_dashboard.py [--port 8050] [--db data/papers.db]
"""

import sys
import argparse
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from visualization import TrendDashboard


def main():
    parser = argparse.ArgumentParser(description='Paper Trend Tracking Dashboard')
    parser.add_argument('--port', type=int, default=8050, help='Dashboard port (default: 8050)')
    parser.add_argument('--db', type=str, default='data/papers.db', help='Database path')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  📊 PAPER TREND TRACKING DASHBOARD")
    print("=" * 70)
    print(f"\n📁 Database: {args.db}")
    print(f"🌐 Port: http://localhost:{args.port}")
    print(f"🖥️  Host: {args.host}")
    print("\n⏳ Loading dashboard...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        dashboard = TrendDashboard(db_path=args.db)
        dashboard.create_dashboard(port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you've run the pipeline first:")
        print("      python run_pipeline.py")
        print("   2. Check if database exists:")
        print(f"      ls -lh {args.db}")
        print("   3. Install dash if missing:")
        print("      pip install dash plotly")
        sys.exit(1)


if __name__ == "__main__":
    main()
