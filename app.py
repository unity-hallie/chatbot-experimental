from flask import Flask, request, jsonify, render_template

from chatbot.ethical_ai_chatbot import EthicalAIChatbot

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
    bot.handle_request(user_id, message)
    response = bot.chat_history.get_history(user_id)[-1]['response']
    return jsonify({'response': response})


if __name__ == "__main__":
    app.run(debug=True)
