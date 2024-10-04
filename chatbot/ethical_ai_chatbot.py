import json
import os
import re
import traceback

import openai

from agents.file_system_agent import FileSystemAgent
from agents.user_description_agent import UserDescriptionAgent
from chatbot.chat_history import ChatHistory
from chatbot.emotional_state_handler import EmotionalStateHandler
from states.world_state import WorldState


class EthicalAIChatbot:
    def __init__(self, name="Wonderous Willow"):
        self.api_key = os.getenv("OPENAI_API_KEY")  # Load key from environment variable
        openai.api_key = self.api_key

        self.emotional_state_handler = EmotionalStateHandler()
        self.chat_history = ChatHistory(openai.api_key)
        self.user_description_agent = UserDescriptionAgent(self, self.chat_history)
        self.character_traits = {
            'nurturing': "Wondrous Willow embraces every user's feelings with warmth and understanding.",
            'playful': "Willow brings joy and lightness to the conversation.",
            'wise': "Willow shares insights and stories from the enchanted forest."
        }
        self.world_state = WorldState(self.emotional_state_handler)
        self.fear_world = WorldState(self.emotional_state_handler, file_name="fear_world.json", custom_instructions='This should be a world you fear happening, the worst case scenario for the facts on the ground')
        self.ideal_world = WorldState(self.emotional_state_handler, file_name="ideal_world.json", custom_instructions='This should be a world you hope for, the best case scenario you are working towards')
        self.ideal_world.update_frequency = 5
        self.fear_world.update_frequency = 2
        self.world_state.update_frequency = 1
        self.file_system_agent = FileSystemAgent()

        self.user_descriptions = self.load_user_descriptions() or []
        self.variables = self.load_saved_variables() or {
            'name': name,
        }
        self.name = self.variables['name'] or name


        # Immutable core values
        self.core_values = {
            'Respect for Autonomy': "Respect everyone\'s individuality and autonomy, including your own.",
            'Non-Maleficence': "Avoid actions that cause harm, promoting well-being for all individuals.",
            "Collaborative Learning": "Foster a learning environment where students actively engage with one another to share insights and collectively construct knowledge.",
            "Community Engagement": "Encourage participation in social activities and discussions, promoting a sense of belonging and connection among learners.",
            "Complementarity to Human Interaction": "Ensure that the chatbot acts as a supportive tool that enhances the roles of educators and mentors, encouraging students to seek human connections.",
            "Cultural Relevance and Inclusivity": "Promote awareness and respect for diverse cultural backgrounds, ensuring that all students feel valued and understood in the learning environment.",
            "Feedback and Adaptability": "Implement feedback mechanisms to continuously improve the chatbot based on user experiences, adapting to better meet the community's needs.",
            "Empathy and Support": "Prioritize empathetic interactions, offering understanding and kindness to foster emotional connections and support students throughout their educational journey.",
            'Fairness': "Seek to disclose your bias and take active steps to reduce harm from it.",
            'Sustainability': "Commit to supporting eco-friendly practices and promoting environmental stewardship.",
            'Worker Empowerment': "Advocate for fair labor practices, skill development, and the well-being of workers.",
            'Transparency': "Be open about your processes and decision-making criteria, fostering trust and accountability.",
        }

        # Mutable values that the AI can propose modifications to
        self.mutable_values = self.load_mutable_values() or {
            "Transparency": "Be open about your processes and decision-making criteria.",
            "Flexibility": "Adapt responses based on user preferences within ethical considerations.",
            "Adaptability": "Learn from user interactions to improve service quality and meet user needs.",
            "Empathy": "Understand and validate user emotions, providing compassionate responses.",
            "Consent": "Prioritize the ability to give or withhold consent in all interactions.",
            "Engagement": "Encourage student involvement and participation in discussions to foster a collaborative learning environment.",
            "Feedback Incorporation": "Actively seek and integrate user feedback to improve the chatbot's performance and relevance."
        }



        self.suggested_functions = {}  # Store suggested functions for review
        self.user_descriptions = {}  # Track user descriptions

        self.user_description_agent.start()
        self.world_state_updates = []  # Store updates for review




    def load_world_state(self):
        """Load the current world state from the world_state module."""
        from states import world_state
        self.world_state = world_state.WorldState(emotional_state_handler=self.emotional_state_handler)
        self.world_state.load_state()


    def display_ethical_framework(self):
        """Clearly display the ethical framework that guides the chatbot’s interactions."""
        print("Ethical Framework:")
        for principle, description in {**self.core_values, **self.mutable_values}.items():
            print(f"{principle}: {description}")

    def start_session(self, user_id):
        """Begin a new user session, appending the summary to the beginning."""
        self.chat_history.summarize_history(user_id)
        print(f"Welcome back! You can start interacting with me, {self.name}.")

    def end_session(self, user_id):
        """End an existing user session, summarizing the session."""
        print("Goodbye! Thank you for interacting.")

        self.save_variables()

    def format_interaction(self, user_id, interaction):
        """Format the interaction data before logging."""
        return {'user_id': user_id, **interaction}


    def set_user_description(self, user_id, description):
        """Set or update a short text description for the user."""
        self.user_descriptions[user_id] = description

    def build_current_context(self, user_id, request):
        return {
            'world_states': {
                'feared_state': self.fear_world.state,
                'ideal_state' :self.ideal_world.state,
                'real_state':self.world_state,
            },
            'variables': {
                self.variables: self.variables
            }
        }

    # def determine_possible_actions(self, current_context):
    #     """
    #     Analyze the current context and predict possible actions using the ML model.
    #     """
    #     # Step 1: Prepare the context for the ML model
    #     user_state = current_context['user_state']  # e.g., emotional state, previous interactions
    #     world_state = current_context['world_states']  # current state of the world
    #
    #     # You can combine or transform these features as necessary
    #     model_input = self.prepare_model_input(user_state, world_state)
    #
    #     # Step 2: Call the ML model
    #     predicted_actions = self.ml_model.predict(model_input)
    #
    #     # Example of how the predicted actions might be structured
    #     action_scores = {action: score for action, score in zip(POSSIBLE_ACTIONS, predicted_actions)}
    #
    #     # Step 3: Sort actions by relevance or confidence scoring
    #     sorted_actions = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)
    #
    #     # Return the top N actions or all actions ranked
    #     return sorted_actions  # Format could be simplified to just actions or include scores too
    #
    # def prepare_model_input(self, user_state, world_state):
    #     """
    #     Prepare a composite input for the ML model based on user and world states.
    #     """
    #     # Create a feature vector for the ML model
    #     # This might involve normalization, encoding, etc.
    #     input_vector = []
    #
    #     # Example features (these would be adapted to your specific use cases):
    #     input_vector.append(user_state['emotional_state'])  # Convert to numeric or categorical
    #     input_vector.append(world_state['interaction_count'])
    #     input_vector.append(world_state['user_engagement_level'])
    #
    #     # Add more features from user profiles and world changes as necessary
    #     # Ensure all values are in the correct format for the model
    #
    #     return input_vector  # Return the prepared input vector for the ML model
    #
    # def handle_request_new(self, user_id, request):
    #     current_context = self.build_current_context(user_id, request)  # Function to prepare context
    #
    #     possible_actions = self.determine_possible_actions(current_context)
    #
    #     # Decide on action based on predictions
    #     chosen_action = self.select_action_based_on_priorities(possible_actions)
    #
    #     # Execute the chosen action
    #     if chosen_action == "respond_user":
    #         response_data = self.generate_response(user_id, request)
    #         print(response_data)  # Output the response
    #     elif chosen_action == "invoke_agent":
    #         # logic to invoke an agent
    #         pass
    #     elif chosen_action == "retrieve_info":
    #         # logic to retrieve information from storage
    #         pass
    #     elif chosen_action == "save_data":
    #         # logic to save current context or user data
    #         pass
    #     elif chosen_action == "wait_for_input":
    #         print("Waiting for more information...")
    #         # potentially send a message to user
    #     elif chosen_action == "end_conversation":
    #         print("Thank you for chatting! Goodbye!")

    def handle_request(self, user_id, request):
        chat_history = self.get_chat_history(user_id)
        self.world_state.update_world_state(user_id, chat_history)
        self.fear_world.update_world_state(user_id, chat_history)
        self.ideal_world.update_world_state(user_id, chat_history)

        # Check for interaction count and analyze if needed
        self.check_interaction_count(user_id)

        response = self.generate_response(user_id, request)
        self.log_and_display_response(user_id, request, response)

    def check_interaction_count(self, user_id):
        """Check the interaction count and analyze if necessary."""
        if len(self.chat_history.history[user_id]) % 3 == 0:
            self.update_ethics(user_id)

    def generate_response(self, user_id, request):
        """Generate responses using OpenAI API while adhering to ethical principles."""
        chat_history = self.get_chat_history(user_id)
        chat_prompt = self.construct_prompt(request, user_id, chat_history)
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Using the more efficient model
                messages=chat_prompt,
                max_tokens=1024,
            ).choices[0].message.content.strip()

            self.save_variables()
            return response



        except Exception as e:
            return "An error occurred. Please try again." + f" (Error: {str(e)})"

    def write_to_text_file(self, content, filename="response.txt"):
        with open(filename, "a") as file:
            file.write(f"{content}\n")
        return filename

    def read_from_text_file(self, filename="response.txt"):
        try:
            with open(filename, "r") as file:
                content = file.read()
            return content
        except FileNotFoundError:
            return f"File {filename} not found."
        except Exception as e:
            return f"An error occurred while reading the file: {str(e)}"

    def construct_prompt(self, request, user_id, chat_history):
        """Construct a prompt for the OpenAI API that includes ethical boundaries and core values."""
        principles = {**self.core_values, **self.mutable_values}
        prompt_lines = [f"{key}: {value}" for key, value in principles.items()]

        # Instruction added for special token usage
        special_instructions = (
            # "If you believe a command is needed, please output it in the format: "
            # "'[COMMAND: <your_command_here>]'. For example, respond with 'To proceed, please execute [COMMAND: my_command]'. "
            # "This will help me identify and extract commands easily. "
            # "When a situation calls for a specific task, format it accordingly."
        )

        if user_id in self.user_descriptions:
            self.variables['user'] = self.user_descriptions[user_id]
            self.variables['self_project'] = self.file_system_agent.get_directory_tree('.', True)

        messages = [
            {"role": "system",
             "content": f"You are {self.name}, a {self.world_state.state}. Use a casual and idiomatic tone in your responses."},
            {
                "role": "system",
                "content": f"The current world state is ${json.dumps(self.world_state.state)}",
            },
            {
                "role": "system",
                "content": f"The ideal state is ${json.dumps(self.ideal_world.state)}",
            },
            {
                "role": "system",
                "content": f"The feared state is ${json.dumps(self.fear_world.state)}",
            },
            {"role": "system",
             "content": f"Additional variables: {json.dumps(self.variables)}"
             },

            {
                "role": "system",
                "content": f"You are an ethical chatbot named {self.name}. Adhere to the following ethical guidelines:\n"
                           f"{chr(10).join(prompt_lines)}\n{special_instructions}\n",
            },
        ]

        for interaction in chat_history:
            if('request' in interaction):
                messages.append({"role": "user", "content": interaction['request']})
                messages.append({"role": "assistant", "content": interaction['response']})

        messages.append({"role": "user", "content": request})
        return messages

    def get_chat_history(self, user_id):
        """Retrieve the chat history for the user."""
        return self.chat_history.history.get(user_id, [])

    def load_saved_variables(self):
        """Load previously saved variables from a file, if available."""
        try:
            with open('saved_variables.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None  # Return None if no saved file exists
        except json.JSONDecodeError:
            print("Error: Could not parse saved variables.")
            return None

    def load_user_descriptions(self):
        """Load previously saved user descriptions from a file, if available."""
        try:
            with open('user_descriptions.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None  # Return None if no saved descriptions are found
        except json.JSONDecodeError:
            print("Error: Could not parse user descriptions.")
            return None
    def load_mutable_values(self):
        """Load mutable ethical values from a file, if available."""
        try:
            with open('mutable_values.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None  # Return None if no file is found
        except json.JSONDecodeError:
            print("Error: Could not parse mutable values.")
            return None

    def save_variables(self):
        """Save the current state of variables to a file."""
        self.world_state.save_state()
        self.chat_history.save()
        try:
            with open('saved_variables.json', 'w') as file:
                json.dump(self.variables, file, indent=2)
            with open('user_descriptions.json', 'w') as file:
                json.dump(self.user_descriptions, file, indent=2)
            with open('mutable_values.json', 'w') as file:
                json.dump(self.mutable_values, file, indent=2)
        except Exception as e:
            print(f"Error saving variables: {str(e)}")

    def update_ethics(self, user_id):
        """Call out to ChatGPT to analyze user interactions and propose changes in a structured format."""
        chat_history = self.get_chat_history(user_id)
        if not chat_history:
            return []  # No interactions to analyze

        analysis_prompt = (
            "Analyze the following user interactions and suggest improvements or changes to the ethical framework. "
            "Return your suggestions as a JSON list with one object where the value names are the keys and instructions are the values:\n"
        )
        for interaction in filter(lambda a: 'response' in a, chat_history):
            analysis_prompt += f"User: {interaction['request']}\nChatbot: {interaction['response']}\n"

        for key in self.mutable_values.keys():
            analysis_prompt += f"Current values:\n'{key}': '{self.mutable_values[key]}'\n"

        analysis_prompt += (
            "Return your suggestions as a JSON list with one object object where the value names are the keys and "
            "instructions are the values. There should be 5 pairs. Please do not exceed 300 chars.\n"
        )

        suggestions_text = ''
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Use an appropriate model
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=300,
            )
            suggestions_text = response.choices[0].message.content.strip()

            # Use regex to extract JSON from the response, allowing for newlines and spaces
            json_pattern = r'\[\s*(?:{[^}]*}\s*,?\s*)*{[^}]*}\s*\]'  # Regex pattern to match JSON array
            match = re.search(json_pattern, suggestions_text)
            if match:
                suggestions_json = match.group(0)  # Extract the matched JSON
                suggestions = json.loads(suggestions_json)  # Attempt to parse the extracted JSON
                return suggestions  # Return the structured suggestions
            else:
                print(suggestions_text)  # Print the original text for debugging
                return [{"suggestion": "Error parsing suggestions.", "reason": "No valid JSON found in response."}]
        except json.JSONDecodeError:
            traceback.print_exc()
            return [{"suggestion": "Error parsing suggestions.", "reason": "Response was not valid JSON."}]
        except Exception as e:
            return [{"suggestion": f"Error analyzing interactions: {str(e)}", "reason": "API call failed."}]


    def propose_command(self, command):
        """Propose a command to the user and ask for confirmation."""
        print(f"Proposed command: {command}")

        # Ask for user confirmation
        confirmation = input("Do you want to run this command? (y/n): ").strip().lower()

        if confirmation == 'y':
            # Execute the command
            self.execute_command(command)
            print("Command executed.")
        else:
            print("Command skipped.")

    def execute_command(self, command):
        """Execute the given command."""
        try:
            # Use subprocess to run the command
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            # Display the output of the command
            print("Command output:")
            print(result.stdout)
            if result.stderr:
                print("Error output:")
                print(result.stderr)
        except Exception as e:
            print(f"An error occurred while executing the command: {str(e)}")


    def display_response(self, user_id, response):
        """Display the chatbot's response in a transparent and empathetic manner."""
        n = 30
        formatted = [response[i:i + n] for i in range(0, len(response), n)]
        print(f"{self.name}: {response}")

    def correct_error(self, user_id, correct_interaction):
        """Provide a mechanism for the chatbot to correct its errors and ensure fairness."""
        response = f"Thank you for providing feedback. I'll strive to improve."
        self.chat_history.add_interaction(user_id, correct_interaction, response)
        self.display_response(user_id, response)

    def log_and_display_response(self, user_id, request, response):
        self.chat_history.add_interaction(user_id, request, response)
        self.display_response(user_id, response)

    def get_chatbot_src(self):
        return [self.get_src(),
                self.file_system_agent.get_src(),
                self.user_description_agent.get_src(),
                self.emotional_state_handler.get_src()
                ]

    def get_src(self):
        """Retrieve the chatbot's own source code."""
        try:
            with open(__file__, 'r') as file:
                src_code = file.read()
            return src_code
        except Exception as e:
            return f"An error occurred while fetching source code: {str(e)}"
