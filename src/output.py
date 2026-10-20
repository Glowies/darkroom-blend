"""Keeps the File Output node of the Darkroom graph in sync with the Darkroom panel.

The node has one item for the SDR and one for the HDR output, identified by
their names ending in "SDR" / "HDR". Each item overrides the node's format so it
can use its own display, with the scene's view transform.
"""

import bpy

from . import library

OUTPUT_NODE_NAME = "File Output"
OUTPUT_KINDS = ("SDR", "HDR")

# Scene view settings mirrored onto the outputs
VIEW_SETTINGS = ("view_transform", "look", "exposure", "gamma")

# Image format settings copied from the node format to each item. File format
# first, as it determines which values the others accept.
FORMAT_SETTINGS = (
    "media_type",
    "file_format",
    "color_mode",
    "color_depth",
    "quality",
    "compression",
    "exr_codec",
    "use_exr_interleave",
    "tiff_codec",
    "jpeg2k_codec",
    "use_jpeg2k_ycc",
    "use_jpeg2k_cinema_preset",
    "use_jpeg2k_cinema_48",
)

FORMAT_EXTENSIONS = {
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "AVIF": ".avif",
    "PNG": ".png",
    "TIFF": ".tif",
    "OPEN_EXR": ".exr",
}


def active_output_node(scene):
    """The File Output node of the scene's compositor node group, if it's a Darkroom one."""
    tree = scene.compositing_node_group
    if not tree or not tree.name.startswith("Darkroom"):
        return None
    return tree.nodes.get(OUTPUT_NODE_NAME)


def output_items(node):
    """{"SDR": item, "HDR": item} for the node's items whose names end in SDR / HDR."""
    items = {}
    for item in node.file_output_items:
        for kind in OUTPUT_KINDS:
            if item.name.upper().endswith(kind):
                items.setdefault(kind, item)
    return items


def output_settings(scene):
    """{"SDR": (enabled, display name), "HDR": ...} from the Darkroom panel."""
    darkroom = scene.darkroom
    # The enums resolve a name missing from the OCIO config to the first display
    return {
        "SDR": (darkroom.use_sdr_output, darkroom.sdr_display),
        "HDR": (darkroom.use_hdr_output, darkroom.hdr_display),
    }


def set_if_changed(owner, attr, value):
    # Avoids redundant updates, and re-triggering our own view settings subscription
    if getattr(owner, attr) != value:
        setattr(owner, attr, value)


def sync_item_format(node, item, display, view_settings, is_hdr):
    """Make item use node's format, with display and view_settings. Returns warnings."""
    warnings = []
    item.override_node_format = True
    item.save_as_render = True
    fmt = item.format

    for attr in FORMAT_SETTINGS:
        try:
            set_if_changed(fmt, attr, getattr(node.format, attr))
        except (AttributeError, TypeError):
            # Not applicable to this file format
            pass

    if is_hdr and fmt.color_depth == "8":
        # 8 bits bands visibly with PQ/HLG; use the lowest higher depth available
        depths = [d.identifier for d in fmt.bl_rna.properties["color_depth"].enum_items]
        higher = [d for d in depths if d.isdigit() and int(d) > 8]
        if higher:
            fmt.color_depth = min(higher, key=int)

    set_if_changed(fmt, "color_management", "OVERRIDE")

    if display in library.available_displays():
        set_if_changed(fmt.display_settings, "display_device", display)
    else:
        warnings.append(f"Display '{display}' is not in the current OCIO config")

    # Display first: the views available depend on it
    for attr in VIEW_SETTINGS:
        try:
            set_if_changed(fmt.view_settings, attr, getattr(view_settings, attr))
        except TypeError:
            warnings.append(
                f"{attr.replace('_', ' ').capitalize()} '{getattr(view_settings, attr)}' "
                f"is not available for display '{fmt.display_settings.display_device}'"
            )
    return warnings


def sync_file_output(scene):
    """Apply the Darkroom panel's output settings to the File Output node.

    Returns a list of warnings, e.g. for missing displays or output items.
    """
    node = active_output_node(scene)
    if node is None:
        return []

    warnings = []
    items = output_items(node)
    for kind, (enabled, display) in output_settings(scene).items():
        item = items.get(kind)
        if item is None:
            if enabled:
                warnings.append(f"'{OUTPUT_NODE_NAME}' node has no input named '…{kind}'")
            continue
        for warning in sync_item_format(node, item, display, scene.view_settings, kind == "HDR"):
            warnings.append(f"{kind} output: {warning}")
    return warnings


def item_output_path(node, item):
    """Path the node writes item to, or None for formats without a known extension."""
    extension = ""
    if node.use_file_extension:
        extension = FORMAT_EXTENSIONS.get(item.format.file_format)
        if extension is None:
            return None
    directory = bpy.path.abspath(node.directory)
    return f"{directory}{node.file_name}{item.name}{extension}"


class disabled_outputs_unlinked:
    """Context manager: unlinks the inputs of disabled outputs so the node skips
    them, and relinks them afterwards. Blender skips unconnected inputs only."""

    def __init__(self, scene):
        self.scene = scene
        self.removed = []

    def __enter__(self):
        node = active_output_node(self.scene)
        if node is None:
            return self
        tree = node.id_data
        items = output_items(node)
        for kind, (enabled, _) in output_settings(self.scene).items():
            item = items.get(kind)
            if enabled or item is None:
                continue
            socket = node.inputs.get(item.name)
            for link in list(socket.links) if socket else []:
                self.removed.append((tree, link.from_socket, link.to_socket))
                tree.links.remove(link)
        return self

    def __exit__(self, *exc):
        for tree, from_socket, to_socket in self.removed:
            tree.links.new(from_socket, to_socket)
        return False


# Owner of the view settings subscription
_msgbus_owner = object()


def on_view_settings_changed(*_args):
    scene = bpy.context.scene
    if scene is not None:
        sync_file_output(scene)


def subscribe():
    bpy.msgbus.clear_by_owner(_msgbus_owner)
    for attr in VIEW_SETTINGS:
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.ColorManagedViewSettings, attr),
            owner=_msgbus_owner,
            args=(),
            notify=on_view_settings_changed,
        )


@bpy.app.handlers.persistent
def resubscribe_on_load(_dummy):
    # Loading a file clears all message bus subscriptions
    subscribe()


def register():
    subscribe()
    bpy.app.handlers.load_post.append(resubscribe_on_load)


def unregister():
    if resubscribe_on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(resubscribe_on_load)
    bpy.msgbus.clear_by_owner(_msgbus_owner)
