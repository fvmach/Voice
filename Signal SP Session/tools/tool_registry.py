"""
Tool Registry for OpenAI Function Calling

This module provides a central registry for all tools available to the AI agents.
Tools can be registered with their OpenAI function definitions and execution handlers.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
import json

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all OpenAI function tools"""

    def __init__(self):
        self.tools: Dict[str, dict] = {}  # name -> OpenAI function definition
        self.handlers: Dict[str, Callable] = {}  # name -> execution handler
        self.agent_tools: Dict[str, List[str]] = {}  # agent_name -> list of tool names
        self.tool_usage_stats: Dict[str, int] = {}  # tool_name -> call count
        self.tool_errors: Dict[str, int] = {}  # tool_name -> error count
        self.tool_metadata: Dict[str, dict] = {}  # tool_name -> additional metadata

    def register_tool(
        self,
        name: str,
        definition: dict,
        handler: Callable,
        agents: Optional[List[str]] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Register a tool with its OpenAI definition and execution handler

        Args:
            name: Unique tool identifier
            definition: OpenAI function definition (JSON schema)
            handler: Callable that executes the tool
            agents: List of agent names that can use this tool (None = all agents)
            metadata: Optional metadata about the tool (category, priority, etc.)
        """
        if name in self.tools:
            logger.warning(f"[TOOL] Tool '{name}' already registered, overwriting")

        self.tools[name] = definition
        self.handlers[name] = handler
        self.tool_usage_stats[name] = 0
        self.tool_errors[name] = 0

        # Store metadata
        if metadata:
            self.tool_metadata[name] = metadata

        # Register tool for specific agents or all agents
        if agents:
            for agent in agents:
                if agent not in self.agent_tools:
                    self.agent_tools[agent] = []
                if name not in self.agent_tools[agent]:
                    self.agent_tools[agent].append(name)

        logger.info(f"[TOOL] Registered tool: {name} (available to: {agents or 'all agents'})")

    def unregister_tool(self, name: str) -> None:
        """Remove a tool from the registry"""
        if name in self.tools:
            del self.tools[name]
            del self.handlers[name]

            # Remove from agent mappings
            for agent in self.agent_tools:
                if name in self.agent_tools[agent]:
                    self.agent_tools[agent].remove(name)

            logger.info(f"[TOOL] Unregistered tool: {name}")

    def get_tool_definitions(self, agent_name: Optional[str] = None) -> List[dict]:
        """
        Return list of OpenAI function definitions for specified agent

        Args:
            agent_name: Name of agent (None = return all tools)

        Returns:
            List of OpenAI function definition dicts
        """
        if agent_name and agent_name in self.agent_tools:
            # Return only tools available to this agent
            tool_names = self.agent_tools[agent_name]
            definitions = [self.tools[name] for name in tool_names if name in self.tools]
        else:
            # Return all tools
            definitions = list(self.tools.values())

        logger.debug(f"[TOOL] Returning {len(definitions)} tool definitions for agent: {agent_name or 'all'}")
        return definitions

    def get_tool_names(self, agent_name: Optional[str] = None) -> List[str]:
        """Get list of tool names available to an agent"""
        if agent_name and agent_name in self.agent_tools:
            return self.agent_tools[agent_name]
        return list(self.tools.keys())

    async def execute_tool(self, name: str, arguments: dict, agent_name: Optional[str] = None) -> dict:
        """
        Execute a tool by name with given arguments

        Args:
            name: Tool name
            arguments: Arguments dict (parsed from OpenAI tool call)
            agent_name: Optional name of agent calling the tool (for analytics)

        Returns:
            Dict with tool execution result

        Raises:
            ValueError: If tool not found
            Exception: If tool execution fails
        """
        if name not in self.handlers:
            logger.error(f"[TOOL] Tool '{name}' not found in registry")
            raise ValueError(f"Tool '{name}' not found")

        handler = self.handlers[name]

        # Increment usage counter
        self.tool_usage_stats[name] = self.tool_usage_stats.get(name, 0) + 1

        try:
            logger.info(f"[TOOL] Executing tool: {name} (agent: {agent_name or 'unknown'}) with arguments: {json.dumps(arguments, ensure_ascii=False)[:200]}")

            # Execute handler (may be sync or async)
            import asyncio
            import inspect

            if inspect.iscoroutinefunction(handler):
                result = await handler(**arguments)
            else:
                result = handler(**arguments)

            logger.info(f"[TOOL] Tool '{name}' executed successfully (total calls: {self.tool_usage_stats[name]})")
            return result

        except Exception as e:
            # Increment error counter
            self.tool_errors[name] = self.tool_errors.get(name, 0) + 1

            logger.error(f"[TOOL] Error executing tool '{name}': {e} (total errors: {self.tool_errors[name]})")
            import traceback
            logger.error(f"[TOOL] Traceback:\n{traceback.format_exc()}")
            raise

    def list_tools(self) -> List[str]:
        """Return list of all registered tool names"""
        return list(self.tools.keys())

    def tool_exists(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self.tools

    def get_tool_info(self, name: str) -> Optional[dict]:
        """Get information about a specific tool"""
        if name not in self.tools:
            return None

        return {
            "name": name,
            "definition": self.tools[name],
            "available_to": [agent for agent, tools in self.agent_tools.items() if name in tools],
            "usage_count": self.tool_usage_stats.get(name, 0),
            "error_count": self.tool_errors.get(name, 0),
            "metadata": self.tool_metadata.get(name, {})
        }

    def get_tool_stats(self) -> dict:
        """Get usage statistics for all tools"""
        return {
            "total_tools": len(self.tools),
            "total_calls": sum(self.tool_usage_stats.values()),
            "total_errors": sum(self.tool_errors.values()),
            "tool_usage": dict(sorted(
                self.tool_usage_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "tool_errors": dict(sorted(
                self.tool_errors.items(),
                key=lambda x: x[1],
                reverse=True
            ))
        }

    def get_agent_tool_stats(self, agent_name: str) -> dict:
        """Get tool statistics for a specific agent"""
        if agent_name not in self.agent_tools:
            return {
                "agent": agent_name,
                "available_tools": [],
                "tool_count": 0
            }

        agent_tools = self.agent_tools[agent_name]
        return {
            "agent": agent_name,
            "available_tools": agent_tools,
            "tool_count": len(agent_tools),
            "usage_by_tool": {
                tool: self.tool_usage_stats.get(tool, 0)
                for tool in agent_tools
            }
        }


# Global registry instance
_global_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance (singleton pattern)"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        logger.info("[TOOL] Created global tool registry")
    return _global_registry


def reset_tool_registry() -> None:
    """Reset the global registry (useful for testing)"""
    global _global_registry
    _global_registry = None
    logger.info("[TOOL] Reset global tool registry")
