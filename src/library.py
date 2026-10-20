import bpy
import os

BLEND_FILE_PATH = os.path.join(os.path.dirname(__file__), "darkroom-data.blend")
WORKSPACE_NAME = "Darkroom"

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

def available_colorspaces():
    """Names of the input colorspaces in the OCIO config Blender has loaded."""
    items = bpy.types.ColorManagedInputColorspaceSettings.bl_rna.properties["name"].enum_items
    return [item.identifier for item in items]


# Custom property on images: the colorspace Blender picked when loading the file,
# restored when the input colorspace is set back to Auto.
AUTO_COLORSPACE_KEY = "darkroom_auto_colorspace"


def apply_input_colorspace(image, colorspace):
    """Set image to colorspace, or to the one Blender picked on load if colorspace
    is empty (Auto). Returns False if colorspace isn't in the current OCIO config."""
    available = available_colorspaces()
    if not colorspace:
        colorspace = image.get(AUTO_COLORSPACE_KEY, "")
        if colorspace not in available:
            return True
    elif colorspace not in available:
        return False

    if image.colorspace_settings.name != colorspace:
        image.colorspace_settings.name = colorspace
    return True


def active_darkroom_image(scene):
    """The input image of the scene's compositor node group, if it's a Darkroom one."""
    tree = scene.compositing_node_group
    if not tree or not tree.name.startswith("Darkroom"):
        return None
    image_node = tree.nodes.get("Darkroom Input Image")
    return image_node.image if image_node else None


def nodes_with_missing_colorspaces(tree):
    """Convert Colorspace nodes in tree (and its groups) whose colorspace the OCIO
    config lacks, as "<group> / <node>" labels. Blender reads a missing name as ""."""
    available = set(available_colorspaces())
    found = []
    for node in tree.nodes:
        if node.bl_idname == "CompositorNodeConvertColorSpace":
            if {node.from_color_space, node.to_color_space} - available:
                found.append(f"{tree.name} / {node.name}")
        elif node.bl_idname == "CompositorNodeGroup" and node.node_tree:
            found.extend(nodes_with_missing_colorspaces(node.node_tree))
    return found


def load_darkroom_workspace():
    """Load the Darkroom workspace from the data blend file."""
    if WORKSPACE_NAME in bpy.data.workspaces:
        return

    with bpy.data.libraries.load(BLEND_FILE_PATH, link=False) as (data_from, data_to):
        data_to.workspaces = [WORKSPACE_NAME]
