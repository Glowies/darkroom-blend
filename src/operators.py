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


class DARKROOM_OT_reset_graph(bpy.types.Operator):
    """Reset the compositing graph"""
    bl_idname = "darkroom.reset_graph"
    bl_label = "Reset Graph"

    def execute(self, context):
        scene = context.scene
        tree = scene.node_tree
        tree.nodes.clear()

        image_node = tree.nodes.new(type='CompositorNodeImage')
        image_node.location = -300, 0

        exposure_node = tree.nodes.new(type='CompositorNodeExposure')
        exposure_node.name = "Darkroom Exposure"
        exposure_node.location = -150, 0

        rgb_curves_node = tree.nodes.new(type='CompositorNodeCurveRGB')
        rgb_curves_node.location = 0, 0
        rgb_curves_node.mapping.tone = 'FILMLIKE'
        for i in range(4):
            rgb_curves_node.mapping.curves[i].points.new(0.18, 0.18)

        bright_contrast_node = tree.nodes.new(type='CompositorNodeBrightContrast')
        bright_contrast_node.name = "Darkroom Bright/Contrast"
        bright_contrast_node.location = 300, 0

        viewer_node = tree.nodes.new(type='CompositorNodeViewer')
        viewer_node.location = 600, -200

        file_output_node = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output_node.location = 600, 0

        darkroom = context.scene.darkroom
        if darkroom.files and darkroom.active_file_index >= 0:
            file_item = darkroom.files[darkroom.active_file_index]
            filepath = os.path.join(darkroom.directory, file_item.name)
            image = bpy.data.images.get(os.path.basename(filepath))
            if image:
                image_node.image = image

        # Link nodes
        tree.links.new(image_node.outputs[0], exposure_node.inputs[0])
        tree.links.new(exposure_node.outputs[0], rgb_curves_node.inputs['Image'])
        tree.links.new(rgb_curves_node.outputs['Image'], bright_contrast_node.inputs[0])
        tree.links.new(bright_contrast_node.outputs[0], viewer_node.inputs[0])
        tree.links.new(bright_contrast_node.outputs[0], file_output_node.inputs[0])

        return {'FINISHED'}


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

        # Check if image is already loaded by checking the filepath
        image = bpy.data.images.get(os.path.basename(filepath))
        if not image:
            image = bpy.data.images.load(filepath)
            image.name = os.path.basename(filepath)
        
        image.colorspace_settings.name = 'ACEScg'

        # Get the image node
        image_node = None
        for node in tree.nodes:
            if node.type == 'IMAGE':
                image_node = node
                break
        
        # If no image node, create the graph
        if not image_node:
            bpy.ops.darkroom.reset_graph()
            for node in tree.nodes:
                if node.type == 'IMAGE':
                    image_node = node
                    break

        image_node.image = image

        return {'FINISHED'}

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
    bpy.utils.register_class(DARKROOM_OT_reset_graph)

def unregister():
    bpy.utils.unregister_class(DARKROOM_OT_render_image)
    bpy.utils.unregister_class(DARKROOM_OT_load_image)
    bpy.utils.unregister_class(DARKROOM_OT_open_folder)
    bpy.utils.unregister_class(DARKROOM_OT_reset_graph)