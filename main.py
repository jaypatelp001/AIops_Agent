from agent import root_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

def main():
    print("Starting AIOps Agent...")
    query = "There is a bug in the codebase folder. Please find the trace.json file, identify the error source file, analyze the issue, fix the code, and validate the fix."
    
    print(f"Query: {query}")
    
    # Initialize the runner with the root agent
    runner = InMemoryRunner(agent=root_agent)
    
    user_id = "aio_ops_user"
    session_id = "aio_ops_session"
    
    # Create the session
    runner.session_service._create_session_impl(
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id
    )
    
    print("\n--- Agent Workflow Started ---\n")
    
    # runner.run is a synchronous generator that yields events
    try:
        events = runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=query)])
        )
        
        for event in events:
            # Check if the event has content and parts
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(part.text, end="", flush=True)
            
            # Monitor for errors
            if hasattr(event, 'error_message') and event.error_message:
                print(f"\n[Error]: {event.error_message}")
    except Exception as e:
        print(f"\n[Error]: {e}")
        import traceback
        traceback.print_exc()

    print("\n\n--- Process Completed ---")

if __name__ == "__main__":
    main()
