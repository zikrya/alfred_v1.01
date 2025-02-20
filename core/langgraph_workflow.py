import json
import os
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from core.ai import model
from core.tool_execution import execute_tool_call
from core.tools import get_tool_registry

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Error: OPENAI_API_KEY is not set in .env!")

embeddings = OpenAIEmbeddings(
    openai_api_key=api_key, model="text-embedding-3-large"
)

vectorstore = InMemoryVectorStore(embedding=embeddings)

tool_registry = get_tool_registry()
tool_documents = [
    Document(
        page_content=tool.description,
        metadata={"tool_name": tool.name}
    )
    for tool in tool_registry.values()
]

vectorstore.add_documents(tool_documents)
print("✅ Tools successfully added to vector store!")


class State(dict):
    """Graph state to track messages and tool executions."""
    messages: list


def find_best_tool(user_query: str):
    """🔍 Use vector embeddings to find the best matching tool."""
    retrieved_tools = vectorstore.similarity_search(user_query, k=1)

    if retrieved_tools:
        best_tool = retrieved_tools[0].metadata["tool_name"]
        print(f"\n✅ Best Matching Tool: {best_tool}")
        return best_tool

    print("\n No relevant tool found.")
    return None


def call_ai(state: State):
    """🤖 Invoke AI model after selecting the best tool from embeddings."""
    messages = state["messages"]
    user_query = messages[-1].content

    best_tool = find_best_tool(user_query)

    if not best_tool:
        # No valid tool
        return {"messages": state["messages"], "next_step": END}

    # ✅ Modify user query to instruct AI to generate only the right arguments
    modified_query = f"Use the '{best_tool}' tool. {user_query}"

    response = model.invoke([HumanMessage(content=modified_query)])

    state["messages"].append(response)

    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": state["messages"], "next_step": "tools"}

    return {"messages": state["messages"], "next_step": END}


def execute_tools(state: State):
    """🔧 Execute the selected tool and return structured responses."""
    latest_ai_message = state["messages"][-1]

    if hasattr(latest_ai_message, "tool_calls") and latest_ai_message.tool_calls:
        print(f"\n🔧 Executing tool: {latest_ai_message.tool_calls}")

        tool_responses = execute_tool_call(latest_ai_message.tool_calls)

        tool_messages = [
            ToolMessage(
                content=json.dumps({"result": resp}),
                tool_call_id=call["id"]
            )
            for call, resp in zip(latest_ai_message.tool_calls, tool_responses)
        ]

        return {"messages": state["messages"] + tool_messages, "next_step": "ai"}

    return {"messages": state["messages"], "next_step": END}


def determine_next_step(state: State):
    """🚦 Determine if we need another tool execution or if we're done."""
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
    test_input = "Create a Batman folder in my desktop Directory"
    response = graph.invoke({"messages": [HumanMessage(content=test_input)]})
    print("\n🎩 Alfred: ", response["messages"][-1].content)
