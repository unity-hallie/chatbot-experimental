from flask import Flask, request, jsonify, render_template
from chatbot.ethical_ai_chatbot import EthicalAIChatbot
import re

app = Flask(__name__)
bot = EthicalAIChatbot(name="Guidon")

@app.route('/')
def index():
    """Serve the front-end HTML page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle user input and return chatbot response."""
    user_id = request.json.get('user_id')
    message = request.json.get('message')
    bot.handle_request(user_id, sanitize_input(message))
    response = bot.chat_history.get_history(user_id)[-1]['response']
    return jsonify({'response': response})

@app.route('/world_state', methods=['GET'])
def get_world_state():
    """Return the current world state."""
    state = bot.world_states[0].state  # Assuming you're interested in the first world state
    return jsonify(state)


@app.route('/chat_history', methods=['GET'])
def chat_history():
    user_id = request.args.get('user_id')
    history = bot.chat_history.format_chat_history(user_id)  # Adjust this call as per your chat history structure
    return jsonify(history)

@app.route('/files', methods=['GET'])
def get_files():
    """Return the current files in the user directory."""
    user_directory = '.'  # You can specify a different directory if needed
    directory_tree = bot.file_system_agent.get_directory_tree(user_directory, full=True)
    return jsonify(directory_tree)

@app.route('/user_directory', methods=['GET'])
def get_user_directory():
    """Return the user's directory information."""
    user_directory = '.'  # Specify the user's directory or path here
    directory_tree = bot.file_system_agent.get_directory_tree(user_directory, full=True)
    return jsonify(directory_tree)



def sanitize_input(user_input):
    # Step 1: Handle encoding issues
    try:
        sanitized = user_input.encode('utf-8').decode('utf-8')
    except UnicodeDecodeError:
        return ""  # Invalid input handles

    # Step 2: Remove script tags and strip unwanted characters
    sanitized = re.sub(r'<[^>]*>', '', sanitized)  # Strip out any HTML
    sanitized = re.sub(r'[^a-zA-Z0-9\s.,!?\'\"-]', '', sanitized)  # Only allow certain characters

    # Step 3: Limit input length
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


if __name__ == "__main__":
    app.run(debug=True)

import re
