import bpy
import os

BLEND_FILE_PATH = os.path.join(os.path.dirname(__file__), "darkroom-data.blend")

def load_darkroom_template():
    """Load all node groups from the data blend file and return the Darkroom Template."""
    template_name = "Darkroom Template"

    # Check if the template is already loaded
    if template_name in bpy.data.node_groups:
        return bpy.data.node_groups[template_name]

    with bpy.data.libraries.load(BLEND_FILE_PATH, link=True) as (data_from, data_to):
        data_to.node_groups = data_from.node_groups

    # Find the appended template
    loaded_template = bpy.data.node_groups.get(template_name)
    
    return loaded_template

def load_darkroom_workspace():
    """Load the Darkroom workspace from the data blend file."""
    workspace_name = "Darkroom"

    if workspace_name in bpy.data.workspaces:
        return

    with bpy.data.libraries.load(BLEND_FILE_PATH, link=False) as (data_from, data_to):
        data_to.workspaces = [workspace_name]
