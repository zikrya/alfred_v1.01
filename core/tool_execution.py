import sys
import os
import json
from langchain_core.messages import ToolMessage
from core.command_handler import get_tool_function

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


def fix_ai_path(path):
    """Fixes AI's incorrect path mapping."""
    if path.lower() in ["desktop", "/desktop"]:
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() in ["documents", "/documents"]:
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.expanduser(path)


def validate_tool_call(tool_name, args):
    """Validates the tool call before execution."""
    expected_function = get_tool_function(tool_name)

    if expected_function is None:
        print(f"⚠️ Error: No tool function found for '{tool_name}'")
        return False

    expected_args = expected_function.args_schema.__annotations__.keys()
    received_args = args.keys()

    missing_args = expected_args - received_args
    extra_args = received_args - expected_args

    if missing_args:
        print(
            f" Error: Missing required arguments {missing_args} for '{tool_name}'")
        return False
    if extra_args:
        print(
            f" Warning: Extra arguments {extra_args} provided to '{tool_name}'")

    return True


def execute_tool_call(tool_calls):
    """Processes AI responses and executes tool calls after validation."""
    print(f"\n Received tool calls: {tool_calls}")

    tool_messages = []

    for tool_call in tool_calls:
        try:
            tool_name = tool_call["name"]
            raw_args = tool_call["args"]

            print(f"\n Raw tool arguments (string): {raw_args}")

            args = json.loads(json.dumps(raw_args))

            if "path" in args:
                args["path"] = fix_ai_path(args["path"])

            print(f"\n🔍 Validating tool call: {tool_name} with args {args}")

            if not validate_tool_call(tool_name, args):
                print(
                    f"\n Tool call validation failed: {tool_name} not executed.")
                continue

            print(f"\n Running tool: {tool_name} with args {args}")

            tool_function = get_tool_function(tool_name)
            if tool_function:
                result = tool_function.invoke(args)
                print(f"\nTool Execution Result: {result}")
                tool_messages.append(ToolMessage(
                    tool_call_id=tool_call.get("id", tool_name),
                    name=tool_name,
                    content=result
                ))
            else:
                print(f"\n Tool function '{tool_name}' not found!")

        except Exception as e:
            print(f"\n Error processing tool call: {e}")

    return {"messages": tool_messages}
