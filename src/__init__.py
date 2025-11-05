bl_info = {
    "name": "Darkroom",
    "author": "Gemini",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > UI > Darkroom",
    "description": "A digital darkroom for developing EXR images",
    "category": "Compositing",
}

_needs_reload = "bpy" in locals()

import bpy
from . import (
    properties,
    operators,
    ui,
    states,
)

if _needs_reload:
    import importlib
    properties = importlib.reload(properties)
    operators = importlib.reload(operators)
    ui = importlib.reload(ui)
    states = importlib.reload(states)
    print("Add-on Reloaded")


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()