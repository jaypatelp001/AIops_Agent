import os
import subprocess
import json
from pathlib import Path


def read_file(file_path: str) -> str:
    """Reads the content of a file."""
    print(f"📖 [FILE] Reading file: {file_path}")
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """
    Creates a new file with 'fixed_' prefix in the same directory as the original file.
    Generic implementation that works with any file path.
    
    Example: 
        - Input: 'codebase/services/user.py'
        - Output: 'codebase/services/fixed_user.py'
    """
    try:
        # Extract directory and filename
        path_obj = Path(file_path)
        directory = path_obj.parent
        original_filename = path_obj.name
        
        # Create new filename with 'fixed_' prefix
        fixed_filename = f"fixed_{original_filename}"
        
        # Construct full path for the fixed file
        fixed_file_path = directory / fixed_filename
        
        print(f"📝 [FILE] Creating fixed file: {fixed_file_path}")
        
        # Write content to the new fixed file
        with open(fixed_file_path, "w") as f:
            f.write(content)
        
        result = f"Successfully created fixed file: {fixed_file_path}\nOriginal file unchanged: {file_path}"
        print(f"✅ [FILE] {result}")
        return result
        
    except Exception as e:
        return f"Error creating fixed file for {file_path}: {str(e)}"


def list_files(directory: str = ".") -> str:
    """Lists files in the specified directory."""
    try:
        files = os.listdir(directory)
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"


def find_trace_file() -> str:
    """
    Searches for trace.json file in the codebase directory.
    Returns the full path to the trace.json file.
    Always searches in the 'codebase' folder.
    """
    base_directory = "codebase"
    print(f"🔍 [SEARCH] Looking for trace.json in {base_directory}")
    try:
        base_path = Path(base_directory)

        # Search for trace.json files
        trace_files = list(base_path.rglob("trace.json"))

        if not trace_files:
            return f"Error: No trace.json file found in {base_directory}"

        if len(trace_files) == 1:
            trace_path = str(trace_files[0])
            print(f"✅ [FOUND] trace.json at: {trace_path}")
            return trace_path
        else:
            # Multiple trace files found
            paths = "\n".join([str(f) for f in trace_files])
            return f"Multiple trace.json files found:\n{paths}\nUsing first one: {str(trace_files[0])}"

    except Exception as e:
        return f"Error searching for trace.json: {str(e)}"


