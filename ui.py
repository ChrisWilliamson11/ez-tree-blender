import bpy

class EZTree_PT_Base:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EZ-Tree'
    bl_context = 'objectmode'

class EZTree_PT_Main(EZTree_PT_Base, bpy.types.Panel):
    bl_label = "EZ-Tree"
    bl_idname = "EZTREE_PT_main"

    def draw(self, context):
        layout = self.layout
        
        # Determine data source
        # If active object has eztree_props, use it (Live Edit Mode)
        # Else use Scene props (New Tree Mode)
        
        obj = context.active_object
        if obj and hasattr(obj, "eztree_props") and obj.eztree_props.branch.levels > 0: 
            # Check levels > 0 is a heuristic to see if populated? 
            # Or just check if it's the "TreeBranch" object.
            # Best check: Is it an EZ-Tree object?
            # We assume if it has the pointer property initialized it is one. 
            # Note: PointerProperty is always present on Object type, 
            # but we can check if it has meaningful data? 
            # Actually weak reference. 
            # Better: Check if name starts with TreeBranch or we tag it.
            # Let's assume user works with generated trees.
            props = obj.eztree_props
            layout.label(text=f"Editing: {obj.name}", icon='EDITMODE_HLT')
        else:
            props = context.scene.eztree_props
            layout.label(text="Creating New Tree", icon='ADD')
        
        # Presets Menu (Only allow applying presets to Scene props for creation? 
        # Or apply to Live object too? Live is better!)
        row = layout.row()
        row.label(text="Presets:")
        # We need to pass context override or let operator handle detection of source.
        # Operator `EZTree_OT_ApplyPresetMenu` calls `apply_preset(context.scene.eztree_props)`. 
        # We need to update that operator too.
        row.operator_menu_enum("eztree.apply_preset_menu", "preset_enum", text="Select Preset")

        layout.separator()
        
        layout.operator("eztree.generate", text="Generate Tree", icon='OUTLINER_OB_MESH')
        layout.operator("eztree.add_wind", text="Add Wind Animation", icon='FORCE_WIND')
        
        layout.prop(props, "seed")
        layout.prop(props, "type")

class EZTree_PT_Bark(EZTree_PT_Base, bpy.types.Panel):
    bl_label = "Bark"
    bl_idname = "EZTREE_PT_bark"
    bl_parent_id = "EZTREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj and hasattr(obj, "eztree_props") and "TreeBranch" in obj.name: # Simple name check for now
             props = obj.eztree_props.bark
        else:
             props = context.scene.eztree_props.bark
        
        layout.prop(props, "type")
        layout.prop(props, "tint")
        layout.prop(props, "flatShading")
        layout.prop(props, "textured")
        col = layout.column(align=True)
        col.prop(props, "textureScaleX")
        col.prop(props, "textureScaleY")

class EZTree_PT_Branch(EZTree_PT_Base, bpy.types.Panel):
    bl_label = "Branches"
    bl_idname = "EZTREE_PT_branch"
    bl_parent_id = "EZTREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj and hasattr(obj, "eztree_props") and "TreeBranch" in obj.name:
             props = obj.eztree_props.branch
        else:
             props = context.scene.eztree_props.branch
        
        layout.prop(props, "levels")
        
        # Force Global
        box = layout.box()
        box.label(text="Global Force")
        box.prop(props, "force_dir")
        box.prop(props, "force_strength")
        
        # Iterate Levels
        # Limit to available props (0-3)
        max_level = min(props.levels, 3) 
        
        for i in range(max_level + 1):
            level_name = "Trunk (Level 0)" if i == 0 else f"Level {i}"
            
            box = layout.box()
            # Making it look like a sub-panel with an icon?
            box.label(text=level_name, icon='GROUP_VERTEX')
            
            # Grouping
            col = box.column(align=True)
            
            # Main Dims
            row = col.row(align=True)
            row.prop(props, f"length_{i}", text="Length")
            row.prop(props, f"radius_{i}", text="Radius")
            
            # Shape
            row = col.row(align=True)
            row.prop(props, f"taper_{i}", text="Taper")
            row.prop(props, f"twist_{i}", text="Twist")
            
            col.prop(props, f"gnarliness_{i}", text="Gnarliness")
            
            # Placement (only for children)
            if i > 0:
                col.separator()
                col.label(text="Placement")
                row = col.row(align=True)
                row.prop(props, f"angle_{i}", text="Angle")
                row.prop(props, f"start_{i}", text="Start")
            
            # Topology
            col.separator()
            row = col.row(align=True)
            row.prop(props, f"sections_{i}", text="Sections")
            row.prop(props, f"segments_{i}", text="Segments")
            
            # Children Count (next level)
            if i < props.levels and i < 3: # Can't have children at max level or if no prop
                col.separator()
                col.prop(props, f"children_{i}", text=f"Branches (Level {i+1} Count)")

class EZTree_PT_Leaves(EZTree_PT_Base, bpy.types.Panel):
    bl_label = "Leaves"
    bl_idname = "EZTREE_PT_leaves"
    bl_parent_id = "EZTREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        if obj and hasattr(obj, "eztree_props") and "TreeBranch" in obj.name:
             props = obj.eztree_props.leaves
        else:
             props = context.scene.eztree_props.leaves
        
        layout.prop(props, "type")
        layout.prop(props, "billboard")
        layout.prop(props, "angle")
        layout.prop(props, "count")
        layout.prop(props, "start")
        layout.prop(props, "size")
        layout.prop(props, "sizeVariance")
        layout.prop(props, "tint")
        layout.prop(props, "alphaTest")

classes = (
    EZTree_PT_Main,
    EZTree_PT_Bark,
    EZTree_PT_Branch,
    EZTree_PT_Leaves,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
