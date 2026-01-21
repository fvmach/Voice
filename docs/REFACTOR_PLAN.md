# Codebase Refactoring Plan
## Cross-Channel AI Agents - Agent Routing & Tool Calling Fixes

**Created:** 2025-12-15
**Status:** Awaiting Approval

---

## Executive Summary

This refactoring plan addresses critical issues in the agent routing and tool calling architecture. The main problems are:

1. **No actual tool calling** - Tools are defined but not registered with OpenAI
2. **Text-based routing** - Unreliable regex pattern matching instead of structured function calls
3. **Monolithic architecture** - 2000+ line single file makes maintenance difficult
4. **Dead code** - Multiple unused implementations causing confusion

**Estimated Impact:** High - Will significantly improve reliability and maintainability
**Risk Level:** Medium - Requires careful migration with backward compatibility

---

## Phase 1: Enable Proper OpenAI Function Calling (HIGH PRIORITY)

### Issue
Currently, tools are loaded from JSON but never registered with OpenAI. The system relies on:
- Text pattern matching for banking operations (BEFORE LLM sees input)
- Text-based `#route_to:` tags for agent routing (AFTER LLM responds)

### Solution
Implement proper OpenAI function calling with structured tool definitions.

### Changes Required

#### 1.1 Create Unified Tool Registry
**New File:** `Signal SP Session/tools/tool_registry.py`

```python
class ToolRegistry:
    """Central registry for all OpenAI function tools"""

    def __init__(self):
        self.tools = {}
        self.handlers = {}

    def register_tool(self, name: str, definition: dict, handler: callable):
        """Register a tool with its OpenAI definition and execution handler"""

    def get_tool_definitions(self) -> list:
        """Return list of OpenAI function definitions"""

    def execute_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool by name with given arguments"""
```

**Purpose:**
- Single source of truth for all tools
- Separates tool definition from execution
- Enables easy addition of new tools

#### 1.2 Migrate Banking Tools to Function Calling
**File:** `Signal SP Session/tools/banking_tools.py`

**Changes:**
1. Add OpenAI function definitions for:
   - `get_account_balance` - Retrieve customer account balance
   - `get_transaction_history` - Get recent transactions
   - `check_transfer_eligibility` - Validate transfer parameters

2. Update banking tool handlers to be callable by tool registry

3. Remove text pattern matching from main handler loop

**Before (current):**
```python
# server.py line 1301-1302
if self.banking_tools and self.customer_phone:
    banking_response = self.banking_tools.process_user_input(text, self.customer_phone, self.language)
```

**After:**
```python
# LLM will call tool via OpenAI function calling
# Handler executes tool and returns result to LLM
# LLM incorporates result into natural language response
```

#### 1.3 Convert Agent Routing to Structured Tools
**Files:**
- `Signal SP Session/tools/route-to-specialist.json` → Convert to function definition
- `Signal SP Session/tools/route-to-generalist.json` → Convert to function definition

**New Function Definitions:**
```json
{
  "type": "function",
  "function": {
    "name": "route_to_specialist",
    "description": "Transfer customer to a specialist agent when their query requires expertise",
    "parameters": {
      "type": "object",
      "properties": {
        "agent_name": {
          "type": "string",
          "enum": ["Sunny", "Max", "Io"],
          "description": "The specialist agent to route to"
        },
        "reason": {
          "type": "string",
          "description": "Brief reason for routing (for context transfer)"
        }
      },
      "required": ["agent_name", "reason"]
    }
  }
}
```

**Benefits:**
- Structured routing with validation
- LLM provides routing reason automatically
- Eliminates regex parsing of response text
- Can route bidirectionally (any agent to any agent)

#### 1.4 Update LLM Client for Tool Support
**File:** `Signal SP Session/server.py` (lines 801-906)

**Changes:**
1. Add `tools` parameter to OpenAI API calls
2. Implement tool call handling loop:
   ```python
   async def get_completion_from_history(self, history, language, agent_name, customer_profile):
       while True:
           response = await openai_call(messages, tools=tool_definitions)

           if response.finish_reason == "tool_calls":
               # Execute tools and add results to messages
               for tool_call in response.tool_calls:
                   result = tool_registry.execute_tool(tool_call.name, tool_call.arguments)
                   messages.append({"role": "tool", "content": result, "tool_call_id": tool_call.id})
               continue
           else:
               # Return final response
               return response.content
   ```
3. Handle streaming with tool calls (more complex - may need to disable streaming during tool use)

