import bpy

def add_wind_modifier(obj):
    # Ensure object is a Mesh
    if obj.type != 'MESH':
        return

    # Check if modifier exists
    mod_name = "EZTree_Wind"
    mod = obj.modifiers.get(mod_name)
    if not mod:
        mod = obj.modifiers.new(name=mod_name, type='NODES')
    
    # Check if node group exists
    group_name = "EZTree_Wind_NodeGroup"
    node_group = bpy.data.node_groups.get(group_name)
    if not node_group:
        node_group = create_wind_node_group(group_name)
    
    mod.node_group = node_group
    
    # Set default input values if needed
    # (Node group defaults handle this)

def create_wind_node_group(name):
    # Create new node group
    ng = bpy.data.node_groups.new(name=name, type='GeometryNodeTree')
    
    # Interface
    # Inputs: Geometry, Time, Wind Scale, Wind Strength
    # Outputs: Geometry
    
    # Cleaner way for 4.0+ interface vs 3.x... using explicit node creation for simplicity/compatibility
    # We will just use Group Input / Group Output nodes and configure them
    
    input_node = ng.nodes.new('NodeGroupInput')
    output_node = ng.nodes.new('NodeGroupOutput')
    input_node.location = (-800, 0)
    output_node.location = (800, 0)
    
    # Setup Inputs (Blender 4.0+ uses interface items, 3.6 uses inputs.new)
    # Check version? Let's try flexible approach or assume 4.0? 
    # User didn't specify version. 3.6 LTS or 4.0 usually. 
    # Use 'interface.new_socket' for 4.0+ if available, else 'inputs.new'.
    
    def create_socket(is_input, name, socket_type):
        collection = ng.interface.new_socket(name, in_out='INPUT' if is_input else 'OUTPUT', socket_type=socket_type)
        return collection
        
    # Attempt 4.0 API
    try:
        # Input Sockets
        # geometry comes default usually? No, must create.
        if not ng.interface.items_tree: # empty
             ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
             ng.interface.new_socket("Time", in_out='INPUT', socket_type='NodeSocketFloat')
             ng.interface.new_socket("Scale", in_out='INPUT', socket_type='NodeSocketFloat')
             ng.interface.new_socket("Strength", in_out='INPUT', socket_type='NodeSocketVector')
             
             ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
        
    except AttributeError:
        # Fallback for < 4.0 (inputs/outputs list)
        ng.inputs.new('NodeSocketGeometry', 'Geometry')
        ng.inputs.new('NodeSocketFloat', 'Time')
        ng.inputs.new('NodeSocketFloat', 'Scale')
        ng.inputs.new('NodeSocketVector', 'Strength')
        ng.outputs.new('NodeSocketGeometry', 'Geometry')
    
    # Defaults
    # Setting defaults on the node group inputs is tricky via API across versions.
    # We'll set them on the modifier usually.
    
    # Create Nodes
    
    # Position
    pos_node = ng.nodes.new('GeometryNodeInputPosition')
    pos_node.location = (-600, 200)
    
    # Vector Math: Scale Position (Pos / Scale)
    vec_scale = ng.nodes.new('ShaderNodeVectorMath')
    vec_scale.operation = 'DIVIDE'
    vec_scale.location = (-400, 200)
    
    # Noise Texture (4D)
    noise = ng.nodes.new('ShaderNodeTexNoise')
    noise.noise_dimensions = '4D'
    noise.location = (-200, 200)
    
    # Vector Math: Subtract 0.5 (Center noise around 0)
    vec_sub = ng.nodes.new('ShaderNodeVectorMath')
    vec_sub.operation = 'SUBTRACT'
    vec_sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    vec_sub.location = (0, 200)
    
    # Vector Math: Multiply by Strength
    vec_mult = ng.nodes.new('ShaderNodeVectorMath')
    vec_mult.operation = 'MULTIPLY'
    vec_mult.location = (200, 200)
    
    # Set Position
    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    set_pos.location = (400, 0)
    
    # Linkage
    links = ng.links
    
    # Input Geometry -> Set Pos Geometry
    links.new(input_node.outputs[0], set_pos.inputs['Geometry'])
    # Set Pos Geometry -> Output
    links.new(set_pos.outputs['Geometry'], output_node.inputs[0])
    
    # Input Time -> Noise W
    # Input node outputs index depends on creation order. 0=Geo, 1=Time, 2=Scale, 3=Strength
    links.new(input_node.outputs[1], noise.inputs['W'])
    
    # Input Scale -> Vec Scale (Divide by Scale)
    # Position -> Vec Scale [0]
    links.new(pos_node.outputs['Position'], vec_scale.inputs[0])
    # Scale -> Vec Scale [1] (Wait, Vector Divide by Float? No, Vector Math Divide expects Vector.
    # Need to verify if Vector Math accepts Float connection to Vector input (implicit conversion). Yes usually.)
    links.new(input_node.outputs[2], vec_scale.inputs[1])
    
    # Vec Scale -> Noise Vector
    links.new(vec_scale.outputs['Vector'], noise.inputs['Vector'])
    
    # Noise Color -> Vec Sub
    links.new(noise.outputs['Color'], vec_sub.inputs[0])
    
    # Vec Sub -> Vec Mult
    links.new(vec_sub.outputs['Vector'], vec_mult.inputs[0])
    
    # Input Strength -> Vec Mult [1]
    links.new(input_node.outputs[3], vec_mult.inputs[1])
    
    # Vec Mult -> Set Pos Offset
    links.new(vec_mult.outputs['Vector'], set_pos.inputs['Offset'])
    
    return ng
