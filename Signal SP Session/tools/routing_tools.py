"""
Agent Routing Tools for OpenAI Function Calling

This module provides structured routing functions that allow agents to transfer
customers to specialist agents based on their needs.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Valid agent names
VALID_AGENTS = ["Olli", "Sunny", "Max", "Io"]

# Agent information with enhanced metadata
AGENT_INFO = {
    "Olli": {
        "role": "generalist",
        "description": "General banking support and initial customer contact",
        "expertise": ["general_banking", "account_inquiries", "basic_support", "navigation"],
        "can_route_to": ["Sunny", "Max", "Io"],
        "priority": 1  # First contact agent
    },
    "Sunny": {
        "role": "onboarding",
        "description": "New customer onboarding and account setup",
        "expertise": ["onboarding", "kyc", "account_creation", "signup_bonus", "document_verification"],
        "can_route_to": ["Olli", "Max", "Io"],
        "priority": 2  # Specialist
    },
    "Max": {
        "role": "wealth",
        "description": "Wealth management for high-net-worth customers",
        "expertise": ["wealth_management", "private_banking", "high_value_transactions", "estate_planning", "tax_optimization"],
        "can_route_to": ["Olli", "Io"],
        "priority": 3  # High-tier specialist
    },
    "Io": {
        "role": "investments",
        "description": "Investment products and portfolio advice",
        "expertise": ["investments", "portfolio_management", "crypto", "funds", "market_analysis", "financial_planning"],
        "can_route_to": ["Olli", "Max"],
        "priority": 2  # Specialist
    }
}

# Routing keywords for intelligent agent matching
ROUTING_TRIGGERS = {
    "Sunny": {
        "keywords": ["onboarding", "new account", "signup", "register", "kyc", "verification", "bonus",
                     "criar conta", "cadastro", "novo cliente", "verificação", "documentos"],
        "contexts": ["account_creation", "new_customer"]
    },
    "Max": {
        "keywords": ["wealth", "private banking", "high value", "estate", "tax optimization", "premium",
                     "gestão de patrimônio", "private", "alto valor", "investimento grande"],
        "contexts": ["high_net_worth", "large_transaction"],
        "min_balance": 1000000  # R$ 1M threshold for wealth management
    },
    "Io": {
        "keywords": ["investment", "portfolio", "crypto", "fund", "owl growth", "smart savings",
                     "esg select", "robo-advisor", "market", "stocks", "bonds",
                     "investimento", "carteira", "fundo", "ações", "mercado", "criptomoeda"],
        "contexts": ["investment_inquiry", "portfolio_advice"]
    }
}


def route_to_agent(agent_name: str, reason: str, context: Optional[str] = None, current_agent: Optional[str] = None) -> dict:
    """
    Transfer the customer to a specialist agent.

    This function is called when the AI determines that the customer's query
    requires expertise from a different agent.

    Args:
        agent_name: Name of the target agent (Olli, Sunny, Max, or Io)
        reason: Brief explanation of why routing is needed
        context: Optional additional context to pass to the new agent
        current_agent: Optional name of the current agent (for validation)

    Returns:
        Dict with routing result
    """
    logger.info(f"[ROUTING TOOL] route_to_agent called: {agent_name}, reason: {reason}, from: {current_agent}")

    # Validate agent name
    if agent_name not in VALID_AGENTS:
        logger.warning(f"[ROUTING TOOL] Invalid agent name: {agent_name}")
        return {
            "success": False,
            "error": "invalid_agent",
            "message": f"Agent '{agent_name}' is not valid. Valid agents are: {', '.join(VALID_AGENTS)}",
            "valid_agents": VALID_AGENTS
        }

    # Check if routing to self
    if current_agent and agent_name == current_agent:
        logger.warning(f"[ROUTING TOOL] Attempted to route to same agent: {agent_name}")
        return {
            "success": False,
            "error": "same_agent",
            "message": f"Already speaking with {agent_name}. No routing needed.",
            "current_agent": current_agent
        }

    # Validate routing permission (check if current agent can route to target)
    if current_agent and current_agent in AGENT_INFO:
        allowed_targets = AGENT_INFO[current_agent].get("can_route_to", [])
        if agent_name not in allowed_targets:
            logger.warning(f"[ROUTING TOOL] {current_agent} cannot route to {agent_name}")
            return {
                "success": False,
                "error": "routing_not_allowed",
                "message": f"{current_agent} cannot transfer to {agent_name}. Allowed targets: {', '.join(allowed_targets)}",
                "allowed_targets": allowed_targets
            }

    # Get agent info
    agent_info = AGENT_INFO.get(agent_name, {})

    logger.info(f"[ROUTING TOOL] Routing approved: {current_agent or 'system'} -> {agent_name} ({agent_info.get('role')}): {reason}")

    return {
        "success": True,
        "target_agent": agent_name,
        "target_role": agent_info.get("role"),
        "target_expertise": agent_info.get("expertise", []),
        "reason": reason,
        "context": context,
        "from_agent": current_agent,
        "message": f"Transferring to {agent_name} - {agent_info.get('description')}"
    }


def get_specialist_info(agent_name: Optional[str] = None) -> dict:
    """
    Get information about specialist agents.

    This function helps the AI understand which specialists are available
    and what they can help with.

    Args:
        agent_name: Optional specific agent to get info about (returns all if None)

    Returns:
        Dict with agent information
    """
    logger.info(f"[ROUTING TOOL] get_specialist_info called for: {agent_name or 'all'}")

    if agent_name:
        if agent_name not in VALID_AGENTS:
            return {
                "success": False,
                "error": "invalid_agent",
                "message": f"Agent '{agent_name}' not found"
            }

        return {
            "success": True,
            "agent": agent_name,
            "info": AGENT_INFO[agent_name]
        }

    # Return all agents
    return {
        "success": True,
        "agents": AGENT_INFO
    }


def suggest_agent_route(query: str, customer_balance: Optional[float] = None, current_agent: Optional[str] = None) -> dict:
    """
    Suggest the best agent to handle a customer query based on keywords and context.

    This function analyzes the query and returns routing suggestions without performing the route.
    Useful for proactive routing decisions.

    Args:
        query: Customer query or conversation context
        customer_balance: Optional customer account balance for wealth routing
        current_agent: Current agent handling the conversation

    Returns:
        Dict with routing suggestion
    """
    logger.info(f"[ROUTING TOOL] suggest_agent_route called with query: {query[:50]}...")

    query_lower = query.lower()
    scores = {}

    # Score each agent based on keyword matches
    for agent_name, triggers in ROUTING_TRIGGERS.items():
        score = 0

        # Check keyword matches
        for keyword in triggers.get("keywords", []):
            if keyword.lower() in query_lower:
                score += 1

        # Balance-based routing for Max
        if agent_name == "Max" and customer_balance:
            min_balance = triggers.get("min_balance", 0)
            if customer_balance >= min_balance:
                score += 5  # Strong signal for wealth management

        if score > 0:
            scores[agent_name] = score

    # No clear match
    if not scores:
        return {
            "success": True,
            "suggestion": None,
            "confidence": 0.0,
            "message": "No specialist routing suggested - query suitable for generalist",
            "stay_with": current_agent or "Olli"
        }

    # Find best match
    best_agent = max(scores, key=scores.get)
    max_score = scores[best_agent]
    confidence = min(max_score / 5.0, 1.0)  # Normalize to 0-1

    # Check if routing is allowed
    if current_agent and current_agent in AGENT_INFO:
        allowed = AGENT_INFO[current_agent].get("can_route_to", [])
        if best_agent not in allowed:
            return {
                "success": True,
                "suggestion": None,
                "confidence": 0.0,
                "message": f"Best match {best_agent} not accessible from {current_agent}",
                "blocked": True,
                "best_match": best_agent,
                "allowed_targets": allowed
            }

    return {
        "success": True,
        "suggestion": best_agent,
        "confidence": confidence,
        "score": max_score,
        "agent_info": AGENT_INFO[best_agent],
        "all_scores": scores,
        "message": f"Suggested routing to {best_agent} (confidence: {confidence:.2f})"
    }


# OpenAI Function Definitions
ROUTING_FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "route_to_agent",
            "description": """Transfer the customer to a specialist agent when their query requires specific expertise.

