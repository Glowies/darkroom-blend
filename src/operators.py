import bpy
import os

class DARKROOM_OT_open_folder(bpy.types.Operator):
    """Open a folder of EXR files"""
    bl_idname = "darkroom.open_folder"
    bl_label = "Open EXR Folder"
    
    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        scene = context.scene
        darkroom = scene.darkroom
        
        darkroom.files.clear()
        darkroom.directory = self.directory

        if os.path.isdir(self.directory):
            for f in os.listdir(self.directory):
                if f.lower().endswith(".exr"):
                    new_file = darkroom.files.add()
                    new_file.name = f
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class DARKROOM_OT_load_image(bpy.types.Operator):
    """Load the selected image into the compositor"""
    bl_idname = "darkroom.load_image"
    bl_label = "Load Image"

    def execute(self, context):
        scene = context.scene
        darkroom = scene.darkroom
        
        if not darkroom.files:
            return {'CANCELLED'}

        # Get the selected file
        file_item = darkroom.files[darkroom.active_file_index]
        filepath = os.path.join(darkroom.directory, file_item.name)

        # Set up compositor
        scene.use_nodes = True
        tree = scene.node_tree
        tree.nodes.clear()

        # Check if image is already loaded by checking the filepath
        image = None
        for img in bpy.data.images:
            if img.filepath == filepath:
                image = img
                break
        
        if not image:
            image = bpy.data.images.load(filepath)
        
        image.colorspace_settings.name = 'ACEScg'

        # Create nodes
        image_node = tree.nodes.new(type='CompositorNodeImage')
        image_node.image = image
        image_node.location = -300, 0

        rgb_curves_node = tree.nodes.new(type='CompositorNodeCurveRGB')
        rgb_curves_node.location = 0, 0
        for i in range(4):
            rgb_curves_node.mapping.curves[i].points.new(0.18, 0.18)

        bright_contrast_node = tree.nodes.new(type='CompositorNodeBrightContrast')
        bright_contrast_node.name = "Darkroom Bright/Contrast"
        bright_contrast_node.location = 300, 0

        viewer_node = tree.nodes.new(type='CompositorNodeViewer')
        viewer_node.location = 600, -200

        file_output_node = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output_node.location = 600, 0
        if darkroom.output_directory:
            file_output_node.base_path = darkroom.output_directory
            
            # Create a file slot for the output
            input_name = os.path.splitext(os.path.basename(filepath))[0]
            file_output_node.file_slots.clear()
            file_output_node.file_slots.new(input_name + "_render")

        # Link nodes
        tree.links.new(image_node.outputs[0], rgb_curves_node.inputs['Image'])
        tree.links.new(rgb_curves_node.outputs['Image'], bright_contrast_node.inputs[0])
        tree.links.new(bright_contrast_node.outputs[0], viewer_node.inputs[0])
        tree.links.new(bright_contrast_node.outputs[0], file_output_node.inputs[0])

        return {'FINISHED'}

class DARKROOM_OT_render_image(bpy.types.Operator):
    """Render the final image"""
    bl_idname = "darkroom.render_image"
    bl_label = "Render Image"

    def execute(self, context):
        bpy.ops.render.render()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DARKROOM_OT_open_folder)
    bpy.utils.register_class(DARKROOM_OT_load_image)
    bpy.utils.register_class(DARKROOM_OT_render_image)

def unregister():
    bpy.utils.unregister_class(DARKROOM_OT_render_image)
    bpy.utils.unregister_class(DARKROOM_OT_load_image)
    bpy.utils.unregister_class(DARKROOM_OT_open_folder)