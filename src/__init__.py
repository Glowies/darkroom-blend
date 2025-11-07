_needs_reload = "bpy" in locals()

import bpy
from . import (
    properties,
    operators,
    ui,
    states,
    library,
    keymap,
)

def load_workspace_handler(dummy):
    library.load_darkroom_workspace()

if _needs_reload:
    import importlib
    properties = importlib.reload(properties)
    operators = importlib.reload(operators)
    ui = importlib.reload(ui)
    states = importlib.reload(states)
    library = importlib.reload(library)
    keymap = importlib.reload(keymap)
    print("Add-on Reloaded")


def register():
    properties.register()
    operators.register()
    ui.register()
    keymap.register()
    bpy.app.handlers.load_post.append(load_workspace_handler)


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
    keymap.unregister()
    bpy.app.handlers.load_post.remove(load_workspace_handler)