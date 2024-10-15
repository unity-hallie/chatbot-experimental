import json
import os
import re
import subprocess
import traceback

import openai

from agents.file_system_agent import FileSystemAgent
from agents.user_description_agent import UserDescriptionAgent
from chatbot.chat_history import ChatHistory
from chatbot.emotional_state_handler import EmotionalStateHandler
from states.mutation_world_state import MutationWorldState


class EthicalAIChatbot:
    def __init__(self, name="Wonderous Willow"):
        self.api_key = os.getenv("OPENAI_API_KEY")  # Load key from environment variable
        openai.api_key = self.api_key
        self.shared_files = []
        self.emotional_state_handler = EmotionalStateHandler()
        self.chat_history = ChatHistory(openai.api_key)
        # self.user_description_agent = UserDescriptionAgent(self, self.chat_history)

        self.world_states = [
            MutationWorldState(
                self.emotional_state_handler,
                tokens_per_second=1,
                update_size=1000,
                file_name="incremental_world_state.json",
                custom_instructions="This is the stable view of the current world state. It should represent the world as it actually is generally."),
            MutationWorldState(
                self.emotional_state_handler,
                tokens_per_second=500,
                update_size=500,
                max_history_length=1,
                file_name="topic_state.json",
                custom_instructions="This is the view of the topics being discussed. "
                                    " It should reflect the CURRENT conversational topics. If something isn't being discussed, backburner it and move the currently discussed topic to the fore. Use this to keep track of different topics we may be switching between and try to keep it relatively lean."),
        ]
        # self.world_state =
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

        # self.user_description_agent.start()
        self.world_state_updates = []  # Store updates for review


    def display_ethical_framework(self):
        """Clearly display the ethical framework that guides the chatbot’s interactions."""
        print("Ethical Framework:")
        for principle, description in {**self.core_values, **self.mutable_values}.items():
            print(f"{principle}: {description}")

    def start_session(self, user_id, mode="CLI"):
        """Begin a new user session, appending the summary to the beginning."""
        self.set_user_mode(mode)
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
            'world_states': map(lambda a: a.state, self.world_states),
            'variables': {
                self.variables: self.variables
            }
        }

    def extract_commands(self, request):
        """Extract commands and associated data from a request."""
        pattern = r'```(\w+)\n(.*?)```'  # Matches commands within triple backticks
        matches = re.findall(pattern, request, re.DOTALL)
        commands = [{ 'cmd_type': cmd_type, 'data': data.strip() } for cmd_type, data in matches]
        return commands

    def handle_commands(self, user_id, request, chat_history):
        if self.user_interaction_mode == "CLI" and request.startswith('~~'):
            history = self.chat_history.get_history(user_id)
            command_results = []
            if request.startswith('~~~'):

                request_command = request[3:].strip()  # Strip '~~~'
                updated_command = self.file_system_agent.fill_in_command(user_id, request_command, openai, history)

                if '```' in updated_command:  # Check for code snippets
                    # Extract bash/PowerShell commands from the request
                    commands = self.extract_commands(updated_command)
                    for command in commands:

                        if input(f"Do you want to run the command? (y/n) {updated_command}") == 'y':
                            command_result = self.file_system_agent.execute_command(command["data"])
                            print(command_result)
                            command_results.append([command, command_result])
                        else:
                            break
                    self.chat_history.add_interaction(user_id, request, json.dumps(command_results))

            else:
                command =  request[2:].strip()  # Strip '~~'
                if input(f"Do you want to run the command? (y/n) {command}") == 'y':
                    print(command)
                    command_results = [command, self.file_system_agent.execute_command(command)]
                    self.chat_history.add_interaction(user_id, request, json.dumps(command_results))
                    self.chat_history.save()
                    print(command_results[1])
                    print(json.dumps(command_results))

            # Prepare the prompt with command and its result
            prompt = f"Executed Commands: {json.dumps(command_results)}"

            return {
                "role" : "user",
                "content" : prompt
            }
        return None

    def handle_request(self, user_id, request):
        chat_history = self.get_chat_history(user_id)
        file_prompt = self.file_system_agent.handle_request(request)

        handled_commands = self.handle_commands(user_id, request, chat_history)

        additional_messages = [file_prompt]

        if handled_commands:
            self.log_and_display_response(user_id, request, json.dumps(handled_commands))
            return

        for state in self.world_states:
            state.update_world_state(user_id, chat_history, request)

        response = self.generate_response(user_id, request, additional_messages)

        self.log_and_display_response(user_id, request, json.dumps(response))

    def set_user_mode(self, mode):
        """Sets the user interaction mode ('CLI' or 'Web')."""
        if mode in ["CLI", "Web"]:
            self.user_interaction_mode = mode




    def generate_response(self, user_id, request, additional_messages = []):
        """Generate responses using OpenAI API while adhering to ethical principles."""
        chat_history = self.get_chat_history(user_id)
        chat_prompt = self.construct_prompt(request, user_id, chat_history, additional_messages)
        self.log_full_request(chat_prompt)
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Using the more efficient model
                messages=chat_prompt,
                max_tokens=2048,
            ).choices[0].message.content.strip()

            self.save_variables()
            return response



        except Exception as e:
            return "An error occurred. Please try again." + f" (Error: {str(e)})"

    def log_full_request(self, messages):
        self.write_to_text_file(json.dumps(messages, indent=2), "messages.json", "w")

    def write_to_text_file(self, content, filename="response.txt", mode="a"):
        with open(filename, mode) as file:
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


    def construct_prompt(self, request, user_id, chat_history, additional_messages = []):
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

        messages = [
            {"role": "system",
             "content": f"You are {self.name}. Use a casual and idiomatic tone in your responses."},
            {
                "role": "system",
                "content": f"You are an ethical chatbot named {self.name}. Adhere to the following ethical guidelines:\n"
                           f"{chr(10).join(prompt_lines)}\n{special_instructions}\n",
            },
            {"role": "system",
             "content": f"Additional variables: {json.dumps(self.variables)}"
             },
        ]



        for interaction in chat_history:
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

        for world_state in self.world_states:
            messages.append({"role": "system", "content": world_state.custom_instructions + " " + json.dumps(world_state.state,indent=2)})
        messages.append({"role": "user", "content": request})

        for message in additional_messages:
            messages.append(message)

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
        self.chat_history.save()
        try:
            with open('saved_variables.json', 'w') as file:
                json.dump(self.variables, file, indent=2)
            with open('mutable_values.json', 'w') as file:
                json.dump(self.mutable_values, file, indent=2)
        except Exception as e:
            print(f"Error saving variables: {str(e)}")

    def update_ethics(self, user_id):
        """Call out to ChatGPT to analyze user interactions and propose changes in a structured format."""
        chat_history = self.chat_history.get_history(user_id)
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
            "Return your suggestions as a JSON object where the value names are the keys and "
            f"instructions are the values. (example: {json.dumps(self.mutable_values)}. There should be 8 pairs. Please do not exceed 1000 chars.\n"
        )

        suggestions_text = ''
        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",  # Use an appropriate model
                messages=[{"role": "system", "content": analysis_prompt}],
                max_tokens=300,
            )
            suggestions_text = response.choices[0].message.content.strip()
            # Use regex to extract JSON from the response, allowing for newlines and spaces
            pattern = r'```json(.*?)```'
            matches = re.findall(pattern, suggestions_text, re.DOTALL)
            match = matches[0] if len(matches) > 0 else None

            if match:
                suggestions_json = match  # Extract the matched JSON
                suggestions = json.loads(suggestions_json)  # Attempt to parse the extracted JSON
                self.mutable_values = suggestions
                print (self.mutable_values)
                self.save_variables()
            else:
                print(suggestions_text)  # Print the original text for debugging
                return [{"suggestion": "Error parsing suggestions.", "reason": "No valid JSON found in response."}]
        except json.JSONDecodeError:
            traceback.print_exc()
            print("parse error")
            return [{"suggestion": "Error parsing suggestions.", "reason": "Response was not valid JSON."}]
        except Exception as e:
            print(str(e))
            return [{"suggestion": f"Error analyzing interactions: {str(e)}", "reason": "API call failed."}]

    def display_response(self, user_id, response):
        """Display the chatbot's response in a transparent and empathetic manner."""
        n = 30
        try:
            print(f"{self.name}: {response}")
        except Exception as e:
            print(f"An error occurred ")
            print(f"{self.name}: {response.encode('utf-8')}")


    # def correct_error(self, user_id, correct_interaction):
    #     """Provide a mechanism for the chatbot to correct its errors and ensure fairness."""
    #     response = f"Thank you for providing feedback. I'll strive to improve."
    #     self.chat_history.add_interaction(user_id, correct_interaction, response)
    #     self.display_response(user_id, response)

    def log_and_display_response(self, user_id, request, response):
        self.chat_history.add_interaction(user_id, request, response)
        self.display_response(user_id, response)


    def get_src(self):
        """Retrieve the chatbot's own source code."""
        try:
            with open(__file__, 'r') as file:
                src_code = file.read()
            return src_code
        except Exception as e:
            return f"An error occurred while fetching source code: {str(e)}"