def find_error_source_file() -> str:
    """
    Reads trace.json to identify the source file that caused the error.
    Returns information about the error file and its location.
    Always searches in the 'codebase' folder.
    Supports both old simple format and new OpenTelemetry format.
    Intelligently parses exception.stack_details to find NON-EXTERNAL files first.
    """
    base_directory = "codebase"
    print(f"🔍 [SEARCH] Analyzing trace.json to find error source file")
    try:
        # First find the trace file
        trace_path = find_trace_file()

        if trace_path.startswith("Error"):
            return trace_path

        # Read and parse trace.json
        with open(trace_path, "r") as f:
            trace_data = json.load(f)

        error_message = None
        error_file = None
        error_line = None
        
        # Handle new OpenTelemetry format (array with event_attributes)
        if isinstance(trace_data, list) and len(trace_data) > 0:
            event = trace_data[0]
            if "event_attributes" in event:
                attrs = event["event_attributes"]
                error_message = attrs.get("exception.message", "Unknown error")
                
                # PRIORITY 1: Parse exception.stack_details (JSON string with detailed info)
                stack_details_str = attrs.get("exception.stack_details", "")
                if stack_details_str:
                    try:
                        stack_details = json.loads(stack_details_str)
                        # Find the FIRST non-external file in the stack
                        for frame in stack_details:
                            is_external = frame.get("exception.is_file_external", "true")
                            if is_external == "false":  # This is our code!
                                file_path = frame.get("exception.file", "")
                                error_line = frame.get("exception.line", None)
                                
                                if file_path:
                                    # Extract relative path after /srv/app/
                                    if "/srv/app/" in file_path:
                                        error_file = file_path.split("/srv/app/")[1]
                                    else:
                                        error_file = os.path.basename(file_path)
                                    
                                    print(f"✅ [STACK_DETAILS] Found non-external file: {error_file}")
                                    break
                    except json.JSONDecodeError:
                        print("⚠️ [STACK_DETAILS] Failed to parse, falling back to stacktrace")
                
                # PRIORITY 2: If stack_details didn't work, parse exception.stacktrace
                if not error_file:
                    stacktrace = attrs.get("exception.stacktrace", "")
                    if stacktrace:
                        lines = stacktrace.split("\n")
                        # Find the LAST /srv/app/ file (bottom of stack = actual error)
                        for line in reversed(lines):
                            if "File" in line and ".py" in line and "/srv/app/" in line:
                                start = line.find('"') + 1
                                end = line.find('"', start)
                                if start > 0 and end > start:
                                    full_path = line[start:end]
                                    if "/srv/app/" in full_path:
                                        error_file = full_path.split("/srv/app/")[1]
                                    else:
                                        error_file = full_path
                                    
                                    # Extract line number
                                    if "line" in line:
                                        try:
                                            line_parts = line.split("line")
                                            if len(line_parts) > 1:
                                                line_num = line_parts[1].strip().split(",")[0].strip()
                                                error_line = int(line_num)
                                        except:
                                            pass
                                    print(f"✅ [STACKTRACE] Found file: {error_file}")
                                    break
        
        # Handle old simple format
        elif isinstance(trace_data, dict):
            error_message = trace_data.get("error", "Unknown error")
            if "traceback" in trace_data:
                for line in trace_data["traceback"]:
                    if "File" in line and ".py" in line:
                        # Extract file path from traceback line
                        # Format: '  File "/path/to/file.py", line X, in <module>'
                        start = line.find('"') + 1
                        end = line.find('"', start)
                        if start > 0 and end > start:
                            error_file = line[start:end]
                            break

        if not error_file:
            return (
                f"Could not extract error source file from trace.json at {trace_path}"
            )

        # Get just the filename (in case it's a full path)
        error_filename = os.path.basename(error_file)

        # Search for this file in the base_directory
        base_path = Path(base_directory)
        matching_files = list(base_path.rglob(error_filename))

        if not matching_files:
            return f"Error source file '{error_filename}' not found in {base_directory}"

        actual_file_path = str(matching_files[0])

        result = f"""
✅ [FOUND] Error Analysis:
- Trace file: {trace_path}
- Error: {error_message}
- Source file: {actual_file_path}
- Error line: {error_line if error_line else 'Unknown'}
- Original path in trace: {error_file}

Use read_file('{actual_file_path}') to read the faulty code.
"""
        print(result)
        return result

    except json.JSONDecodeError as e:
        return f"Error parsing trace.json: {str(e)}"
    except Exception as e:
        return f"Error finding error source file: {str(e)}"


