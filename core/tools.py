import os
import subprocess
import platform
import re
import uuid
import PyPDF2
import docx
from concurrent.futures import ThreadPoolExecutor
from langchain_core.tools import StructuredTool, tool
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings


### 📌 TOOL REGISTRATION & VECTOR STORE ###
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")


def create_tool(name: str, description: str, func):
    """Dynamically creates a StructuredTool."""
    formatted_name = re.sub(r"[^\w\s]", "", name).replace(" ", "_")
    return StructuredTool.from_function(func, name=formatted_name, description=description)


# Initialize Tool Registry
TOOL_REGISTRY = {}


def register_tool(name: str, description: str, func):
    """Registers a tool dynamically with an embedding."""
    tool_id = str(uuid.uuid4())
    TOOL_REGISTRY[tool_id] = create_tool(name, description, func)
    return tool_id

# Function to get tool registry


def get_tool_registry():
    return TOOL_REGISTRY

# Function to initialize vector store for tool retrieval


def initialize_vector_store():
    tool_documents = [
        Document(page_content=tool.description, id=tool_id,
                 metadata={"tool_name": tool.name})
        for tool_id, tool in TOOL_REGISTRY.items()
    ]

    vector_store = InMemoryVectorStore(embedding=embeddings)
    vector_store.add_documents(tool_documents)

    return vector_store


VECTOR_STORE = None  # Initialize lazily


### 📌 SYSTEM COMMAND TOOLS ###
@tool
def resolve_path(path: str) -> str:
    """Resolves a user-provided path to its absolute system path."""
    if path.lower() == "desktop":
        return os.path.join(os.path.expanduser("~"), "Desktop")
    elif path.lower() == "documents":
        return os.path.join(os.path.expanduser("~"), "Documents")
    return os.path.expanduser(path)


register_tool("Resolve Path",
              "Resolves relative paths to absolute paths.", resolve_path)


@tool
def create_folder(folder_name: str, path: str = ".") -> str:
    """Creates a new folder at the specified path."""
    full_path = os.path.join(resolve_path(path), folder_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        return f"Folder '{folder_name}' created at {full_path}."
    except Exception as e:
        return f"Error creating folder '{folder_name}': {e}"


register_tool("Create Folder",
              "Creates a folder at a specified location.", create_folder)


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


register_tool(
    "Create File", "Creates a new file at a given path.", create_file)


@tool
def list_files_and_folders(path: str = ".") -> list:
    """Lists all files and folders in a specified directory."""
    try:
        return os.listdir(resolve_path(path))
    except Exception as e:
        return [f"Error accessing the directory: {e}"]


register_tool("List Files and Folders",
              "Lists all files and directories in a path.", list_files_and_folders)


@tool
def read_file_content(file_path: str) -> str:
    """Reads the content of `.txt`, `.pdf`, and `.docx` files."""
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


register_tool("Read File Content",
              "Reads content from .txt, .pdf, and .docx files.", read_file_content)


@tool
def append_to_file(file_path: str, content: str) -> str:
    """Appends text to an existing file."""
    resolved_path = resolve_path(file_path)

    if not os.path.exists(resolved_path):
        return f"Error: File '{resolved_path}' does not exist."

    try:
        with open(resolved_path, 'a') as file:
            file.write(content + "\n")
        return f"Content appended to {resolved_path} successfully."
    except Exception as e:
        return f"Error appending to file '{resolved_path}': {e}"


register_tool("Append to File",
              "Appends content to a specified file.", append_to_file)


### 📌 FILE SEARCH & EXECUTION TOOLS ###
@tool
def search_for_file(filename: str, search_path: str = "/") -> str:
    """Searches for a specific file in the given directory."""
    result = search_target_parallel(search_path, filename)
    return result.split(": ")[1].strip() if "Target found:" in result else f"File '{filename}' not found."


register_tool("Search for File",
              "Finds a file in a given directory.", search_for_file)


@tool
def search_for_folder(foldername: str, search_path: str = "/") -> str:
    """Searches for a specific folder within a directory."""
    return search_target_parallel(search_path, foldername)


register_tool("Search for Folder",
              "Finds a folder in a given directory.", search_for_folder)


@tool
def open_file_or_folder(target_name: str, search_path: str = "/") -> str:
    """Opens a file or folder if found in the given search path."""
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
        elif system == "Darwin":
            subprocess.run(["open", path])
        elif system == "Linux":
            subprocess.run(["xdg-open", path])
        else:
            return "Unsupported operating system."
        return f"'{target_name}' opened successfully."
    except Exception as e:
        return f"Error opening '{target_name}': {e}"


register_tool("Open File or Folder",
              "Opens a file or folder in the system.", open_file_or_folder)


### 📌 HELPER FUNCTIONS ###
def search_target_scandir(path, target_name):
    """Scans a directory for a file or folder and returns its path if found."""
    try:
        with os.scandir(path) as entries:
            subdirs = []
            for entry in entries:
                if (entry.is_file() or entry.is_dir()) and entry.name == target_name:
                    return entry.path
                elif entry.is_dir(follow_symlinks=False):
                    subdirs.append(entry.path)
            return subdirs
    except (PermissionError, OSError):
        return []


def search_target_parallel(root_directory, target_name, max_workers=8):
    """Searches for a file or folder in a directory and its subdirectories using parallel processing."""
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
