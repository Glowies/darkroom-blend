_needs_reload = "bpy" in locals()

import bpy

from . import (
    library,
    operators,
    output,
    properties,
    states,
    ui,
)


@bpy.app.handlers.persistent
def load_workspace_handler(dummy):
    # Persistent so it runs for every file loaded, not only the startup file.
    library.load_darkroom_workspace()


if _needs_reload:
    import importlib

    properties = importlib.reload(properties)
    operators = importlib.reload(operators)
    ui = importlib.reload(ui)
    states = importlib.reload(states)
    library = importlib.reload(library)
    output = importlib.reload(output)
    print("Add-on Reloaded")


def register():
    properties.register()
    operators.register()
    ui.register()
    output.register()
    bpy.app.handlers.load_post.append(load_workspace_handler)


def unregister():
    output.unregister()
    ui.unregister()
    operators.unregister()
    properties.unregister()
    if load_workspace_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_workspace_handler)
