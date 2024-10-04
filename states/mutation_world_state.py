import json
import traceback

import openai
from datetime import datetime


class MutationWorldState:
    def __init__(self, emotional_state_handler, file_name='world_state.json', custom_instructions="",
                 model_name='gpt-4o-mini'):
        self.emotional_state_handler = emotional_state_handler
        self.custom_instructions = custom_instructions
        self.model_name = model_name
        self.state = {
            'directory_tree': '',
            'model': model_name,
            'custom_instructions': custom_instructions,
            'ethic_update_interval': 10,
            "interaction_count": 0,
            'last_interaction_time': '',
            'user': {},
            'user_emotional_state': 'neutral',
            'world_description': '',
        }
        self.file_name = file_name
        self.load_state()

    def load_state(self):
        try:
            with open(self.file_name, 'r') as file:
                proposed_state = json.load(file)
                for k, v in proposed_state.items():
                    self.state[k] = v
        except FileNotFoundError:
            self.state = {}  # Initialize with empty or default state
        except json.JSONDecodeError:
            print("Error: Could not parse world state.")

    def save_state(self):
        try:
            with open(self.file_name, 'w') as file:
                json.dump(self.state, file, indent=2)
        except Exception as e:
            print(f"Error saving world state: {str(e)}")


    def update_interaction(self):
        interaction_count = self.state['interaction_count'] \
            if ('interaction_count' in self.state
                and isinstance(self.state['interaction_count'], int)) \
            else 0
        self.state['interaction_count'] = interaction_count + 1
        self.state['last_interaction_time'] = datetime.now().isoformat()

    def update_world_state(self, user_id, chat_history):
        """Update the world state with input states."""

        # Determine the appropriate mutation based on chat history
        mutations = self.generate_mutation_from_interactions(chat_history)
        self.apply_mutation(mutations)
        self.update_interaction()
        self.save_state()

    def generate_mutation_from_interactions(self, chat_history):
        """Generate mutations based on recent interactions."""
        prompt = self.create_mutation_prompt(chat_history)
        mutations = '{}'
        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system",
                     "content": "You are an AI tasked with proposing mutations to an AI world state."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
            )
            # Extract and decode the mutation JSON from the response
            mutations = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            return json.loads(mutations)  # Convert to JSON
        except Exception as e:
            print(f"Error generating mutations: {str(e)}")
            print(mutations)
            return {}

    def create_mutation_prompt(self, chat_history, special_instructions=""):
        """Create a prompt to suggest mutations based on user interactions."""
        recent_history = chat_history[-5:]
        formatted_history = "\n".join([
            f"User: {interaction['request']}\nAI: {interaction['response']}"
            for interaction in recent_history
        ])

        prompt = (
            f"{special_instructions}\n"
            f"{self.custom_instructions}"
            f"Based on the following recent interactions, please suggest mutations to the world state to bring it in line in the following format:\n"
            "{{ \"key_name\": \"new_value\" } for setting a value or:\n"
            r'{ "key_name": {{ \"action": "+/-", "value" : "amount" }} for addition or subtraction of numbers or:\n'
            f"{{ \"list_name\": {{ \"action\": \"add/remove\", \"value\": \"item\" }} }}\n\n"
            f"{{ \"map_name\": {{ \"action\": \"add/remove\", \"value\": \"item\", \"key\": \"item_key\", \"value\" : \"item_value\" }} }}\n\n"
            f"{formatted_history}\n\n"
            "For example, a response could be: { \"user_emotional_state\": \"happy\" } or "
            "{ \"some_list\": { \"action\": \"add\", \"value\": \"new_item\" } } or "
            "{ \"total\": { \"action\":  \"+\", \"value\" : 1 } \n"
            "Return the mutations as a JSON object. Please double check to make sure the types of the variables being mutated are consistent. Use no more than 200 characters."
        )

        return prompt

    def apply_mutation(self, mutation):
        """Apply single-key-value changes or list modifications."""
        for key, value in mutation.items():
            targetExists = key in self.state
            targetValue = self.state[key] if targetExists else None
            if isinstance(value, dict) and "action" in value:
                if value["action"] == "+":
                    if not isinstance(targetValue, (int, float)):
                        targetValue = 0
                    self.state[key] = targetValue + value["value"]
                if value["action"] == "-":
                    if not isinstance(targetValue, (int, float)):
                        targetValue = 0
                    self.state[key] = targetValue - value["value"]
                if value["action"] == "addYea":
                    # Assuming it's a list in the state
                    if not targetExists:
                        targetValue = {} if "key" in value else []
                    if isinstance(targetValue, list):
                        targetValue.append(value["value"])  # Add item to the list
                        self.state[key] = targetValue
                    elif isinstance(targetValue, dict) and "key" in value:
                        targetValue[value["key"]] = value["value"]
                        self.state[key] = targetValue
                elif value["action"] == "remove":
                    if key in self.state and value["value"] in self.state[key]:
                        self.state[key].remove(value["value"])  # Remove item from the list
            else:
                self.state[key] = value  # Set or update a single key-value


# mutation_set_value = {
#     "key_name": "new_value"  # Directly set a value for a key
# }
#
# # Add an item to a list
# mutation_add_item = {
#     "list_name": {
#         "action": "add",
#         "value": "new_item"
#     }
# }
#
# # Remove an item from a list
# mutation_remove_item = {
#     "list_name": {
#         "action": "remove",
#         "value": "item_to_remove"
#     }
# }
