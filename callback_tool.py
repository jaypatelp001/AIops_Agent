import os
from google.adk.planners import BuiltInPlanner
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types
from typing import Optional, Union, Awaitable
from google.adk.tools.agent_tool import AgentTool

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from memory_agent import search_memory

# ========================================
# BEFORE MODEL CALLBACK - AUTOMATIC MEMORY SEARCH
# ========================================
async def memory_search_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Runs BEFORE every LLM call to inject memory context.
    Searches memory based on user's message and adds results to system instruction.
    """
    try:
        agent_name = callback_context.agent_name

        # Extract the last user message
        last_user_message = ""
        if llm_request.contents and llm_request.contents[-1].role == "user":
            if llm_request.contents[-1].parts:
                last_user_message = llm_request.contents[-1].parts[0].text

        if not last_user_message or not last_user_message.strip():
            return None

        # Search memory (Awaited)
        try:
            memory_result = await search_memory(query=last_user_message, limit=50)
        except Exception as mem_error:
            return None  # Continue without memory

        # Process memory results
        memory_context = ""
        if memory_result.get("status") == "success":
            memory_context = memory_result.get("memories", "")
            memory_count = memory_result.get("count", 0)
        else:
            return None  # No memory to inject

        # Inject memory into system instruction
        if memory_context:
            original_instruction = (
                llm_request.config.system_instruction
                or types.Content(role="system", parts=[])
            )

            # Ensure system_instruction is Content type
            if not isinstance(original_instruction, types.Content):
                original_instruction = types.Content(
                    role="system", parts=[types.Part(text=str(original_instruction))]
                )

            if not original_instruction.parts:
                original_instruction.parts.append(types.Part(text=""))

            # Add memory context to system instruction
            memory_prefix = f"""
========================================
RELEVANT MEMORIES FROM PAST CONVERSATIONS
========================================

{memory_context}

IMPORTANT: Apply constraints from memories above when relevant to current query.
========================================

"""

            # Prepend memory to existing instruction
            original_text = original_instruction.parts[0].text or ""
            modified_text = memory_prefix + original_text
            original_instruction.parts[0].text = modified_text

            llm_request.config.system_instruction = original_instruction
            print(f"✅ [MEMORY] Injected {memory_count} relevant memories for {agent_name}")

        # Return None to proceed with modified request
        return None

    except Exception as e:
        # print(f"❌ [MEMORY CALLBACK ERROR] {str(e)}")
        return None  # Continue without memory on error
