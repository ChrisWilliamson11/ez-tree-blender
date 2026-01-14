import bpy
import bmesh
from math import radians
from .generator import TreeGenerator
from .utils import props_to_options
from .utils_copy import copy_props

def update_existing_tree(obj):
    if not obj or not hasattr(obj, "eztree_props"):
        return

    # Check if we are already updating (avoid recursion loop if property update triggers another update)
    # Using a simple check if possible, or assume Blender handles property update loop prevention reasonably well
    # (it does usually, unless we set property inside update).
    
    # We are setting mesh data, not properties, so safe.
    
    props = obj.eztree_props
    options = props_to_options(props)
    
    # Generate new mesh data
    generator = TreeGenerator(options)
    # We need to access generating geometry only, not creating new objects
    # generator.generate() creates mesh datablocks currently.
    # We should reuse existing meshes if possible or swap them.
    
    # Generator returns (branch_mesh, leaf_mesh)
    new_branch_mesh, new_leaf_mesh = generator.generate()
    
    # Identify which object part this is
    # The `obj` passed might be the parent (branch) or child (leaf).
    # Current structure: Branch Object -> Leaf Object (child)
    
    branch_obj = None
    leaf_obj = None
    
    if "TreeBranch" in obj.name or (obj.children and "TreeLeaf" in obj.children[0].name):
        branch_obj = obj
        if obj.children:
            leaf_obj = obj.children[0]
    elif "TreeLeaf" in obj.name and obj.parent:
        leaf_obj = obj
        branch_obj = obj.parent
        
    # If we can't find the pair, maybe it was separated.
    # We'll rely on the object passed being the one holding properties (Branch).
    # If `obj` is leaf, it might not have props if we only copy to root.
    # We should enable copy on root only.
    
    if branch_obj:
        # Swap mesh data
        old_mesh = branch_obj.data
        branch_obj.data = new_branch_mesh
        
        # Assign Material
        bark_mat = ensure_material("EZTree_Bark", props.bark.tint,
                                   type_name=props.bark.type,
                                   is_bark=True,
                                   props=props.bark)
        if branch_obj.data.materials:
            branch_obj.data.materials[0] = bark_mat
        else:
            branch_obj.data.materials.append(bark_mat)

        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
            
    if leaf_obj:
         old_mesh = leaf_obj.data
         leaf_obj.data = new_leaf_mesh
         
         # Assign Material
         leaf_mat = ensure_material("EZTree_Leaf", props.leaves.tint,
                                    type_name=props.leaves.type,
                                    is_bark=False,
                                    props=props.leaves)
         if leaf_obj.data.materials:
            leaf_obj.data.materials[0] = leaf_mat
         else:
            leaf_obj.data.materials.append(leaf_mat)

         if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    elif new_leaf_mesh:
         # If leaf object didn't exist but now we have leaves?
         # Create it and parent it
         # This is complex for "update". For now assume structure exists.
         # If leaves count becomes 0, we might want to hide/remove leaf obj options.
         # Creating new leaf obj implies linking to scene?
         pass

import os

def get_asset_path():
    return os.path.join(os.path.dirname(__file__), "assets")

def load_image(filepath):
    if not os.path.exists(filepath):
        return None
    filename = os.path.basename(filepath)
    if filename in bpy.data.images:
        return bpy.data.images[filename]
    return bpy.data.images.load(filepath)

