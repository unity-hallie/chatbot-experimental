import json
import traceback

import openai
from datetime import datetime

MUTATION_TYPE_DEF = '''// Define the action type with specific string literals
type Action = 'add' | 'remove' | 'update' | 'set' | '+' | '-';

// Create a base interface for Mutation
interface BaseMutation {
    key_name: string; // The key to be mutated
    action: Action; // Action must be one of the defined Action types
}

// Define your Mutations based on the action
type Mutation =
    | (BaseMutation & { action: '+'; value: number }) // If action is '+', value is a number
    | (BaseMutation & { action: '-'; value: number }) // If action is '-', value is a number
    | (BaseMutation & { action: 'add' | 'remove'; value: string }) // 'add' or 'remove', value is a string
    | (BaseMutation & { action: 'update' | 'set'; value: any }); // 'update' or 'set', value can be any

// Example of using the defined Mutation type
const addMutation: Mutation = {
    key_name: "user_engagement",
    action: '+',
    value: 5 // Must be a number
};

const removeMutation: Mutation = {
    key_name: "user_items",
    action: 'remove',
    value: "itemID123" // Must be a string
};

const updateMutation: Mutation = {
    key_name: "user_feedback",
    action: 'update',
    value: { text: "Great!" } // Can be any type here
};'''

class MutationWorldState:
    def __init__(self,
                 emotional_state_handler,
                 update_frequency=1,
                 tokens_per_second=1,
                 update_size=100,
                 file_name='world_state.json',
                 custom_instructions="",
                 model_name='gpt-4o-mini'):
        self.update_size = update_size
        self.token_bank = 0
        self.last_token_cost = self.update_size
        self.tokens_per_second = tokens_per_second
        self.emotional_state_handler = emotional_state_handler
        self.custom_instructions = custom_instructions
        self.model_name = model_name
        self.update_frequency = update_frequency
        self.interaction_count = 0
        self.last_update = datetime.now()
        self.state = {
            'directory_tree': '',
            'model': model_name,
            'custom_instructions': custom_instructions,
            'ethic_update_interval': 10,
            'last_interaction_time': '',
            'user': {},
            'user_emotional_state': 'neutral',
            'world_description': '',
        }
        self.file_name = file_name
        self.load_state()
        self.load_mutations()

    def load_state(self):
        try:
            with open(f'./states/{self.file_name}', 'r') as file:
                proposed_state = json.load(file)
                for k, v in proposed_state.items():
                    self.state[k] = v
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
        self.save_mutations()

    def load_mutations(self):
        try:
            with open(f'./states/mut_{self.file_name}', 'r') as file:
                self.mutations_list = json.load(file)
        except FileNotFoundError:
            self.mutations_list = []  # Initialize with empty or default state
        except json.JSONDecodeError:
            print("Error: Could not parse mutations.")

    def save_mutations(self):
        try:
            with open(f'./states/mut_{self.file_name}', 'w') as file:
                json.dump(self.mutations_list, file, indent=2)
        except Exception as e:
            print(f"Error saving world state: {str(e)}")

    def update_interaction(self):
        self.interaction_count += 1

    def update_world_state(self, user_id, chat_history, last_request):
        """Update the world state with input states."""
        # Determine the appropriate mutation based on chat history
        delta_time = datetime.now() - self.last_update
        self.token_bank += ( delta_time.total_seconds() * self.tokens_per_second)
        print(f"{self.file_name} bank : {self.token_bank} / {self.last_token_cost}")
        if self.token_bank > self.last_token_cost:
            self.last_update = datetime.now()
            mutations = self.generate_mutation_from_interactions(chat_history, last_request)
            for mutation in mutations:
                self.apply_mutation(mutation)
            self.update_interaction()
            self.save_state()
            return True
        return False

    def generate_mutation_from_interactions(self, chat_history, last_request):
        """Generate mutations based on recent interactions."""
        prompt = self.create_mutation_prompt(chat_history, last_request)
        mutations = '{}'
        try:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system",
                     "content": "You are an AI tasked with proposing mutations to an AI world state."},
                    {"role": "user", "content": last_request},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.update_size,
            )
            # Extract and decode the mutation JSON from the response
            mutations = response.choices[0].message.content.strip().replace('```json', '').replace('```', '')
            self.last_token_cost = response.usage.total_tokens
            self.token_bank -= self.last_token_cost
            print(json.loads(mutations))
            return json.loads(mutations)  # Convert to JSON
        except Exception as e:
            print(f"Error generating mutations: {str(e)}")
            print(mutations)
            return {}

    def create_mutation_prompt(self, chat_history, special_instructions=""):
        history_length = min(len(chat_history) - 1, 5)
        """Create a prompt to suggest mutations based on user interactions."""

        recent_history = chat_history[-history_length:]
        formatted_history = json.dumps(recent_history)

        prompt = (
            f"{special_instructions}\n"
            f"{self.custom_instructions}"
            "The previous world state is"
            f"{json.dumps(self.state)}"
            f"The current time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"
            f"Based on the following recent interactions, please suggest mutations to the world state"
            f" to bring it in line in the following history:\n"
            f"{formatted_history}"
            f"\n"
            f"Return the mutations as a list of JSON of type Mutation. Please double check "        
            f"to make sure the types of the variables being mutated are consistent. "
            f"Use no more than {self.update_size} tokens."
            "You should return ONLY a json list that conforms to type Mutation[] as in the def below"
            f"{MUTATION_TYPE_DEF}"

        )

        return prompt

    def apply_mutation(self, mutation):
        """
        Apply a mutation based on the provided mutation structure.
        The mutation must contain the 'action' and 'value' keys with appropriate types.
        """
        action = mutation.get('action')
        value = mutation.get('value')
        key = mutation.get('key_name')
        target_exists = key in self.state
        target_value = self.state[key] if target_exists else None
        errors = []
        if action in {'+', '-'}:
            if isinstance(value, (int, float)):
                if not isinstance(target_value, (int, float)):
                    errors.append(f"Error: The target value for '+' or '-' is not a number: {target_value}")
                else:
                    self.state[key] += value if action == '+' else -value
            else:
                errors.append(
                    "Error: The value for '+' or '-' must be a number." + json.dumps(mutation, indent=2))

        elif action in {'add', 'remove'}:
            if isinstance(value, str):
                if action == 'add':
                    if target_exists and not isinstance(target_value, list):
                        self.state[key] = [target_value]
                    elif key not in self.state:
                        self.state[key] = []
                    # Provide logic for how to add items, e.g., to a list or a dictionary
                    self.state[key].append(value)  # Adjust to where you want to add
                elif action == 'remove':
                    # Example logic for removal
                    if key in self.state:
                        del self.state[key]
            else:
                errors.append("Error: The value for 'add' or 'remove' must be a string." + json.dumps(mutation, indent=2))

        elif action in {'update', 'set'}:
            # For update/set actions, it's contextual based on key_name
            key_name = mutation.get('key_name')
            if key_name:
                self.state[key_name] = value  # Update or set the value directly
            else:
                errors.append("Error: Invalid key name for update/set action." + json.dumps(mutation, indent=2))
        else:
            errors.append("Error: Unrecognized action." + json.dumps(mutation, indent=2))

        if errors:
            mutation.update({'errors': errors})
        self.mutations_list.append(mutation)
        self.state["recent_mutation_errors"] = errors


