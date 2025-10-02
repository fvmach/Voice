# llm_client_enhanced.py
# Enhanced LLM client with OpenAI Functions support
# Maintains backward compatibility with existing LLM client

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from openai import OpenAI

from tools.banking_tools_enhanced import get_enhanced_banking_tools, FunctionResult

logger = logging.getLogger(__name__)

@dataclass
class ConversationConfig:
    sentence_end_patterns = ['.', '!', '?', '\n']
    partial_timeout = 1.5
    max_buffer_size = 1000
    openai_model = os.getenv('OPENAI_MODEL')  # Must be set in environment variables

class EnhancedLLMClient:
    """Enhanced LLM client with OpenAI Functions support"""
    
    def __init__(self, config: ConversationConfig):
        self.config = config
        
        # Add debugging for OpenAI client creation
        logger.info(f"[DEBUG] About to create OpenAI() client in EnhancedLLMClient")
        
        try:
            self.client = OpenAI()
            logger.info(f"[DEBUG] OpenAI() client created successfully in EnhancedLLMClient")
        except Exception as e:
            logger.error(f"[ERR] Failed to create OpenAI() client in EnhancedLLMClient: {e}")
            import traceback
            logger.error(f"[ERR] Enhanced OpenAI client traceback:\n{traceback.format_exc()}")
            raise
        
        logger.info(f"[DEBUG] About to get enhanced banking tools")
        self.banking_tools = get_enhanced_banking_tools()
        logger.info(f"[DEBUG] About to build function schemas")
        self.function_schemas = self._build_function_schemas()
        logger.info(f"[DEBUG] EnhancedLLMClient initialization complete")
    
    def _build_function_schemas(self) -> List[Dict]:
        """Build function schemas for the current agent context"""
        # Start with banking functions
        schemas = self.banking_tools.get_function_schemas()
        
        # Add agent routing functions (to be implemented later)
        # schemas.extend(self._get_agent_routing_schemas())
        
        return schemas
    
    async def initialize(self):
        """Initialize the client"""
        pass
    
    async def close(self):
        """Close the client"""
        pass
    
    async def get_completion_with_functions(
        self, 
        text: str, 
        language: str, 
        agent_name: str = "Olli", 
        customer_profile: dict = None,
        customer_phone: str = None
    ) -> AsyncGenerator[str, None]:
        """Get completion with OpenAI Functions support"""
        
        # Build agent context (reusing existing function)
        from server import build_agent_context
        context = build_agent_context(agent_name, customer_profile)
        
        messages = [
            {
                "role": "system",
                "content": (
                    f"{context}\n\n"
                    f"You are talking to a customer through a phone call. "
                    f"Speak in {language}. But respect user's request if they ask to switch language.\n"
                    f"Respond conversationally. Avoid special characters or emojis. Optimize responses for speech to text.\n"
                    f"IMPORTANT: Use the available functions when appropriate. For banking requests, use banking functions. "
                    f"For account access issues, use help functions. Don't provide banking information without using the proper function.\n"
                    f"If you need to route to a specialist agent (Sunny, Max, or Io), "
                    f"provide a helpful response first, then add #route_to:<AgentName> at the very end. "
                    f"The routing command #route_to:<AgentName> will NOT be spoken to the customer."
                )
            },
            {"role": "user", "content": text}
        ]
        
        # Prepare function call
        def sync_stream():
            return self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                tools=self.function_schemas if self.function_schemas else None,
                tool_choice="auto" if self.function_schemas else None,
                stream=True
            )
        
        try:
            stream = await asyncio.to_thread(sync_stream)
            
            # Collect the response and any function calls
            response_content = []
            function_calls = []
            current_tool_call = None
            
            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Handle regular content
                if delta.content:
                    response_content.append(delta.content)
                    yield delta.content
                
                # Handle function calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        if tool_call.index is not None:
                            # Start of new tool call or continuation
                            if len(function_calls) <= tool_call.index:
                                function_calls.extend([None] * (tool_call.index + 1 - len(function_calls)))
                            
                            if function_calls[tool_call.index] is None:
                                function_calls[tool_call.index] = {
                                    'id': tool_call.id or '',
                                    'function': {'name': '', 'arguments': ''}
                                }
                            
                            current_tool_call = function_calls[tool_call.index]
                            
                            if tool_call.function:
                                if tool_call.function.name:
                                    current_tool_call['function']['name'] += tool_call.function.name
                                if tool_call.function.arguments:
                                    current_tool_call['function']['arguments'] += tool_call.function.arguments
            
            # Execute function calls if any
            if function_calls:
                yield "\n\n"  # Add some space before function execution
                
                for tool_call in function_calls:
                    if tool_call and tool_call['function']['name']:
                        logger.info(f"[FUNC] Executing function: {tool_call['function']['name']}")
                        
                        # Execute the function
                        if tool_call['function']['name'] in ['get_account_balance', 'help_with_account_access', 'initiate_transfer']:
                            # Add customer_phone to function arguments for banking functions
                            try:
                                args = json.loads(tool_call['function']['arguments']) if tool_call['function']['arguments'] else {}
                                if customer_phone and 'language' not in args:
                                    args['language'] = language
                                if customer_phone and 'customer_phone' not in args:
                                    args['customer_phone'] = customer_phone
                                
                                result = self.banking_tools.execute_function(
                                    tool_call['function']['name'], 
                                    json.dumps(args),
                                    tool_call['id']
                                )
                                
                                if result.success:
                                    # Stream the function result
                                    words = result.content.split()
                                    for i, word in enumerate(words):
                                        if i == 0:
                                            yield word
                                        else:
                                            yield f" {word}"
                                        await asyncio.sleep(0.02)  # Small delay for natural streaming
                                else:
                                    logger.error(f"[FUNC] Function execution failed: {result.content}")
                                    yield f"Desculpe, houve um erro ao processar sua solicitação."
                                    
                            except Exception as e:
                                logger.error(f"[FUNC] Error executing function {tool_call['function']['name']}: {e}")
                                yield "Desculpe, houve um erro ao processar sua solicitação."
                        else:
                            logger.warning(f"[FUNC] Unknown function: {tool_call['function']['name']}")
                            yield "Desculpe, não consegui processar essa função."
        
        except Exception as e:
            logger.error(f"[ERR] Enhanced LLM streaming error: {e}")
            yield "Desculpe, ocorreu um erro."
    
    async def get_completion_from_history_with_functions(
        self, 
        history: list, 
        language: str, 
        agent_name: str = "Olli", 
        customer_profile: dict = None,
        customer_phone: str = None
    ) -> AsyncGenerator[str, None]:
        """Get completion from history with OpenAI Functions support"""
        
        # Build agent context (reusing existing function)
        from server import build_agent_context
        context = build_agent_context(agent_name, customer_profile)
        
        messages = [
            {"role": "system", "content": (
                f"{context}\n\n"
                f"You are talking to a customer through a phone call. "
                f"Speak in {language}, but you can switch languages if needed to English and Latin American Spanish."
                f"Respond conversationally. Avoid special characters or emojis. Optimize responses for speech to text.\n"
                f"IMPORTANT: Use the available functions when appropriate. For banking requests, use banking functions. "
                f"For account access issues, use help functions. Don't provide banking information without using the proper function.\n"
                f"If you need to route to a specialist agent (Sunny, Max, or Io), "
                f"provide a helpful response first, then add #route_to:<AgentName> at the very end. "
                f"The routing command #route_to:<AgentName> will NOT be spoken to the customer."
            )}
        ] + history
        
        # Prepare function call
        def sync_stream():
            return self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                tools=self.function_schemas if self.function_schemas else None,
                tool_choice="auto" if self.function_schemas else None,
                stream=True
            )
        
        try:
            stream = await asyncio.to_thread(sync_stream)
            
            # Collect the response and any function calls
            response_content = []
            function_calls = []
            
            for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta
                
                # Handle regular content
                if delta.content:
                    response_content.append(delta.content)
                    yield delta.content
                
                # Handle function calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        if tool_call.index is not None:
                            # Start of new tool call or continuation
                            if len(function_calls) <= tool_call.index:
                                function_calls.extend([None] * (tool_call.index + 1 - len(function_calls)))
                            
                            if function_calls[tool_call.index] is None:
                                function_calls[tool_call.index] = {
                                    'id': tool_call.id or '',
                                    'function': {'name': '', 'arguments': ''}
                                }
                            
                            current_tool_call = function_calls[tool_call.index]
                            
                            if tool_call.function:
                                if tool_call.function.name:
                                    current_tool_call['function']['name'] += tool_call.function.name
                                if tool_call.function.arguments:
                                    current_tool_call['function']['arguments'] += tool_call.function.arguments
            
            # Execute function calls if any
            if function_calls:
                for tool_call in function_calls:
                    if tool_call and tool_call['function']['name']:
                        logger.info(f"[FUNC] Executing function: {tool_call['function']['name']}")
                        
                        # Execute the function
                        if tool_call['function']['name'] in ['get_account_balance', 'help_with_account_access', 'initiate_transfer']:
                            try:
                                args = json.loads(tool_call['function']['arguments']) if tool_call['function']['arguments'] else {}
                                if customer_phone and 'language' not in args:
                                    args['language'] = language
                                if customer_phone and 'customer_phone' not in args:
                                    args['customer_phone'] = customer_phone
                                
                                result = self.banking_tools.execute_function(
                                    tool_call['function']['name'], 
                                    json.dumps(args),
                                    tool_call['id']
                                )
                                
                                if result.success:
                                    # Stream the function result
                                    words = result.content.split()
                                    for i, word in enumerate(words):
                                        if i == 0:
                                            yield word
                                        else:
                                            yield f" {word}"
                                        await asyncio.sleep(0.02)  # Small delay for natural streaming
                                else:
                                    logger.error(f"[FUNC] Function execution failed: {result.content}")
                                    yield f"Desculpe, houve um erro ao processar sua solicitação."
                                    
                            except Exception as e:
                                logger.error(f"[FUNC] Error executing function {tool_call['function']['name']}: {e}")
                                yield "Desculpe, houve um erro ao processar sua solicitação."
                        else:
                            logger.warning(f"[FUNC] Unknown function: {tool_call['function']['name']}")
                            yield "Desculpe, não consegui processar essa função."
        
        except Exception as e:
            logger.error(f"[ERR] Enhanced LLM streaming error: {e}")
            yield "Desculpe, ocorreu um erro."
    
    # Backward compatibility methods
    async def get_completion(self, text: str, language: str, agent_name: str = "Olli", customer_profile: dict = None):
        """Backward compatible completion method"""
        async for token in self.get_completion_with_functions(text, language, agent_name, customer_profile):
            yield token
    
    async def get_completion_from_history(self, history: list, language: str, agent_name: str = "Olli", customer_profile: dict = None):
        """Backward compatible completion from history method"""
        async for token in self.get_completion_from_history_with_functions(history, language, agent_name, customer_profile):
            yield token
