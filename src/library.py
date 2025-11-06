import bpy
import os

def load_darkroom_template():
    """Load all node groups from the data blend file and return a copy of the Darkroom Template."""
    blend_file_path = os.path.join(os.path.dirname(__file__), "darkroom-data.blend")
    template_name = "Darkroom Template"

    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
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
        if lib.filepath == blend_file_path:
            bpy.data.libraries.remove(lib)
            break

    return new_tree
