from utils.utils import extract_file_name, extract_content


def analyze_request(request):
    """Analyze the user's request and return structured intent data."""
    if "read" in request:
        return {
            "action": "read",
            "file": extract_file_name(request)  # Function to extract the file name
        }
    elif "write" in request:
        return {
            "action": "write",
            "file": extract_file_name(request),
            "content": extract_content(request)  # Function to extract the content
        }
    else:
        return {"action": "unknown"}
