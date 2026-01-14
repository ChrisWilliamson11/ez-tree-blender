import bpy
import json
import os
from .utils import props_to_options
from .enums import TreeType, BarkType, LeafType, Billboard

def get_preset_path():
    return os.path.join(os.path.dirname(__file__), "presets")

def load_preset_json(name):
    path = os.path.join(get_preset_path(), name)
    if not os.path.exists(path):
        print(f"Preset not found: {path}")
        return None
    
    with open(path, 'r') as f:
        return json.load(f)

def apply_preset(props, preset_name):
    json_data = load_preset_json(preset_name)
    if not json_data:
        return

    # Helper function to set property safely
    def set_prop(obj, key, val):
        if hasattr(obj, key):
            # Check for Enum
            # If val is string and prop is enum, assumes value matches enum key/value
            try:
                setattr(obj, key, val)
            except TypeError:
                pass # safely ignore mismatches for now

    # Top Level
    if 'seed' in json_data: props.seed = json_data['seed']
    if 'type' in json_data: props.type = json_data['type']
    
    # Bark
    if 'bark' in json_data:
        b = json_data['bark']
        if 'type' in b: props.bark.type = b['type']
        if 'tint' in b: 
            # JSON tint is int (0xffffff), Blender is Color wrapper? 
            # In properties.py tint is FloatVectorProperty.
            # Need to conver int to rgb
            hex_val = b['tint']
            r = ((hex_val >> 16) & 255) / 255.0
            g = ((hex_val >> 8) & 255) / 255.0
            b_val = (hex_val & 255) / 255.0
            props.bark.tint = (r, g, b_val)
            
        if 'flatShading' in b: props.bark.flatShading = b['flatShading']
        if 'textured' in b: props.bark.textured = b['textured']
        if 'textureScale' in b:
            props.bark.textureScaleX = b['textureScale'].get('x', 1)
            props.bark.textureScaleY = b['textureScale'].get('y', 1)

    # Leaves
    if 'leaves' in json_data:
        l = json_data['leaves']
        if 'type' in l: props.leaves.type = l['type']
        if 'billboard' in l: props.leaves.billboard = l['billboard']
        if 'angle' in l: props.leaves.angle = l['angle']
        if 'count' in l: props.leaves.count = l['count']
        if 'start' in l: props.leaves.start = l['start']
        if 'size' in l: props.leaves.size = l['size']
        if 'sizeVariance' in l: props.leaves.sizeVariance = l['sizeVariance']
        if 'tint' in l:
            hex_val = l['tint']
            r = ((hex_val >> 16) & 255) / 255.0
            g = ((hex_val >> 8) & 255) / 255.0
            b_val = (hex_val & 255) / 255.0
            props.leaves.tint = (r, g, b_val)
        if 'alphaTest' in l: props.leaves.alphaTest = l['alphaTest']

    # Branch
    if 'branch' in json_data:
        br = json_data['branch']
        if 'levels' in br: props.branch.levels = br['levels']
        
        # Mapped dict properties
        def map_dict_prop(json_dict, prop_prefix, target_obj):
             for key, val in json_dict.items():
                 # Key comes in as string "0", "1", etc.
                 prop_name = f"{prop_prefix}_{key}"
                 if hasattr(target_obj, prop_name):
                     setattr(target_obj, prop_name, val)
        
        if 'angle' in br: map_dict_prop(br['angle'], 'angle', props.branch)
        if 'children' in br: map_dict_prop(br['children'], 'children', props.branch)
        if 'gnarliness' in br: map_dict_prop(br['gnarliness'], 'gnarliness', props.branch)
        if 'length' in br: map_dict_prop(br['length'], 'length', props.branch)
        if 'radius' in br: map_dict_prop(br['radius'], 'radius', props.branch)
        if 'sections' in br: map_dict_prop(br['sections'], 'sections', props.branch)
        if 'segments' in br: map_dict_prop(br['segments'], 'segments', props.branch)
        if 'start' in br: map_dict_prop(br['start'], 'start', props.branch)
        if 'taper' in br: map_dict_prop(br['taper'], 'taper', props.branch)
        if 'twist' in br: map_dict_prop(br['twist'], 'twist', props.branch)
        
        if 'force' in br:
            f = br['force']
            if 'direction' in f:
                d = f['direction']
                props.branch.force_dir = (d['x'], d['y'], d['z'])
            if 'strength' in f:
                props.branch.force_strength = f['strength']

class EZTree_OT_LoadPreset(bpy.types.Operator):
    bl_idname = "eztree.load_preset"
    bl_label = "Load Preset"
    bl_description = "Load a tree preset"
    
    filepath: bpy.props.StringProperty()
    preset_name: bpy.props.StringProperty()
    
    def execute(self, context):
        props = context.scene.eztree_props
        apply_preset(props, self.preset_name)
        return {'FINISHED'}

