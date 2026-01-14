import bpy
from bpy.props import (
    IntProperty, FloatProperty, BoolProperty, EnumProperty, 
    FloatVectorProperty, PointerProperty, StringProperty
)
from .enums import BarkType, Billboard, LeafType, TreeType

# Helper to map enums to Blender EnumProperty items
def enum_to_items(enum_cls):
    return [(e.value, e.name, "") for e in enum_cls]

class EZTree_BarkProps(bpy.types.PropertyGroup):
    type: EnumProperty(
        items=enum_to_items(BarkType),
        name="Bark Type",
        default=BarkType.Oak.value
    )
    tint: FloatVectorProperty(
        name="Tint",
        subtype='COLOR',
        default=(1.0, 1.0, 1.0),
        min=0, max=1
    )
    flatShading: BoolProperty(name="Flat Shading", default=False)
    textured: BoolProperty(name="Textured", default=True)
    textureScaleX: FloatProperty(name="Texture Scale X", default=1.0)
    textureScaleY: FloatProperty(name="Texture Scale Y", default=1.0)

class EZTree_BranchProps(bpy.types.PropertyGroup):
    levels: IntProperty(name="Levels", default=3, min=0, max=4)
    
    # We need to flatten the dict structure for Blender props.
    # Arrays can work if size is fixed, but dictionary keys like '1', '2' map to levels.
    # Simpler to have explicit props for each level or just arrays.
    # Level max is usually around 3 or 4.
    # Using arrays for compact UI.
    
    # Angle (Levels 1-3)
    angle_1: FloatProperty(name="Angle L1", default=70)
    angle_2: FloatProperty(name="Angle L2", default=60)
    angle_3: FloatProperty(name="Angle L3", default=60)
    
    # Children (Levels 0-2)
    children_0: IntProperty(name="Children L0", default=7)
    children_1: IntProperty(name="Children L1", default=7)
    children_2: IntProperty(name="Children L2", default=5)
    
    # Force
    force_dir: FloatVectorProperty(name="Force Direction", default=(0, 1, 0))
    force_strength: FloatProperty(name="Force Strength", default=0.01)
    
    # Gnarliness (0-3)
    gnarliness_0: FloatProperty(name="Gnarliness L0", default=0.15)
    gnarliness_1: FloatProperty(name="Gnarliness L1", default=0.2)
    gnarliness_2: FloatProperty(name="Gnarliness L2", default=0.3)
    gnarliness_3: FloatProperty(name="Gnarliness L3", default=0.02)
    
    # Length (0-3)
    length_0: FloatProperty(name="Length L0", default=20)
    length_1: FloatProperty(name="Length L1", default=20)
    length_2: FloatProperty(name="Length L2", default=10)
    length_3: FloatProperty(name="Length L3", default=1)
    
    # Radius (0-3)
    radius_0: FloatProperty(name="Radius L0", default=1.5)
    radius_1: FloatProperty(name="Radius L1", default=0.7)
    radius_2: FloatProperty(name="Radius L2", default=0.7)
    radius_3: FloatProperty(name="Radius L3", default=0.7)
    
    # Sections (0-3)
    sections_0: IntProperty(name="Sections L0", default=12)
    sections_1: IntProperty(name="Sections L1", default=10)
    sections_2: IntProperty(name="Sections L2", default=8)
    sections_3: IntProperty(name="Sections L3", default=6)
    
    # Segments (0-3)
    segments_0: IntProperty(name="Segments L0", default=8)
    segments_1: IntProperty(name="Segments L1", default=6)
    segments_2: IntProperty(name="Segments L2", default=4)
    segments_3: IntProperty(name="Segments L3", default=3)
    
    # Start (1-3)
    start_1: FloatProperty(name="Start L1", default=0.4, min=0, max=1)
    start_2: FloatProperty(name="Start L2", default=0.3, min=0, max=1)
    start_3: FloatProperty(name="Start L3", default=0.3, min=0, max=1)
    
    # Taper (0-3)
    taper_0: FloatProperty(name="Taper L0", default=0.7, min=0, max=1)
    taper_1: FloatProperty(name="Taper L1", default=0.7, min=0, max=1)
    taper_2: FloatProperty(name="Taper L2", default=0.7, min=0, max=1)
    taper_3: FloatProperty(name="Taper L3", default=0.7, min=0, max=1)
    
    # Twist (0-3)
    twist_0: FloatProperty(name="Twist L0", default=0)
    twist_1: FloatProperty(name="Twist L1", default=0)
    twist_2: FloatProperty(name="Twist L2", default=0)
    twist_3: FloatProperty(name="Twist L3", default=0)

class EZTree_LeafProps(bpy.types.PropertyGroup):
    type: EnumProperty(items=enum_to_items(LeafType), name="Leaf Type", default=LeafType.Oak.value)
    billboard: EnumProperty(items=enum_to_items(Billboard), name="Billboard", default=Billboard.Double.value)
    angle: FloatProperty(name="Angle", default=10)
    count: IntProperty(name="Count", default=5) # Default increased slightly for visibility? No keep default 1? 1 is very low. JS default was 1? No check default. JS default was 1.
    start: FloatProperty(name="Start", default=0, min=0, max=1)
    size: FloatProperty(name="Size", default=2.5)
    sizeVariance: FloatProperty(name="Size Variance", default=0.7)
    tint: FloatVectorProperty(name="Tint", subtype='COLOR', default=(1,1,1), min=0, max=1)
    alphaTest: FloatProperty(name="Alpha Test", default=0.5, min=0, max=1)

class EZTree_Props(bpy.types.PropertyGroup):
    seed: IntProperty(name="Seed", default=0)
    type: EnumProperty(items=enum_to_items(TreeType), name="Tree Type", default=TreeType.Deciduous.value)
    bark: PointerProperty(type=EZTree_BarkProps)
    branch: PointerProperty(type=EZTree_BranchProps)
    leaves: PointerProperty(type=EZTree_LeafProps)

def register():
    bpy.utils.register_class(EZTree_BarkProps)
    bpy.utils.register_class(EZTree_BranchProps)
    bpy.utils.register_class(EZTree_LeafProps)
    bpy.utils.register_class(EZTree_Props)
    
    bpy.types.Scene.eztree_props = PointerProperty(type=EZTree_Props)

def unregister():
    del bpy.types.Scene.eztree_props
    
    bpy.utils.unregister_class(EZTree_Props)
    bpy.utils.unregister_class(EZTree_LeafProps)
    bpy.utils.unregister_class(EZTree_BranchProps)
    bpy.utils.unregister_class(EZTree_BarkProps)
