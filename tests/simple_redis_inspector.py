#!/usr/bin/env python3
"""
Simple Redis Session Inspector (Windows Compatible)
Analyzes your current Redis sessions
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

import redis
from app.core.utils import get_env_value

def inspect_redis():
    """Simple Redis inspection for your session data"""
    
    print("Redis Session Inspector")
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
    
    # Get all session-related keys
    all_keys = client.keys("session:*")
    print(f"\nTotal Redis keys with 'session:' prefix: {len(all_keys)}")
    
    if not all_keys:
        print("No session data found in Redis")
        return
    
    # Analyze key patterns
    key_patterns = {}
    session_ids = set()
    
    for key in all_keys:
        parts = key.split(':')
        if len(parts) >= 2:
            if len(parts) >= 3:
                session_id = parts[1]
                key_type = ':'.join(parts[2:])
                session_ids.add(session_id)
                
                if key_type not in key_patterns:
                    key_patterns[key_type] = 0
                key_patterns[key_type] += 1
    
    print(f"\nUnique session IDs found: {len(session_ids)}")
    print(f"Key type patterns:")
    for pattern, count in sorted(key_patterns.items()):
        print(f"  {pattern}: {count} keys")
    
    # Show some example sessions
    print(f"\nExample session IDs (first 10):")
    for i, session_id in enumerate(list(session_ids)[:10], 1):
        print(f"  {i:2d}. {session_id}")
    
    if len(session_ids) > 10:
        print(f"    ... and {len(session_ids) - 10} more")
    
    # Check memory usage
    try:
        info = client.info()
        memory_usage = info.get('used_memory_human', 'unknown')
        total_keys = info.get('db0', {}).get('keys', 0) if 'db0' in info else len(all_keys)
        print(f"\nRedis Stats:")
        print(f"  Memory usage: {memory_usage}")
        print(f"  Total keys in DB: {total_keys}")
        print(f"  Connected clients: {info.get('connected_clients', 0)}")
    except Exception as e:
        print(f"Could not get Redis stats: {e}")
    
    # Interactive options
    print(f"\nCleanup Options:")
    print("1. Show detailed session breakdown")
    print("2. Count keys by date pattern")
    print("3. Clean old sessions (>7 days)")
    print("4. Exit")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            # Show session details
            print(f"\nDetailed Session Analysis:")
            session_details = {}
            
            for key in all_keys:
                parts = key.split(':')
                if len(parts) >= 3:
                    session_id = parts[1]
                    key_type = ':'.join(parts[2:])
                    
                    if session_id not in session_details:
                        session_details[session_id] = []
                    session_details[session_id].append(key_type)
            
            print(f"Sessions with their key types:")
            for i, (session_id, key_types) in enumerate(list(session_details.items())[:10], 1):
                print(f"  {i:2d}. {session_id}")
                print(f"      Keys: {', '.join(key_types)}")
                
        elif choice == "2":
            # Count by date
            print(f"\nSession count by date pattern:")
            date_counts = {}
            
            for session_id in session_ids:
                # Extract date from session ID (assuming format sess_YYYYMMDD_*)
                if session_id.startswith('sess_') and len(session_id) > 8:
                    date_part = session_id[5:13]  # Extract YYYYMMDD
                    if date_part not in date_counts:
                        date_counts[date_part] = 0
                    date_counts[date_part] += 1
                else:
                    if 'other' not in date_counts:
                        date_counts['other'] = 0
                    date_counts['other'] += 1
            
            for date, count in sorted(date_counts.items()):
                print(f"  {date}: {count} sessions")
                
        elif choice == "3":
            # Clean old sessions
            print(f"\nIdentifying old sessions...")
            
            current_date = datetime.now()
            cutoff_date = current_date.strftime("%Y%m%d")
            
            old_sessions = []
            for session_id in session_ids:
                if session_id.startswith('sess_') and len(session_id) > 8:
                    date_part = session_id[5:13]
                    if date_part < cutoff_date:
                        # Find all keys for this session
                        session_keys = [k for k in all_keys if f":{session_id}:" in k]
                        old_sessions.extend(session_keys)
            
            if old_sessions:
                print(f"Found {len(old_sessions)} keys from old sessions")
                confirm = input(f"Delete these keys? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    deleted = client.delete(*old_sessions)
                    print(f"Deleted {deleted} old session keys")
                else:
                    print("Cleanup cancelled")
            else:
                print("No old sessions found")
        
        print(f"\nInspection complete!")
        
    except KeyboardInterrupt:
        print(f"\nInspection cancelled")
    except Exception as e:
        print(f"\nError during inspection: {e}")

if __name__ == "__main__":
    try:
        inspect_redis()
    except Exception as e:
        print(f"\nInspector failed: {e}")
        import traceback
        traceback.print_exc()