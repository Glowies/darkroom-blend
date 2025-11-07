import bpy

class DARKROOM_PT_panel(bpy.types.Panel):
    """Creates a Panel in the Compositor Window"""
    bl_label = "Darkroom"
    bl_idname = "DARKROOM_PT_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Darkroom'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        darkroom = scene.darkroom

        layout.operator("darkroom.toggle_file_browser")

        layout.prop(darkroom, "output_directory")

        col = layout.column(align=True)
        
        layout.operator("darkroom.render_image")
        layout.operator("darkroom.reset_graph")
        layout.operator("node.backimage_fit", text="Fit Backdrop")


def register():
    bpy.utils.register_class(DARKROOM_PT_panel)

def unregister():
    bpy.utils.unregister_class(DARKROOM_PT_panel)