**Impact:**
- Enables real function calling
- More reliable than text parsing
- Allows tool chaining (multiple tools in sequence)

---

## Phase 2: Modularize Server Architecture (MEDIUM PRIORITY)

### Issue
Single 2000+ line file is difficult to maintain, test, and debug.

### Solution
Extract components into logical modules.

### Proposed Structure

```
Signal SP Session/
├── server.py                    # Main entry point (200 lines)
├── config/
│   ├── __init__.py
│   ├── settings.py              # Centralized configuration
│   └── environment.py           # Use existing file
├── agents/
│   ├── __init__.py
│   ├── agent.py                 # Agent and AgentRegistry classes
│   ├── registry.py              # Agent registration logic
│   └── context_builder.py      # build_agent_context function
├── llm/
│   ├── __init__.py
│   ├── client.py                # LLMClient class with tool support
│   └── config.py                # ConversationConfig
├── handlers/
│   ├── __init__.py
│   ├── websocket.py             # TwilioWebSocketHandler
│   ├── http.py                  # HTTP routes (dashboard, webhooks)
│   └── intelligence.py          # Intelligence data handling
├── tools/
│   ├── __init__.py
│   ├── tool_registry.py         # NEW: Tool registry
│   ├── banking_tools.py         # Updated with function definitions
│   ├── routing_tools.py         # NEW: Agent routing functions
│   ├── conversations_logger.py  # Existing
│   └── personalization.py       # Existing
└── utils/
    ├── __init__.py
    ├── logging.py               # Colored logging setup
    └── helpers.py               # Utility functions
```

### Migration Steps

#### 2.1 Extract Agent System
1. Move `Agent` and `AgentRegistry` classes to `agents/agent.py`
2. Move `build_agent_context` to `agents/context_builder.py`
3. Move agent registration to `agents/registry.py`
4. Update imports in `server.py`

**Files Modified:**
- `server.py` (remove lines 613-762)
- New: `agents/agent.py`
- New: `agents/context_builder.py`
- New: `agents/registry.py`

#### 2.2 Extract LLM Client
1. Move `LLMClient` class to `llm/client.py`
2. Move `ConversationConfig` to `llm/config.py`
3. Add tool calling support (from Phase 1)

**Files Modified:**
- `server.py` (remove lines 788-906)
- New: `llm/client.py`
- New: `llm/config.py`

#### 2.3 Extract WebSocket Handler
1. Move `TwilioWebSocketHandler` to `handlers/websocket.py`
2. Keep only initialization and route registration in `server.py`

**Files Modified:**
- `server.py` (remove lines 908-1800)
- New: `handlers/websocket.py`

#### 2.4 Extract HTTP Routes
1. Move dashboard routes to `handlers/http.py`
2. Move intelligence webhook to `handlers/intelligence.py`
3. Use aiohttp route decorators for organization

**Files Modified:**
- `server.py` (remove HTTP route definitions)
- New: `handlers/http.py`
- New: `handlers/intelligence.py`

#### 2.5 Consolidate Configuration
1. **Use existing** `config/environment.py` instead of inline env detection
2. Create `config/settings.py` for app-wide settings
3. Remove duplicate environment detection from `server.py` (lines 938-967)

**Files Modified:**
- `server.py` (remove duplicate env detection)
- `config/environment.py` (use as-is)
- New: `config/settings.py`

---

## Phase 3: Clean Up Dead Code (LOW PRIORITY)

### Issue
Multiple unused implementations causing confusion and maintenance burden.

### Solution
Remove or clearly document unused code.

### Actions

#### 3.1 Enhanced Tool System
**Decision Required:** Enable or remove?

**Option A: Remove** (Recommended if not using in next 2 months)
- Delete `llm_client_enhanced.py`
- Delete `banking_tools_enhanced.py`
- Remove `USE_OPENAI_FUNCTIONS` environment variable references

**Option B: Keep for Future**
- Move to `archive/` or `experimental/` directory
- Add README explaining purpose and future plans
- Document why currently disabled

#### 3.2 Empty Directories
- **Remove** `agents/` directory (currently empty)
- Will be recreated in Phase 2 with actual content

#### 3.3 Test Backups
- Move `tests/server_v1_backup.py` to `archive/` or delete
- Not good practice to keep backups in version control (use git)

#### 3.4 Startup Scripts
**Decision Required:** Which startup approach?

Current files:
- `server.py` - Main server (used in production)
- `start_complete_server.py` - Unified launcher
- `Conversations/server.js` - Separate Node.js app

