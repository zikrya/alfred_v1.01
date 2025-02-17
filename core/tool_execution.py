import sys
import os
import json
from langchain_core.messages import HumanMessage
from core.command_handler import get_tool_function
from core.ai import model_with_tools

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


def fix_ai_path(path):
    """Fixes AI's incorrect path mapping."""
    if path.lower() in ["desktop", "/desktop"]:
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() in ["documents", "/documents"]:
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.expanduser(path)


def execute_tool_call(tool_calls):
    """Processes AI responses and executes system commands when detected."""
    print(f"\n  Received tool calls: {tool_calls}")

    results = []
    for tool_call in tool_calls:
        try:
            tool_name = tool_call["name"]
            raw_args = tool_call["args"]

            print(f"\n📜 Raw tool arguments (string): {raw_args}")

            args = json.loads(json.dumps(raw_args))

            if "path" in args:
                args["path"] = fix_ai_path(args["path"])

            print(f"\n Running tool: {tool_name} with args {args}")

            tool_function = get_tool_function(tool_name)
            if tool_function:
                result = tool_function.invoke(args)
                print(f"\n Tool Execution Result: {result}")
                results.append(result)
            else:
                print(f"\n  Tool function '{tool_name}' not found!")

        except Exception as e:
            print(f"\n Error processing tool call: {e}")

    return results
