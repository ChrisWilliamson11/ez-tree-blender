import bpy
from .wind import add_wind_modifier

class EZTree_OT_AddWind(bpy.types.Operator):
    bl_idname = "eztree.add_wind"
    bl_label = "Add Wind"
    bl_description = "Add Geometry Nodes Wind Modifier to selected object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Please select a mesh object.")
            return {'CANCELLED'}
        
        add_wind_modifier(obj)
        
        # Add driver for Time?
        # Or just let user animate it. Driver is easier for instant gratification.
        mod = obj.modifiers.get("EZTree_Wind")
        if mod:
            # Add driver to input 2 (Time) - Index depends on inputs
            # Input 0: Geometry, 1: Time
            # mod.node_group.inputs doesn't correspond 1:1 to mod properties dictionary access
            # usually mod["Socket_Name"]
            
            # Find the identifier for "Time"
            # It's usually "Socket_2" or similar internal name.
            # But we can access inputs by name via the node group interface logic implicitly.
            # Actually, `mod[identifier]` is how we set values.
            
            # Let's frame # driver
            # We need to know the property name.
            # Usually we can look at `mod.keys()`
            # Safe bet: #frame / 24.
            # Find "Time" input identifier
            ng = mod.node_group
            time_id = None
            
            # Blender 4.0+
            if hasattr(ng, "interface"):
                for item in ng.interface.items_tree:
                    if item.name == "Time":
                        time_id = item.identifier
                        break
            # Blender < 4.0
            elif hasattr(ng, "inputs"):
                for item in ng.inputs:
                    if item.name == "Time":
                        time_id = item.identifier
                        break
            
            if time_id:
                # Add Driver: frame / 24.0
                d = mod.driver_add(f'["{time_id}"]')
                d.driver.expression = "frame / 24.0"

        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(EZTree_OT_AddWind)

def unregister():
    bpy.utils.unregister_class(EZTree_OT_AddWind)
