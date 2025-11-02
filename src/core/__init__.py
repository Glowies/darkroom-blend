_needs_reload = "bpy" in locals()

import bpy
from . import (
    object_move,
)

if _needs_reload:
    import importlib

    object_move = importlib.reload(object_move)
