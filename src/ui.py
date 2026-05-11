import bpy


class DARKROOM_PT_panel(bpy.types.Panel):
    """Creates a Panel in the Compositor Window"""

    bl_label = "Darkroom"
    bl_idname = "DARKROOM_PT_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    # # hide the panel if this panel is not in a Compositor Node Tree context
    # # (this only make sense if we're adding this as a side panel in the node editor)
    # @classmethod
    # def poll(cls, context):
    #     return context.space_data.tree_type == "CompositorNodeTree"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        darkroom = scene.darkroom

        layout.operator("darkroom.toggle_file_browser")

        layout.prop(darkroom, "output_directory")

        row = layout.row()
        row.scale_y = 3.0
        row.operator("darkroom.render_image")

        layout.operator("darkroom.reset_graph")
        layout.operator("node.backimage_fit", text="Fit Backdrop")


def register():
    bpy.utils.register_class(DARKROOM_PT_panel)


def unregister():
    bpy.utils.unregister_class(DARKROOM_PT_panel)
