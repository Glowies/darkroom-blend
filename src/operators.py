import bpy
import os
from pathlib import Path
from . import states, library

prev_relpath = None
prev_dirpath = None
filebrowser_state = states.FileBrowserState()

def is_image(path):
    return path.suffix.lower() in {'.exr', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}

def callback_filename_change(dummy):
    """
    This will be registered as a draw handler on the filebrowser and runs everytime the
    area gets redrawn. This handles the dynamic loading of the selected media.
    """
    global prev_relpath
    global prev_dirpath

    area = bpy.context.area
    if area.type != 'FILE_BROWSER':
        return

    active_file = bpy.context.active_file
    directory = Path(bpy.path.abspath(area.spaces.active.params.directory.decode("utf-8")))
    
    active_relpath = active_file.relative_path if active_file else None

    if prev_dirpath != directory:
        prev_dirpath = directory

    if not active_file:
        return

    if prev_relpath == active_relpath:
        return

    active_filepath = directory / active_relpath
    if is_image(active_filepath):
        bpy.ops.darkroom.load_image_from_path(filepath=str(active_filepath))

    prev_relpath = active_relpath


class DARKROOM_OT_load_image_from_path(bpy.types.Operator):
    """Load an image from a filepath into the compositor"""
    bl_idname = "darkroom.load_image_from_path"
    bl_label = "Load Image From Path"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        filename = os.path.basename(self.filepath)
        node_group_name = f"Darkroom - {filename}"

        # Check if a node group for this image already exists
        tree = bpy.data.node_groups.get(node_group_name)

        if not tree:
            # If it doesn't exist, create a new one from the template
            template_tree = library.load_darkroom_template()
            if not template_tree:
                self.report({'ERROR'}, "Failed to load Darkroom Template node group.")
                return {'CANCELLED'}
            tree = template_tree.copy()
            tree.name = node_group_name
        
        # Assign the tree to the scene's compositing node group
        scene.compositing_node_group = tree

        # Check if image is already loaded by checking the filepath
        image = bpy.data.images.get(filename)
        if not image:
            image = bpy.data.images.load(self.filepath)
            image.name = filename
        
        image.colorspace_settings.name = 'ACEScg'

        # Get the image node
        image_node = tree.nodes.get("Darkroom Input Image")
        
        if image_node:
            image_node.image = image
        else:
            self.report({'WARNING'}, "'Darkroom Input Image' node not found.")

        # Switch Image Editor to Viewer Node
        for area in context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                if "Viewer Node" in bpy.data.images:
                    area.spaces.active.image = bpy.data.images["Viewer Node"]

        return {'FINISHED'}


class DARKROOM_OT_reset_graph(bpy.types.Operator):
    """Reset the compositing graph by loading from the data blend file."""
    bl_idname = "darkroom.reset_graph"
    bl_label = "Reset Graph"

    def execute(self, context):
        scene = context.scene
        active_tree = scene.compositing_node_group

        if not active_tree or not active_tree.name.startswith("Darkroom"):
            self.report({'ERROR'}, "No active Darkroom node group to reset.")
            return {'CANCELLED'}

        # Store the image and name
        image_node = active_tree.nodes.get("Darkroom Input Image")
        image = image_node.image if image_node else None
        original_name = active_tree.name

        # Remove the existing node group
        bpy.data.node_groups.remove(active_tree)

        # Create a new one from the template
        template_tree = library.load_darkroom_template()
        if not template_tree:
            self.report({'ERROR'}, "Failed to load Darkroom Template node group.")
            return {'CANCELLED'}
        new_tree = template_tree.copy()

        # Restore the name and image
        new_tree.name = original_name
        if image:
            new_image_node = new_tree.nodes.get("Darkroom Input Image")
            if new_image_node:
                new_image_node.image = image

        # Assign the new tree to the scene
        scene.compositing_node_group = new_tree

        return {'FINISHED'}


class DARKROOM_OT_render_image(bpy.types.Operator):
    """Render the final image"""
    bl_idname = "darkroom.render_image"
    bl_label = "Render Image"

    def execute(self, context):
        darkroom = context.scene.darkroom
        tree = context.scene.compositing_node_group
        
        if not tree or not tree.name.startswith("Darkroom"):
            self.report({'ERROR'}, "No active Darkroom node group found.")
            return {'CANCELLED'}

        if not darkroom.output_directory:
            self.report({'ERROR'}, "Output directory not set")
            return {'CANCELLED'}

        image_node = tree.nodes.get("Darkroom Input Image")
        output_node = tree.nodes.get("File Output")
        
        if not image_node or not image_node.image or not output_node:
            self.report({'ERROR'}, "Required nodes not found in compositor")
            return {'CANCELLED'}

        output_node.directory = darkroom.output_directory
        
        input_filename = os.path.splitext(image_node.image.name)[0]
        output_filename = f"{input_filename}"
        output_node.file_name = output_filename

        bpy.ops.render.render()

        output_path = os.path.join(darkroom.output_directory, output_filename)
        self.report({'INFO'}, f"Image rendered to: {output_path}")
        print(f"Image rendered to: {output_path}")

        return {'FINISHED'}

class DARKROOM_OT_toggle_file_browser(bpy.types.Operator):
    """Toggle the file browser in the compositor"""
    bl_idname = "darkroom.toggle_file_browser"
    bl_label = "Toggle File Browser"

    def execute(self, context):
        global filebrowser_state
        screen = context.screen
        node_editor_area = None
        image_editor_area = None
        file_browser_area = None

        for area in screen.areas:
            if area.type == 'NODE_EDITOR':
                node_editor_area = area
            elif area.type == 'IMAGE_EDITOR':
                image_editor_area = area
            elif area.type == 'FILE_BROWSER':
                file_browser_area = area

        if file_browser_area:
            filebrowser_state = states.FileBrowserState(area=file_browser_area)
            # Override the context to close the file browser area
            with context.temp_override(area=file_browser_area):
                bpy.ops.screen.area_close()
        else:
            # Prioritize splitting the Image Editor if it exists
            area_to_split = image_editor_area or node_editor_area
            if area_to_split:
                with context.temp_override(area=area_to_split):
                    bpy.ops.screen.area_split(direction='VERTICAL', factor=0.3)
                    new_area = screen.areas[-1]
                    new_area.type = 'FILE_BROWSER'
                    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                    filebrowser_state.apply_to_area(new_area)

        return {'FINISHED'}

draw_handlers_fb = []

def register():
    bpy.utils.register_class(DARKROOM_OT_load_image_from_path)
    bpy.utils.register_class(DARKROOM_OT_render_image)
    bpy.utils.register_class(DARKROOM_OT_reset_graph)
    bpy.utils.register_class(DARKROOM_OT_toggle_file_browser)
    
    draw_handlers_fb.append(
        bpy.types.SpaceFileBrowser.draw_handler_add(
            callback_filename_change, (None,), "WINDOW", "POST_PIXEL"
        )
    )

def unregister():
    bpy.utils.unregister_class(DARKROOM_OT_render_image)
    bpy.utils.unregister_class(DARKROOM_OT_load_image_from_path)
    bpy.utils.unregister_class(DARKROOM_OT_reset_graph)
    bpy.utils.unregister_class(DARKROOM_OT_toggle_file_browser)

    for handler in draw_handlers_fb:
        bpy.types.SpaceFileBrowser.draw_handler_remove(handler, "WINDOW")
