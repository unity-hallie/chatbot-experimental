import os
from dotenv import load_dotenv

from chatbot.ethical_ai_chatbot import EthicalAIChatbot

# Load environment variables from .env file
load_dotenv()

if __name__ == "__main__":

    api_key = os.getenv("OPENAI_API_KEY")  # Ensure you're loading from the environment variable
    chatbot = EthicalAIChatbot(name="Guidon")
    chatbot.display_ethical_framework()
    user_id = "hallie"
    chatbot.start_session(user_id)
    print("You can start interacting with the chatbot (type 'exit' to end).")

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            chatbot.end_session(user_id)
            break
        chatbot.handle_request(user_id, user_input)

