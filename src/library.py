import bpy
import os

BLEND_FILE_PATH = os.path.join(os.path.dirname(__file__), "darkroom-data.blend")

def load_darkroom_template():
    """Load all node groups from the data blend file and return a copy of the Darkroom Template."""
    template_name = "Darkroom Template"

    with bpy.data.libraries.load(BLEND_FILE_PATH, link=False) as (data_from, data_to):
        data_to.node_groups = data_from.node_groups

    # Find the appended template
    loaded_template = bpy.data.node_groups.get(template_name)
    if not loaded_template:
        return None

    # Create a copy and rename it
    new_tree = loaded_template.copy()
    new_tree.name = "Darkroom"

    # Clean up the appended library data blocks
    for lib in bpy.data.libraries:
        if lib.filepath == BLEND_FILE_PATH:
            bpy.data.libraries.remove(lib)
            break

    return new_tree

def load_darkroom_workspace():
    """Load the Darkroom workspace from the data blend file."""
    workspace_name = "Darkroom"

    if workspace_name in bpy.data.workspaces:
        return

    with bpy.data.libraries.load(BLEND_FILE_PATH, link=False) as (data_from, data_to):
        data_to.workspaces = [workspace_name]
