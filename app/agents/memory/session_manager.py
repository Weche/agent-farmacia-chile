#!/usr/bin/env python3
"""
Session Manager for AI Agent
Handles session creation, storage, and lifecycle management using Redis
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import redis
import logging
from app.core.utils import get_env_value

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages user sessions and conversation state in Redis
    """
    
    def __init__(self):
        # Redis connection (reuse existing client)
        self.redis_url = get_env_value("REDIS_URL")
        self.redis_client = None
        
        # Session configuration
        self.session_expiry_hours = int(get_env_value("SESSION_EXPIRY_HOURS", "24"))
        self.max_conversation_length = int(get_env_value("MAX_CONVERSATION_LENGTH", "50"))
        self.cleanup_interval = int(get_env_value("SESSION_CLEANUP_INTERVAL", "3600"))  # 1 hour
        
        # Redis key patterns
        self.session_metadata_key = "session:{session_id}:metadata"
        self.session_messages_key = "session:{session_id}:messages"
        self.session_context_key = "session:{session_id}:context"
        self.session_tools_key = "session:{session_id}:tools_used"
        
    def connect(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("✅ SessionManager Redis connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ SessionManager Redis connection failed: {e}")
            self.redis_client = None
            return False
    
    def create_session(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session with unique ID
        
        Args:
            user_context: Optional initial user context (location, preferences, etc.)
            
        Returns:
            Session ID string
        """
        if not self.redis_client:
            if not self.connect():
                raise Exception("Redis connection not available for session creation")
        
        # Generate unique session ID
        session_id = f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Session metadata
        metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "message_count": 0,
            "user_context": user_context or {},
            "session_language": "es",  # Default to Spanish
            "total_tools_used": 0,
            "status": "active"
        }
        
        try:
            # Store session metadata with expiration
            metadata_key = self.session_metadata_key.format(session_id=session_id)
            self.redis_client.hset(metadata_key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in metadata.items()})
            self.redis_client.expire(metadata_key, self.session_expiry_hours * 3600)
            
            # Initialize empty message list
            messages_key = self.session_messages_key.format(session_id=session_id)
            self.redis_client.expire(messages_key, self.session_expiry_hours * 3600)
            
            # Initialize empty context
            context_key = self.session_context_key.format(session_id=session_id)
            self.redis_client.expire(context_key, self.session_expiry_hours * 3600)
            
            # Initialize tools tracking
            tools_key = self.session_tools_key.format(session_id=session_id)
            self.redis_client.expire(tools_key, self.session_expiry_hours * 3600)
            
            logger.info(f"✅ Created new session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session metadata dict or None if not found
        """
        if not self.redis_client:
            return None
            
        try:
            metadata_key = self.session_metadata_key.format(session_id=session_id)
            session_data = self.redis_client.hgetall(metadata_key)
            
            if not session_data:
                return None
            
            # Parse JSON fields
            for key in ["user_context"]:
                if key in session_data:
                    try:
                        session_data[key] = json.loads(session_data[key])
                    except:
                        session_data[key] = {}
            
            # Convert numeric fields
            for key in ["message_count", "total_tools_used"]:
                if key in session_data:
                    session_data[key] = int(session_data[key])
            
            return session_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get session {session_id}: {e}")
            return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session last activity timestamp
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            metadata_key = self.session_metadata_key.format(session_id=session_id)
            self.redis_client.hset(metadata_key, "last_active", datetime.now().isoformat())
            
            # Extend expiration
            self.redis_client.expire(metadata_key, self.session_expiry_hours * 3600)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update session activity {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all associated data
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            # Delete all session keys
            keys_to_delete = [
                self.session_metadata_key.format(session_id=session_id),
                self.session_messages_key.format(session_id=session_id),
                self.session_context_key.format(session_id=session_id),
                self.session_tools_key.format(session_id=session_id)
            ]
            
            deleted_count = self.redis_client.delete(*keys_to_delete)
            logger.info(f"🗑️ Deleted session {session_id} ({deleted_count} keys)")
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to delete session {session_id}: {e}")
            return False
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions
        
        Returns:
            Number of active sessions
        """
        if not self.redis_client:
            return 0
            
        try:
            pattern = self.session_metadata_key.format(session_id="*")
            keys = self.redis_client.keys(pattern)
            return len(keys)
            
        except Exception as e:
            logger.error(f"❌ Failed to count active sessions: {e}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis handles this automatically, but we can track)
        
        Returns:
            Number of sessions cleaned up
        """
        # Redis TTL handles expiration automatically
        # This method is for logging/monitoring purposes
        active_count = self.get_active_sessions_count()
        logger.info(f"🧹 Session cleanup check: {active_count} active sessions")
        return active_count

# Global session manager instance
session_manager = SessionManager()

async def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    if not session_manager.redis_client:
        session_manager.connect()
    return session_manager
