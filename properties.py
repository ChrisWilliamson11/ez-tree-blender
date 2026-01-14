import bpy
from bpy.props import (
    IntProperty, FloatProperty, BoolProperty, EnumProperty, 
    FloatVectorProperty, PointerProperty, StringProperty
)
from .enums import BarkType, Billboard, LeafType, TreeType

# Callback for property updates (Geometry)
def update_tree(self, context):
    # Avoid updates when not appropriate or if checks fail
    if not context.active_object or getattr(context.scene, "eztree_loading_preset", False):
        return
    
    # Check if the active object is an EZ-Tree object (has the props)
    # The 'self' here is the PropertyGroup (e.g. EZTree_BarkProps), not the Object.
    # We need to find the root object.
    # Usually we can't easily traverse up from PropertyGroup to Object owner in `update`.
    # BUT, if we edit from UI, context.active_object is the one being edited.
    
    # We trigger an operator or function to regenerate logic.
    # "eztree.regenerate"
    
    # Verify we are actually editing an object with our props
    if hasattr(context.active_object, "eztree_props"):
         # Trigger regeneration
         # We use a timer or direct call? Direct call might lag UI.
         # For "Live" feel, direct is okay for simple trees, maybe laggy for complex.
         # Let's try direct call to an update function.
         # We need to import the regeneration logic.
         from .operators import update_existing_tree
         update_existing_tree(context.active_object)

# Callback for material updates (Performance Optimization)
def update_material(self, context):
    if not context.active_object or getattr(context.scene, "eztree_loading_preset", False):
        return
    
    if hasattr(context.active_object, "eztree_props"):
        from .operators import update_existing_materials
        update_existing_materials(context.active_object)

# Helper to map enums to Blender EnumProperty items
def enum_to_items(enum_cls):
    return [(e.value, e.name, "") for e in enum_cls]

class EZTree_BarkProps(bpy.types.PropertyGroup):
    type: EnumProperty(items=enum_to_items(BarkType), name="Bark Type", default=BarkType.Oak.value, update=update_material)
    tint: FloatVectorProperty(name="Tint", subtype='COLOR', default=(1.0, 1.0, 1.0), min=0, max=1, update=update_material)
    flatShading: BoolProperty(name="Flat Shading", default=False, update=update_tree)
    textured: BoolProperty(name="Textured", default=True, update=update_material)
    textureScaleX: FloatProperty(name="Texture Scale X", default=1.0, update=update_material)
    textureScaleY: FloatProperty(name="Texture Scale Y", default=1.0, update=update_material)

