import os
import json
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
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

print("\n Storing tool embeddings...")
vectorstore.add_documents(tool_documents)
print(" Tools successfully added to vector store!")

query = "Create a txt file called Joker"
retrieved_tools = vectorstore.similarity_search(
    query, k=1)

print("\n Best Matching Tool:")
if retrieved_tools:
    best_tool = retrieved_tools[0]
    print(f" Tool Name: {best_tool.metadata['tool_name']}")
    print(f"Description: {best_tool.page_content}")
else:
    print(" No relevant tool found.")