Available agents:
- Olli (generalist): General banking questions and initial support. Can route to any specialist.
- Sunny (onboarding): New account setup, KYC verification, document upload, signup bonuses. Handles all new customer flows.
- Max (wealth): Wealth management, private banking for high-net-worth customers (>R$1M balance), high-value transactions, estate planning, tax optimization.
- Io (investments): Investment products (Owl Growth Fund, Smart Savings, ESG Select, crypto), portfolio management, financial planning, market analysis.

IMPORTANT: Only use this when the customer's needs clearly require a different specialist. Don't route unnecessarily.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "enum": ["Olli", "Sunny", "Max", "Io"],
                        "description": "The name of the specialist agent to transfer to"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Clear explanation of why this routing is needed (will be shared with the specialist)"
                    },
                    "context": {
                        "type": "string",
                        "description": "Important context from the conversation to help the specialist (e.g., specific products mentioned, customer concerns, account details)"
                    }
                },
                "required": ["agent_name", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_specialist_info",
            "description": "Get information about available specialist agents and their areas of expertise. Use this when you need to know which specialist can help with a specific topic before routing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "enum": ["Olli", "Sunny", "Max", "Io"],
                        "description": "Optional: Get info about a specific agent. Leave empty to get all agents."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_agent_route",
            "description": """Analyze customer query and suggest the best agent to handle it without actually performing the transfer.

Use this to:
- Check if routing is recommended based on query keywords
- Validate routing logic before committing to a transfer
- Get confidence score for routing decision

Returns suggestion with confidence score. Does not perform the actual routing.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer query or conversation context to analyze"
                    },
                    "customer_balance": {
                        "type": "number",
                        "description": "Optional: Customer account balance (helps determine if wealth management is appropriate)"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def register_routing_tools(registry, agents: Optional[list] = None) -> None:
    """
    Register routing tools with the tool registry.

    Args:
        registry: ToolRegistry instance
        agents: Optional list of agent names that should have access to routing tools
                If None, all agents get access
    """
    from tools.tool_registry import ToolRegistry

    if not isinstance(registry, ToolRegistry):
        raise TypeError("registry must be a ToolRegistry instance")

    # Register route_to_agent
    registry.register_tool(
        name="route_to_agent",
        definition=ROUTING_FUNCTION_DEFINITIONS[0],
        handler=route_to_agent,
        agents=agents  # Available to specified agents or all
    )

    # Register get_specialist_info
    registry.register_tool(
        name="get_specialist_info",
        definition=ROUTING_FUNCTION_DEFINITIONS[1],
        handler=get_specialist_info,
        agents=agents
    )

    # Register suggest_agent_route
    registry.register_tool(
        name="suggest_agent_route",
        definition=ROUTING_FUNCTION_DEFINITIONS[2],
        handler=suggest_agent_route,
        agents=agents
    )

    logger.info(f"[ROUTING] {len(ROUTING_FUNCTION_DEFINITIONS)} routing tools registered for agents: {agents or 'all'}")
