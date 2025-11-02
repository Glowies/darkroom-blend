_needs_reload = "bpy" in locals()

import bpy
from . import (
    core,
)

if _needs_reload:
    import importlib

    core = importlib.reload(core)
    print("Add-on Reloaded")


def register():
    bpy.utils.register_class(core.object_move.ObjectMoveX)
    bpy.types.VIEW3D_MT_object.append(
        core.object_move.menu_func
    )  # Adds the new operator to an existing menu.


def unregister():
    bpy.utils.unregister_class(core.object_move.ObjectMoveX)
    bpy.types.VIEW3D_MT_object.remove(core.object_move.menu_func)
