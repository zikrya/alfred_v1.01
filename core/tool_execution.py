import sys
import os
import json
import traceback
from core.tools import get_tool_registry, initialize_vector_store
from core.command_handler import get_tool_function

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))

# Initialize vector store on first run
if "VECTOR_STORE" not in globals() or VECTOR_STORE is None:
    VECTOR_STORE = initialize_vector_store()


def fix_ai_path(path):
    """Fixes AI's incorrect path mapping to absolute paths."""
    if path.lower() in ["desktop", "/desktop"]:
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() in ["documents", "/documents"]:
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.expanduser(path)


def find_best_matching_tool(tool_name):
    """Finds the best matching tool from the vector store."""
    global VECTOR_STORE
    if VECTOR_STORE is None:
        VECTOR_STORE = initialize_vector_store()

    tool_docs = VECTOR_STORE.similarity_search(tool_name)

    if not tool_docs:
        return None, f"⚠️ No matching tool found for '{tool_name}'"

    best_match_id = tool_docs[0].id
    tool_registry = get_tool_registry()

    if best_match_id in tool_registry:
        return tool_registry[best_match_id], None

    return None, f"⚠️ Tool '{tool_name}' not found in registry."


def validate_tool_call(tool_name, args):
    """Validates the tool call before execution."""
    tool_function, error_msg = find_best_matching_tool(tool_name)

    if tool_function is None:
        print(error_msg)
        return False

    expected_args = tool_function.args_schema.__annotations__.keys()
    received_args = args.keys()

    missing_args = expected_args - received_args
    extra_args = received_args - expected_args

    if missing_args:
        print(
            f"⚠️ Error: Missing required arguments {missing_args} for '{tool_name}'")
        return False
    if extra_args:
        print(
            f"⚠️ Warning: Extra arguments {extra_args} provided to '{tool_name}'")

    return True


def execute_tool_call(tool_calls):
    """Processes AI responses and executes tool calls after validation."""
    print(f"\n🔧 Received tool calls: {tool_calls}")

    results = []
    for tool_call in tool_calls:
        try:
            tool_name = tool_call.get("name", "").strip()
            raw_args = tool_call.get("args", {})

            print(f"\n📜 Raw tool arguments (string): {raw_args}")

            args = json.loads(json.dumps(raw_args))

            if "path" in args:
                args["path"] = fix_ai_path(args["path"])

            print(f"\n🔍 Validating tool call: {tool_name} with args {args}")

            if not validate_tool_call(tool_name, args):
                print(
                    f"\n❌ Tool call validation failed: {tool_name} not executed.")
                continue

            print(f"\n🚀 Running tool: {tool_name} with args {args}")

            tool_function, _ = find_best_matching_tool(tool_name)
            if tool_function:
                result = tool_function.invoke(args)
                print(f"\n✅ Tool Execution Result: {result}")
                # ✅ Return structured data
                results.append({"tool": tool_name, "result": result})
            else:
                print(f"\n❌ Tool function '{tool_name}' not found!")

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"\n❌ Error processing tool call: {e}\n{error_trace}")
            results.append({"tool": tool_name, "error": str(e)})

    return results  # ✅ Now returns structured results
