import bpy

def update_exposure(self, context):
    scene = context.scene
    if scene.use_nodes:
        exposure_node = scene.node_tree.nodes.get("Darkroom Exposure")
        if exposure_node:
            exposure_node.inputs['Exposure'].default_value = self.exposure

def update_contrast(self, context):
    scene = context.scene
    if scene.use_nodes:
        bright_contrast_node = scene.node_tree.nodes.get("Darkroom Bright/Contrast")
        if bright_contrast_node:
            bright_contrast_node.inputs['Contrast'].default_value = self.contrast

class DarkroomProperties(bpy.types.PropertyGroup):
    output_directory: bpy.props.StringProperty(subtype="DIR_PATH", name="Output Directory")

    
    exposure: bpy.props.FloatProperty(name="Exposure", default=0.0, update=update_exposure)
    contrast: bpy.props.FloatProperty(name="Contrast", default=0.0, update=update_contrast)

def register():
    bpy.utils.register_class(DarkroomProperties)
    bpy.types.Scene.darkroom = bpy.props.PointerProperty(type=DarkroomProperties)

def unregister():
    del bpy.types.Scene.darkroom
    bpy.utils.unregister_class(DarkroomProperties)
