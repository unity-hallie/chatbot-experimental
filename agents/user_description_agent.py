import threading
import time

from chatbot.chat_history import ChatHistory


class UserDescriptionAgent:
    def __init__(self, chatbot, history: ChatHistory):
        self.chatbot = chatbot
        self.history = history
        self.stop_words = set(["the", "is", "in", "and", "to", "of", "for", "a", "with"])
        self.update_interval = 60  # Update every 60 seconds
        self.running = True

    def get_src(self):
        try:
            with open(__file__, 'r') as file:
                src_code = file.read()
            return src_code
        except Exception as e:
            return f"An error occurred while fetching source code: {str(e)}"

    def run(self):
        """Run in a separate thread to update user descriptions periodically."""
        self.update_descriptions()
        while self.running:
            time.sleep(self.update_interval)
            self.update_descriptions()

    def generate_user_description(self, user_id):
        """Generate a description based on user interactions and context using ChatGPT."""
        chat_history = self.history.get_history(user_id)
        if not chat_history:
            return "A curious user."  # Default description

        # Prepare the text to send to ChatGPT for description generation
        interaction_texts = []
        for interaction in filter(lambda a: 'request' in a, chat_history):
            interaction_texts.append(f"User: {interaction['request']}\nChatbot: {interaction['response']}")

        prompt = (
                f"Based on the following interactions, generate a thoughtful and insightful user description. "
                f"Take into account the user's emotional state and engagement level:\n\n"
                + "\n".join(interaction_texts) + "\n"
                                                 f"Please summarize this into a personalized user description."
        )

        # Call ChatGPT instead of manual analysis
        response = self.chatbot.generate_response(user_id, prompt)  # Assuming this method calls the OpenAI API

        self.chatbot.set_user_description(user_id, response)

    def update_descriptions(self):
        """Update user descriptions for all users based on their interactions."""
        for user_id in self.history.get_users():
            self.generate_user_description(user_id)

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        """Stop the update loop when needed."""
        self.running = False
