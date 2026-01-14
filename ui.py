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
        props = context.scene.eztree_props
        
        layout.operator("eztree.generate", text="Generate Tree", icon='OUTLINER_OB_MESH')
        
        layout.prop(props, "seed")
        layout.prop(props, "type")

class EZTree_PT_Bark(EZTree_PT_Base, bpy.types.Panel):
    bl_label = "Bark"
    bl_idname = "EZTREE_PT_bark"
    bl_parent_id = "EZTREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
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
        props = context.scene.eztree_props.branch
        
        layout.prop(props, "levels")
        
        box = layout.box()
        box.label(text="Angles")
        col = box.column(align=True)
        col.prop(props, "angle_1")
        col.prop(props, "angle_2")
        col.prop(props, "angle_3")
        
        box = box.box()
        box.label(text="Children")
        col = box.column(align=True)
        col.prop(props, "children_0")
        col.prop(props, "children_1")
        col.prop(props, "children_2")
        
        box = layout.box()
        box.label(text="Force")
        box.prop(props, "force_dir")
        box.prop(props, "force_strength")
        
        # We can expose other props similarly (Gnarliness, Length, Radius, etc.)
        # Doing a subset for brevity in this initial pass, or full?
        # Full exposure is better.
        
        def draw_level_props(name, prop_prefix):
            box = layout.box()
            box.label(text=name)
            col = box.column(align=True)
            col.prop(props, f"{prop_prefix}_0")
            col.prop(props, f"{prop_prefix}_1")
            col.prop(props, f"{prop_prefix}_2")
            col.prop(props, f"{prop_prefix}_3")

        draw_level_props("Gnarliness", "gnarliness")
        draw_level_props("Length", "length")
        draw_level_props("Radius", "radius")
        
        # Sections/Segments
        box = layout.box()
        box.label(text="Resolution")
        col = box.column(align=True)
        col.label(text="Sections")
        col.prop(props, "sections_0")
        col.prop(props, "sections_1")
        col.prop(props, "sections_2")
        col.prop(props, "sections_3")
        col.label(text="Segments")
        col.prop(props, "segments_0")
        col.prop(props, "segments_1")
        col.prop(props, "segments_2")
        col.prop(props, "segments_3")
        
        box = layout.box()
        box.label(text="Start")
        col = box.column(align=True)
        col.prop(props, "start_1")
        col.prop(props, "start_2")
        col.prop(props, "start_3")
        
        draw_level_props("Taper", "taper")
        draw_level_props("Twist", "twist")

class EZTree_PT_Leaves(EZTree_PT_Base, bpy.types.Panel):
    bl_label = "Leaves"
    bl_idname = "EZTREE_PT_leaves"
    bl_parent_id = "EZTREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
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
