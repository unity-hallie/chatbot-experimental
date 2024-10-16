import subprocess
from chatbot.chat_history import ChatHistory
from components.file_system_component import FileSystemComponent


async def act(file_system: FileSystemComponent,
               user_confirm: callable,
               user_id: str,
               openai,
               request: str,
               chat_history: ChatHistory,
               **kwargs):
    execution_log = []
    commit_msg_file = "COMMIT_MSG"

    # Step 1: Add all changes to Git
    execution_log.append("Step 1: Adding changes to Git...")
    try:
        subprocess.run(['git', 'add', '.'], check=True, cwd=file_system.working_directory)
        execution_log.append("Successfully added changes.")
    except subprocess.CalledProcessError as e:
        error_message = f"Error adding files to Git: {str(e)}. Command: git add ."
        log_and_display_error(user_id, error_message, execution_log)
        return error_message, execution_log

    # Step 2: Get the diff and generate a commit message
    execution_log.append("Step 2: Fetching git diff...")
    try:
        diff_output = subprocess.check_output(['git', 'diff', '--cached'], cwd=file_system.working_directory, text=True)
        execution_log.append(f"User {user_id} is requesting a commit.")
        commit_msg = await generate_commit_message(diff_output, openai, chat_history)
        with open(commit_msg_file, 'w') as f:
            f.write(commit_msg)
        execution_log.append(f"Diff fetched and commit message generated: {commit_msg}")
    except subprocess.CalledProcessError as e:
        error_message = f"Error fetching git diff: {str(e)}. Command: git diff --cached"
        log_and_display_error(user_id, error_message, execution_log)
        return error_message, execution_log

    # User Confirmation Logic
    confirmation_text = f"{commit_msg}\nDo you want to proceed with the commit? (y/n): "
    execution_log.append("Step 3: Awaiting user confirmation for commit...")

    if await user_confirm(confirmation_text):
        execution_log.append("User confirmed commit.")
        try:
            subprocess.run(['git', 'commit', '-F', commit_msg_file], check=True, cwd=file_system.working_directory)
            execution_log.append("Successfully committed changes.")
            return "Changes committed successfully.", execution_log
        except subprocess.CalledProcessError as e:
            error_message = f"Error committing changes: {str(e)}. Command: git commit -F COMMIT_MSG"
            log_and_display_error(user_id, error_message, execution_log)
            return error_message, execution_log

    return "Commit cancelled by the user.", execution_log

def log_and_display_error(user_id, error_message, execution_log):
    print(f"ERROR for user {user_id}: {error_message}")
    execution_log.append(error_message)  # log error into the execution log for later retrieval


async def generate_commit_message(diff_output, openai, chat_history):
    """
    Generate a detailed commit message based on the diff output.

    :param diff_output: The output from the 'git diff --cached' command
    :param openai: OpenAI API client for making requests
    :param chat_history: ChatHistory object for logging conversations
    :return: A generated commit message
    """

    # Prepare a prompt for the AI to generate a commit message
    prompt = (
        "Below is a summary of code changes based on the diff output provided:\n\n"
        f"{diff_output}\n\n"
        "Generate a detailed commit message that includes a summary of the changes, key improvements, and reasons for these changes. Do not exceed 500 tokens please"
    )

    # Log the prompt
    chat_history.add_interaction("bot", prompt, "Generating commit message...")

    try:
        # Call OpenAI's API to generate the message
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Using a cheaper model as specified
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Limit the length of the response
            temperature=0.7,  # Set the creativity of the response
        )

        # Extract the commit message from the response
        commit_message = response.choices[0].message.content.strip()

        # Log the generated commit message
        chat_history.add_interaction("bot", prompt, commit_message)  # Log the AI's output

        return commit_message  # Return the finalized commit message

    except Exception as e:
        print(f"Error generating commit message: {str(e)}")
        return f"Unable to generate commit message due to an error. {str(e)}"

# Exported command
git_commit = {
    "command": "git_commit",
    "description": "Handles Git commit operations including adding changes, generating commit messages, and confirming user actions.",
    "act": act
}