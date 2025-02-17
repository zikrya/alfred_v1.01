from core.ai import model_with_tools
from core.prompt import format_prompt
from core.tool_execution import execute_tool_call
import sys
import os
import json
from langchain_core.messages import SystemMessage, HumanMessage

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


def chat_with_alfred(user_input):
    """Ensures AI receives formatted prompts and properly invokes tool calls."""

    print(f"\n🗣️ You: {user_input}")
    print("\n🚀 Processing user input...")

    formatted_prompt = format_prompt(user_input)

    if hasattr(formatted_prompt, "messages"):
        messages = formatted_prompt.messages
    else:
        raise ValueError(f"Unexpected format in prompt: {formatted_prompt}")

    print(f"\n📜 Extracted Messages for AI: {messages}")

    response = model_with_tools.invoke(messages)

    print(f"\n🤖 AI Response (RAW): {response}")

    if hasattr(response, "tool_calls") and response.tool_calls:
        print(f"\n✅ AI detected proper tool calls. Executing...\n")
        return execute_tool_call(response.tool_calls)

    try:
        parsed_response = json.loads(response.content)
        if "function" in parsed_response and "arguments" in parsed_response:
            tool_call = [{
                "name": parsed_response["function"],
                "args": parsed_response["arguments"]
            }]
            return execute_tool_call(tool_call)
    except json.JSONDecodeError:
        pass

    print("\n⚠️ Response is not a tool call. Proceeding normally.")
    return response.content


if __name__ == "__main__":
    user_input = "Create a folder named Batman on my Desktop"
    response = chat_with_alfred(user_input)
    print(f"\n🤖 Alfred: {response}")
