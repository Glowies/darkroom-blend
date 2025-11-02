import bpy

class DARKROOM_UL_file_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False)

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

        layout.operator("darkroom.open_folder")

        if darkroom.directory:
            layout.label(text="Directory: " + darkroom.directory)
            layout.template_list("DARKROOM_UL_file_list", "", darkroom, "files", darkroom, "active_file_index")

            layout.prop(darkroom, "output_directory")

            if darkroom.files:
                col = layout.column(align=True)
                col.prop(darkroom, "exposure")
                col.prop(darkroom, "contrast")
                
                layout.operator("darkroom.render_image")


def register():
    bpy.utils.register_class(DARKROOM_UL_file_list)
    bpy.utils.register_class(DARKROOM_PT_panel)

def unregister():
    bpy.utils.unregister_class(DARKROOM_PT_panel)
    bpy.utils.unregister_class(DARKROOM_UL_file_list)