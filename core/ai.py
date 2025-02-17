from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from core.tools import create_folder, create_file, list_files_and_folders, open_file_or_folder, append_to_file

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize AI model
model = ChatOpenAI(openai_api_key=api_key, model_name="gpt-4o")

# ✅ Bind tools correctly
tools = [create_folder, create_file, list_files_and_folders,
         open_file_or_folder, append_to_file]
model_with_tools = model.bind_tools(tools)

print("✅ AI Model with Tools Initialized")  # Debugging

if __name__ == "__main__":
    response = model.invoke("What can you do?")
    print(response.content)
