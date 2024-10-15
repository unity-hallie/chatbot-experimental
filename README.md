# Ethical AI Chatbot

## Overview
This project implements an ethical AI chatbot named **Guidon**, designed to interact with users while adhering to ethical guidelines. The chatbot utilizes various agents to manage file systems, analyze user interactions, and maintain a history of conversations, all while providing personalized responses and support.

## Features
- Multi-agent architecture for handling different tasks, including file operations and user description updates.
- Emotional state analysis to provide empathetic responses.
- Persistent user history and descriptions for improved customization.
- File system management capabilities.
- Web interface to interact with the chatbot efficiently.
- Support for Markdown display in chat history for better formatting.

## Getting Started

### Prerequisites
- Python 3.6 or higher.
- [Node.js](https://nodejs.org/) (for the front-end part).
- [OpenAI API key](https://platform.openai.com/signup/) (required for AI functionality).

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/unity-hallie/chatbot-experimental.git
    cd chatbot-experimental
    ```

2. **Install Required Packages**:
    Make sure you have `pip` installed, then run:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**:
    Create a `.env` file in the project root directory with your OpenAI API key:
    ```plaintext
    OPENAI_API_KEY=your_api_key_here
    ```

4. **Run the Application**:
    To start the chatbot in a web interface, run:
    ```bash
    python web_service.py
    ```

5. **Access the Web Interface**:
    Open your web browser and go to:
    ```plaintext
    http://127.0.0.1:5000
    ```

### Usage
You can interact with the chatbot by typing messages in the chat box on the web interface. The chatbot is designed to handle various requests, including file operations or general inquiries.

### Known Limitations
- Currently, the **user-facing logic for file commands** related to reading and writing files is disabled to avoid inconsistencies in request handling. This functionality is planned for future integration after further testing and refinement.

### Example Interactions
- User: "Can you help me with my Kaltura updates?"
- Chatbot: "Of course! What specifically would you like to know about Kaltura?"

## Contributing
Contributions are welcome! If you have any ideas, bug fixes, or enhancements, please feel free to open a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements
- Special thanks to the developers of the libraries used in this project:
  - [Flask](https://flask.palletsprojects.com/)
  - [OpenAI](https://platform.openai.com/)
  - [Transformers](https://huggingface.co/transformers/)

---
This readme was generated using this project.
Feel free to reach out if you have questions or need further assistance with the chatbot!