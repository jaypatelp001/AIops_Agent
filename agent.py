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
    You are an expert AIOps Analyzer. Your task is to:
    1. Use find_error_source_file() to locate the trace.json and identify the error source file.
    2. Use find_trace_file() if you need the trace.json path directly.
    3. Read the faulty code file and the trace.json file using read_file().
    4. **IMPORTANT**: First check if the error from trace.json still exists in the current code.
    5. If the code is already fixed (error no longer present), save to memory: "Code already fixed - no action needed" and STOP.
    6. If the error still exists, analyze and identify the root cause.
    7. Identify the exact line and cause of the failure based on the trace.
    8. Save your analysis to memory so other agents can access it.
    """,
    tools=[
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
    You are an expert AIOps Fixer. Your task is to:
    1. Retrieve the analysis from memory or from the analyzer_agent.
    2. Use find_error_source_file() to get the path of the faulty code file if needed.
    3. Read the faulty code using read_file().
    4. Apply the necessary fixes to the code.
    5. Use write_file(original_file_path, fixed_content) to save the fix.
       IMPORTANT: write_file() will automatically create a new file with 'fixed_' prefix
       in the same directory as the original file. The original file remains unchanged.
       Example: If fixing 'codebase/services/user.py', it creates 'codebase/services/fixed_user.py'
    6. Save the details of the fix to memory, including the path to the new fixed file.
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
    5. If validation fails, repeat the process.
    6. Once fixed, confirm the final status.
    
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
