#!/usr/bin/env python3
"""
Tool Registry for AI Agent
Manages registration and access to all agent tools
"""

import logging
from typing import Dict, List, Any, Optional
from app.agents.tools.base_tool import BaseTool
from app.agents.tools.farmacia_tools import SearchFarmaciasTool, SearchFarmaciasNearbyTool, GetCommunesTool
from app.agents.tools.medicamento_tools import LookupMedicamentoTool, GetMedicationCategoriestool

logger = logging.getLogger(__name__)

# Import Google Maps tools
try:
    from app.tools.google_maps_tools import (
        GoogleMapsGeocodingTool,
        GoogleMapsReverseGeocodingTool,
        GoogleMapsPlacesNearbyTool,
        GoogleMapsDistanceMatrixTool
    )
    GOOGLE_MAPS_AVAILABLE = True
except ImportError:
    GOOGLE_MAPS_AVAILABLE = False
    logger.warning("⚠️ Google Maps tools not available - install google maps dependencies")

class ToolRegistry:
    """
    Registry for managing AI agent tools
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        default_tools = [
            SearchFarmaciasTool(),
            SearchFarmaciasNearbyTool(),
            GetCommunesTool(),
            LookupMedicamentoTool(),
            GetMedicationCategoriestool()
        ]
        
        # Add Google Maps tools if available
        if GOOGLE_MAPS_AVAILABLE:
            google_maps_tools = [
                GoogleMapsGeocodingTool(),
                GoogleMapsReverseGeocodingTool(),
                GoogleMapsPlacesNearbyTool(),
                GoogleMapsDistanceMatrixTool()
            ]
            default_tools.extend(google_maps_tools)
            logger.info("🗺️ Google Maps tools added to registry")
        
        for tool in default_tools:
            self.register_tool(tool)
            logger.info(f"✅ Registered tool: {tool.name}")
    
    def register_tool(self, tool: BaseTool) -> bool:
        """
        Register a new tool
        
        Args:
            tool: Tool instance to register
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not isinstance(tool, BaseTool):
                logger.error(f"❌ Tool must be instance of BaseTool: {type(tool)}")
                return False
            
            if tool.name in self.tools:
                logger.warning(f"⚠️ Tool {tool.name} already registered, replacing...")
            
            self.tools[tool.name] = tool
            logger.debug(f"📝 Registered tool: {tool.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to register tool: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all registered tools
        
        Returns:
            List of all tools
        """
        return list(self.tools.values())
    
    def get_tool_names(self) -> List[str]:
        """
        Get names of all registered tools
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all tools
        
        Returns:
            List of tool information dictionaries
        """
        return [tool.get_tool_info() for tool in self.tools.values()]
    
    def get_openai_functions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function definitions for all tools
        
        Returns:
            List of OpenAI function definitions
        """
        return [tool.get_openai_function_definition() for tool in self.tools.values()]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": self.get_tool_names()
            }
        
        try:
            result = await tool.run(**kwargs)
            logger.info(f"🔧 Executed tool '{tool_name}' - Success: {result.get('success', False)}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Tool execution failed for '{tool_name}': {e}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name
            }
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for all tools
        
        Returns:
            Dictionary with usage statistics
        """
        stats = {
            "total_tools": len(self.tools),
            "tools": {}
        }
        
        total_usage = 0
        for tool_name, tool in self.tools.items():
            tool_stats = {
                "usage_count": tool.usage_count,
                "last_used": tool.last_used.isoformat() if tool.last_used else None,
                "description": tool.description
            }
            stats["tools"][tool_name] = tool_stats
            total_usage += tool.usage_count
        
        stats["total_usage"] = total_usage
        
        # Most used tool
        if self.tools:
            most_used = max(self.tools.values(), key=lambda t: t.usage_count)
            stats["most_used_tool"] = {
                "name": most_used.name,
                "usage_count": most_used.usage_count
            }
        
        return stats
    
    def validate_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a tool call without executing it
        
        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            
        Returns:
            Validation result
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "valid": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        try:
            validation_result = tool._validate_parameters(parameters)
            return validation_result
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }


# Global tool registry instance
tool_registry = ToolRegistry()

def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    return tool_registry
