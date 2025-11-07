import bpy

addon_keymaps = []

def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('node.backimage_zoom', 'WHEELUPMOUSE', 'PRESS', alt=True)
        kmi.properties.factor = 1.2
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new('node.backimage_zoom', 'WHEELDOWNMOUSE', 'PRESS', alt=True)
        kmi.properties.factor = 0.833
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
