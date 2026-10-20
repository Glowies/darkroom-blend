import functools

import bpy

from . import library, output

AUTO = "AUTO"


# Blender doesn't keep its own reference to dynamic enum item strings, so the
# lists must stay alive (see the EnumProperty docs). Blender only loads its OCIO
# config at startup, so each list is built once and the cache keeps it alive.
@functools.cache
def colorspace_enum_items():
    return [(AUTO, "Auto", "Use the colorspace Blender picks for the file")] + [
        (name, name, "") for name in library.available_colorspaces()
    ]


@functools.cache
def display_enum_items():
    return [
        (name, library.display_ui_name(name), "")
        for name in library.available_displays()
    ]


def colorspace_items(self, context):
    return colorspace_enum_items()


def display_items(self, context):
    return display_enum_items()


def default_sdr_display(self):
    scene_display = self.id_data.display_settings.display_device
    if not library.is_hdr_display(scene_display):
        return scene_display
    displays = library.available_displays()
    return next((d for d in displays if not library.is_hdr_display(d)), None)


def default_hdr_display(self):
    displays = library.available_displays()
    return next((d for d in displays if library.is_hdr_display(d)), None)


def name_enum(name_attr, items, empty_id=None, default=None, **kwargs):
    """EnumProperty that stores its value as a name in the name_attr property.

    Blender stores dynamic enums by index, which shifts between OCIO configs. A
    stored name missing from the current config shows as default(self) if
    given, else the first item. If given, empty_id is the item stored as an
    empty name.
    """

    def get(self):
        ids = [item[0] for item in items(self, None)]
        name = getattr(self, name_attr) or empty_id
        if name not in ids and default is not None:
            name = default(self)
        return ids.index(name) if name in ids else 0

    def set(self, value):
        name = items(self, None)[value][0]
        setattr(self, name_attr, "" if name == empty_id else name)

    return bpy.props.EnumProperty(items=items, get=get, set=set, **kwargs)


def update_input_colorspace(self, context):
    # self belongs to the scene, which may not be context.scene
    image = library.active_darkroom_image(self.id_data)
    if image:
        library.apply_input_colorspace(image, self.input_colorspace_name)


def update_outputs(self, context):
    output.sync_file_output(self.id_data)


class DarkroomProperties(bpy.types.PropertyGroup):
    output_directory: bpy.props.StringProperty(subtype="DIR_PATH", name="Output Directory")
    input_colorspace_name: bpy.props.StringProperty(
        name="Input Colorspace Name",
        description="Colorspace assigned to loaded images. Empty for Auto",
        options={"HIDDEN"},
    )
    input_colorspace: name_enum(
        "input_colorspace_name",
        colorspace_items,
        empty_id=AUTO,
        name="Input Colorspace",
        description="Colorspace of images loaded from the file browser. "
        "Also applied to the image in the open Darkroom node group",
        update=update_input_colorspace,
    )

    use_sdr_output: bpy.props.BoolProperty(
        name="SDR Output",
        description="Write the SDR output when rendering",
        default=True,
        update=update_outputs,
    )
    sdr_display_name: bpy.props.StringProperty(options={"HIDDEN"})
    sdr_display: name_enum(
        "sdr_display_name",
        display_items,
        default=default_sdr_display,
        name="Display",
        description="Display the SDR output is encoded for",
        update=update_outputs,
    )

    use_hdr_output: bpy.props.BoolProperty(
        name="HDR Output",
        description="Write the HDR output when rendering",
        default=True,
        update=update_outputs,
    )
    hdr_display_name: bpy.props.StringProperty(options={"HIDDEN"})
    hdr_display: name_enum(
        "hdr_display_name",
        display_items,
        default=default_hdr_display,
        name="Display",
        description="Display the HDR output is encoded for",
        update=update_outputs,
    )

def register():
    bpy.utils.register_class(DarkroomProperties)
    bpy.types.Scene.darkroom = bpy.props.PointerProperty(type=DarkroomProperties)

def unregister():
    del bpy.types.Scene.darkroom
    bpy.utils.unregister_class(DarkroomProperties)
