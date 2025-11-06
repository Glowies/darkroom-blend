_needs_reload = "bpy" in locals()

import bpy
from . import (
    properties,
    operators,
    ui,
    states,
    library,
)

if _needs_reload:
    import importlib
    properties = importlib.reload(properties)
    operators = importlib.reload(operators)
    ui = importlib.reload(ui)
    states = importlib.reload(states)
    library = importlib.reload(library)
    print("Add-on Reloaded")


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()