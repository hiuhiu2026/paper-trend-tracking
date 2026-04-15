#!/usr/bin/env python3
"""
Virtual Cell Literature Tracker - Launcher

Quick launcher for Virtual Cell tracking with network analysis and dashboard.

Usage:
    python run_virtualcell.py              # Basic (3 days, with network)
    python run_virtualcell.py --days 7     # Last week
    python run_virtualcell.py --dashboard  # Launch dashboard after collection
"""

import sys
import argparse
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from virtual_cell_tracker import VirtualCellTracker


def main():
    parser = argparse.ArgumentParser(
        description='Virtual Cell Literature Tracker - Complete Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect last 3 days with network analysis (default)
  python run_virtualcell.py
  
  # Collect last week, launch dashboard
  python run_virtualcell.py --days 7 --dashboard
  
  # Quick report only (skip network building)
  python run_virtualcell.py --days 1 --no-network
  
  # Full analysis with custom time window
  python run_virtualcell.py --days 14 --time-window month --dashboard
  
  # Dashboard only (using existing database)
  python run_virtualcell.py --dashboard
        """
    )
    
    parser.add_argument('--days', type=int, default=3, 
                        help='Days to look back (default: 3)')
    parser.add_argument('--max', type=int, default=50, 
                        help='Max papers per query (default: 50)')
    parser.add_argument('--output', type=str, default=None, 
                        help='Output report file')
    parser.add_argument('--config', type=str, default='config.virtualcell.yaml', 
                        help='Config file')
    parser.add_argument('--no-network', action='store_true', 
                        help='Skip network building')
    parser.add_argument('--time-window', type=str, default='week', 
                        choices=['day', 'week', 'month'], 
                        help='Network time window')
    parser.add_argument('--dashboard', action='store_true',
                        help='Launch dashboard after collection')
    parser.add_argument('--dashboard-port', type=int, default=8051,
                        help='Dashboard port (default: 8051)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  🧬 VIRTUAL CELL LITERATURE TRACKER")
    print("  Powered by AI + Network Analysis")
    print("=" * 70)
    print()
    
    # Initialize tracker
    tracker = VirtualCellTracker(config_path=args.config)
    
    # Run collection and analysis
    tracker.run(
        days_back=args.days,
        max_per_query=args.max,
        output_file=args.output,
        build_network=not args.no_network,
        time_window=args.time_window
    )
    
    # Launch dashboard if requested
    if args.dashboard:
        print("\n" + "=" * 70)
        print("  🚀 LAUNCHING DASHBOARD")
        print("=" * 70)
        
        from visualization import TrendDashboard
        
        vc_db = tracker.output_dir / "virtual_cell_papers.db"
        
        if vc_db.exists():
            print(f"\n📊 Database: {vc_db}")
            print(f"🌐 Dashboard: http://localhost:{args.dashboard_port}")
            print(f"   Press Ctrl+C to stop\n")
            
            try:
                dashboard = TrendDashboard(db_path=str(vc_db))
                dashboard.create_dashboard(port=args.dashboard_port, debug=False)
            except KeyboardInterrupt:
                print("\n\n👋 Dashboard stopped by user")
            except Exception as e:
                print(f"\n❌ Dashboard error: {e}")
                print("\n💡 Try:")
                print("   python run_dashboard.py --db", vc_db)
        else:
            print(f"\n⚠️  Database not found: {vc_db}")
            print("   Run without --no-network to create it")


if __name__ == "__main__":
    main()
