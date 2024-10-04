import re


def is_command(request):
    """Check if the user's request resembles a command."""
    command_pattern = r'\[COMMAND: ([^\]]+)\]'  # Capture command within square brackets
    command_matches = re.findall(command_pattern, request)  # Find all commands in the user's input

    return command_matches  # Return a list of captured commands


def extract_file_name(request):
    """Extract the file name from the request."""
    # This is a naive implementation; it should be handled more robustly
    parts = request.split()
    return parts[1] if len(parts) > 1 else None


def extract_content(request):
    """Extract the content to write from the request."""
    # Assuming the content follows the file name in a 'write' command
    parts = request.split()
    return " ".join(parts[2:]) if len(parts) > 2 else None


def generate_instructions(request_analysis):
    """Generate a structured set of instructions based on the request analysis."""
    prompt = (
        f"Based on the user intent to {request_analysis['action']}, "
        f"generate a structured set of instructions for agents to execute. "
        f"Include agent names and required actions. The request details: {request_analysis}."
    )

    # Call the Generative AI model to get instructions
    instructions = generate_response_with_generative_ai(prompt)
    return instructions  # Expected to be in a structured format


def generate_response_with_generative_ai(prompt):
    """Hits the Generative AI model to produce response based on prompt."""
    # Placeholder for actual AI response logic
    # For example:
    # response = openai.ChatCompletion.create(...)
    # return response['choices'][0]['text']

    # Example return for demonstration purposes
    return [
        {"agent": "file_system_agent", "action": "read", "file": "myfile.txt"},
        {"agent": "another_agent", "action": "some_other_action"}
    ]


def dispatch_instructions(instructions, agent_manager):
    """Dispatch generated instructions to the appropriate agents and gather responses."""
    responses = []
    for instruction in instructions:
        agent_name = instruction["agent"]
        action = instruction["action"]
        file = instruction.get("file", None)
        content = instruction.get("content", None)

        agent = agent_manager.get_agent(agent_name)

        if action == "read":
            if file:
                response = agent.handle_request(f"read {file}")
            else:
                response = "Error: No file specified for reading."
        elif action == "write":
            if file and content:
                response = agent.handle_request(f"write {file} {content}")
            else:
                response = "Error: Insufficient arguments for writing."
        else:
            response = "Error: Unknown action."

        responses.append(response)

    return responses
