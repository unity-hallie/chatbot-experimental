import os

from dotenv import load_dotenv
from chatbot.ethical_ai_chatbot import EthicalAIChatbot
from flask import Flask, jsonify, request
from threading import Thread

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)
bot = EthicalAIChatbot(name="Eleanor")

@app.route('/')
def index():
    """Serve the front-end HTML page."""
    return '<h1>Welcome to the Ethical AI Chatbot!</h1>'

@app.route('/chat', methods=['POST'])
def chat():
    """Handle user input and return chatbot response."""
    user_id = request.json.get('user_id')
    message = request.json.get('message')
    bot.handle_request(user_id, message)
    response = bot.chat_history.get_history(user_id)[-1]['response']
    return jsonify({'response': response})

@app.route('/world_state', methods=['GET'])
def get_world_state():
    """Return the current world state."""
    state = bot.world_states[0].state  # Assuming you’re interested in the first world state
    return jsonify(state)

@app.route('/chat_history', methods=['GET'])
def chat_history():
    """Return the user's chat history."""
    user_id = request.args.get('user_id')
    history = bot.chat_history.format_chat_history(user_id)  # Adjust this call as per your chat history structure
    return jsonify(history)

@app.route('/files', methods=['GET'])
def get_files():
    """Return the current files in the user directory."""
    user_directory = '.'  # You can specify a different directory if needed
    directory_tree = bot.file_system_agent.get_directory_tree(user_directory, full=True)
    return jsonify(directory_tree)

def run_flask_app():
    """Run the Flask app."""
    app.run(debug=True)

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")  # Ensure you're loading from the environment variable
    bot.start_session("hallie")
    # Start Flask app in a separate thread
    #thread = Thread(target=run_flask_app)
    #thread.start()

    print("You can start interacting with the chatbot (type 'exit' to end).")

    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            bot.end_session("hallie")
            break
        bot.handle_request("hallie", user_input)