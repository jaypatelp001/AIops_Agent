# COPY THIS INTO agent.py starting at line 66

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
