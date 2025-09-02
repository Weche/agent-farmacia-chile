#!/usr/bin/env python3
"""
Analyze database size and structure for Redis migration assessment
"""
import sqlite3
import os
import sys

def analyze_database():
    db_path = 'pharmacy_finder.db'
    
    # Check file size
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        print(f"📁 Database file size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
    else:
        print("❌ Database file not found!")
        return
    
    # Connect and analyze data
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count records
        cursor.execute('SELECT COUNT(*) FROM pharmacies')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM pharmacies WHERE es_turno = 1')
        turno = cursor.fetchone()[0]
        
        print(f"📊 Records: {total:,} total pharmacies, {turno:,} de turno")
        
        # Analyze structure
        cursor.execute('PRAGMA table_info(pharmacies)')
        columns = cursor.fetchall()
        print(f"🏗️  Table structure: {len(columns)} columns")
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")
        
        # Sample data size analysis
        cursor.execute('SELECT * FROM pharmacies LIMIT 1')
        sample = cursor.fetchone()
        if sample:
            # Estimate average record size
            sample_str = str(sample)
            estimated_record_size = len(sample_str.encode('utf-8'))
            estimated_total_size = (estimated_record_size * total) / (1024 * 1024)
            print(f"📏 Estimated data size: ~{estimated_total_size:.2f} MB ({estimated_record_size} bytes/record)")
        
        # Redis assessment
        print(f"\n🔍 Redis Migration Assessment:")
        print(f"   Current DB size: {size_mb:.2f} MB")
        print(f"   Redis limit: 30 MB")
        print(f"   Fits in Redis: {'✅ YES' if size_mb < 30 else '❌ NO'}")
        print(f"   Available space: {30 - size_mb:.2f} MB")
        
        if size_mb < 30:
            print(f"   Recommendation: ✅ Safe to migrate to Redis")
            print(f"   Cache strategy: Consider using Redis for hot data + SQLite for persistence")
        else:
            print(f"   Recommendation: ❌ Use Redis as cache layer only")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    analyze_database()
