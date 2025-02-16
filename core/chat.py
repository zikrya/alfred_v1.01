from core.ai import get_chat_model
from core.prompt import format_prompt
import sys
import os

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


def chat_with_alfred(user_input):
    model = get_chat_model()
    prompt = format_prompt(user_input)
    response = model.invoke(prompt)
    return response.content


# Test
if __name__ == "__main__":
    print(chat_with_alfred("What's the weather like today?"))
