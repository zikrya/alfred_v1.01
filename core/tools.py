from langchain_core.tools import tool
import os
import subprocess
import platform
import PyPDF2
import docx
from concurrent.futures import ThreadPoolExecutor

### 🏗️ SYSTEM FUNCTIONS AS TOOLS ###


@tool
def create_folder(folder_name: str, path: str = ".") -> str:
    """Creates a folder at the specified path."""

    if path.lower() == "desktop":
        path = os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() == "documents":
        path = os.path.join(os.path.expanduser("~"), "Documents")
    else:
        path = os.path.expanduser(path)

    full_path = os.path.join(path, folder_name)

    try:
        os.makedirs(full_path, exist_ok=True)
        return f" Folder '{folder_name}' created at {full_path}."
    except Exception as e:
        return f" Error creating folder '{folder_name}': {e}"


@tool
def create_file(file_name: str, path: str = ".") -> str:
    """Creates an empty file at the specified path."""
    full_path = os.path.join(os.path.expanduser(path), file_name)
    try:
        with open(full_path, 'w') as file:
            file.write("")
        return f" File '{file_name}' created at {full_path}."
    except Exception as e:
        return f" Error creating file '{file_name}': {e}"


@tool
def list_files_and_folders(path: str = ".") -> list:
    """Lists all files and folders in a given directory."""
    try:
        return os.listdir(os.path.expanduser(path))
    except Exception as e:
        return [f"Error accessing the directory: {e}"]


@tool
def open_file_or_folder(target_name: str, search_path: str = "/") -> str:
    """Searches for a file or folder and opens it."""
    full_path = os.path.join(os.path.expanduser(search_path), target_name)
    if os.path.exists(full_path):
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["start", full_path], shell=True)
            elif system == "Darwin":
                subprocess.run(["open", full_path])
            elif system == "Linux":
                subprocess.run(["xdg-open", full_path])
            return f"'{target_name}' opened successfully."
        except Exception as e:
            return f"Error opening '{target_name}': {e}"
    else:
        return f"'{target_name}' not found."


@tool
def append_to_file(file_path: str, content: str) -> str:
    """Appends text to an existing file."""
    try:
        with open(os.path.expanduser(file_path), 'a') as file:
            file.write(content + "\n")
        return f"Content appended to {file_path} successfully."
    except Exception as e:
        return f"Error appending to file '{file_path}': {e}"
