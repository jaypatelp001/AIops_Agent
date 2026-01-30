# AIOps - Autonomous Bug Fixing System

## Overview

This is an autonomous AI-powered system that automatically detects, analyzes, fixes, and validates bugs in code. The system uses multiple specialized AI agents that work together, communicate through shared memory, and use various tools to accomplish their tasks.

## System Architecture

### Core Components

1. **Agents** - Specialized AI workers that perform specific tasks
2. **Tools** - Functions that agents can call to interact with files and data
3. **Memory System** - Shared storage for agents to communicate and persist information
4. **Callback System** - Automatic memory injection before each AI call

---

## Agents (4 Total)

### 1. Root Agent (Orchestrator)
**Role**: Main coordinator that manages the entire workflow

**Responsibilities**:
- Receives the initial bug report
- Calls other agents in the correct sequence
- Monitors the overall process
- Makes decisions about when to retry or stop
- Reports final status to the user

**Model**: gemini-2.5-flash with thinking capabilities

**Tools Available**:
- Can call all three sub-agents
- Access to memory functions
- No direct file access (delegates to sub-agents)

---

### 2. Analyzer Agent
**Role**: Detective that finds and diagnoses bugs

**Responsibilities**:
- Check if the error from trace.json still exists in current code
- If code is already fixed, report this and stop the workflow
- Locate the trace.json file in the codebase folder
- Find the source code file that caused the error
- Read and parse error traces
- Identify the root cause of the bug
- Determine which line of code is problematic
- Save analysis findings to shared memory

**Model**: gemini-2.5-flash

**Tools Available**:
- check_if_error_exists() - Verifies if error still exists in current code
- find_error_source_file() - Automatically locates trace.json and identifies error file
- find_trace_file() - Directly finds trace.json path
- list_codebase_files() - Lists all files in codebase folder
- read_file() - Reads any file content
- list_files() - Lists files in any directory
- save_memory() - Saves findings to memory
- get_all_memories() - Retrieves past findings

**Output**: Detailed analysis saved to memory including error type, location, and cause

---

### 3. Fixer Agent
**Role**: Surgeon that applies code fixes

**Responsibilities**:
- Retrieve analysis from memory
- Locate the faulty source file
- Read the current code
- Apply the necessary fix based on analysis
- Write the corrected code back to the file
- Document the fix in shared memory

**Model**: gemini-2.5-flash

**Tools Available**:
- find_error_source_file() - Locates the file to fix
- find_trace_file() - Gets trace information if needed
- read_file() - Reads the faulty code
- write_file() - Writes the fixed code
- save_memory() - Documents the fix
- get_all_memories() - Retrieves analysis and context

**Output**: Fixed code file and fix documentation in memory

---

### 4. Validator Agent
**Role**: Quality checker that verifies fixes

**Responsibilities**:
- Locate and read the fixed code file
- Read the original trace.json to understand the bug
- Review the fix to ensure it addresses the root cause
- Verify no new issues were introduced
- Confirm the fix is complete and correct
- Save validation results to memory

**Model**: gemini-2.5-flash

**Tools Available**:
- find_error_source_file() - Locates the fixed file
- find_trace_file() - Gets original error information
- read_file() - Reads the fixed code
- save_memory() - Saves validation results
- get_all_memories() - Retrieves fix details and analysis

**Output**: Validation report in memory (pass/fail with reasoning)

---

## Tools (10 Total)

### File Discovery Tools (4)

#### 1. check_if_error_exists()
- **Purpose**: Verifies if the error from trace.json still exists in the current code
- **How it works**: 
  - Reads trace.json to get error details
  - Locates the source file mentioned in traceback
  - Extracts error type and line number
  - Provides analysis to help determine if code is already fixed
- **Returns**: Error verification report with recommendations
- **Used by**: Analyzer agent (to avoid fixing already-fixed code)

#### 2. find_trace_file()
- **Purpose**: Automatically locates trace.json in the codebase folder
- **How it works**: Recursively searches the codebase directory for trace.json
- **Returns**: Full path to trace.json file
- **Used by**: Analyzer, Fixer, Validator agents

#### 3. find_error_source_file()
- **Purpose**: Identifies which source file caused the error
- **How it works**: 
  - First calls find_trace_file() to get trace.json
  - Parses the traceback to extract the error file path
  - Searches codebase folder for that file
  - Returns detailed error analysis
