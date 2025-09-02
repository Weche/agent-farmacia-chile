#!/usr/bin/env python3
"""
Conversation Memory for AI Agent
Handles conversation history and context storage in Redis
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from app.agents.memory.session_manager import session_manager

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Manages conversation history and context for AI agent sessions
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_manager = session_manager
        
        # Ensure Redis connection
        if not self.session_manager.redis_client:
            self.session_manager.connect()
        
        # Conversation configuration
        self.max_context_tokens = 4000  # Approximate token limit for context
        self.max_messages = 50  # Maximum messages to keep in memory
        
    async def add_message(self, role: str, content: str, tool_calls: Optional[List[Dict]] = None, metadata: Optional[Dict] = None) -> bool:
        """
        Add a message to conversation history
        
        Args:
            role: 'user', 'assistant', or 'system'
            content: Message content
            tool_calls: Optional tool calls made by assistant
            metadata: Optional message metadata
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session_manager.redis_client:
            logger.error("Redis client not available for adding message")
            return False
            
        try:
            # Create message object
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "tool_calls": tool_calls or [],
                "metadata": metadata or {}
            }
            
            # Add to Redis list
            messages_key = self.session_manager.session_messages_key.format(session_id=self.session_id)
            result = self.session_manager.redis_client.lpush(messages_key, json.dumps(message))
            logger.debug(f"Added message to {messages_key}, list length now: {result}")
            
            # Maintain max message limit
            self.session_manager.redis_client.ltrim(messages_key, 0, self.max_messages - 1)
            
            # Set expiration for messages key
            self.session_manager.redis_client.expire(messages_key, self.session_manager.session_expiry_hours * 3600)
            
            # Update session metadata
            await self._update_message_count()
            self.session_manager.update_session_activity(self.session_id)
            
            logger.debug(f"💬 Added {role} message to session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add message to session {self.session_id}: {e}")
            return False
    
    async def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for the session
        
        Args:
            limit: Optional limit on number of messages to return
            
        Returns:
            List of message dictionaries (newest first)
        """
        if not self.session_manager.redis_client:
            logger.error("Redis client not available for getting conversation history")
            return []
            
        try:
            messages_key = self.session_manager.session_messages_key.format(session_id=self.session_id)
            logger.debug(f"Getting messages from key: {messages_key}")
            
            # Get messages from Redis (newest first due to lpush)
            message_limit = limit or self.max_messages
            raw_messages = self.session_manager.redis_client.lrange(messages_key, 0, message_limit - 1)
            logger.debug(f"Retrieved {len(raw_messages)} raw messages from Redis")
            
            # Parse JSON messages
            messages = []
            for i, raw_message in enumerate(raw_messages):
                try:
                    message = json.loads(raw_message)
                    messages.append(message)
                    logger.debug(f"Parsed message {i}: {message['role']} - {message['content'][:50]}...")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Failed to parse message {i} in session {self.session_id}")
                    continue
            
            # Reverse to get chronological order (oldest first)
            messages.reverse()
            logger.debug(f"Returning {len(messages)} messages in chronological order")
            
            return messages
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation history for session {self.session_id}: {e}")
            return []
    
    async def get_context_for_llm(self) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM input
        
        Returns:
            List of messages in OpenAI format
        """
        try:
            history = await self.get_conversation_history()
            
            # Convert to OpenAI format
            llm_messages = []
            for message in history:
                llm_message = {
                    "role": message["role"],
                    "content": message["content"]
                }
                
                # Add tool calls if present (only for assistant messages with proper OpenAI tool call format)
                if message.get("tool_calls") and message["role"] == "assistant":
                    tool_calls = message["tool_calls"]
                    # Check if tool calls are in the proper OpenAI format
                    if tool_calls and isinstance(tool_calls[0], dict):
                        # If it's our simplified format, convert to OpenAI format
                        if "tool" in tool_calls[0]:
                            # Skip adding simplified tool calls to avoid API errors
                            # These will be handled by the agent directly
                            pass
                        else:
                            # It's already in OpenAI format, use as-is
                            llm_message["tool_calls"] = tool_calls
                
                llm_messages.append(llm_message)
            
            return llm_messages
            
        except Exception as e:
            logger.error(f"❌ Failed to format context for LLM in session {self.session_id}: {e}")
            return []
    
    async def add_context(self, key: str, value: Any) -> bool:
        """
        Add context information to the session
        
        Args:
            key: Context key
            value: Context value
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session_manager.redis_client:
            return False
            
        try:
            context_key = self.session_manager.session_context_key.format(session_id=self.session_id)
            
            # Store context as JSON
            context_data = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            
            self.session_manager.redis_client.hset(context_key, key, json.dumps(context_data))
            
            # Update session activity
            self.session_manager.update_session_activity(self.session_id)
            
            logger.debug(f"📝 Added context '{key}' to session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add context to session {self.session_id}: {e}")
            return False
    
    async def get_context(self, key: str) -> Optional[Any]:
        """
        Get context information from the session
        
        Args:
            key: Context key
            
        Returns:
            Context value or None if not found
        """
        if not self.session_manager.redis_client:
            return None
            
        try:
            context_key = self.session_manager.session_context_key.format(session_id=self.session_id)
            raw_context = self.session_manager.redis_client.hget(context_key, key)
            
            if not raw_context:
                return None
            
            context_data = json.loads(raw_context)
            return context_data.get("value")
            
        except Exception as e:
            logger.error(f"❌ Failed to get context '{key}' from session {self.session_id}: {e}")
            return None
    
    async def get_all_context(self) -> Dict[str, Any]:
        """
        Get all context information for the session
        
        Returns:
            Dictionary of context key-value pairs
        """
        if not self.session_manager.redis_client:
            return {}
            
        try:
            context_key = self.session_manager.session_context_key.format(session_id=self.session_id)
            raw_context = self.session_manager.redis_client.hgetall(context_key)
            
            context = {}
            for key, raw_value in raw_context.items():
                try:
                    context_data = json.loads(raw_value)
                    context[key] = context_data.get("value")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Failed to parse context '{key}' in session {self.session_id}")
                    continue
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to get all context from session {self.session_id}: {e}")
            return {}
    
    async def log_tool_usage(self, tool_name: str, tool_args: Dict, result: Any) -> bool:
        """
        Log tool usage for session analytics
        
        Args:
            tool_name: Name of the tool used
            tool_args: Arguments passed to the tool
            result: Tool execution result
            
        Returns:
            True if successful, False otherwise
        """
        if not self.session_manager.redis_client:
            return False
            
        try:
            tools_key = self.session_manager.session_tools_key.format(session_id=self.session_id)
            
            # Create tool usage log entry
            tool_log = {
                "tool": tool_name,
                "timestamp": datetime.now().isoformat(),
                "args": tool_args,
                "success": result is not None and not isinstance(result, Exception),
                "result_type": type(result).__name__
            }
            
            # Add to Redis list
            self.session_manager.redis_client.lpush(tools_key, json.dumps(tool_log))
            
            # Keep last 100 tool uses
            self.session_manager.redis_client.ltrim(tools_key, 0, 99)
            
            # Update total tools counter
            await self._increment_tools_count()
            
            logger.debug(f"🔧 Logged tool usage '{tool_name}' in session {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log tool usage in session {self.session_id}: {e}")
            return False
    
    async def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the conversation session
        
        Returns:
            Dictionary with conversation statistics
        """
        try:
            session_data = self.session_manager.get_session(self.session_id)
            if not session_data:
                return {}
            
            history = await self.get_conversation_history()
            context = await self.get_all_context()
            
            return {
                "session_id": self.session_id,
                "created_at": session_data.get("created_at"),
                "last_active": session_data.get("last_active"),
                "total_messages": len(history),
                "total_tools_used": session_data.get("total_tools_used", 0),
                "context_keys": list(context.keys()),
                "language": session_data.get("session_language", "es"),
                "status": session_data.get("status", "active")
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation summary for session {self.session_id}: {e}")
            return {}
    
    async def _update_message_count(self) -> None:
        """Update message count in session metadata"""
        try:
            metadata_key = self.session_manager.session_metadata_key.format(session_id=self.session_id)
            self.session_manager.redis_client.hincrby(metadata_key, "message_count", 1)
        except Exception as e:
            logger.error(f"❌ Failed to update message count: {e}")
    
    async def _increment_tools_count(self) -> None:
        """Increment tools used count in session metadata"""
        try:
            metadata_key = self.session_manager.session_metadata_key.format(session_id=self.session_id)
            self.session_manager.redis_client.hincrby(metadata_key, "total_tools_used", 1)
        except Exception as e:
            logger.error(f"❌ Failed to increment tools count: {e}")


def create_conversation_memory(session_id: str) -> ConversationMemory:
    """Create a ConversationMemory instance for a session"""
    return ConversationMemory(session_id)
