#!/usr/bin/env python3
"""
Check Dashboard Database

Diagnose why dashboard shows "no data available"
"""

import sys
from pathlib import Path

# Check database
db_path = Path("output/virtual_cell_papers.db")

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    print("\n💡 Solution: Run the tracker first")
    print("   python run_virtualcell.py --days 3 --network")
    sys.exit(1)

print(f"✅ Database found: {db_path}")
print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB\n")

# Check tables
import sqlite3

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("📊 Database Tables:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    table_name = table[0]
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   - {table_name}: {count} rows")

print()

# Check specific tables
print("📋 Detailed Check:")

# Papers
cursor.execute("SELECT COUNT(*) FROM papers")
paper_count = cursor.fetchone()[0]
print(f"   Papers: {paper_count}")

if paper_count > 0:
    cursor.execute("SELECT id, title, source FROM papers LIMIT 3")
    for row in cursor.fetchall():
        print(f"     - [{row[2]}] {row[1][:60]}...")

# Keywords
cursor.execute("SELECT COUNT(*) FROM keywords")
keyword_count = cursor.fetchone()[0]
print(f"   Keywords: {keyword_count}")

# Snapshots
cursor.execute("SELECT COUNT(*) FROM keyword_network_snapshots")
snapshot_count = cursor.fetchone()[0]
print(f"   Network Snapshots: {snapshot_count}")

if snapshot_count > 0:
    cursor.execute("SELECT time_window, snapshot_date, num_nodes, num_edges FROM keyword_network_snapshots ORDER BY snapshot_date DESC LIMIT 3")
    for row in cursor.fetchall():
        print(f"     - {row[0]}: {row[2]} nodes, {row[3]} edges ({row[1]})")

# Trend metrics
cursor.execute("SELECT COUNT(*) FROM trend_metrics")
trend_count = cursor.fetchone()[0]
print(f"   Trend Metrics: {trend_count}")

conn.close()

print()

# Diagnosis
if paper_count == 0:
    print("❌ No papers in database")
    print("\n💡 Solution:")
    print("   1. Run: python run_virtualcell.py --days 3 --network")
    print("   2. Make sure --network flag is included")
elif snapshot_count == 0:
    print("⚠️  Papers exist but no network snapshots")
    print("\n💡 Solution:")
    print("   Run with --network flag:")
    print("   python run_virtualcell.py --days 3 --network")
else:
    print("✅ Database looks good!")
    print("\n🚀 Launch dashboard:")
    print("   python run_virtualcell.py --dashboard")
    print("   # or")
    print("   python run_dashboard.py --db output/virtual_cell_papers.db")
