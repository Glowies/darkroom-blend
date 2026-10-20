import bpy

from . import library

AUTO = "AUTO"

# Blender doesn't keep its own reference to dynamic enum item strings, so they
# must stay alive here or the UI shows garbage.
_colorspace_items = []


def colorspace_items(self, context):
    global _colorspace_items
    _colorspace_items = [
        (AUTO, "Auto", "Use the colorspace Blender picks for the file"),
    ] + [(name, name, "") for name in library.available_colorspaces()]
    return _colorspace_items


def get_input_colorspace(self):
    # The name is stored instead of the enum index, which shifts between OCIO
    # configs. A name missing from the current config shows as Auto.
    names = [item[0] for item in colorspace_items(self, None)]
    name = self.input_colorspace_name or AUTO
    return names.index(name) if name in names else 0


def set_input_colorspace(self, value):
    names = [item[0] for item in colorspace_items(self, None)]
    name = names[value]
    self.input_colorspace_name = "" if name == AUTO else name


def update_input_colorspace(self, context):
    # self belongs to the scene, which may not be context.scene
    image = library.active_darkroom_image(self.id_data)
    if image:
        library.apply_input_colorspace(image, self.input_colorspace_name)


class DarkroomProperties(bpy.types.PropertyGroup):
    output_directory: bpy.props.StringProperty(subtype="DIR_PATH", name="Output Directory")
    input_colorspace_name: bpy.props.StringProperty(
        name="Input Colorspace Name",
        description="Colorspace assigned to loaded images. Empty for Auto",
        options={"HIDDEN"},
    )
    input_colorspace: bpy.props.EnumProperty(
        name="Input Colorspace",
        description="Colorspace of images loaded from the file browser. "
        "Also applied to the image in the open Darkroom node group",
        items=colorspace_items,
        get=get_input_colorspace,
        set=set_input_colorspace,
        update=update_input_colorspace,
    )

def register():
    bpy.utils.register_class(DarkroomProperties)
    bpy.types.Scene.darkroom = bpy.props.PointerProperty(type=DarkroomProperties)

def unregister():
    del bpy.types.Scene.darkroom
    bpy.utils.unregister_class(DarkroomProperties)
