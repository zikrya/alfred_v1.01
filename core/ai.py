from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from core.tools import get_tool_registry

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(
    openai_api_key=api_key,
    model_name="gpt-4o"
)

# ✅ Ensure AI has the correct tools
tools = list(get_tool_registry().values())
model_with_tools = model.bind_tools(tools)

print("\n✅ AI Model Bound to Tools Successfully!")