- **Returns**: Error summary with file paths and error details
- **Used by**: Analyzer, Fixer, Validator agents

#### 4. list_codebase_files()
- **Purpose**: Shows all files in the codebase directory
- **How it works**: Recursively lists all files in codebase folder
- **Returns**: List of all file paths
- **Used by**: Analyzer agent (for understanding project structure)

---

### File Operation Tools (3)

#### 5. read_file(file_path)
- **Purpose**: Reads content from any file
- **Parameters**: file_path - path to the file to read
- **Returns**: File content as string
- **Used by**: All agents

#### 6. write_file(file_path, content)
- **Purpose**: Writes content to a file
- **Parameters**: 
  - file_path - where to write
  - content - what to write
- **Returns**: Success/error message
- **Used by**: Fixer agent (to save fixed code)

#### 7. list_files(directory)
- **Purpose**: Lists files in a specific directory
- **Parameters**: directory - path to list
- **Returns**: List of files and folders
- **Used by**: Analyzer agent

---

### Memory Tools (2)

#### 8. save_memory(query, memories)
- **Purpose**: Saves information to shared memory
- **Parameters**:
  - query - description/key for the memory
  - memories - the actual information to store
- **How it works**: Stores data in memory.json with embeddings for semantic search
- **Used by**: All agents (to share findings)

#### 9. get_all_memories()
- **Purpose**: Retrieves all stored memories
- **Returns**: All memory entries
- **Used by**: All agents (to see what others have done)

---

### Memory Search Tool (1)

#### 10. search_memory(query, limit)
- **Purpose**: Finds relevant memories using semantic search
- **Parameters**:
  - query - what to search for
  - limit - max number of results
- **How it works**: Uses embeddings to find semantically similar memories
- **Returns**: Most relevant memory entries
- **Used by**: Callback system (automatic, before every AI call)

---

## Agent Communication

### How Agents Talk to Each Other

Agents do NOT directly communicate. Instead, they use **shared memory** as a communication channel.

#### Communication Flow:

1. **Analyzer Agent** completes analysis
   - Calls save_memory() with findings
   - Memory stored in memory.json

