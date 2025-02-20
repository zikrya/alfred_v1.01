from core.tools import (
    create_folder,
    create_file,
    open_file_or_folder,
    append_to_file,
    read_file_content,
    search_and_append_to_file,
    resolve_path,
    search_for_target,
    list_files_and_folders
)


def get_tool_function(tool_name):
    """Returns the correct function based on the tool name."""
    tool_mapping = {
        "create_folder": create_folder,
        "create_file": create_file,
        "open_file_or_folder": open_file_or_folder,
        "append_to_file": append_to_file,
        "read_file_content": read_file_content,
        "search_for_target": search_for_target,
        "search_and_append_to_file": search_and_append_to_file,
        "resolve_path": resolve_path,
        "list_files_and_folders": list_files_and_folders,  # ✅ Added here
    }

    tool_name = tool_name.lower()  # ✅ Convert AI's tool name to lowercase
    function = tool_mapping.get(tool_name)
    print(
        f"\n get_tool_function() - Looking for: {tool_name}, Found: {function}")
    return function
