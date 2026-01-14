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
    
    # Get or create Principled BSDF
    bsdf = None
    for n in tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if not bsdf:
        bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        
    # Get Link to Output
    # Ensure BSDF is connected to Output
    out_node = None
    for n in tree.nodes:
        if n.type == 'OUTPUT_MATERIAL':
            out_node = n
            break
    if not out_node:
        out_node = tree.nodes.new('ShaderNodeOutputMaterial')
        out_node.location = (300, 0)
        
    if not bsdf.outputs[0].is_linked:
        tree.links.new(bsdf.outputs[0], out_node.inputs[0])
        
    # Helper to clean up specific nodes (simple approach: clear all except Output and BSDF? No, expensive.
    # Reuse nodes if they exist.)
    
    # For simplicity in this "Live" caching: 
    # Check if we already have the setup. 
    # We identify nodes by Name/Label or checking links.
    
    # Texture Logic
    should_texture = type_name and props and getattr(props, 'textured', True)
    
    # Mapping and Coord Nodes
    tex_coord = tree.nodes.get('EZ_TexCoord')
    mapping = tree.nodes.get('EZ_Mapping')
    
    if should_texture:
        if not tex_coord:
            tex_coord = tree.nodes.new('ShaderNodeTexCoord')
            tex_coord.name = 'EZ_TexCoord'
            tex_coord.location = (-900, 0)
            
        if not mapping:
            mapping = tree.nodes.new('ShaderNodeMapping')
            mapping.name = 'EZ_Mapping'
            mapping.label = "EZ Mapping"
            mapping.location = (-700, 0)
            tree.links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
            
        # Update Scale
        if is_bark and props:
            # Check for scale props
            sx = getattr(props, 'textureScaleX', 1.0)
            sy = getattr(props, 'textureScaleY', 1.0)
            mapping.inputs['Scale'].default_value = (sx, sy, 1.0)
        else:
            mapping.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    
    # Function to get/create Image Node
    def get_image_node(node_name, y_loc):
        node = tree.nodes.get(node_name)
        newly_created = False
        if not node:
            node = tree.nodes.new('ShaderNodeTexImage')
            node.name = node_name
            node.location = (-500, y_loc)
            newly_created = True
        return node, newly_created

    base_path = get_asset_path()
    
    # --- Base Color ---
    # Always needed. 
    # If Textured: Mix(Multiply, Image, Color) -> BSDF
    # If Not: Color -> BSDF
    
    # Check for Mix Node
    mix_color = tree.nodes.get('EZ_MixColor')
    tex_color = tree.nodes.get('EZ_TexColor')
    
    if should_texture and is_bark:
         t = type_name.lower()
         img_path = os.path.join(base_path, "bark", f"{t}_color_1k.jpg")
         img = load_image(img_path)
         
         if img:
             tex_color, _ = get_image_node('EZ_TexColor', 300)
             tex_color.image = img
             tree.links.new(mapping.outputs['Vector'], tex_color.inputs['Vector'])
             
             if not mix_color:
                 mix_color = tree.nodes.new('ShaderNodeMixRGB')
                 mix_color.name = 'EZ_MixColor'
                 mix_color.blend_type = 'MULTIPLY'
                 mix_color.inputs[0].default_value = 1.0
                 mix_color.location = (-200, 300)
             
             mix_color.inputs[2].default_value = (color[0], color[1], color[2], 1.0)
             tree.links.new(tex_color.outputs['Color'], mix_color.inputs[1])
             tree.links.new(mix_color.outputs['Color'], bsdf.inputs['Base Color'])
         else:
             # Fallback to color
             bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
             
    elif should_texture and not is_bark: # Leaves
         t = type_name.lower()
         img_path = os.path.join(base_path, "leaves", f"{t}_color.png")
         img = load_image(img_path)
         
         if img:
             tex_color, _ = get_image_node('EZ_TexColor', 300)
             tex_color.image = img
             # Leaves typically use default mapping (UV map creates individual leaf UVs)
             # But if we want scale? Usually scale 1 for leaves on quad.
             tree.links.new(mapping.outputs['Vector'], tex_color.inputs['Vector'])
             
             if not mix_color:
                 mix_color = tree.nodes.new('ShaderNodeMixRGB')
                 mix_color.name = 'EZ_MixColor'
                 mix_color.blend_type = 'MULTIPLY'
                 mix_color.inputs[0].default_value = 1.0
                 mix_color.location = (-200, 300)
             
             mix_color.inputs[2].default_value = (color[0], color[1], color[2], 1.0)
             tree.links.new(tex_color.outputs['Color'], mix_color.inputs[1])
             tree.links.new(mix_color.outputs['Color'], bsdf.inputs['Base Color'])
             
             # Alpha
             tree.links.new(tex_color.outputs['Alpha'], bsdf.inputs['Alpha'])
             mat.blend_method = 'CLIP'
         else:
             bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
             
    else:
        # Not textured or Texture failed
        # Remove Mix if exists? Or just unhook.
        bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
        # Unlink BSDF Color input if linked
        if bsdf.inputs['Base Color'].is_linked:
             tree.links.remove(bsdf.inputs['Base Color'].links[0])


    # --- Normal Map (Bark Only) ---
    tex_norm = tree.nodes.get('EZ_TexNorm')
    norm_map = tree.nodes.get('EZ_NormMap')
    
    if should_texture and is_bark:
         t = type_name.lower()
         img_path = os.path.join(base_path, "bark", f"{t}_normal_1k.jpg")
         img = load_image(img_path)
         if img:
             tex_norm, _ = get_image_node('EZ_TexNorm', 0)
             tex_norm.image = img
             tex_norm.image.colorspace_settings.name = 'Non-Color'
             tree.links.new(mapping.outputs['Vector'], tex_norm.inputs['Vector'])
             
             if not norm_map:
                 norm_map = tree.nodes.new('ShaderNodeNormalMap')
                 norm_map.name = 'EZ_NormMap'
                 norm_map.location = (-200, 0)
            
             tree.links.new(tex_norm.outputs['Color'], norm_map.inputs['Color'])
             tree.links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])
    else:
         # Unlink Normal
         if bsdf.inputs['Normal'].is_linked:
             tree.links.remove(bsdf.inputs['Normal'].links[0])
             
    # --- Roughness (Bark Only) ---
    tex_rough = tree.nodes.get('EZ_TexRough')
    if should_texture and is_bark:
         t = type_name.lower()
         img_path = os.path.join(base_path, "bark", f"{t}_roughness_1k.jpg")
         img = load_image(img_path)
         if img:
             tex_rough, _ = get_image_node('EZ_TexRough', -300)
             tex_rough.image = img
             tex_rough.image.colorspace_settings.name = 'Non-Color'
             tree.links.new(mapping.outputs['Vector'], tex_rough.inputs['Vector'])
             tree.links.new(tex_rough.outputs['Color'], bsdf.inputs['Roughness'])
    else:
         if bsdf.inputs['Roughness'].is_linked:
             tree.links.remove(bsdf.inputs['Roughness'].links[0])

    return mat

def update_existing_materials(obj):
    if not obj or not hasattr(obj, "eztree_props"):
        return
    
    props = obj.eztree_props
    
    # Update Bark
    # Need to find bark material. Usually slot 0 on branch obj.
    # Determine which object is branch.
    branch_obj = None
    leaf_obj = None
    
    if "TreeBranch" in obj.name:
        branch_obj = obj
        if obj.children and "TreeLeaf" in obj.children[0].name:
             leaf_obj = obj.children[0]
    elif "TreeLeaf" in obj.name and obj.parent:
        leaf_obj = obj
        branch_obj = obj.parent
        
    if branch_obj:
        ensure_material("EZTree_Bark", props.bark.tint, 
                        type_name=props.bark.type, 
                        is_bark=True, 
                        props=props.bark)
                        
    if leaf_obj:
        ensure_material("EZTree_Leaf", props.leaves.tint, 
                       type_name=props.leaves.type, 
                       is_bark=False, 
                       props=props.leaves)


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
