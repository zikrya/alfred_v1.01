import json
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from core.ai import model_with_tools
from core.tool_execution import execute_tool_call


class State(dict):
    """Graph state to track messages and tool executions."""
    messages: list


def call_ai(state: State):
    """Invoke AI model and determine next step."""
    messages = state["messages"]
    response = model_with_tools.invoke(messages)

    state["messages"].append(response)

    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": state["messages"], "next_step": "tools"}

    return {"messages": state["messages"], "next_step": END}


def execute_tools(state: State):
    """Execute tools and append properly formatted responses."""
    latest_ai_message = state["messages"][-1]

    if hasattr(latest_ai_message, "tool_calls") and latest_ai_message.tool_calls:
        print(f"\n🔧 Executing tool: {latest_ai_message.tool_calls}")

        tool_responses = execute_tool_call(latest_ai_message.tool_calls)

        tool_messages = [
            ToolMessage(
                content=json.dumps(
                    {"result": resp["result"] if "result" in resp else "Error"}),
                tool_call_id=call["id"]
            )
            for call, resp in zip(latest_ai_message.tool_calls, tool_responses)
        ]

        return {"messages": state["messages"] + tool_messages, "next_step": "ai"}

    return {"messages": state["messages"], "next_step": END}


def determine_next_step(state: State):
    """Returns the correct next step based on AI response."""
    if hasattr(state["messages"][-1], "tool_calls") and state["messages"][-1].tool_calls:
        return "tools"
    return END


graph = StateGraph(State)
graph.add_node("ai", call_ai)
graph.add_node("tools", execute_tools)

graph.add_edge(START, "ai")
graph.add_conditional_edges("ai", determine_next_step)
graph.add_edge("tools", "ai")

graph = graph.compile()

if __name__ == "__main__":
    test_input = "Where is my Batman folder located"
    response = graph.invoke({"messages": [HumanMessage(content=test_input)]})
    print("\n🎩 Alfred: ", response["messages"][-1].content)
