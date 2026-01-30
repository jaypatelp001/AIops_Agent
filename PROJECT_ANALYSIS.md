# 🔍 AIOps Project - Deep Analysis

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Agents Deep Dive](#agents-deep-dive)
4. [Tools Deep Dive](#tools-deep-dive)
5. [Memory System](#memory-system)
6. [Communication Flow](#communication-flow)
7. [Complete Workflow](#complete-workflow)
8. [Technical Stack](#technical-stack)
9. [Key Design Patterns](#key-design-patterns)
10. [Example Execution](#example-execution)

---

## 🎯 Project Overview

### What is AIOps?
**AIOps** is an **Autonomous AI-Powered Bug Fixing System** that automatically detects, analyzes, fixes, and validates bugs in code without human intervention.

### Core Problem It Solves
Traditional debugging requires:
- ✅ Manual error trace analysis
- ✅ Code investigation
- ✅ Writing fixes
- ✅ Testing fixes

AIOps **automates all of this** using specialized AI agents.

### Key Characteristics
- **Autonomous**: Runs end-to-end without human intervention
- **Multi-Agent**: Uses 4 specialized AI agents working together
- **Memory-Based**: Agents communicate through shared memory
- **Semantic Search**: Uses embeddings for intelligent context retrieval
- **Modular**: Easy to extend with new agents/tools
- **Transparent**: All decisions logged for inspection

---

## 🏗️ Architecture & Design

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER INPUT                       │
│           "Fix the bug in codebase folder"          │
└─────────────────────────────┬───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────┐
│                  ROOT AGENT                         │
│              (Orchestrator)                         │
│  - Manages workflow                                 │
│  - Calls sub-agents                                 │
│  - Makes decisions                                  │
└─────┬───────────┬────────────┬──────────────────────┘
      │           │            │
      ▼           ▼            ▼
┌──────────┐ ┌────────┐ ┌───────────┐
│ ANALYZER │ │ FIXER  │ │ VALIDATOR │
│  AGENT   │ │ AGENT  │ │  AGENT    │
└────┬─────┘ └───┬────┘ └─────┬─────┘
     │           │            │
     └───────────┼────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  SHARED MEMORY  │
        │  (memory.json)  │
        │  - Analysis     │
        │  - Fixes        │
        │  - Validations  │
        └─────────────────┘
                 ▲
                 │
        ┌────────┴────────┐
        │   FILE TOOLS    │
        │  - read_file    │
        │  - write_file   │
        │  - find_trace   │
        │  - find_error   │
        └─────────────────┘
```

### Component Breakdown

#### 1. **Agents Layer** (4 Agents)
- Root Agent (Orchestrator)
- Analyzer Agent (Detective)
- Fixer Agent (Surgeon)
- Validator Agent (QA)

#### 2. **Tools Layer** (10 Tools)
- **File Discovery**: find_trace_file, find_error_source_file, list_codebase_files, check_if_error_exists
- **File Operations**: read_file, write_file, list_files
- **Memory Operations**: save_memory, get_all_memories, search_memory

#### 3. **Memory Layer**
- **Session Memory**: Stores current run's findings (memory.json)
- **Agent Memory**: Long-term learning (placeholder - agent_memory.json)
- **Callback System**: Auto-injected contextual memories

#### 4. **Execution Layer**
- InMemoryRunner: Manages agent execution
- Session Service: Handles user sessions
- Event Streaming: Real-time output

---

## 🤖 Agents Deep Dive

### 1. Root Agent (Orchestrator)

**Role**: Main conductor of the entire workflow

**Model**: `gemini-2.5-flash` with thinking capabilities

**Key Responsibilities**:
```
1. Receive user's bug report
2. Orchestrate the workflow:
   ├─ Call Analyzer Agent
   ├─ Check analysis results
   ├─ If bug found → Call Fixer Agent
   ├─ Call Validator Agent
   └─ Report final status
3. Handle retries if validation fails
4. Make high-level decisions
```

**Tools Available**:
- AgentTool(analyzer_agent) - Can invoke analyzer
- AgentTool(fixer_agent) - Can invoke fixer
- AgentTool(validator_agent) - Can invoke validator
- save_memory() - Save orchestration decisions
- get_all_memories() - Review all agent findings

**Thinking Configuration**:
```python
thinking_config=types.ThinkingConfig(
    include_thoughts=True,
    thinking_budget=512,  # 512 tokens for reasoning
)
```

**Special Features**:
- ✅ Only agent that can call other agents
- ✅ Has reasoning/thinking capabilities
- ✅ No direct file access (delegates to sub-agents)

**Decision Logic**:
```
IF analyzer says "Code already fixed":
    → STOP, report to user
ELSE IF analyzer finds bug:
    → Call fixer
    → Call validator
    IF validator FAILS:
        → Retry with fixer
    ELSE:
        → Success, report results
```

---

### 2. Analyzer Agent (Detective)

**Role**: Forensic investigator that diagnoses bugs

**Model**: `gemini-2.5-flash`

**Key Responsibilities**:
```
1. Locate trace.json in codebase
2. Find the error source file
3. Check if error still exists in current code
4. If already fixed → Report and stop
5. If not fixed → Analyze root cause:
   ├─ Read error trace
   ├─ Read faulty code
   ├─ Identify exact line and error type
   └─ Determine why it failed
6. Save comprehensive analysis to memory
```

**Tools Available**:
- **check_if_error_exists()** - Verify error still present
- **find_error_source_file()** - Auto-locate error file
- **find_trace_file()** - Get trace.json path
- **list_codebase_files()** - Explore project structure
- **read_file()** - Read any file
- **list_files()** - List directory contents
- **save_memory()** - Store analysis
- **get_all_memories()** - Review context

**Analysis Output Example**:
```
Root Cause Analysis:
- Error Type: TypeError
- File: codebase/app.py
- Line: 6
- Function: calculate_sum
- Problem: Missing argument 'b' in function call
- Expected: calculate_sum(20, 30)
- Actual: calculate_sum(20,)
```

**Smart Features**:
- ✅ Checks if code already fixed before wasting API calls
- ✅ Automatically finds files (no manual paths needed)
- ✅ Saves structured findings to memory

---

### 3. Fixer Agent (Surgeon)

**Role**: Code surgeon that applies fixes

**Model**: `gemini-2.5-flash`

**Key Responsibilities**:
```
1. Retrieve analysis from memory (auto-injected)
2. Locate the faulty source file
3. Read current code
4. Apply fix based on analysis:
   ├─ Understand root cause
   ├─ Generate corrected code
   └─ Ensure fix is minimal and targeted
5. Write fixed code back to file
6. Document the fix in memory
```

**Tools Available**:
- **find_error_source_file()** - Locate file to fix
- **find_trace_file()** - Get trace info if needed
- **read_file()** - Read faulty code
- **write_file()** - Write fixed code ⚠️ (Only agent with write access!)
- **save_memory()** - Document fix
- **get_all_memories()** - Get analysis

**Fix Documentation Example**:
```
Fixed TypeError in codebase/app.py on line 6.
The calculate_sum function was called with only one argument,
but it expects two. Added second argument (30) to function call.
```

**Important Notes**:
- ✅ **ONLY** agent with write_file() access (safety!)
- ✅ Receives analyzer's findings automatically via callback
- ✅ Makes minimal, targeted changes

---

### 4. Validator Agent (QA Checker)

**Role**: Quality assurance that verifies fixes

**Model**: `gemini-2.5-flash`

**Key Responsibilities**:
```
1. Locate and read fixed code
2. Review original trace.json
3. Compare fix against root cause
4. Verify fix addresses the issue
5. Check for introduced bugs
6. Save validation report to memory
```

**Tools Available**:
- **find_error_source_file()** - Locate fixed file
- **find_trace_file()** - Get original error
- **read_file()** - Read fixed code
- **save_memory()** - Save validation
- **get_all_memories()** - Review analysis & fix

**Validation Output Example**:
```
Validation: SUCCESS
The fix addresses the TypeError by providing all required
arguments to calculate_sum function. Function also improved
with type conversions int(a) + int(b).
```

**Validation Criteria**:
- ✅ Does fix address root cause?
- ✅ Is the fix technically correct?
- ✅ Are there any introduced errors?
- ✅ Is the fix minimal and safe?

**No Execution**:
Currently does **static analysis only** (no code execution for safety)

---

## 🛠️ Tools Deep Dive

### File Discovery Tools

#### 1. **find_trace_file()**

**Purpose**: Auto-locate trace.json in codebase

**How It Works**:
```python
1. Set base_directory = "codebase"
2. Use Path.rglob("trace.json") to search recursively
3. Return first match or list all if multiple found
```

**Output**:
```
✅ [FOUND] trace.json at: codebase/trace.json
```

**Used By**: Analyzer, Fixer, Validator

---

#### 2. **find_error_source_file()**

**Purpose**: Identify which source file caused error

**How It Works**:
```python
1. Call find_trace_file() to get trace.json path
2. Read and parse trace.json (JSON)
3. Extract file path from traceback line:
   - Parse: 'File "/path/to/file.py", line X'
   - Extract filename: app.py
4. Search codebase folder for that filename
5. Return detailed error analysis
```

**Output**:
```
✅ [FOUND] Error Analysis:
- Trace file: codebase/trace.json
- Error: TypeError: calculate_sum() missing 1 required positional argument: 'b'
- Source file: codebase/app.py
- Original path in trace: /Users/jay.patel/Desktop/aiops/app.py

Use read_file('codebase/app.py') to read the faulty code.
```

**Used By**: Analyzer, Fixer, Validator

---

#### 3. **check_if_error_exists()**

**Purpose**: Verify if error from trace still exists in current code

**How It Works**:
```python
1. Get trace.json and parse error details
2. Extract error type, line number
3. Locate source file
4. Read current code
5. Provide recommendation for analyzer
```

**Output**:
```
📋 [CHECK] Error Verification Results:
- Trace file: codebase/trace.json
- Original error: TypeError: calculate_sum() missing 1 required positional argument: 'b'
- Source file: codebase/app.py
- Error line: 6

Current Code Analysis:
⚠️ Type error detected in trace...

💡 Recommendation: Analyzer should compare trace error with current code
   to confirm if fix is needed.
   Read file 'codebase/app.py' and check if error condition still exists.
```

**Used By**: Analyzer (to avoid fixing already-fixed code)

**Why Important**: Saves API calls and prevents modifying working code

---

#### 4. **list_codebase_files()**

**Purpose**: Show all files in project

**How It Works**:
```python
1. Set base_directory = "codebase"
2. Recursively walk directory tree
3. Collect all file paths
4. Return sorted list
```

**Output**:
```
Files in codebase:
app.py
trace.json
```

**Used By**: Analyzer (for project structure understanding)

---

### File Operation Tools

#### 5. **read_file(file_path)**

**Purpose**: Read content from any file

**Parameters**: `file_path` - Path to file

**Returns**: File content as string

**Example**:
```python
read_file("codebase/app.py")
→ "def calculate_sum(a, b):\n    return int(a) + int(b)\n..."
```

**Used By**: All agents

---

#### 6. **write_file(file_path, content)**

**Purpose**: Write content to file (fixes!)

**Parameters**: 
- `file_path` - Where to write
- `content` - What to write

**Returns**: Success message

**Example**:
```python
write_file("codebase/app.py", fixed_code)
→ "Successfully wrote to codebase/app.py"
```

⚠️ **Security**: Only Fixer Agent has access!

**Used By**: Fixer Agent only

---

#### 7. **list_files(directory)**

**Purpose**: List files in specific directory

**Parameters**: `directory` - Path to list

**Returns**: Newline-separated file list

**Used By**: Analyzer

---

### Memory Tools

#### 8. **save_memory(text, metadata)**

**Purpose**: Save information to shared memory

**Parameters**:
- `text` - Main content to save
- `metadata` - Optional structured data

**How It Works**:
```python
1. Create memory entry with:
   - Unique ID
   - Text content
   - Metadata
   - Timestamp
2. Add to ADK InMemoryMemoryService (for vector search)
3. Append to local cache
4. Persist to memory.json
```

**Example**:
```python
await save_memory(
    text="Root Cause: TypeError on line 6 - missing argument 'b'",
    metadata={"error_type": "TypeError", "line": 6}
)
```

**Output**:
```
💾 [MEMORY] Persisted to memory.json
```

**Used By**: All agents

---

#### 9. **get_all_memories()**

**Purpose**: Retrieve all stored memories

**Returns**: All memory entries as text

**Example Output**:
```
- Root Cause Analysis: TypeError in calculate_sum function...
- Fixed TypeError in codebase/app.py on line 6...
- The fix addresses the TypeError by providing all required arguments...
```

**Used By**: All agents (manual context retrieval)

---

#### 10. **search_memory(query, limit)**

**Purpose**: Semantic search for relevant memories

**Parameters**:
- `query` - What to search for
- `limit` - Max results

**How It Works**:
```python
1. Convert query to embedding (vector)
2. Search InMemoryMemoryService using ADK
3. Find semantically similar memories
4. Return top N results
```

**Example**:
```python
search_memory("How to fix the bug", limit=5)
→ Returns memories about bug analysis and fixes
```

**Used By**: Callback system (automatic, before every AI call)

**Magic**: Uses **embeddings** - finds relevant info even without exact keyword matches!

---

## 🧠 Memory System

### Two-Layer Memory Architecture

#### Layer 1: Session Memory (memory.json)

**Purpose**: Stores current bug-fixing session

**Structure**:
```json
{
  "id": "unique-uuid",
  "text": "Human-readable memory content",
  "metadata": {
    "error_type": "TypeError",
    "line": 6,
    "file": "codebase/app.py"
  },
  "timestamp": "7590.277076916"
}
```

**Lifecycle**:
- Created when agents save findings
- Persists throughout entire session
- Can be cleared between bug reports
- Stored in `memory.json`

**Contents**:
- ✅ Root cause analysis
- ✅ Fix details
- ✅ Validation results
- ✅ Agent decisions

**Storage Technology**:
- JSON file for persistence
- In-memory cache for fast access
- Vector embeddings for semantic search

---

#### Layer 2: Agent Memory (agent_memory.json)

**Purpose**: Long-term learning (future feature)

**Status**: Placeholder (not actively used)

**Potential Uses**:
- Remember common bug patterns
- Store successful fix strategies
- Learn from past mistakes
- Build expertise over time

---

### Memory Callback System

**What It Does**: Automatically injects relevant memories before **every** AI call

**How It Works**:

```
1. User sends message to agent
   ↓
2. BEFORE AI processes it:
   ├─ Callback intercepts request
   ├─ Extracts user's message
   ├─ Calls search_memory(message, limit=50)
   ├─ Finds top 50 relevant memories
   └─ Injects into system instruction
   ↓
3. AI receives enhanced context
   ↓
4. AI makes informed decision
```

**Implementation**:
```python
async def memory_search_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    # Extract user message
    last_user_message = llm_request.contents[-1].parts[0].text
    
    # Search memory
    memory_result = await search_memory(
        query=last_user_message,
        limit=50
    )
    
    # Inject into system instruction
    memory_prefix = f"""
    RELEVANT MEMORIES FROM PAST CONVERSATIONS:
    {memory_result['memories']}
    
    IMPORTANT: Apply constraints from memories above.
    """
    
    llm_request.config.system_instruction = (
        memory_prefix + original_instruction
    )
    
    return None  # Continue with modified request
```

**Benefits**:
- ✅ Agents automatically know what others did
- ✅ No manual context passing needed
- ✅ Semantic search finds relevant info (not just keywords)
- ✅ Reduces redundant work

**Example**:

When Fixer Agent starts:
```
User message: "Fix the bug based on analysis"
                      ↓
Callback searches memory for "Fix the bug based on analysis"
                      ↓
Finds Analyzer's memory: "Root Cause: TypeError on line 6..."
                      ↓
Injects into Fixer's context
                      ↓
Fixer now knows the analysis without explicit passing
```

**Attached To**: All 4 agents via `before_model_callback=memory_search_callback`

---

## 🔄 Communication Flow

### How Agents Communicate

**Key Principle**: Agents do **NOT** directly call each other!

**Communication Method**: Shared Memory

### Communication Patterns

#### Pattern 1: Sequential Agent Communication

```
Analyzer Agent
    ↓ (saves to memory)
[MEMORY: "Root cause: TypeError on line 6"]
    ↓ (Root calls Fixer)
Fixer Agent
    ↓ (callback auto-injects memory)
Fixer receives: "Root cause: TypeError on line 6"
    ↓ (applies fix, saves to memory)
[MEMORY: "Fixed: Added argument to line 6"]
    ↓ (Root calls Validator)
Validator Agent
    ↓ (callback auto-injects both memories)
Validator receives: 
    - "Root cause: TypeError on line 6"
    - "Fixed: Added argument to line 6"
```

#### Pattern 2: Memory-Driven Workflow

```
┌─────────────┐
│  Analyzer   │
│  analyzes   │
│   + saves   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  memory.json    │
│  + embeddings   │
└──────┬──────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────┐      ┌────────────┐
│  Fixer   │      │ Validator  │
│ (reads)  │      │  (reads)   │
└──────────┘      └────────────┘
```

### Agent Coordination Rules

1. **Only Root Agent can invoke other agents**
   - Uses AgentTool wrapper
   - Manages execution order

2. **Sub-agents communicate via memory**
   - save_memory() to write
   - get_all_memories() to read manually
   - Callback injects automatically

3. **No circular dependencies**
   - Clear hierarchy: Root → Sub-agents
   - Sub-agents never call each other

4. **Memory is the single source of truth**
   - All findings stored in memory
   - Persistent across agent calls
   - Inspectable for debugging

---

## 🎬 Complete Workflow

### End-to-End Bug Fixing Process

```
┌─────────────────────────────────────────┐
│  STEP 1: User Starts System             │
│  $ python main.py                       │
│  Query: "Fix bug in codebase folder"    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STEP 2: Root Agent Receives Task       │
│  - Understands goal                     │
│  - Plans workflow                       │
│  - Prepares to call sub-agents          │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STEP 3: Root Calls Analyzer Agent      │
│  Analyzer:                              │
│  ├─ check_if_error_exists()             │
│  ├─ find_trace_file()                   │
│  │  → "codebase/trace.json"             │
│  ├─ find_error_source_file()            │
│  │  → "codebase/app.py"                 │
│  ├─ read_file("trace.json")             │
│  ├─ read_file("app.py")                 │
│  ├─ Analyzes: TypeError on line 6       │
│  └─ save_memory("Root cause: ...")      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STEP 4: Root Checks Analysis           │
│  IF "Code already fixed":               │
│     → STOP and report                   │
│  ELSE:                                  │
│     → Continue to fixer                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STEP 5: Root Calls Fixer Agent         │
│  Fixer:                                 │
│  ├─ Callback auto-injects analysis      │
│  ├─ find_error_source_file()            │
│  ├─ read_file("app.py")                 │
│  ├─ Generates fixed code                │
│  ├─ write_file("app.py", fixed_code)    │
│  └─ save_memory("Fixed: ...")           │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STEP 6: Root Calls Validator Agent     │
│  Validator:                             │
│  ├─ Callback injects analysis + fix     │
│  ├─ read_file("trace.json")             │
│  ├─ read_file("app.py") # fixed         │
│  ├─ Compares fix vs original error      │
│  ├─ Validates correctness               │
│  └─ save_memory("Validation: SUCCESS")  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  STEP 7: Root Evaluates Results         │
│  IF validation PASSED:                  │
│     → Report success to user            │
│  ELSE:                                  │
│     → Retry with Fixer                  │
└─────────────────────────────────────────┘
```

### State Transitions

```
[INITIAL] → User Query
    ↓
[ANALYZING] → Analyzer working
    ↓
[ANALYZED] → Analysis complete, saved to memory
    ↓
[CHECKING] → Root checks if fix needed
    ↓
[FIXING] → Fixer applying changes
    ↓
[FIXED] → Fix applied, saved to memory
    ↓
[VALIDATING] → Validator checking fix
    ↓
[COMPLETE] → Success or retry
```

---

## 💻 Technical Stack

### Core Technologies

#### 1. **Google AI SDK (ADK)**
```python
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.memory import InMemoryMemoryService
from google.adk.planners import BuiltInPlanner
from google.genai import types
```

**Components Used**:
- **LlmAgent**: Base agent class
- **InMemoryRunner**: Executes agents
- **InMemoryMemoryService**: Memory with embeddings
- **BuiltInPlanner**: Agent planning and thinking
- **AgentTool**: Wrap agents as tools

#### 2. **AI Model**
```
Model: gemini-2.5-flash
Provider: Google Generative AI
Features:
- Fast response time
- Cost-effective
- Thinking capabilities
- Tool use (function calling)
```

#### 3. **Python Standard Library**
```python
import os           # File operations
import json         # Parse trace.json
import asyncio      # Async memory operations
from pathlib import Path  # File searching
```

#### 4. **Environment Management**
```python
from dotenv import load_dotenv
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
```

### File Structure

```
aiops/
├── main.py                # Entry point, runner setup
├── agent.py               # 4 agent definitions
├── file_tools.py          # 10 tool implementations
├── memory_agent.py        # Memory system
├── callback_tool.py       # Memory callback
├── config.py              # Configuration
├── memory.json            # Session memory storage
├── agent_memory.json      # Long-term memory (unused)
├── .env                   # API keys
├── README.md              # Documentation
│
└── codebase/              # Code to be fixed
    ├── app.py            # Buggy/fixed source code
    └── trace.json        # Error trace information
```

### Execution Flow (Code Level)

**main.py**:
```python
1. Import root_agent from agent.py
2. Create InMemoryRunner(agent=root_agent)
3. Create session (user_id, session_id)
4. Call runner.run(new_message=query)
5. Stream and print events
```

**agent.py**:
```python
1. Define 4 agents:
   - analyzer_agent (tools: file discovery + read)
   - fixer_agent (tools: read + write)
   - validator_agent (tools: read only)
   - root_agent (tools: other agents)
2. Attach memory_search_callback to all
```

**file_tools.py**:
```python
1. Implement 10 functions
2. All use "codebase" as base directory
3. Return strings (agent-readable)
```

**memory_agent.py**:
```python
1. Load memory.json on startup
2. Initialize InMemoryMemoryService
3. Provide async save/search functions
4. Auto-persist to JSON
```

**callback_tool.py**:
```python
1. Define memory_search_callback
2. Intercept LlmRequest before model
3. Search memory based on user message
4. Inject results into system instruction
```

---

## 🎨 Key Design Patterns

### 1. **Multi-Agent Pattern**

**Concept**: Divide complex task among specialized agents

**Implementation**:
- Root Agent = Orchestrator
- Analyzer = Specialist in diagnosis
- Fixer = Specialist in coding
- Validator = Specialist in QA

**Benefits**:
- Clear separation of concerns
- Easier to debug
- Can improve individual agents independently
- More maintainable

---

### 2. **Shared Memory Pattern**

**Concept**: Agents communicate via shared data store

**Implementation**:
```python
# Agent A saves
await save_memory("Finding: Bug on line 5")

# Agent B retrieves (automatic via callback)
# Receives: "Finding: Bug on line 5" in context
```

**Benefits**:
- Decoupled agents
- Persistent communication
- Inspectable history
- No tight coupling

---

### 3. **Callback Injection Pattern**

**Concept**: Auto-enhance context before AI calls

**Implementation**:
```python
before_model_callback=memory_search_callback

# Before every AI call:
# 1. Search memory
# 2. Inject results
# 3. AI gets enhanced context
```

**Benefits**:
- Automatic context
- No manual passing
- Semantic relevance
- Consistent behavior

---

### 4. **Tool Abstraction Pattern**

**Concept**: Wrap functionality as callable tools

**Implementation**:
```python
tools=[
    read_file,        # Function becomes tool
    write_file,
    save_memory,
]
```

**Benefits**:
- AI can call tools dynamically
- Type-safe parameters
- Composable functionality
- Easy to extend

---

### 5. **Semantic Search Pattern**

**Concept**: Find relevant info using meaning, not keywords

**Implementation**:
```python
# Uses embeddings (vector representations)
search_memory("How to fix bug")
→ Finds "Root cause: TypeError" (semantically related)
```

**Benefits**:
- Intelligent retrieval
- Better than keyword matching
- Handles paraphrasing
- Context-aware

---

### 6. **Fail-Safe Pattern**

**Concept**: Verify before proceeding

**Implementation**:
```python
# check_if_error_exists() before fixing
if "Code already fixed":
    STOP
else:
    proceed_with_fix()
```

**Benefits**:
- Prevents wasted work
- Safety against breaking working code
- Cost optimization
- Better UX

---

## 🎯 Example Execution

### Initial State

**codebase/app.py** (Buggy):
```python
def calculate_sum(a, b):
    return a + b

if __name__ == "__main__":
    result = calculate_sum(20,)  # ❌ Missing argument!
    print(f"Result: {result}")
```

**codebase/trace.json**:
```json
{
  "error": "TypeError: calculate_sum() missing 1 required positional argument: 'b'",
  "traceback": [
    "File \"/Users/jay.patel/Desktop/aiops/app.py\", line 6, in <module>",
    "    result = calculate_sum(\"20\")"
  ]
}
```

---

### Execution Trace

#### 🚀 Step 1: System Starts
```
$ python main.py

🚀 Starting AIOps Agent...
Query: There is a bug in the codebase folder. Please find the trace.json file, 
       identify the error source file, analyze the issue, fix the code, and 
       validate the fix.

--- Agent Workflow Started ---
```

#### 🔍 Step 2: Analyzer Agent

**Tool Calls**:
```
📂 [LIST] Listing all files in codebase
✅ [LIST] Found 2 files

🔍 [CHECK] Verifying if error still exists in code
🔍 [SEARCH] Looking for trace.json in codebase
✅ [FOUND] trace.json at: codebase/trace.json

🔍 [SEARCH] Analyzing trace.json to find error source file
```

**Analysis**:
```
✅ [FOUND] Error Analysis:
- Trace file: codebase/trace.json
- Error: TypeError: calculate_sum() missing 1 required positional argument: 'b'
- Source file: codebase/app.py
- Original path in trace: /Users/jay.patel/Desktop/aiops/app.py
```

**Memory Saved**:
```json
{
  "text": "Root Cause Analysis:\nThe `calculate_sum` function expects two arguments (a and b).\nHowever, in `app.py` on line 6, the function is called with only one argument: `result = calculate_sum(20,)`.\nThis results in a `TypeError: calculate_sum() missing 1 required positional argument: 'b'`.\n\nExact line of failure: `codebase/app.py`, line 6\nCause of failure: Missing the second argument 'b' when calling `calculate_sum`.",
  "metadata": {
    "missing_argument": "b",
    "line": 6,
    "error_type": "TypeError",
    "function": "calculate_sum",
    "file": "codebase/app.py"
  }
}
```

#### 🔧 Step 3: Fixer Agent

**Callback Injects**:
```
✅ [MEMORY] Injected 1 relevant memories for fixer_agent
Memory: "Root Cause Analysis: TypeError on line 6..."
```

**Tool Calls**:
```
📖 [FILE] Reading file: codebase/app.py
📝 [FILE] Writing to file: codebase/app.py
```

**Fix Applied**:
```python
def calculate_sum(a, b):
    # Fix: Ensure both arguments are integers before summing
    return int(a) + int(b)

if __name__ == "__main__":
    result = calculate_sum(20, 30)  # ✅ Fixed: Added second argument
    print(f"Result: {result}")
```

**Memory Saved**:
```json
{
  "text": "Fixed TypeError in `codebase/app.py` on line 6. The `calculate_sum` function was called with only one argument, but it expects two. Added a second argument (30) to the function call.",
  "metadata": {
    "line": 6,
    "fix_type": "TypeError",
    "file": "codebase/app.py",
    "description": "Added missing argument to calculate_sum function."
  }
}
```

#### ✅ Step 4: Validator Agent

**Callback Injects**:
```
✅ [MEMORY] Injected 2 relevant memories for validator_agent
Memory 1: "Root Cause Analysis..."
Memory 2: "Fixed TypeError in codebase/app.py..."
```

**Tool Calls**:
```
📖 [FILE] Reading file: codebase/trace.json
📖 [FILE] Reading file: codebase/app.py
```

**Validation**:
```
The fix successfully resolves the 'TypeError: calculate_sum() missing 1 
required positional argument: 'b'' by providing two arguments (20, 30) 
when calling the calculate_sum function in the main block.

Additionally, the function now includes type casting (int(a) + int(b)), 
which is a good practice for handling potential string inputs.
```

**Memory Saved**:
```json
{
  "text": "The fix successfully resolves the TypeError by providing two arguments (20, 30) when calling calculate_sum. Function also improved with type casting.",
  "metadata": {}
}
```

#### 🎉 Step 5: Root Reports Success

```
--- Process Completed ---

✅ Bug fixed successfully!
   - Analyzed: TypeError on line 6
   - Fixed: Added missing argument
   - Validated: Fix confirmed correct
```

---

### Final State

**memory.json**:
```json
[
  {
    "id": "e78a3648-8f5d-4263-bcf6-2eb971174ae1",
    "text": "Root Cause Analysis: TypeError on line 6...",
    "metadata": {"error_type": "TypeError", "line": 6}
  },
  {
    "id": "82a16854-5682-4d1f-8842-4db19a77d16d",
    "text": "Fixed TypeError in codebase/app.py...",
    "metadata": {"fix_type": "TypeError"}
  },
  {
    "id": "61ef872b-677a-429b-975e-7974c8f8bce2",
    "text": "Validation: SUCCESS",
    "metadata": {"validation_status": "success"}
  }
]
```

**codebase/app.py** (Fixed):
```python
def calculate_sum(a, b):
    return int(a) + int(b)

if __name__ == "__main__":
    result = calculate_sum(20, 30)
    print(f"Result: {result}")
```

---

## 🎓 Summary

### What Makes This System Special?

1. **Fully Autonomous**: No human intervention needed
2. **Multi-Agent**: 4 specialized AI agents working together
3. **Memory-Driven**: Agents share knowledge via semantic memory
4. **Auto-Context**: Callback system injects relevant memories
5. **Modular**: Easy to add new agents/tools
6. **Transparent**: All decisions logged in memory.json
7. **Safe**: Static analysis only, no code execution
8. **Smart**: Checks if code already fixed before proceeding

### Key Technologies

- **Google ADK**: Agent framework
- **gemini-2.5-flash**: AI model
- **InMemoryMemoryService**: Vector-based memory
- **Semantic Search**: Embedding-based retrieval
- **Async Python**: For memory operations

### Agent Responsibilities

| Agent | Role | Write Access | Key Tools |
|-------|------|--------------|-----------|
| Root | Orchestrator | ❌ | Other agents |
| Analyzer | Detective | ❌ | File discovery, read |
| Fixer | Surgeon | ✅ | Read, write |
| Validator | QA | ❌ | Read only |

### Communication Model

```
Agents → save_memory() → memory.json → search_memory() → callback → Agents
```

### Future Potential

- ✅ Code execution in sandbox
- ✅ Multi-file bug fixing
- ✅ Automated test generation
- ✅ Pattern learning (agent_memory.json)
- ✅ Parallel bug processing
- ✅ Git integration
- ✅ UI dashboard

---

## 📊 Architecture Diagram (Complete)

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                │
│                    (main.py)                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │    InMemoryRunner             │
         │    - Session Management       │
         │    - Event Streaming          │
         └───────────────┬───────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                     ROOT AGENT                               │
│    (Orchestrator - gemini-2.5-flash + thinking)              │
│    Tools: [analyzer_agent, fixer_agent, validator_agent]    │
└─┬────────────────────┬────────────────────┬──────────────────┘
  │                    │                    │
  ▼                    ▼                    ▼
┌────────────────┐ ┌──────────────┐ ┌────────────────┐
│ ANALYZER AGENT │ │ FIXER AGENT  │ │VALIDATOR AGENT │
│ (Detective)    │ │ (Surgeon)    │ │ (QA Checker)   │
├────────────────┤ ├──────────────┤ ├────────────────┤
│ Tools:         │ │ Tools:       │ │ Tools:         │
│ - check_error  │ │ - read_file  │ │ - read_file    │
│ - find_trace   │ │ - write_file │ │ - find_trace   │
│ - find_error   │ │ - find_error │ │ - find_error   │
│ - read_file    │ │ - save_memory│ │ - save_memory  │
│ - save_memory  │ │              │ │                │
└────────┬───────┘ └──────┬───────┘ └───────┬────────┘
         │                │                 │
         └────────────────┼─────────────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │   MEMORY SYSTEM              │
            ├──────────────────────────────┤
            │  InMemoryMemoryService       │
            │  (Vector Embeddings)         │
            │           +                  │
            │  memory.json                 │
            │  (Persistent Storage)        │
            └──────────────┬───────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │  CALLBACK SYSTEM              │
            │  memory_search_callback       │
            │  - Auto-inject memories       │
            │  - Before every AI call       │
            │  - Semantic search (limit=50) │
            └───────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │  FILE SYSTEM                  │
            │  codebase/                    │
            │  ├─ app.py (source code)      │
            │  └─ trace.json (error trace)  │
            └───────────────────────────────┘
```

---

**End of Analysis**

This covers the complete architecture, agents, tools, memory system, communication flow, and execution pattern of the AIOps autonomous bug-fixing system! 🎉
