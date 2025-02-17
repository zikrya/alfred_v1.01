from core.tools import create_folder, create_file, list_files_and_folders, open_file_or_folder, append_to_file


def get_tool_function(tool_name):
    """Returns the correct function based on the tool name."""
    tool_mapping = {
        "create_folder": create_folder,
        "create_file": create_file,
        "list_files_and_folders": list_files_and_folders,
        "open_file_or_folder": open_file_or_folder,
        "append_to_file": append_to_file,
    }
    function = tool_mapping.get(tool_name)
    print(
        f"\n get_tool_function() - Looking for: {tool_name}, Found: {function}")
    return function
