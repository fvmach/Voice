# OpenAI Functions Integration

This document describes the OpenAI Functions integration for the Cross-Channel AI Agents platform, specifically for enhanced banking tools handling.

## Overview

The platform now supports OpenAI Functions (also known as "tools" in the API) to provide more intelligent and context-aware tool execution. This replaces the pattern-matching approach with semantic understanding by GPT.

## Architecture

### Components

1. **Enhanced Banking Tools** (`tools/banking_tools_enhanced.py`)
   - Extends the original banking tools with OpenAI Functions support
   - Maintains backward compatibility
   - Provides structured function schemas for the OpenAI API

2. **Enhanced LLM Client** (`llm_client_enhanced.py`)
   - Handles OpenAI Functions execution
   - Streams both conversational and function responses
   - Maintains backward compatibility with the original LLM client

3. **Feature Flag Integration** (in `server.py`)
   - Conditional loading based on `USE_OPENAI_FUNCTIONS` environment variable
   - Seamless fallback to original implementation

## Benefits

### Before (Pattern Matching)
```python
# Over-triggered on keywords
if "saldo" in text.lower():
    return get_balance()  # Triggers even for "Não perguntei o saldo"
```

### After (OpenAI Functions)
```python
# GPT decides when to use functions based on context
"Não consigo acessar minha conta" → help_with_account_access()
"Qual é meu saldo?" → get_account_balance()
```

## Available Functions

### Banking Functions

#### `get_account_balance`
- **Description**: Get current account balance, credit card debt, and loyalty points
- **Parameters**:
  - `account_type`: "checking", "savings", "credit", "all" (default: "all")
  - `include_details`: boolean (default: true)
- **Usage**: Triggered when customer explicitly asks for balance information

#### `help_with_account_access`
- **Description**: Provide help when customer cannot access their account
- **Parameters**:
  - `issue_type`: "login_failed", "password_reset", "locked_account", "app_access", "general_access"
  - `language`: "pt-BR", "en-US", "es-US" (default: "pt-BR")
- **Usage**: Triggered when customer has login or access issues

#### `initiate_transfer`
- **Description**: Help with money transfers, PIX, or sending money
- **Parameters**:
  - `transfer_type`: "pix", "ted", "doc", "internal_transfer"
  - `language`: "pt-BR", "en-US", "es-US" (default: "pt-BR")
- **Usage**: Triggered when customer wants to make transfers

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Enable OpenAI Functions (default: false)
USE_OPENAI_FUNCTIONS=true

# Required for API access
OPENAI_API_KEY=your_openai_api_key_here
```

## Platform Integration

### Existing Features Preserved

✅ **Conversations Manager Integration**: All conversation logging continues to work
✅ **Agent Routing**: Agent switching with #route_to:<Agent> commands
✅ **Language Switching**: Multi-language support (pt-BR, en-US, es-US)  
✅ **Dashboard Broadcasting**: Real-time updates to dashboard
✅ **Transcription Integration**: Twilio Intelligence integration unchanged
✅ **Backward Compatibility**: Original banking tools remain as fallback

### Enhanced Features

🚀 **Intelligent Tool Selection**: GPT decides when to use tools based on context
🚀 **Better Intent Recognition**: Distinguishes between balance inquiry vs access issues
🚀 **Structured Parameters**: Functions receive properly parsed parameters
🚀 **Multi-language Function Responses**: Functions adapt to conversation language
🚀 **Conversation Flow Awareness**: Tools understand conversation history

## Testing

### Direct Function Testing
```bash
cd "Signal SP Session"
python test_openai_functions.py
```

### Manual Testing Scenarios

1. **Balance Inquiry**: "Qual é o meu saldo?" → Should trigger `get_account_balance()`
2. **Access Issue**: "Não consigo acessar minha conta" → Should trigger `help_with_account_access()`
3. **Transfer Request**: "Quero fazer um PIX" → Should trigger `initiate_transfer()`
4. **Mixed Context**: "Você já me falou o saldo, eu só queria ajuda para acessar" → Should NOT trigger balance check

## Deployment Strategy

### Phase 1: Development Testing (Current)
- Feature flag disabled by default (`USE_OPENAI_FUNCTIONS=false`)
- Original implementation continues to work
- Enhanced implementation available for testing

### Phase 2: Gradual Rollout
- Enable feature flag on specific agents or channels
- Monitor for improvements in conversation quality
- Validate function execution accuracy

### Phase 3: Full Migration
- Enable feature flag by default
- Remove original pattern-matching approach
- Optimize function schemas based on usage data

## Monitoring and Logging

### Function Execution Logs
```
[FUNC] Executing function: get_account_balance
[BANK] Banking response generated
```

### Dashboard Integration
- Function calls broadcast as `banking-action` events
- Real-time monitoring of tool usage
- Error tracking and success rates

### Conversation Tracking
- Functions integrate with existing Conversations Manager
- Banking actions logged with metadata
- Full conversation context preserved

## Error Handling

### Graceful Degradation
1. If OpenAI Functions fail → Fall back to conversational response
2. If function execution fails → Provide helpful error message
3. If API timeout → Continue conversation without blocking

### Error Messages
- **Portuguese**: "Desculpe, houve um erro ao processar sua solicitação."
- **English**: "Sorry, there was an error processing your request."
- **Spanish**: "Lo siento, hubo un error al procesar tu solicitud."

## Future Extensions

### Planned Enhancements
- Agent routing functions (replace #route_to: commands)
- Conversation intelligence functions (CSAT, sentiment analysis)
- Multi-step workflows (transfer confirmations, account setup)
- External integrations (CRM, ticketing systems)

### Architecture Extensibility
The function registry pattern allows easy addition of new tools:

```python
# Add new function
registry.register("new_function", {
    "function": execute_new_function,
    "schema": {...}
})
```

## Impact on Other Platform Apps

### Conversations Manager (`server.js`)
- ✅ No changes required
- ✅ Continues to receive conversation logs
- ✅ Banking action events available in API

### PWA Dashboard
- ✅ No changes required  
- ✅ Receives enhanced banking action events
- ✅ Function execution visibility

### Webhook Integrations
- ✅ No changes required
- ✅ Enhanced metadata in conversation logs
- ✅ Function execution context available

## Best Practices

### Function Design
1. **Clear Descriptions**: Make function purposes unambiguous
2. **Proper Parameters**: Use enums and validation for structured input
3. **Language Awareness**: Support multi-language responses
4. **Error Handling**: Provide meaningful error messages

### Conversation Flow
1. **Context Preservation**: Functions should not break conversation flow
2. **Natural Streaming**: Function responses stream naturally like conversation
3. **User Intent**: Respect what the user actually wants (don't over-execute)

### Monitoring
1. **Function Usage**: Track which functions are called and when
2. **Success Rates**: Monitor function execution success vs failure
3. **Conversation Quality**: Measure improvement in user satisfaction

---

This implementation provides a solid foundation for intelligent tool handling while maintaining full backward compatibility and platform integration.
