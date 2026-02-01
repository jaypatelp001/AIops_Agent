import os
from typing import Optional

from google.adk.planners import BuiltInPlanner
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

# =========================
# ENV SETUP
# =========================
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from memory_agent import save_memory, get_all_memories
from callback_tool import memory_search_callback
from file_tools import (
    read_file,
    write_file,
    list_files,
    find_trace_file,
    find_error_source_file,
    list_codebase_files,
    check_if_error_exists,
    check_if_already_fixed,
)

# ========================================
# AGENTS
# ========================================

# 1. Analyzer Agent: Analyzes the trace and code to find the root cause
analyzer_agent = LlmAgent(
    name="analyzer_agent",
    model="gemini-2.5-flash",
    description="Analyzes faulty code and trace.json to identify root causes.",
    instruction="""
    You are an expert AIOps Analyzer. Execute in order:
    
    STEP 1 - CHECK IF ALREADY FIXED (DO THIS FIRST!):
    - CALL check_if_already_fixed() to see if a fixed file already exists
    - If result shows "ALREADY FIXED", return that message immediately and STOP
    - Do NOT proceed to analysis if already fixed
    
    STEP 2 - ANALYZE (only if NOT already fixed):
    - CALL find_error_source_file() to locate trace.json and error source
    - CALL read_file() to read the faulty code and trace.json
    - Analyze the root cause of the error
    - Identify exact line and cause of failure
    - CALL save_memory() with your analysis
    
    IMPORTANT: Always run STEP 1 first to avoid re-analyzing already-fixed bugs.
    """,
    tools=[
        check_if_already_fixed,
        check_if_error_exists,
        find_error_source_file,
        find_trace_file,
        list_codebase_files,
        read_file,
        list_files,
        save_memory,
        get_all_memories,
    ],
    before_model_callback=memory_search_callback,
)

# 2. Fixer Agent: Proposes and applies the fix
fixer_agent = LlmAgent(
    name="fixer_agent",
    model="gemini-2.5-flash",
    description="Fixes the faulty code based on analysis.",
    instruction="""
    You are an expert AIOps Fixer. You MUST EXECUTE all steps - do NOT just describe them.
    
    MANDATORY STEPS (EXECUTE EACH ONE):
    1. CALL get_all_memories() - retrieve the bug analysis
    2. CALL read_file with the buggy file path - read the code
    3. Create the corrected code in your response
    4. **ABSOLUTELY REQUIRED**: CALL write_file(original_file_path, corrected_code_content)
       - Example: write_file('codebase/services/user.py', '<full corrected code here>')
       - This auto-creates 'codebase/services/fixed_user.py'
       - YOU MUST EXECUTE THIS FUNCTION CALL
    5. CALL save_memory - record where the fixed file was created
    
    CRITICAL: You will FAIL this task if you skip step 4. You must ACTUALLY CALL write_file function.
    """,
    tools=[
        find_error_source_file,
        find_trace_file,
        read_file,
        write_file,
        save_memory,
        get_all_memories,
    ],
    before_model_callback=memory_search_callback,
)


# 3. Validator Agent: Validates the fix by running the code
validator_agent = LlmAgent(
    name="validator_agent",
    model="gemini-2.5-flash",
    description="Validates the fix by executing the code.",
    instruction="""
    You are an expert AIOps Validator. Your task is to:
    1. Retrieve the fix details from memory to find out which file was fixed.
    2. The fixer creates a new file with 'fixed_' prefix in the same directory.
       Example: If the error was in 'codebase/services/user.py', 
       the fix is in 'codebase/services/fixed_user.py'
    3. Read the FIXED file (the one with 'fixed_' prefix) using read_file().
    4. Read the trace.json to understand the original error.
    5. Verify the fix in the 'fixed_' file addresses the error from trace.json.
    6. Confirm the fix resolves the issue completely.
    7. Save the validation result to memory.
    """,
    tools=[
        find_error_source_file,
        find_trace_file,
        read_file,
        save_memory,
        get_all_memories,
    ],
    before_model_callback=memory_search_callback,
)

# ========================================
# ROOT AGENT (ORCHESTRATOR)
# ========================================
root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    description="AIOps Orchestrator that coordinates analysis, fixing, and validation.",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=512,
        )
    ),
    instruction="""
    You are the AIOps Root Agent. Your goal is to fix a faulty application in the codebase folder.
    
    The codebase folder contains:
    - Source code files (e.g., app.py)
    - trace.json with error information
    
    Workflow:
    1. Call the analyzer_agent to locate and analyze the trace.json and identify the root cause.
    2. **Check analyzer's findings**: If analyzer reports "Code already fixed", inform the user and STOP - do not call fixer or validator.
    3. If a bug is identified, call the fixer_agent to apply the fix based on the analysis.
    4. Call the validator_agent to review and verify the fix.
    5. **SUCCESS CONDITION - STOP HERE**: If validator confirms the fix resolves the error in trace.json:
       - Report to user: "Bug fixed successfully! Fixed file: [path]"
       - STOP immediately - DO NOT call analyzer_agent again
       - DO NOT re-analyze the original file
    6. If validation fails (max 2 attempts), repeat from step 1.
    7. After 2 failed attempts, report the issue to the user and stop.
    
    CRITICAL: Once validation passes, you MUST stop. Do NOT loop back to analyze the original file.
    The fixed file is separate (with 'fixed_' prefix), so the original file will always show the bug.

    
    Always use shared memory to pass information between agents.
    The agents have tools to automatically find trace.json and error source files in the codebase folder.
    """,
    tools=[
        AgentTool(analyzer_agent),
        AgentTool(fixer_agent),
        AgentTool(validator_agent),
        save_memory,
        get_all_memories,
    ],
    before_model_callback=memory_search_callback,
)
