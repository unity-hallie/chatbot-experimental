import json
import openai
from datetime import datetime

from chatbot.emotional_state_handler import EmotionalStateHandler


class WorldState:
    def __init__(self, emotional_state_handler: EmotionalStateHandler, file_name='world_state.json',
                 custom_instructions="", model='gpt-4o-mini'):
        self.emotional_state_handler = emotional_state_handler
        self.update_frequency = 1
        self.model_name = model
        self.file_name = file_name
        self.custom_instructions = custom_instructions
        self.state = {
            'directory_tree': '',
            'model': self.model_name,
            'custom_instructions': self.custom_instructions,
            'ethic_update_interval': 10,
            "interaction_count": 0,
            'last_interaction_time': None,
            'user_engagement_level': 0,
            'user': {},
            'user_emotional_state': 'neutral',
            'world_description': '',
            'shell_command_suggestions': [],
        }

    def load_state(self):
        try:
            with open(f'./states/{self.file_name}', 'r') as file:
                proposed_state = json.load(file)
                self.state.update(proposed_state)
        except FileNotFoundError:
            self.state = {}  # Initialize with empty or default state
        except json.JSONDecodeError:
            print("Error: Could not parse world state.")

    def save_state(self):
        try:
            with open(f'./states/{self.file_name}', 'w') as file:
                json.dump(self.state, file, indent=2)
        except Exception as e:
            print(f"Error saving world state: {str(e)}")

    def update_interaction(self):
        self.state['interaction_count'] += 1
        self.state['last_interaction_time'] = datetime.now().isoformat()

    def generate_world_state_from_interactions(self, chat_history):
        """Generate advanced aspects of the world state dynamically based on user interactions."""
        prompt = self.create_generation_prompt(chat_history)
        generated_state = ''
        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.get_src()},
                    {"role": "system", "content": prompt},
                    {"role": "system", "content": self.custom_instructions}
                ],
                max_tokens=1024,
            )
            generated_state = response.choices[0].message.content.strip()
            generated_state = generated_state.replace('```json', '')
            generated_state = generated_state.replace('```', '')
            return json.loads(generated_state)
        except Exception as e:
            print(generated_state)
            print(f"Failed to generate world state: {str(e)}")
            return {}

    def create_generation_prompt(self, chat_history):
        """Create a prompt based on previous user interactions for generating world state."""
        chat_len = len(chat_history)
        history = chat_history if chat_len < 5 else chat_history[-5:]
        return f"Based on the following interactions, suggest an updated world state ${json.dumps(history)}\nReturn a JSON object with less than 1000 characters."

    def get_src(self):
        """Retrieve the chatbot's own source code."""
        try:
            with open(__file__, 'r') as file:
                src_code = file.read()
            return src_code
        except Exception as e:
            return f"An error occurred while fetching source code: {str(e)}"

    def update_world_state(self, user_id, chat_history):
        """Update and generate parts of the world state based on user interactions."""
        self.update_interaction()

        self.state['user_emotional_state'] = self.emotional_state_handler.get_emotional_state(chat_history[-5:0])
        if self.state['interaction_count'] % self.update_frequency == 0:  # Generate after every 5 interactions.
            generated_values = self.generate_world_state_from_interactions(chat_history)
            self.state.update(generated_values)  # Update with generated values
            self.save_state()

    def set_directory_tree(self, tree):
        self.state['directory_tree'] = tree
        self.save_state()
