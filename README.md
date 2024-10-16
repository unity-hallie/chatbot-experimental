# Ethical AI Chatbot

## Overview
This project implements an ethical AI chatbot named **Eleanor** (formerly Guidon), designed to interact with users while upholding stringent ethical guidelines. The chatbot utilizes various agents to manage file systems, analyze user interactions, and maintain conversation history, providing personalized responses and support.

## Features
- Multi-agent architecture for handling different tasks, including file operations and user description updates.
- Emotional state analysis to provide empathetic responses, enhancing user engagement.
- File system management capabilities, allowing dynamic handling of user requests.
- Ability to open folders or directories from command line requests, launching a file browser for user navigation.
- A web interface to interact with the chatbot efficiently (please note: the web interface is currently very janky).
- Support for Markdown display in chat history for better formatting.
- Command processing using `~git_commit` for handling Git commits.

## Getting Started

### Prerequisites
- Python 3.6 or higher.
- [Node.js](https://nodejs.org/) (for front-end functionality).
- [OpenAI API key](https://platform.openai.com/signup/) (required for AI functionality).

### Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/unity-hallie/chatbot-experimental.git
   cd chatbot-experimental
   ```
   
2. **Install Required Packages**:
   Run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the project root directory with your OpenAI API key:
   ```plaintext
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Run the Application**:
   To start the chatbot in the Command Line Interface (CLI), run:
   ```bash
   python cli.py
   ```
   While the web interface is also available, it is currently under development and may not provide the best user experience.

5. **Web Interface Usage**:
   If you prefer to use the web interface, run:
   ```bash
   python web_service.py
   ```
   Then, open your web browser and go to:
   ```plaintext
   http://127.0.0.1:5000
   ```

### Usage
You can interact with the chatbot by typing messages in the chat box on the web interface. The chatbot is designed to handle various requests, including file operations or general inquiries. 

When you request to open a folder or directory from the command line, the chatbot will launch a file browser, allowing you to change the current working directory.

### Tilde Command Usage
- **Single Command**: Prepend your command with `~`. Example: `~git_commit` for committing changes in Git.
- **Double Tilde**: Prepend your command with `~~` for executing commands with user input confirmation.
- **Triple Tilde**: Use `~~~` for commands enhanced with AI suggestions.

### Command Breakdown
#### `~git_commit`
This command handles Git commit operations by:
- Adding staged changes.
- Fetching diffs and dynamically generating commit messages based on recent changes.
- Requesting user confirmation before executing the commit.

### Known Limitations
- The **user-facing logic for file commands** related to reading and writing files is disabled to avoid inconsistencies in request handling. This functionality is planned for future integration after further testing and refinement.
- The web interface is currently described as "very janky" and will require improvements for better usability.

### User Engagement and Emotional Intelligence
- The chatbot tracks emotional states and user engagement to provide contextually aware interactions, ensuring a supportive user experience.

## NOTE
- To delete logs, empty the logs folder, delete json files in base folder and states folder


## Conclusion
This README outlines the user interactions and functionalities of the Ethical AI Chatbot, ensuring clarity on current capabilities and how they align with ethical considerations.

--- 
Feel free to reach out if you have further revisions or anything else you'd want to address prior to the commit! 😊