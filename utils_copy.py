from .properties import EZTree_Props

def copy_options_to_props(options, target_props):
    # This might be needed if we want to copy from TreeOptions back to property group
    # But usually we copy property group to property group
    pass

def copy_props(source_props, target_props):
    target_props.seed = source_props.seed
    target_props.type = source_props.type
    
    # Bark
    t_b = target_props.bark
    s_b = source_props.bark
    t_b.type = s_b.type
    t_b.tint = s_b.tint
    t_b.flatShading = s_b.flatShading
    t_b.textured = s_b.textured
    t_b.textureScaleX = s_b.textureScaleX
    t_b.textureScaleY = s_b.textureScaleY
    
    # Leaves
    t_l = target_props.leaves
    s_l = source_props.leaves
    t_l.type = s_l.type
    t_l.billboard = s_l.billboard
    t_l.angle = s_l.angle
    t_l.count = s_l.count
    t_l.start = s_l.start
    t_l.size = s_l.size
    t_l.sizeVariance = s_l.sizeVariance
    t_l.tint = s_l.tint
    t_l.alphaTest = s_l.alphaTest
    
    # Branch
    t_br = target_props.branch
    s_br = source_props.branch
    t_br.levels = s_br.levels
    
    for i in range(1, 4):
        setattr(t_br, f"angle_{i}", getattr(s_br, f"angle_{i}"))
        setattr(t_br, f"start_{i}", getattr(s_br, f"start_{i}"))
    
    for i in range(3):
        setattr(t_br, f"children_{i}", getattr(s_br, f"children_{i}"))
    
    t_br.force_dir = s_br.force_dir
    t_br.force_strength = s_br.force_strength
    
    for i in range(4):
        for attr in ["gnarliness", "length", "radius", "sections", "segments", "taper", "twist"]:
            setattr(t_br, f"{attr}_{i}", getattr(s_br, f"{attr}_{i}"))
