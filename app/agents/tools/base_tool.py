#!/usr/bin/env python3
"""
Base Tool Class for AI Agent
Provides foundation for all agent tools with common functionality
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseTool(ABC):
    """
    Abstract base class for all AI agent tools
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usage_count = 0
        self.last_used = None
        
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters
        
        Returns:
            Dictionary with tool execution result
        """
        pass
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for tool parameters
        
        Returns:
            JSON schema dictionary
        """
        pass
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the tool with error handling and logging
        
        Returns:
            Standardized tool result
        """
        start_time = datetime.now()
        
        try:
            # Validate parameters
            validation_result = self._validate_parameters(kwargs)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Parameter validation failed: {validation_result['error']}",
                    "tool": self.name,
                    "execution_time_ms": 0
                }
            
            # Execute tool
            result = await self.execute(**kwargs)
            
            # Update usage statistics
            self.usage_count += 1
            self.last_used = datetime.now()
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Standardize successful result
            return {
                "success": True,
                "data": result,
                "tool": self.name,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.error(f"❌ Tool {self.name} failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "tool": self.name,
                "execution_time_ms": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate parameters against schema
        
        Args:
            params: Parameters to validate
            
        Returns:
            Validation result with success flag and error message
        """
        try:
            schema = self.get_parameters_schema()
            required_params = schema.get("required", [])
            
            # Check required parameters
            for param in required_params:
                if param not in params:
                    return {
                        "valid": False,
                        "error": f"Missing required parameter: {param}"
                    }
            
            # Check parameter types
            properties = schema.get("properties", {})
            for param_name, param_value in params.items():
                if param_name in properties:
                    expected_type = properties[param_name].get("type")
                    if expected_type:
                        if not self._check_type(param_value, expected_type):
                            return {
                                "valid": False,
                                "error": f"Parameter '{param_name}' must be of type {expected_type}"
                            }
            
            return {"valid": True, "error": None}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {e}"
            }
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, allow it
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get tool information for registration
        
        Returns:
            Tool information dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema(),
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }
    
    def get_openai_function_definition(self) -> Dict[str, Any]:
        """
        Get OpenAI function calling format definition
        
        Returns:
            OpenAI function definition
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema()
            }
        }
