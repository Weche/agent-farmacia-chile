#!/usr/bin/env python3
"""
Redis Session Cleanup - Remove sessions older than 2 days
"""

import os
import sys
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

import redis
from app.core.utils import get_env_value

def cleanup_old_sessions():
    """Clean Redis sessions older than 2 days"""
    
    print("Redis Session Cleanup - 2 Day Cutoff")
    print("=" * 50)
    
    # Connect to Redis
    redis_url = get_env_value("REDIS_URL")
    try:
        client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        client.ping()
        print("SUCCESS: Redis connected")
    except Exception as e:
        print(f"ERROR: Redis connection failed: {e}")
        return
    
    # Calculate cutoff date (2 days ago)
    cutoff_date = (datetime.now() - timedelta(days=2)).strftime("%Y%m%d")
    print(f"Cutoff date: {cutoff_date} (sessions before this will be deleted)")
    
    # Get all session keys
    all_keys = client.keys("session:*")
    print(f"Total session keys found: {len(all_keys)}")
    
    if not all_keys:
        print("No sessions found")
        return
    
    # Find old sessions
    old_keys = []
    session_dates = {}
    
    for key in all_keys:
        parts = key.split(':')
        if len(parts) >= 2:
            session_id = parts[1]
            
            # Extract date from session ID (format: sess_YYYYMMDD_HHMMSS_hash)
            if session_id.startswith('sess_') and len(session_id) > 13:
                date_part = session_id[5:13]  # Extract YYYYMMDD
                
                if date_part < cutoff_date:
                    old_keys.append(key)
                
                # Track dates for reporting
                if date_part not in session_dates:
                    session_dates[date_part] = 0
                session_dates[date_part] += 1
            else:
                # Handle special cases like test sessions
                if 'test' in session_id.lower():
                    old_keys.append(key)
    
    print(f"\nSession distribution by date:")
    for date, count in sorted(session_dates.items()):
        status = "TO DELETE" if date < cutoff_date else "KEEP"
        print(f"  {date}: {count} keys ({status})")
    
    print(f"\nFound {len(old_keys)} keys from old sessions to delete")
    
    if old_keys:
        # Group by session for cleaner output
        sessions_to_delete = set()
        for key in old_keys:
            parts = key.split(':')
            if len(parts) >= 2:
                sessions_to_delete.add(parts[1])
        
        print(f"This affects {len(sessions_to_delete)} unique sessions:")
        for i, session_id in enumerate(list(sessions_to_delete)[:10], 1):
            print(f"  {i:2d}. {session_id}")
        if len(sessions_to_delete) > 10:
            print(f"    ... and {len(sessions_to_delete) - 10} more")
        
        print(f"\nPROCEEDING WITH DELETION...")
        
        try:
            # Delete old keys in batches
            batch_size = 50
            total_deleted = 0
            
            for i in range(0, len(old_keys), batch_size):
                batch = old_keys[i:i + batch_size]
                deleted = client.delete(*batch)
                total_deleted += deleted
                print(f"Deleted batch {i//batch_size + 1}: {deleted} keys")
            
            print(f"\nSUCCESS: Deleted {total_deleted} old session keys")
            
            # Show updated stats
            remaining_keys = client.keys("session:*")
            print(f"Remaining session keys: {len(remaining_keys)}")
            
            # Memory after cleanup
            try:
                info = client.info()
                memory_usage = info.get('used_memory_human', 'unknown')
                print(f"Redis memory usage after cleanup: {memory_usage}")
            except:
                pass
                
        except Exception as e:
            print(f"ERROR during deletion: {e}")
    else:
        print("No old sessions found to delete")
    
    print(f"\nCleanup complete!")

if __name__ == "__main__":
    try:
        cleanup_old_sessions()
    except Exception as e:
        print(f"\nCleanup failed: {e}")
        import traceback
        traceback.print_exc()