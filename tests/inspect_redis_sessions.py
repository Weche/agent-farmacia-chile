#!/usr/bin/env python3
"""
Redis Session Inspector
Inspects and manages Redis sessions for the pharmacy finder app
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app.agents.memory.session_manager import SessionManager
from app.cache.redis_client import get_redis_client

async def inspect_redis_sessions():
    """Inspect all Redis sessions and provide cleanup options"""
    
    print("Redis Session Inspector")
    print("=" * 50)
    
    # Get Redis client
    redis_client = get_redis_client()
    if not redis_client:
        print("ERROR: Redis not available")
        return
    
    print("SUCCESS: Redis connected")
    
    # Get session manager
    session_manager = SessionManager()
    if not session_manager.connect():
        print("ERROR: Session manager connection failed")
        return
    
    # 1. Count all sessions
    print("\nSESSION OVERVIEW")
    print("-" * 30)
    
    # Get all session keys
    session_keys = []
    try:
        # Look for session keys
        all_keys = redis_client.keys("session:*")
        session_keys = [key.decode() if isinstance(key, bytes) else key for key in all_keys]
        
        print(f"Total sessions in Redis: {len(session_keys)}")
        
        if not session_keys:
            print("✅ No sessions found - Redis is clean!")
            return
            
    except Exception as e:
        print(f"❌ Error getting session keys: {e}")
        return
    
    # 2. Analyze sessions
    print(f"\n🔎 ANALYZING {len(session_keys)} SESSIONS")
    print("-" * 40)
    
    active_sessions = []
    expired_sessions = []
    invalid_sessions = []
    
    for key in session_keys:
        try:
            session_data = redis_client.hgetall(key)
            if not session_data:
                invalid_sessions.append(key)
                continue
                
            # Decode if necessary
            if isinstance(next(iter(session_data.keys())), bytes):
                session_data = {k.decode(): v.decode() for k, v in session_data.items()}
            
            created_at = session_data.get('created_at')
            last_active = session_data.get('last_active', created_at)
            
            if created_at and last_active:
                created_time = datetime.fromisoformat(created_at)
                active_time = datetime.fromisoformat(last_active)
                
                # Consider active if used in last 24 hours
                if datetime.now() - active_time < timedelta(hours=24):
                    active_sessions.append({
                        'key': key,
                        'session_id': key.replace('session:', ''),
                        'created': created_time,
                        'last_active': active_time,
                        'language': session_data.get('session_language', 'unknown'),
                        'context': session_data.get('user_context', '{}')
                    })
                else:
                    expired_sessions.append({
                        'key': key,
                        'session_id': key.replace('session:', ''),
                        'created': created_time,
                        'last_active': active_time,
                        'age_days': (datetime.now() - active_time).days
                    })
            else:
                invalid_sessions.append(key)
                
        except Exception as e:
            print(f"❌ Error processing {key}: {e}")
            invalid_sessions.append(key)
    
    # 3. Report results
    print(f"✅ Active sessions (< 24h): {len(active_sessions)}")
    print(f"⏰ Expired sessions (> 24h): {len(expired_sessions)}")
    print(f"❌ Invalid sessions: {len(invalid_sessions)}")
    
    # 4. Show active sessions
    if active_sessions:
        print(f"\n🟢 ACTIVE SESSIONS ({len(active_sessions)})")
        print("-" * 25)
        for i, session in enumerate(active_sessions[:10], 1):  # Show first 10
            hours_ago = (datetime.now() - session['last_active']).total_seconds() / 3600
            context = json.loads(session['context']) if session['context'] != '{}' else {}
            location = context.get('location', 'Unknown')
            
            print(f"{i:2d}. {session['session_id'][:12]}... ({session['language']})")
            print(f"    Last active: {hours_ago:.1f}h ago | Location: {location}")
        
        if len(active_sessions) > 10:
            print(f"    ... and {len(active_sessions) - 10} more")
    
    # 5. Show expired sessions
    if expired_sessions:
        print(f"\n🟡 EXPIRED SESSIONS ({len(expired_sessions)})")
        print("-" * 26)
        for i, session in enumerate(expired_sessions[:5], 1):  # Show first 5
            print(f"{i:2d}. {session['session_id'][:12]}... (inactive {session['age_days']} days)")
        
        if len(expired_sessions) > 5:
            print(f"    ... and {len(expired_sessions) - 5} more")
    
    # 6. Show invalid sessions
    if invalid_sessions:
        print(f"\n🔴 INVALID SESSIONS ({len(invalid_sessions)})")
        print("-" * 25)
        for key in invalid_sessions[:5]:
            print(f"  - {key}")
        if len(invalid_sessions) > 5:
            print(f"    ... and {len(invalid_sessions) - 5} more")
    
    # 7. Check conversation memory
    print(f"\n💬 CONVERSATION MEMORY ANALYSIS")
    print("-" * 35)
    
    # Look for conversation keys
    convo_keys = redis_client.keys("conversation:*")
    convo_count = len(convo_keys)
    print(f"Total conversation histories: {convo_count}")
    
    # 8. Cleanup recommendations
    print(f"\n🧹 CLEANUP RECOMMENDATIONS")
    print("-" * 30)
    
    if expired_sessions:
        print(f"💡 Consider cleaning {len(expired_sessions)} expired sessions")
    
    if invalid_sessions:
        print(f"💡 Consider removing {len(invalid_sessions)} invalid sessions")
    
    if convo_count > len(session_keys):
        orphaned = convo_count - len(session_keys)
        print(f"💡 Found {orphaned} potentially orphaned conversation histories")
    
    # 9. Interactive cleanup (optional)
    print(f"\n🤔 CLEANUP OPTIONS")
    print("-" * 20)
    print("1. Clean expired sessions (> 7 days)")
    print("2. Clean invalid sessions")
    print("3. Clean orphaned conversations")
    print("4. Show detailed session info")
    print("5. Exit without changes")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            # Clean very old sessions
            very_old = [s for s in expired_sessions if s['age_days'] > 7]
            if very_old:
                print(f"\n🧹 Cleaning {len(very_old)} sessions older than 7 days...")
                for session in very_old:
                    try:
                        redis_client.delete(session['key'])
                        # Also clean conversation
                        redis_client.delete(f"conversation:{session['session_id']}")
                        print(f"  ✅ Cleaned {session['session_id'][:12]}...")
                    except Exception as e:
                        print(f"  ❌ Error cleaning {session['session_id'][:12]}...: {e}")
                print(f"✅ Cleanup complete!")
            else:
                print("No sessions older than 7 days found.")
                
        elif choice == "2":
            # Clean invalid sessions
            if invalid_sessions:
                print(f"\n🧹 Cleaning {len(invalid_sessions)} invalid sessions...")
                for key in invalid_sessions:
                    try:
                        redis_client.delete(key)
                        print(f"  ✅ Cleaned {key}")
                    except Exception as e:
                        print(f"  ❌ Error cleaning {key}: {e}")
                print(f"✅ Cleanup complete!")
            else:
                print("No invalid sessions found.")
                
        elif choice == "3":
            # Clean orphaned conversations
            print(f"\n🧹 Checking for orphaned conversations...")
            session_ids = {key.replace('session:', '') for key in session_keys}
            
            cleaned = 0
            for convo_key in convo_keys:
                convo_session_id = convo_key.decode().replace('conversation:', '') if isinstance(convo_key, bytes) else convo_key.replace('conversation:', '')
                if convo_session_id not in session_ids:
                    try:
                        redis_client.delete(convo_key)
                        cleaned += 1
                        print(f"  ✅ Cleaned orphaned conversation for {convo_session_id[:12]}...")
                    except Exception as e:
                        print(f"  ❌ Error cleaning conversation {convo_session_id[:12]}...: {e}")
            
            if cleaned:
                print(f"✅ Cleaned {cleaned} orphaned conversations!")
            else:
                print("No orphaned conversations found.")
                
        elif choice == "4":
            # Show detailed info
            if active_sessions:
                session = active_sessions[0]
                print(f"\n📋 DETAILED SESSION INFO")
                print(f"Session ID: {session['session_id']}")
                print(f"Created: {session['created']}")
                print(f"Last Active: {session['last_active']}")
                print(f"Language: {session['language']}")
                context = json.loads(session['context']) if session['context'] != '{}' else {}
                print(f"Context: {json.dumps(context, indent=2)}")
                
        print(f"\n✅ Session inspection complete!")
        
    except KeyboardInterrupt:
        print(f"\n👋 Session inspection cancelled")
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(inspect_redis_sessions())
    except Exception as e:
        print(f"\n💥 Inspector failed: {e}")
        import traceback
        traceback.print_exc()