2. **Root Agent** calls Fixer Agent
   - Fixer Agent starts working
   - Before making any decision, callback system automatically searches memory
   - Relevant memories (including Analyzer's findings) are injected into Fixer's context

3. **Fixer Agent** reads the analysis from memory
   - Uses get_all_memories() or relies on auto-injected context
   - Applies fix based on analysis
   - Saves fix details to memory

4. **Validator Agent** receives context
   - Auto-injected memories include both analysis and fix details
   - Can also explicitly call get_all_memories()
   - Validates based on complete history

#### Key Points:
- Agents never call each other directly
- Only Root Agent can invoke other agents (using AgentTool)
- All information sharing happens through memory
- Memory is persistent across the entire workflow

---

## Memory System

### Two Types of Memory

#### 1. Session Memory (memory.json)
**Purpose**: Stores all findings, analysis, fixes, and validations during the current session

**Structure**:
```
Each memory entry contains:
- query: Description of what was stored
- memories: The actual information
- timestamp: When it was saved
- embedding: Vector representation for semantic search
```

**Lifecycle**:
- Persists across the entire bug-fixing session
- Can be cleared between different bug reports
- Loaded at startup, saved after each memory operation

**Used For**:
- Sharing analysis between agents
- Tracking what has been done
- Providing context for decisions

---

#### 2. Agent Memory (agent_memory.json)
**Purpose**: Stores long-term learnings and patterns

**Currently**: Not actively used in this implementation (placeholder for future enhancements)

**Potential Uses**:
- Remember common bug patterns
- Store successful fix strategies
- Learn from past mistakes

---

### Memory Callback System

**What It Does**: Automatically injects relevant memories before every AI model call

**How It Works**:

1. User sends a message to an agent
2. **Before** the AI model processes it:
   - Callback function intercepts the request
   - Extracts the user's message
   - Calls search_memory() with the message as query
   - Finds top 50 relevant memories
   - Injects memories into the system instruction
3. AI model receives enhanced context with relevant memories
4. AI makes better decisions based on past information

**Benefits**:
- Agents automatically know what others have done
- No need to manually pass context
- Semantic search finds relevant info even if keywords don't match
- Reduces redundant work

**Implementation**: 
- Function: memory_search_callback() in callback_tool.py
- Attached to all agents via before_model_callback parameter

---

## Workflow

### Complete Bug Fixing Process

1. **User starts the system**
   - Runs main.py
   - Provides query about bug in codebase folder

2. **Root Agent receives the task**
   - Understands the goal: find and fix bug
   - Plans the workflow: analyze → fix → validate

3. **Root Agent calls Analyzer Agent**
   - Analyzer uses find_error_source_file()
   - Locates trace.json and error source file
   - Reads both files
   - Analyzes the error
   - Saves analysis to memory

4. **Root Agent calls Fixer Agent**
   - Fixer's callback automatically injects Analyzer's findings
   - Fixer reads the faulty code
   - Applies the fix based on analysis
   - Writes corrected code to file
   - Saves fix details to memory

5. **Root Agent calls Validator Agent**
   - Validator's callback injects both analysis and fix details
   - Validator reads the fixed code
   - Compares against original error
   - Confirms fix is correct
   - Saves validation result to memory

6. **Root Agent evaluates results**
   - If validation passed: Reports success
   - If validation failed: May retry with Fixer Agent
   - Provides final status to user

---

## Project Structure

```
aiops/
├── codebase/              # Folder containing code to be fixed
│   ├── app.py            # Source code with bugs
│   └── trace.json        # Error trace information
├── agent.py              # Agent definitions (4 agents)
├── file_tools.py         # File operation tools (9 tools)
├── memory_agent.py       # Memory system implementation
├── callback_tool.py      # Memory callback system
├── main.py               # Entry point to run the system
├── config.py             # Configuration settings
├── memory.json           # Session memory storage
└── README.md             # This file
```

---

## Key Design Decisions

### Why Multiple Agents?
- **Separation of concerns**: Each agent has a specific expertise
- **Modularity**: Easy to improve or replace individual agents
- **Clarity**: Clear responsibility boundaries
- **Scalability**: Can add more specialized agents later

### Why Shared Memory?
- **Decoupling**: Agents don't need to know about each other
- **Persistence**: Information survives across agent calls
- **Flexibility**: Easy to add new agents that consume existing memories
- **Debugging**: Can inspect memory.json to see what agents learned

### Why Automatic Memory Injection?
- **Convenience**: Agents don't need to manually search memory
- **Intelligence**: Semantic search finds relevant context automatically
- **Efficiency**: Reduces token usage by only injecting relevant memories
- **Consistency**: Every agent gets the same memory enhancement

### Why No Code Execution?
- **Safety**: Prevents potentially harmful code from running
- **Simplicity**: Static analysis is faster and more predictable
- **Focus**: System focuses on code understanding and fixing
- **Note**: Can be added later if needed for validation

### Why Check If Error Still Exists?
- **Efficiency**: Avoids wasting API calls on already-fixed code
- **Safety**: Prevents modifying working code
- **Intelligence**: System knows when no action is needed
- **User Experience**: Provides clear feedback when code is already correct

---

## How to Replicate This System

### Step 1: Set Up Agents
Create four agents with these characteristics:
- Root Agent: Orchestrator with access to other agents
- Analyzer Agent: Has file discovery and reading tools
- Fixer Agent: Has file reading and writing tools
- Validator Agent: Has file reading tools
- All agents: Have memory tools

### Step 2: Create File Tools
Implement these tools:
- find_trace_file: Search for trace.json
- find_error_source_file: Parse trace and locate error file
- list_codebase_files: List all files in codebase
- read_file: Read file content
- write_file: Write file content
- list_files: List directory contents

### Step 3: Implement Memory System
Build memory with:
- save_memory: Store information with embeddings
- get_all_memories: Retrieve all memories
- search_memory: Semantic search using embeddings
- Storage: JSON file for persistence

### Step 4: Add Memory Callback
Create callback that:
- Intercepts requests before AI processing
- Searches memory based on user message
- Injects relevant memories into system instruction
- Attach to all agents

### Step 5: Define Agent Instructions
Write clear instructions for each agent:
- What their role is
- What tools to use and when
- How to save findings to memory
- What to do if they encounter errors

### Step 6: Create Orchestration
Build main script that:
- Initializes the root agent
- Sends the initial query
- Streams responses
- Handles errors

### Step 7: Test with Sample Bug
Create test case:
- Put buggy code in codebase/app.py
- Create trace.json with error details
- Run the system
- Verify it finds, fixes, and validates

---

## Configuration

### Environment Variables
Set these in .env file:
- GOOGLE_API_KEY: Your Google AI API key
- Any other model-specific settings

### Model Selection
Currently uses: gemini-2.5-flash
- Fast and cost-effective
- Good reasoning capabilities
- Can be changed to other models in agent.py

---

## Memory Format

### Memory Entry Structure
```
{
  "query": "Description of what this memory is about",
  "memories": "The actual information stored",
  "timestamp": "When it was created",
  "embedding": [array of numbers for semantic search]
}
```

### Example Memory Flow
1. Analyzer saves: "Bug analysis: TypeError in calculate_sum function"
2. Fixer searches: "How to fix the bug"
3. System finds: Analyzer's memory (semantic match)
4. Fixer receives: Analysis automatically in context
5. Fixer saves: "Applied fix: Added missing parameter"
6. Validator searches: "Validation needed"
7. System finds: Both analysis and fix memories
8. Validator receives: Complete history

---

## Advantages of This Architecture

1. **Autonomous**: Runs end-to-end without human intervention
2. **Transparent**: All decisions saved to memory for inspection
3. **Modular**: Easy to add/remove/modify agents
4. **Intelligent**: Semantic memory search finds relevant context
5. **Safe**: No code execution, only static analysis
6. **Scalable**: Can handle multiple bugs in sequence
7. **Debuggable**: Memory.json shows complete thought process

---

## Future Enhancements

### Potential Additions:
1. **Code Execution**: Add sandbox runner for validation
2. **Multi-file Fixes**: Handle bugs spanning multiple files
3. **Test Generation**: Create tests to prevent regression
4. **Learning System**: Use agent_memory.json for pattern learning
5. **Parallel Processing**: Analyze multiple bugs simultaneously
6. **Version Control**: Automatic git commits for fixes


---

## Troubleshooting

### Common Issues:

**"Permission denied" errors**
- Cause: Tools trying to access wrong directory
- Fix: Ensure tools hardcode "codebase" directory (no default parameters)

**"Default value not supported" warnings**
- Cause: Google AI doesn't support default parameter values
- Fix: Remove default values, hardcode defaults inside functions

**"Memory failed to load" errors**
- Cause: memory.json is empty or invalid JSON
- Fix: Initialize with empty array: []

**Agents not finding files**
- Cause: Files not in codebase folder
- Fix: Ensure app.py and trace.json are in codebase/ directory

**Agents not sharing information**
- Cause: Not saving to memory or callback not working
- Fix: Verify save_memory() calls and callback attachment

**System tries to fix already-fixed code**
- Cause: Trace.json not updated after fix
- Solution: Analyzer checks if error still exists before attempting fix
- Fix: Run check_if_error_exists() first to verify

---

## Summary

This AIOps system demonstrates autonomous multi-agent collaboration through shared memory. Four specialized agents (Root, Analyzer, Fixer, Validator) work together using nine tools to automatically fix bugs. Communication happens through a persistent memory system with automatic semantic search injection. The architecture is modular, transparent, and can be replicated by following the agent roles, tool implementations, and memory patterns described in this document.

---

---



## Environment Setup (.env)

```
GOOGLE_API_KEY=your_google_api_key_here
```

---

## Dependencies (requirements.txt)

```
google-genai
google-adk
python-dotenv
```

---

## Installation & Usage

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Set Up Environment
Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

### Prepare Codebase
1. Create a `codebase` folder
2. Add your buggy code (e.g., `app.py`)
3. Add the error trace as `trace.json`

### Run the System
```bash
python main.py
```

The system will automatically:
1. Find and analyze the trace.json
2. Locate the error source file
3. Apply a fix
4. Validate the fix
5. Report results

---

## Notes on Implementation

### Key Design Patterns

1. **No Default Parameters**: Google AI doesn't support default parameter values in function declarations, so all defaults are hardcoded inside functions.

2. **Async Memory Operations**: Memory operations are async to support vector search with embeddings.

3. **Dual Memory Storage**: Memories are stored both in InMemoryMemoryService (for semantic search) and in memory.json (for persistence).

4. **Callback Pattern**: The before_model_callback intercepts every LLM request to automatically inject relevant memories.

5. **Tool Composition**: Complex tools (like find_error_source_file) call simpler tools (like find_trace_file) to build functionality.

6. **Error Handling**: All tools return error messages as strings rather than raising exceptions, making them safe for AI agents to use.

---

This completes the full code implementation of the AIOps autonomous bug-fixing system.