**Recommendation:**
- Keep `server.py` as primary for Signal SP Session
- Keep `Conversations/server.js` separate (different technology)
- Document `start_complete_server.py` purpose or remove if unused

---

## Phase 4: Testing & Validation (CRITICAL)

### Issue
Changes must not break existing functionality.

### Solution
Comprehensive testing strategy.

### Testing Plan

#### 4.1 Unit Tests
Create tests for:
- Tool registry registration and execution
- Agent routing logic
- Banking tool function definitions
- Context building with different agents

**New Directory:** `tests/unit/`

#### 4.2 Integration Tests
Test full flows:
- Customer asks for balance → LLM calls banking tool → Response
- Customer asks wealth question → LLM routes to Max → Context transfer
- Multi-turn conversation with agent switching

**New Directory:** `tests/integration/`

#### 4.3 Regression Tests
Ensure existing features still work:
- WebSocket connection and streaming
- Language detection and switching
- Personalization from Segment
- Intelligence data logging
- Dashboard updates

#### 4.4 Manual Testing Checklist
- [ ] Start server successfully
- [ ] Connect via Twilio Conversation Relay
- [ ] Ask for account balance (banking tool)
- [ ] Request routing to specialist (agent routing)
- [ ] Verify dashboard shows correct agent
- [ ] Check conversation logging
- [ ] Test language switching
- [ ] Verify intelligence data capture

---

## Implementation Strategy

### Approach: Incremental Migration with Feature Flags

**Goal:** Deploy changes progressively without breaking production.

### Environment Variables for Gradual Rollout

```bash
# Phase 1: Tool Calling
USE_FUNCTION_CALLING=false           # Enable structured tool calling
BANKING_TOOLS_MODE=pattern|function  # Choose banking implementation
ROUTING_MODE=text|function           # Choose routing implementation

# Phase 2: Modular Architecture
USE_MODULAR_IMPORTS=false            # Use new module structure

# Phase 3: Cleanup
ENHANCED_TOOLS_AVAILABLE=false       # Keep or remove enhanced tools
```

### Rollout Phases

#### Week 1: Phase 1 - Tool Calling Foundation
1. Create tool registry
2. Implement function definitions for banking + routing
3. Update LLM client with tool support
4. Test with feature flag `USE_FUNCTION_CALLING=false` (disabled)
5. **Deploy to staging** with flag=false (no behavior change)

#### Week 2: Phase 1 - Tool Calling Validation
1. Enable `USE_FUNCTION_CALLING=true` in staging
2. Run comprehensive tests
3. Compare behavior with/without function calling
4. Fix any issues discovered
5. **Deploy to production** with flag=true

#### Week 3: Phase 2 - Modularization Part 1
1. Extract agents system
2. Extract LLM client
3. Test with `USE_MODULAR_IMPORTS=true` in dev
4. **Deploy to staging**

#### Week 4: Phase 2 - Modularization Part 2
1. Extract WebSocket handler
2. Extract HTTP routes
3. Consolidate configuration
4. **Deploy to production**

#### Week 5: Phase 3 - Cleanup
1. Remove/archive dead code
2. Update documentation
3. Final testing
4. **Deploy to production**

---

## Risk Assessment

### High Risk Items
1. **Tool calling loop complexity** - Streaming with tool calls is tricky
   - Mitigation: Disable streaming during tool execution, re-enable after

2. **Agent context loss during routing** - Context may not transfer properly
   - Mitigation: Comprehensive transfer message with conversation summary

3. **Breaking existing integrations** - Twilio Conversation Relay, Intelligence
   - Mitigation: Extensive integration testing before each phase

### Medium Risk Items
1. **Import dependency errors** - Modularization may create circular imports
   - Mitigation: Careful dependency management, use dependency injection

2. **Performance degradation** - Tool calling adds LLM round trips
   - Mitigation: Monitor latency, optimize tool execution, use async properly

3. **Configuration confusion** - Multiple environment variables
   - Mitigation: Clear documentation, validation on startup

### Low Risk Items
1. **Dead code removal** - Already unused
   - Mitigation: Keep in git history for 90 days before permanent removal

---

## Success Criteria

### Phase 1 Success Metrics
- [ ] Banking tools callable via OpenAI function calling
- [ ] Agent routing uses structured function instead of text tags
- [ ] Zero regression in existing functionality
- [ ] Tool execution latency < 500ms

### Phase 2 Success Metrics
- [ ] `server.py` reduced to < 300 lines
- [ ] Each module independently testable
- [ ] No circular import dependencies
- [ ] All tests passing

