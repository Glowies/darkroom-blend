import bpy


class DarkroomPanel:
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"


class DARKROOM_PT_panel(DarkroomPanel, bpy.types.Panel):
    bl_label = "Darkroom"
    bl_idname = "DARKROOM_PT_panel"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        scene = context.scene
        darkroom = scene.darkroom

        layout.operator("darkroom.toggle_file_browser")

        col = layout.column()
        col.prop(darkroom, "input_colorspace")
        col.prop(darkroom, "output_directory")

        col.separator()

        col.prop(scene.view_settings, "view_transform", text="View")

        # Layout panels rather than subpanels: subpanels are drawn after this
        # draw(), so the render buttons below would need a subpanel of their
        # own, which gets the subpanel backdrop.
        draw_output_panel(layout, darkroom, "sdr", "SDR Output")
        draw_output_panel(layout, darkroom, "hdr", "HDR Output")

        row = layout.row()
        row.scale_y = 3.0
        row.operator("darkroom.render_image")

        layout.operator("darkroom.reset_graph")


def draw_output_panel(layout, darkroom, kind, label):
    header, body = layout.panel(f"DARKROOM_PT_{kind}_output", default_closed=True)
    header.use_property_split = False
    # Checkbox without text plus a separate label, as Blender's own layout
    # panels do: clicking the label expands, only the box toggles.
    header.prop(darkroom, f"use_{kind}_output", text="")
    header.label(text=label)
    if body:
        body.active = getattr(darkroom, f"use_{kind}_output")
        body.prop(darkroom, f"{kind}_display")


classes = (DARKROOM_PT_panel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
