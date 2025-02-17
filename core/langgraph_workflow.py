from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from core.ai import model_with_tools
from core.tool_execution import execute_tool_call


class State(dict):
    """Graph state to track messages and tool executions."""
    messages: list


def call_ai(state: State):
    """Invoke AI model and determine next step."""
    response = model_with_tools.invoke(state["messages"])
    state["messages"].append(response)

    return {"messages": state["messages"]}


def execute_tools(state: State):
    """Execute tools and append results as ToolMessage with tool_call_id."""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]

            print(f"\n🔧 Executing tool: {tool_name} with args {tool_args}")
            tool_response = execute_tool_call(
                [{"name": tool_name, "args": tool_args}])

            state["messages"].append(
                ToolMessage(content=str(tool_response),
                            tool_call_id=tool_call_id)
            )

    return {"messages": state["messages"]}


graph = StateGraph(State)
graph.add_node("ai", call_ai)
graph.add_node("tools", execute_tools)


def determine_next_step(state: State):
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


graph.add_edge(START, "ai")
graph.add_conditional_edges("ai", determine_next_step, {
                            "tools": "tools", END: END})
graph.add_edge("tools", "ai")

graph = graph.compile()


if __name__ == "__main__":
    test_input = "Create a folder named 'TestLangGraph' on my Desktop."
    response = graph.invoke({"messages": [HumanMessage(content=test_input)]})

    print("\n🎩 Alfred: ", response["messages"][-1].content)
