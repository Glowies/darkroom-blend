import bpy

class DarkroomProperties(bpy.types.PropertyGroup):
    output_directory: bpy.props.StringProperty(subtype="DIR_PATH", name="Output Directory")

def register():
    bpy.utils.register_class(DarkroomProperties)
    bpy.types.Scene.darkroom = bpy.props.PointerProperty(type=DarkroomProperties)

def unregister():
    del bpy.types.Scene.darkroom
    bpy.utils.unregister_class(DarkroomProperties)
