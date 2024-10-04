import datetime
import json
from datetime import time

import openai


class ChatHistory:
    def __init__(self, api_key, history={}):
        self.history = history
        openai.api_key = api_key
        self.load()

    def add_interaction(self, user_id, request, response):
        """Log each interaction with the user."""
        user_history = self.get_history(user_id)

        interaction = {'user_id': user_id, 'request': request, 'response': response}
        user_history.append(interaction)

    def get_history(self, user_id):
        """Retrieve chat histories for a specific user."""
        if user_id not in self.history:
            self.history[user_id] = []
        return self.history[user_id]

    def clear_history(self, user_id):
        """Clear chat history for a specific user if needed."""
        self.history = [interaction for interaction in self.history if interaction['user_id'] != user_id]

    def summarize_history(self, user_id):
        """Summarize the last session and prepend it to the chat history."""
        chat_history = self.get_history(user_id)

        if chat_history:
            with open(f"logs\log_{datetime.datetime.now().strftime('%H%M%S%Y-%m-%d')}.json", 'w') as file:
                json.dump(chat_history, file, indent=2)
            # Generate a summary of the last session
            last_session_summary = self.create_summary(chat_history)

            # Prepend the summary to the chat history
            self.history[user_id] = [
                {"role": "system", "content": f"Previously on our journey: {last_session_summary}"}
            ]
            for interaction in chat_history[-5:]:
                self.history[user_id].append(interaction)

        # Save the updated chat history back

        self.save()
        return chat_history

    def create_summary(self, chat_history):
        """Request a summary of the chat history using the ML model"""
        interaction_texts = []

        for interaction in chat_history:
            interaction_texts.append(json.dumps(interaction))

        combined_history = "\n".join(interaction_texts)

        # Use the ML model to generate a summary
        summary_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are summarizing a conversation. Please output the summary as a five paragraph essay."},
                {"role": "user", "content": combined_history},
            ],
            max_tokens=2000
        )

        # Return the generated summary
        # Return the generated summary
        return summary_response.choices[0].message.content.strip()

    def get_users(self):
        return self.history.keys()

    def load(self):
        """Load previously saved user sessions from a file, if available."""
        try:
            with open('user_sessions.json', 'r') as file:
                self.history = json.load(file)
        except FileNotFoundError:
            return None  # Return None if no saved sessions are found
        except json.JSONDecodeError:
            print("Error: Could not parse user sessions.")
            return None

    def save(self):
        with open('user_sessions.json', 'w') as file:
            json.dump(self.history, file, indent=2)