def ensure_material(name, color, type_name=None, is_bark=True, props=None):
    # type_name: e.g. 'oak', 'pine'
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
    if not mat.use_nodes:
        mat.use_nodes = True
        
    tree = mat.node_tree
    bsdf = tree.nodes.get('Principled BSDF')
    if not bsdf:
        bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
        
    # Base Color
    bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    
    # Textures
    if type_name and props and getattr(props, 'textured', True): # Bark usually has 'textured' prop, leaves implied?
        base_path = get_asset_path()
        try:
            if is_bark:
                # Bark Textures: {type}_color_1k.jpg, etc.
                # Types: oak, birch, pine, willow
                # Enum values might be lowercase? Checked enums.py?
                # Using type_name directly.
                t = type_name.lower()
                
                # Color
                color_path = os.path.join(base_path, "bark", f"{t}_color_1k.jpg")
                img = load_image(color_path)
                if img:
                     tex = tree.nodes.new('ShaderNodeTexImage')
                     tex.image = img
                     tex.location = (-300, 300)
                     # Tint Mix?
                     # MixRGB (Multiply) Color * Tint
                     mix = tree.nodes.new('ShaderNodeMixRGB')
                     mix.blend_type = 'MULTIPLY'
                     mix.inputs[0].default_value = 1.0 # Fac
                     mix.inputs[2].default_value = (color[0], color[1], color[2], 1.0)
                     tree.links.new(tex.outputs['Color'], mix.inputs[1])
                     tree.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
                     
                # Normal
                norm_path = os.path.join(base_path, "bark", f"{t}_normal_1k.jpg")
                img_norm = load_image(norm_path)
                if img_norm:
                     tex_n = tree.nodes.new('ShaderNodeTexImage')
                     tex_n.image = img_norm
                     tex_n.image.colorspace_settings.name = 'Non-Color'
                     tex_n.location = (-300, 0)
                     
                     nmap = tree.nodes.new('ShaderNodeNormalMap')
                     nmap.location = (-100, 0)
                     tree.links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
                     tree.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
                     
                # Roughness
                rough_path = os.path.join(base_path, "bark", f"{t}_roughness_1k.jpg")
                img_r = load_image(rough_path)
                if img_r:
                     tex_r = tree.nodes.new('ShaderNodeTexImage')
                     tex_r.image = img_r
                     tex_r.image.colorspace_settings.name = 'Non-Color'
                     tex_r.location = (-300, -300)
                     tree.links.new(tex_r.outputs['Color'], bsdf.inputs['Roughness'])
                     
            else:
                # Leaves: {type}_color.png
                # Alpha test? 
                t = type_name.lower()
                color_path = os.path.join(base_path, "leaves", f"{t}_color.png")
                img = load_image(color_path)
                if img:
                     tex = tree.nodes.new('ShaderNodeTexImage')
                     tex.image = img
                     tex.location = (-300, 300)
                     
                     # Mix Tint
                     mix = tree.nodes.new('ShaderNodeMixRGB')
                     mix.blend_type = 'MULTIPLY'
                     mix.inputs[0].default_value = 1.0
                     mix.inputs[2].default_value = (color[0], color[1], color[2], 1.0)
                     
                     tree.links.new(tex.outputs['Color'], mix.inputs[1])
                     tree.links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
                     
                     # Alpha
                     tree.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
                     
                     # Material Settings for Alpha
                     mat.blend_method = 'CLIP'
                     mat.shadow_method = 'CLIP'
                     
        except Exception as e:
            print(f"Error loading texture: {e}")

    return mat

class EZTree_OT_Generate(bpy.types.Operator):
    bl_idname = "eztree.generate"
    bl_label = "Generate Tree"
    bl_description = "Generate a tree with current settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.eztree_props
        options = props_to_options(props)
        
        generator = TreeGenerator(options)
        branch_mesh, leaf_mesh = generator.generate()
        
        # Link to Scene
        col = context.collection
        
        branch_obj = bpy.data.objects.new("TreeBranch", branch_mesh)
        leaf_obj = bpy.data.objects.new("TreeLeaf", leaf_mesh)
        
        col.objects.link(branch_obj)
        col.objects.link(leaf_obj)
        
        branch_obj.location = context.scene.cursor.location
        leaf_obj.location = context.scene.cursor.location
        
        # Rotation conversion: Y-up (Generator) to Z-up (Blender)
        # Rotate Parent (Branch) X +90
        # Child (Leaf) stays 0 relative to parent if generated in same space
        branch_obj.rotation_euler = (radians(90), 0, 0)
        leaf_obj.rotation_euler = (0, 0, 0)
        
        # Materials
        bark_mat = ensure_material("EZTree_Bark", props.bark.tint, 
                                   type_name=props.bark.type, 
                                   is_bark=True, 
                                   props=props.bark)
                                   
        leaf_mat = ensure_material("EZTree_Leaf", props.leaves.tint, 
                                   type_name=props.leaves.type, 
                                   is_bark=False, 
                                   props=props.leaves)
        
        if branch_obj.data.materials:
            branch_obj.data.materials[0] = bark_mat
        else:
            branch_obj.data.materials.append(bark_mat)
            
        if leaf_obj.data.materials:
            leaf_obj.data.materials[0] = leaf_mat
        else:
            leaf_obj.data.materials.append(leaf_mat)
        
        # Parent leaves to branches
        leaf_obj.parent = branch_obj
        
        # Copy properties
        copy_props(props, branch_obj.eztree_props)
        
        # Select the tree
        bpy.ops.object.select_all(action='DESELECT')
        branch_obj.select_set(True)
        context.view_layer.objects.active = branch_obj
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(EZTree_OT_Generate)

def unregister():
    bpy.utils.unregister_class(EZTree_OT_Generate)
