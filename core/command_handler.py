from core.tools import (
    create_folder,
    create_file,
    open_file_or_folder,
    append_to_file,
    read_file_content,
    search_for_file,
    search_for_folder,
    search_and_append_to_file,
    resolve_path,
    search_target_scandir,
    search_target_parallel,
    list_files_and_folders
)


# ✅ Centralized tool mapping
TOOL_MAPPING = {
    "create_folder": create_folder,
    "create_file": create_file,
    "open_file_or_folder": open_file_or_folder,
    "append_to_file": append_to_file,
    "read_file_content": read_file_content,
    "search_for_file": search_for_file,
    "search_for_folder": search_for_folder,
    "search_and_append_to_file": search_and_append_to_file,
    "resolve_path": resolve_path,
    "search_target_scandir": search_target_scandir,
    "search_target_parallel": search_target_parallel,
    "list_files_and_folders": list_files_and_folders,
}


def get_tool_function(tool_name):
    """Returns the correct function based on the tool name."""

    function = TOOL_MAPPING.get(tool_name)

    if function:
        print(f"\n✅ get_tool_function() - Found tool: {tool_name}")
    else:
        print(f"\n❌ get_tool_function() - Tool '{tool_name}' not found!")

    return function
