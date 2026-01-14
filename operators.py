import bpy
from .generator import TreeGenerator
from .utils import props_to_options

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
        
        # Parent leaves to branches
        leaf_obj.parent = branch_obj
        
        # Select the tree
        bpy.ops.object.select_all(action='DESELECT')
        branch_obj.select_set(True)
        context.view_layer.objects.active = branch_obj
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(EZTree_OT_Generate)

def unregister():
    bpy.utils.unregister_class(EZTree_OT_Generate)
