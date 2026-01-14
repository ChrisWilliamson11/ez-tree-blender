from .params import TreeOptions, BarkOptions, BranchOptions, LeafOptions
from .enums import BarkType, Billboard, LeafType, TreeType

def props_to_options(props) -> TreeOptions:
    opts = TreeOptions()
    
    opts.seed = props.seed
    opts.type = TreeType(props.type)
    
    # Bark
    opts.bark.type = BarkType(props.bark.type)
    # Tint conversion (Vector to int hex? No, THREE.Color logic. 
    # original JS used hex integer for tint. Ported generator uses what?
    # Generator uses nothing for color yet (just creates mesh), but if we add materials...
    # Let's keep it structurally similar. 
    # But wait, generator doesn't use tint yet except maybe eventually for material.
    # We will pass the tint as is or convert. 
    # `params.py` defines tint as int.
    r, g, b = props.bark.tint
    opts.bark.tint = (int(r * 255) << 16) + (int(g * 255) << 8) + int(b * 255)
    
    opts.bark.flatShading = props.bark.flatShading
    opts.bark.textured = props.bark.textured
    opts.bark.textureScale = {'x': props.bark.textureScaleX, 'y': props.bark.textureScaleY}
    
    # Branch
    b = props.branch
    opts.branch.levels = b.levels
    
    opts.branch.angle = {
        1: b.angle_1, 2: b.angle_2, 3: b.angle_3
    }
    opts.branch.children = {
        0: b.children_0, 1: b.children_1, 2: b.children_2
    }
    opts.branch.force = {
        'direction': {'x': b.force_dir[0], 'y': b.force_dir[1], 'z': b.force_dir[2]},
        'strength': b.force_strength
    }
    opts.branch.gnarliness = {
        0: b.gnarliness_0, 1: b.gnarliness_1, 2: b.gnarliness_2, 3: b.gnarliness_3
    }
    opts.branch.length = {
        0: b.length_0, 1: b.length_1, 2: b.length_2, 3: b.length_3
    }
    opts.branch.radius = {
        0: b.radius_0, 1: b.radius_1, 2: b.radius_2, 3: b.radius_3
    }
    opts.branch.sections = {
        0: b.sections_0, 1: b.sections_1, 2: b.sections_2, 3: b.sections_3
    }
    opts.branch.segments = {
        0: b.segments_0, 1: b.segments_1, 2: b.segments_2, 3: b.segments_3
    }
    opts.branch.start = {
        1: b.start_1, 2: b.start_2, 3: b.start_3
    }
    opts.branch.taper = {
        0: b.taper_0, 1: b.taper_1, 2: b.taper_2, 3: b.taper_3
    }
    opts.branch.twist = {
        0: b.twist_0, 1: b.twist_1, 2: b.twist_2, 3: b.twist_3
    }
    
    # Leaves
    l = props.leaves
    opts.leaves.type = LeafType(l.type)
    opts.leaves.billboard = Billboard(l.billboard)
    opts.leaves.angle = l.angle
    opts.leaves.count = l.count
    opts.leaves.start = l.start
    opts.leaves.size = l.size
    opts.leaves.sizeVariance = l.sizeVariance
    
    r, g, b = l.tint
    opts.leaves.tint = (int(r * 255) << 16) + (int(g * 255) << 8) + int(b * 255)
    
    opts.leaves.alphaTest = l.alphaTest
    
    return opts
