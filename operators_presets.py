import bpy
import os
from .presets import get_preset_path, apply_preset

def get_preset_items(self, context):
    path = get_preset_path()
    if not os.path.exists(path):
        return []
    
    files = [f for f in os.listdir(path) if f.endswith(".json")]
    files.sort()
    
    # Items format: (identifier, name, description)
    return [(f, f.replace(".json", "").replace("_", " ").title(), "") for f in files]

class EZTree_OT_ApplyPresetMenu(bpy.types.Operator):
    bl_idname = "eztree.apply_preset_menu"
    bl_label = "Apply Preset"
    bl_description = "Apply a tree preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_enum: bpy.props.EnumProperty(
        items=get_preset_items,
        name="Preset"
    )

    def execute(self, context):
        props = context.scene.eztree_props
        apply_preset(props, self.preset_enum)
        # Auto-generate after preset load? Maybe optional. User usually clicks Generate.
        # Let's just load parameters for now to be safe.
        self.report({'INFO'}, f"Loaded preset: {self.preset_enum}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(EZTree_OT_ApplyPresetMenu)

def unregister():
    bpy.utils.unregister_class(EZTree_OT_ApplyPresetMenu)