class EZTree_BranchProps(bpy.types.PropertyGroup):
    levels: IntProperty(name="Levels", default=3, min=0, max=4, update=update_tree)
    
    angle_1: FloatProperty(name="Angle L1", default=70, update=update_tree)
    angle_2: FloatProperty(name="Angle L2", default=60, update=update_tree)
    angle_3: FloatProperty(name="Angle L3", default=60, update=update_tree)
    
    children_0: IntProperty(name="Children L0", default=7, update=update_tree)
    children_1: IntProperty(name="Children L1", default=7, update=update_tree)
    children_2: IntProperty(name="Children L2", default=5, update=update_tree)
    
    force_dir: FloatVectorProperty(name="Force Direction", default=(0, 1, 0), update=update_tree)
    force_strength: FloatProperty(name="Force Strength", default=0.01, update=update_tree)
    
    gnarliness_0: FloatProperty(name="Gnarliness L0", default=0.15, update=update_tree)
    gnarliness_1: FloatProperty(name="Gnarliness L1", default=0.2, update=update_tree)
    gnarliness_2: FloatProperty(name="Gnarliness L2", default=0.3, update=update_tree)
    gnarliness_3: FloatProperty(name="Gnarliness L3", default=0.02, update=update_tree)
    
    length_0: FloatProperty(name="Length L0", default=20, update=update_tree)
    length_1: FloatProperty(name="Length L1", default=20, update=update_tree)
    length_2: FloatProperty(name="Length L2", default=10, update=update_tree)
    length_3: FloatProperty(name="Length L3", default=1, update=update_tree)
    
    radius_0: FloatProperty(name="Radius L0", default=1.5, update=update_tree)
    radius_1: FloatProperty(name="Radius L1", default=0.7, update=update_tree)
    radius_2: FloatProperty(name="Radius L2", default=0.7, update=update_tree)
    radius_3: FloatProperty(name="Radius L3", default=0.7, update=update_tree)
    
    sections_0: IntProperty(name="Sections L0", default=12, update=update_tree)
    sections_1: IntProperty(name="Sections L1", default=10, update=update_tree)
    sections_2: IntProperty(name="Sections L2", default=8, update=update_tree)
    sections_3: IntProperty(name="Sections L3", default=6, update=update_tree)
    
    segments_0: IntProperty(name="Segments L0", default=8, update=update_tree)
    segments_1: IntProperty(name="Segments L1", default=6, update=update_tree)
    segments_2: IntProperty(name="Segments L2", default=4, update=update_tree)
    segments_3: IntProperty(name="Segments L3", default=3, update=update_tree)
    
    start_1: FloatProperty(name="Start L1", default=0.4, min=0, max=1, update=update_tree)
    start_2: FloatProperty(name="Start L2", default=0.3, min=0, max=1, update=update_tree)
    start_3: FloatProperty(name="Start L3", default=0.3, min=0, max=1, update=update_tree)
    
    taper_0: FloatProperty(name="Taper L0", default=0.7, min=0, max=1, update=update_tree)
    taper_1: FloatProperty(name="Taper L1", default=0.7, min=0, max=1, update=update_tree)
    taper_2: FloatProperty(name="Taper L2", default=0.7, min=0, max=1, update=update_tree)
    taper_3: FloatProperty(name="Taper L3", default=0.7, min=0, max=1, update=update_tree)
    
    twist_0: FloatProperty(name="Twist L0", default=0, update=update_tree)
    twist_1: FloatProperty(name="Twist L1", default=0, update=update_tree)
    twist_2: FloatProperty(name="Twist L2", default=0, update=update_tree)
    twist_3: FloatProperty(name="Twist L3", default=0, update=update_tree)

class EZTree_LeafProps(bpy.types.PropertyGroup):
    type: EnumProperty(items=enum_to_items(LeafType), name="Leaf Type", default=LeafType.Oak.value, update=update_material)
    billboard: EnumProperty(items=enum_to_items(Billboard), name="Billboard", default=Billboard.Double.value, update=update_tree)
    angle: FloatProperty(name="Angle", default=10, update=update_tree)
    count: IntProperty(name="Count", default=5, update=update_tree)
    start: FloatProperty(name="Start", default=0, min=0, max=1, update=update_tree)
    size: FloatProperty(name="Size", default=2.5, update=update_tree)
    sizeVariance: FloatProperty(name="Size Variance", default=0.7, update=update_tree)
    tint: FloatVectorProperty(name="Tint", subtype='COLOR', default=(1,1,1), min=0, max=1, update=update_material)
    alphaTest: FloatProperty(name="Alpha Test", default=0.5, min=0, max=1, update=update_material)

class EZTree_Props(bpy.types.PropertyGroup):
    seed: IntProperty(name="Seed", default=0, update=update_tree)
    type: EnumProperty(items=enum_to_items(TreeType), name="Tree Type", default=TreeType.Deciduous.value, update=update_tree)
    bark: PointerProperty(type=EZTree_BarkProps)
    branch: PointerProperty(type=EZTree_BranchProps)
    leaves: PointerProperty(type=EZTree_LeafProps)

def register():
    bpy.utils.register_class(EZTree_BarkProps)
    bpy.utils.register_class(EZTree_BranchProps)
    bpy.utils.register_class(EZTree_LeafProps)
    bpy.utils.register_class(EZTree_Props)
    
    # Register on Object as well
    bpy.types.Object.eztree_props = PointerProperty(type=EZTree_Props)
    # Keeping scene for initial creation defaults? Actually, we can just use a temporary operator prop or 
    # keep using Scene props for the "create new" Settings, and then copy them to Object.
    bpy.types.Scene.eztree_props = PointerProperty(type=EZTree_Props)

def unregister():
    del bpy.types.Object.eztree_props
    del bpy.types.Scene.eztree_props
    
    bpy.utils.unregister_class(EZTree_Props)
    bpy.utils.unregister_class(EZTree_LeafProps)
    bpy.utils.unregister_class(EZTree_BranchProps)
    bpy.utils.unregister_class(EZTree_BarkProps)
