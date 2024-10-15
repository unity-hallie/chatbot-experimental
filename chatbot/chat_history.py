import datetime
import json
from datetime import time

import openai


class ChatHistory:
    def __init__(self, api_key, history={}, file_name='history.json'):
        self.history = history
        self.file_name = file_name
        openai.api_key = api_key
        self.load()

    def add_interaction(self, user_id, request, response):
        """Log each interaction with the user."""
        user_history = self.get_history(user_id)

        if len(json.dumps(user_history[:-5])) > 10000:
            self.summarize_history(user_id)
            user_history = self.get_history(user_id)

        interaction = {
            'user_id': user_id,
            'request': request,
            'response': response,
            'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        user_history.append(interaction)
        self.history[user_id] = user_history
        print(self.history[user_id])
        self.save()

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
            with open(f"logs\\log_{datetime.datetime.now().strftime('%H%M%S%Y-%m-%d')}.json", 'w') as file:
                json.dump(chat_history, file, indent=2)
            # Generate a summary of the last session
            last_session_summary = self.create_summary(chat_history)
            chat_history = [a for a in filter(lambda a: not ("role" in a and a["role"] == 'system'), chat_history)]
            self.history[user_id] = chat_history[-1:]

            self.history[user_id].append(
                {
                    "role": "system",
                    "content": f"Previously on our journey: {last_session_summary}",
                    "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            )

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
                {"role": "system",
                 "content": "You are summarizing a conversation. Please output the summary as a JSON representation of the important models discussed"},
                {"role": "user", "content": combined_history},
            ],
            max_tokens=1000
        )

        # Return the generated summary
        return summary_response.choices[0].message.content.strip()

    def get_users(self):
        return self.history.keys()

    def format_chat_history(self, user_id):
        """Format the chat history to a specified client format."""
        formatted_history = []
        for interaction in self.get_history(user_id):
            if 'request' in interaction:
                formatted_history.append({
                    "role": "User",  # Default to 'User'
                    "content": interaction.get('request', ''),
                    "time": interaction.get('time', ''),
                })
                formatted_history.append({
                    "role": "Agent",
                    "content": interaction.get('response', ''),
                    "time": interaction.get('time', ''),
                })
        return formatted_history

    def load(self):
        """Load previously saved user sessions from a file, if available."""
        try:
            with open(self.file_name, 'r') as file:
                self.history = json.load(file)
        except FileNotFoundError:
            return None  # Return None if no saved sessions are found
        except json.JSONDecodeError:
            print("Error: Could not parse user sessions.")
            return None

    def save(self):
        print("saving")
        with open(self.file_name, 'w') as file:
            json.dump(self.history, file, indent=2)

    def get_formatted_history(self, user_id):
        messages = []
        for interaction in self.get_history(user_id):
            if "role" in interaction and interaction["role"] == "system":
                content = interaction["content"] if "content" in interaction else ''
                if 'time' in interaction:
                    content += '\n' + interaction['time']
                message = {
                    "role": "system",
                    "content" : content
                }
                messages.append(interaction)
            if 'request' in interaction:
                messages.append({"role": "user", "content": str(interaction['request'] )+ interaction['time'] if 'time' in interaction else ''})
                messages.append({"role": "assistant", "content": interaction['response']})