# def apply_mutation(state, mutations):
#     """Apply single-key-value changes or list modifications."""
#     for key, value in mutations.items():
#         targetExists = key in state
#         targetValue = state[key] if targetExists else None
#         if not isinstance(value, dict):
#             state[key] = value
#         elif "action" not in value:
#             if key not in state:
#                 state[key] = {}
#             apply_mutation(state[key], value)
#         else:
#             if value["action"] == "+":
#                 valueValue = value["value"]
#                 if not isinstance(targetValue, (int, float)):
#                     targetValue = 0
#                 if not isinstance(valueValue, (int, float)):
#                     targetValue = int(targetValue)
#
#                 state[key] = targetValue + value["value"]
#
#             if value["action"] == "-":
#                 if not isinstance(targetValue, (int, float)):
#                     targetValue = 0
#                 state[key] = targetValue - value["value"]
#             if value["action"] == "addYea":
#                 # Assuming it's a list in the state
#                 if not targetExists:
#                     targetValue = {} if "key" in value else []
#                 if isinstance(targetValue, list):
#                     targetValue.append(value["value"])  # Add item to the list
#                     state[key] = targetValue
#                 elif isinstance(targetValue, dict) and "key" in value:
#                     targetValue[value["key"]] = value["value"]
#                     state[key] = targetValue
#             elif value["action"] == "remove":
#                 if key in state and value["value"] in state[key]:
#                     state[key].remove(value["value"])  # Remove item from the list
#
