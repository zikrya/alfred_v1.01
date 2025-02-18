import os
import json
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Error: OPENAI_API_KEY is not set in .env!")

embeddings = OpenAIEmbeddings(
    openai_api_key=api_key, model="text-embedding-3-large"
)

vectorstore = InMemoryVectorStore(embedding=embeddings)

test_documents = [
    Document(page_content="Test document 1", metadata={"source": "test1"}),
    Document(page_content="Test document 2", metadata={"source": "test2"}),
    Document(page_content="LangGraph is useful for AI workflows",
             metadata={"source": "test3"}),
]

for doc in test_documents:
    print(f"📜 Document Type: {type(doc)}, Content: {doc.page_content}")

print("\n📥 Storing embeddings...")
vectorstore.add_documents(test_documents)
print("✅ Documents successfully added to vector store!")

query = "What is LangGraph?"
retrieved_docs = vectorstore.similarity_search(query)
print("\n🔍 Retrieved Documents:")
for idx, doc in enumerate(retrieved_docs, start=1):
    print(f"{idx}. {doc.page_content} (Source: {doc.metadata['source']})")