def check_if_error_exists() -> str:
    """
    Checks if the error from trace.json still exists in the current code.
    Returns whether the code needs fixing or is already fixed.
    Always checks in the 'codebase' folder.
    Supports both old simple format and new OpenTelemetry format.
    Intelligently parses exception.stack_details to find NON-EXTERNAL files first.
    """
    base_directory = "codebase"
    print(f"🔍 [CHECK] Verifying if error still exists in code")
    try:
        # Get trace file
        trace_path = find_trace_file()
        if trace_path.startswith("Error"):
            return trace_path
        
        # Read trace.json
        with open(trace_path, "r") as f:
            trace_data = json.load(f)
        
        error_msg = ""
        error_file = None
        error_line = None
        
        # Handle new OpenTelemetry format
        if isinstance(trace_data, list) and len(trace_data) > 0:
            event = trace_data[0]
            if "event_attributes" in event:
                attrs = event["event_attributes"]
                error_msg = attrs.get("exception.message", "")
                
                # PRIORITY 1: Parse exception.stack_details
                stack_details_str = attrs.get("exception.stack_details", "")
                if stack_details_str:
                    try:
                        stack_details = json.loads(stack_details_str)
                        for frame in stack_details:
                            is_external = frame.get("exception.is_file_external", "true")
                            if is_external == "false":
                                file_path = frame.get("exception.file", "")
                                error_line = frame.get("exception.line", None)
                                
                                if file_path:
                                    if "/srv/app/" in file_path:
                                        error_file = file_path.split("/srv/app/")[1]
                                    else:
                                        error_file = os.path.basename(file_path)
                                    break
                    except json.JSONDecodeError:
                        pass
                
                # PRIORITY 2: Fallback to stacktrace
                if not error_file:
                    stacktrace = attrs.get("exception.stacktrace", "")
                    if stacktrace:
                        lines = stacktrace.split("\n")
                        for line in reversed(lines):
                            if "File" in line and ".py" in line and "/srv/app/" in line:
                                start = line.find('"') + 1
                                end = line.find('"', start)
                                if start > 0 and end > start:
                                    full_path = line[start:end]
                                    if "/srv/app/" in full_path:
                                        error_file = full_path.split("/srv/app/")[1]
                                    else:
                                        error_file = full_path
                                
                                if "line" in line:
                                    try:
                                        line_parts = line.split("line")
                                        if len(line_parts) > 1:
                                            line_num = line_parts[1].strip().split(",")[0].strip()
                                            error_line = int(line_num)
                                    except:
                                        pass
                                break
        
        # Handle old simple format
        elif isinstance(trace_data, dict):
            error_msg = trace_data.get("error", "")
            if "traceback" in trace_data:
                for line in trace_data["traceback"]:
                    if "File" in line and ".py" in line:
                        start = line.find('"') + 1
                        end = line.find('"', start)
                        if start > 0 and end > start:
                            error_file = line[start:end]
                        # Extract line number if present
                        if "line" in line:
                            try:
                                line_parts = line.split("line")
                                if len(line_parts) > 1:
                                    line_num = line_parts[1].strip().split(",")[0].strip()
                                    error_line = int(line_num)
                            except:
                                pass
                        break
        
        if not error_file:
            return "Could not determine error file from trace.json"
        
        # Find actual file
        error_filename = os.path.basename(error_file)
        base_path = Path(base_directory)
        matching_files = list(base_path.rglob(error_filename))
        
        if not matching_files:
            return f"Error source file '{error_filename}' not found in {base_directory}"
        
        actual_file_path = str(matching_files[0])
        
        # Read current code
        with open(actual_file_path, "r") as f:
            current_code = f.read()
        
        # Check for common error patterns
        result = f"""
📋 [CHECK] Error Verification Results:
- Trace file: {trace_path}
- Original error: {error_msg}
- Source file: {actual_file_path}
- Error line: {error_line if error_line else 'Unknown'}

Current Code Analysis:
"""
        
        # Check specific error patterns
        if "missing" in error_msg.lower() and "argument" in error_msg.lower():
            # Check if function calls have correct arguments
            result += "\n⚠️ Checking for missing argument errors..."
            # This is a heuristic - analyzer should do detailed check
            
        elif "typeerror" in error_msg.lower():
            result += "\n⚠️ Type error detected in trace..."
            
        elif "nameerror" in error_msg.lower():
            result += "\n⚠️ Name/variable error detected in trace..."
        
        elif "attributeerror" in error_msg.lower():
            result += "\n⚠️ Attribute error detected in trace..."
            # Extract the problematic attribute if possible
            if "has no attribute" in error_msg:
                result += f"\n   Error message: {error_msg}"
        
        result += f"\n\n💡 Recommendation: Analyzer should compare trace error with current code to confirm if fix is needed."
        result += f"\n   Read file '{actual_file_path}' and check if the error condition still exists."
        
        print(result)
        return result
        
    except json.JSONDecodeError as e:
        return f"Error parsing trace.json: {str(e)}"
    except Exception as e:
        return f"Error checking if error exists: {str(e)}"


def list_codebase_files() -> str:
    """
    Lists all files in the codebase directory recursively.
    Useful for understanding the project structure.
    Always lists files in the 'codebase' folder.
    """
    base_directory = "codebase"
    print(f"📂 [LIST] Listing all files in {base_directory}")
    try:
        base_path = Path(base_directory)

        if not base_path.exists():
            return f"Error: Directory {base_directory} does not exist"

        files = []
        for file_path in base_path.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(base_path)
                files.append(str(relative_path))

        if not files:
            return f"No files found in {base_directory}"

        result = f"Files in {base_directory}:\n" + "\n".join(sorted(files))
        print(f"✅ [LIST] Found {len(files)} files")
        return result

    except Exception as e:
        return f"Error listing codebase files: {str(e)}"
