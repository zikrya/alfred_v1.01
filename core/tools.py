from langchain_core.tools import tool
import os
import subprocess
import platform
import PyPDF2
import docx

from concurrent.futures import ThreadPoolExecutor


@tool
def resolve_path(path: str) -> str:
    """
    Resolves a user-provided path to its absolute system path.

    **Use this when:**
    - The user provides a relative path (e.g., 'Desktop', 'Documents') and needs the full absolute path.

    **Example Usage:**
    - "What is the absolute path of 'Desktop'?"
    - "Resolve 'Documents' to its full system path."

    **DO NOT USE FOR:**
    - Finding specific files or folders (use `search_for_file()` or `search_for_folder()`).
    """
    if path.lower() == "desktop":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() == "documents":
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.expanduser(path)


@tool
def create_folder(folder_name: str, path: str = ".") -> str:
    """Creates a new folder at the specified path.

    - If the path is relative, it will be resolved to an absolute path.
    - If the folder already exists, no error occurs.
    - Returns the full path of the created folder or an error message.
    """
    full_path = os.path.join(resolve_path(path), folder_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Folder '{folder_name}' created at {full_path}."
    except Exception as e:
        return f"Error creating folder '{folder_name}': {e}"


@tool
def create_file(file_name: str, path: str = ".") -> str:
    """Creates an empty file at the specified path.

    - If the file already exists, it is not modified.
    - If the path is relative, it will be resolved to an absolute path.
    - Returns the full path of the created file or an error message.
    """
    full_path = os.path.join(resolve_path(path), file_name)
    try:
        with open(full_path, 'w') as file:
            file.write("")
        return f"File '{file_name}' created at {full_path}."
    except Exception as e:
        return f"Error creating file '{file_name}': {e}"


@tool
def list_files_and_folders(path: str = ".") -> list:
    """Lists all files and folders in the specified directory.

    - If the path is relative, it is resolved to an absolute path.
    - Returns a list of filenames in the directory or an error message if the directory is inaccessible.
    """
    try:
        return os.listdir(resolve_path(path))
    except Exception as e:
        return [f"Error accessing the directory: {e}"]


@tool
def read_file_content(file_path: str) -> str:
    """Reads the content of a file, supporting `.txt`, `.pdf`, and `.docx` formats.

    - Extracts text from plain text files (`.txt`).
    - Uses OCR to extract text from PDF files (`.pdf`).
    - Reads text from Microsoft Word documents (`.docx`).
    - Returns the extracted content as a string or an error message for unsupported formats.
    """
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
    """Searches for a specific file in the given directory and its subdirectories.

    - Uses parallel processing to improve search speed.
    - Returns the full path of the found file or an error message if not found.
    """
    result = search_target_parallel(search_path, filename)

    if "Target found:" in result:
        return result.split(": ")[1].strip()

    return f"File '{filename}' not found."


@tool
def search_for_folder(foldername: str, search_path: str = "/") -> str:
    """Searches for a specific folder within a directory and its subdirectories.

    - Uses parallel processing to improve efficiency.
    - Returns the full path of the found folder or an error message if not found.
    """
    return search_target_parallel(search_path, foldername)


@tool
def append_to_file(file_path: str, content: str) -> str:
    """Appends text to an existing file.

    - The file path is resolved to an absolute path before appending.
    - If the file does not exist, an error message is returned.
    - Returns a success message upon successful content addition.
    """
    resolved_path = resolve_path(file_path)

    if not os.path.exists(resolved_path):
        return f"Error: File '{resolved_path}' does not exist."

    try:
        with open(resolved_path, 'a') as file:
            file.write(content + "\n")
        return f"Content appended to {resolved_path} successfully."
    except Exception as e:
        return f"Error appending to file '{resolved_path}': {e}"


@tool
def search_and_append_to_file(file_name: str, content: str, search_path: str = "/") -> str:
    """Searches for a file and appends content to it if found.

    - Uses `search_for_file()` to locate the file first.
    - If the file is found, appends content and returns a success message.
    - If the file is not found, returns an error message.
    """
    file_path = search_for_file(file_name, search_path)

    if isinstance(file_path, str) and "found" in file_path:
        return append_to_file(file_path.split(": ")[1], content)
    else:
        return f"File '{file_name}' not found in the search path."


@tool
def open_file_or_folder(target_name: str, search_path: str = "/") -> str:
    """Searches for a file or folder and opens it using the system's default application.

    - Uses `search_for_file()` for files and `search_for_folder()` for folders.
    - If found, opens the file/folder with the system default application.
    - Returns an error message if the file or folder does not exist.
    """
    file_path = search_for_file(target_name, search_path)
    folder_path = search_for_folder(target_name, search_path)

    if isinstance(file_path, str) and os.path.exists(file_path):
        path = file_path
    elif isinstance(folder_path, str) and os.path.exists(folder_path):
        path = folder_path
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


# **Helper functions for parallel searching**
def search_target_scandir(path, target_name):
    """Scans a directory for a file or folder and returns the path if found.

    - Returns a list of subdirectories if the target is not found in the current directory.
    - Handles permission errors gracefully.
    """
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
    """Searches for a file or folder in a directory and its subdirectories using parallel processing.

    - Improves search speed by leveraging multiple threads.
    - Returns the full path if the target is found, otherwise an error message.
    """
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

        return f"Target found: {found_target}" if found_target else f"Target '{target_name}' not found."
