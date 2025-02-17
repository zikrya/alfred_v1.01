from langchain_core.tools import tool
import os
import subprocess
import platform
import PyPDF2
import docx
import openai
from concurrent.futures import ThreadPoolExecutor


@tool
def resolve_path(path: str) -> str:
    """Resolve the user-specified path or use default system paths for known directories."""
    if path.lower() == "desktop":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() == "documents":
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.expanduser(path)


@tool
def create_folder(folder_name: str, path: str = ".") -> str:
    """Creates a folder at the specified path."""
    full_path = os.path.join(resolve_path(path), folder_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Folder '{folder_name}' created at {full_path}."
    except Exception as e:
        return f"Error creating folder '{folder_name}': {e}"


@tool
def create_file(file_name: str, path: str = ".") -> str:
    """Creates an empty file at the specified path."""
    full_path = os.path.join(resolve_path(path), file_name)
    try:
        with open(full_path, 'w') as file:
            file.write("")
        return f"File '{file_name}' created at {full_path}."
    except Exception as e:
        return f"Error creating file '{file_name}': {e}"


@tool
def list_files_and_folders(path: str = ".") -> list:
    """Lists all files and folders in a given directory."""
    try:
        return os.listdir(resolve_path(path))
    except Exception as e:
        return [f"Error accessing the directory: {e}"]


@tool
def read_file_content(file_path: str) -> str:
    """Reads a file and returns its content based on the file type."""
    file_extension = os.path.splitext(file_path)[1].lower()
    content = ""

    try:
        if file_extension == ".txt":
            with open(file_path, 'r') as file:
                content = file.read()
        elif file_extension == ".pdf":
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    content += page.extract_text() or ""
        elif file_extension == ".docx":
            doc = docx.Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        else:
            return f"Unsupported file format: {file_extension}"
    except Exception as e:
        return f"Failed to read file: {e}"

    return content


@tool
def search_for_file(filename: str, search_path: str = "/") -> str:
    """Searches for a file in the specified directory using parallel processing."""
    return search_target_parallel(search_path, filename)


@tool
def search_for_folder(foldername: str, search_path: str = "/") -> str:
    """Searches for a folder in the specified directory using parallel processing."""
    return search_target_parallel(search_path, foldername)


@tool
def append_to_file(file_path: str, content: str) -> str:
    """Appends content to an existing file."""
    try:
        with open(file_path, 'a') as file:
            file.write(content + "\n")
        return f"Content appended to {file_path} successfully."
    except Exception as e:
        return f"Error appending to file '{file_path}': {e}"


@tool
def search_and_append_to_file(file_name: str, content: str, search_path: str = "/") -> str:
    """Search for a file and append content to it."""
    file_path = search_for_file(file_name, search_path)

    if isinstance(file_path, str) and "found" in file_path:
        return append_to_file(file_path.split(": ")[1], content)
    else:
        return f"File '{file_name}' not found in the search path."


@tool
def open_file_or_folder(target_name: str, search_path: str = "/") -> str:
    """Search for a file or folder and open it using the default application."""
    file_path = search_for_file(target_name, search_path)
    folder_path = search_for_folder(target_name, search_path)

    if isinstance(file_path, str) and "found" in file_path:
        path = file_path.split(": ")[1]
    elif isinstance(folder_path, str) and "found" in folder_path:
        path = folder_path.split(": ")[1]
    else:
        return f"'{target_name}' not found."

    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(["start", path], shell=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", path])
        elif system == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            return "Unsupported operating system."
        return f"'{target_name}' opened successfully."
    except Exception as e:
        return f"Error opening '{target_name}': {e}"


# Helper functions for parallel searching
def search_target_scandir(path, target_name):
    """Scan a directory for a file or folder, returning the path if found."""
    try:
        with os.scandir(path) as entries:
            subdirs = []
            for entry in entries:
                try:
                    if (entry.is_file() or entry.is_dir()) and entry.name == target_name:
                        return entry.path
                    elif entry.is_dir(follow_symlinks=False):
                        subdirs.append(entry.path)
                except (PermissionError, OSError):
                    continue
            return subdirs
    except (PermissionError, OSError):
        return []


def search_target_parallel(root_directory, target_name, max_workers=8):
    """Search for a target file or folder in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(
            search_target_scandir, root_directory, target_name)]
        found_target = None
        while futures:
            future = futures.pop(0)
            subdirs = future.result()

            if isinstance(subdirs, str):
                found_target = subdirs
                break
            else:
                for subdir in subdirs:
                    futures.append(executor.submit(
                        search_target_scandir, subdir, target_name))

        if found_target:
            return f"Target found: {found_target}"
        else:
            return f"Target '{target_name}' not found."
