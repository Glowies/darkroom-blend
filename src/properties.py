import bpy

def update_exposure(self, context):
    context.scene.view_settings.exposure = self.exposure

def update_contrast(self, context):
    scene = context.scene
    if scene.use_nodes:
        bright_contrast_node = scene.node_tree.nodes.get("Darkroom Bright/Contrast")
        if bright_contrast_node:
            bright_contrast_node.inputs['Contrast'].default_value = self.contrast

def update_active_file(self, context):
    bpy.ops.darkroom.load_image()

class DarkroomFile(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="File Name")

class DarkroomProperties(bpy.types.PropertyGroup):
    files: bpy.props.CollectionProperty(type=DarkroomFile)
    active_file_index: bpy.props.IntProperty(update=update_active_file)
    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    output_directory: bpy.props.StringProperty(subtype="DIR_PATH", name="Output Directory")

    
    exposure: bpy.props.FloatProperty(name="Exposure", default=0.0, update=update_exposure)
    contrast: bpy.props.FloatProperty(name="Contrast", default=0.0, update=update_contrast)

def register():
    bpy.utils.register_class(DarkroomFile)
    bpy.utils.register_class(DarkroomProperties)
    bpy.types.Scene.darkroom = bpy.props.PointerProperty(type=DarkroomProperties)

def unregister():
    del bpy.types.Scene.darkroom
    bpy.utils.unregister_class(DarkroomProperties)
    bpy.utils.unregister_class(DarkroomFile)