### Phase 3 Success Metrics
- [ ] No unused code files in main directories
- [ ] Clear documentation of what was removed
- [ ] Codebase reduced by > 500 lines

### Overall Success Metrics
- [ ] Agent routing reliability > 95% (vs current ~80% estimated)
- [ ] Banking tool execution success rate > 99%
- [ ] Code coverage > 70%
- [ ] Developer onboarding time reduced by 50%
- [ ] Zero production incidents during rollout

---

## Documentation Updates Required

### Developer Documentation
1. **Architecture Overview** - New modular structure
2. **Tool Development Guide** - How to add new tools to registry
3. **Agent Development Guide** - How to create new agents
4. **Testing Guide** - How to test changes locally

### Operational Documentation
1. **Deployment Guide** - Updated with new environment variables
2. **Troubleshooting Guide** - Common issues with tool calling
3. **Monitoring Guide** - What metrics to watch

### API Documentation
1. **Tool Definitions** - Document all available tools
2. **Agent Capabilities** - What each agent can do
3. **Integration Guide** - For external systems (Twilio, Segment, etc.)

---

## Questions for Discussion

1. **Tool Calling Strategy:**
   - Should we enable streaming during tool calls or collect full response?
   - How many tool rounds should we allow before forcing a response?

2. **Agent Routing:**
   - Should all agents be able to route to any other agent?
   - Or maintain current hub-and-spoke model (Olli as hub)?

3. **Enhanced Tools Decision:**
   - Remove completely or keep for future?
   - If keeping, what's the plan to actually use them?

4. **Configuration Management:**
   - Use existing `config/environment.py` or create new system?
   - How to handle multi-cloud deployments?

5. **Backward Compatibility:**
   - Support old text-based routing temporarily?
   - How long to maintain dual-mode support?

6. **Testing Coverage:**
   - What's acceptable code coverage target?
   - Should we require tests for all new tools/agents?

---

## Next Steps

1. **Review this plan** - Stakeholder approval required
2. **Answer questions** - Resolve open decisions
3. **Create feature branch** - `refactor/tool-calling-and-modularization`
4. **Implement Phase 1** - Tool calling foundation
5. **Iterate based on feedback**

---

## Appendix: Current Issues Log

### Issues Found During Analysis

1. **Agent routing fails silently** - [server.py:1406](../Signal SP Session/server.py#L1406)
   - Warning logged but customer gets no feedback
   - Should inform customer or retry with Olli

2. **Banking API hardcoded** - [banking_tools.py:17](../Signal SP Session/tools/banking_tools.py#L17)
   - No environment configuration
   - Cannot change backend without code modification

3. **Knowledge file empty** - `knowledge/high-value-customer.csv`
   - Loaded but contains no data
   - Max agent has incomplete knowledge

4. **Intelligence data files grow unbounded** - [server.py:302-330](../Signal SP Session/server.py#L302-L330)
   - No rotation or cleanup policy
   - Could cause disk space issues in production

5. **Model name possibly invalid** - [server.py:793](../Signal SP Session/server.py#L793)
   - `gpt-5-mini` - Should verify this model exists
   - OpenAI models: gpt-4o, gpt-4o-mini, gpt-4-turbo, etc.

6. **Duplicate environment detection** - Two implementations
   - [config/environment.py](../config/environment.py) - Comprehensive
   - [server.py:938-967](../Signal SP Session/server.py#L938-L967) - Simplified
   - Should use only one

7. **Missing error handling** - [personalization.py:16-17](../Signal SP Session/tools/personalization.py#L16-L17)
   - Direct environment access without fallback
   - Runtime error if credentials missing

8. **Empty agents directory** - [agents/](../Signal SP Session/agents/)
   - Directory exists but unused
   - Suggests incomplete refactoring attempt

### Priority Order for Fixes

1. **P0 (Critical):** Enable proper tool calling - Fixes core reliability
2. **P1 (High):** Fix agent routing failures - Improve customer experience
3. **P1 (High):** Fix model name validation - Prevent API errors
4. **P2 (Medium):** Modularize architecture - Long-term maintainability
5. **P2 (Medium):** Add banking API configuration - Deployment flexibility
6. **P3 (Low):** Clean up dead code - Code quality
7. **P3 (Low):** Fix intelligence data rotation - Prevent future issues

---

**Document Version:** 1.0
**Last Updated:** 2025-12-15
**Author:** Claude Code Analysis
**Status:** 🟡 Awaiting Approval
