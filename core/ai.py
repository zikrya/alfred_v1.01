from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def get_chat_model():
    return ChatOpenAI(openai_api_key=api_key, model_name="gpt-4")


if __name__ == "__main__":
    model = get_chat_model()
    response = model.invoke("Hello Alfred, how can I assist you today?")
    print(response.content)
