from .enums import BarkType, Billboard, LeafType, TreeType
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class BarkOptions:
    type: BarkType = BarkType.Oak
    tint: int = 0xffffff
    flatShading: bool = False
    textured: bool = True
    textureScale: Dict[str, float] = field(default_factory=lambda: {'x': 1, 'y': 1})

@dataclass
class BranchOptions:
    levels: int = 3
    # Using dictionaries to map levels to values as per original JS structure
    angle: Dict[int, float] = field(default_factory=lambda: {1: 70, 2: 60, 3: 60})
    children: Dict[int, int] = field(default_factory=lambda: {0: 7, 1: 7, 2: 5})
    force: Dict[str, Any] = field(default_factory=lambda: {'direction': {'x': 0, 'y': 1, 'z': 0}, 'strength': 0.01})
    gnarliness: Dict[int, float] = field(default_factory=lambda: {0: 0.15, 1: 0.2, 2: 0.3, 3: 0.02})
    length: Dict[int, float] = field(default_factory=lambda: {0: 20, 1: 20, 2: 10, 3: 1})
    radius: Dict[int, float] = field(default_factory=lambda: {0: 1.5, 1: 0.7, 2: 0.7, 3: 0.7})
    sections: Dict[int, int] = field(default_factory=lambda: {0: 12, 1: 10, 2: 8, 3: 6})
    segments: Dict[int, int] = field(default_factory=lambda: {0: 8, 1: 6, 2: 4, 3: 3})
    start: Dict[int, float] = field(default_factory=lambda: {1: 0.4, 2: 0.3, 3: 0.3})
    taper: Dict[int, float] = field(default_factory=lambda: {0: 0.7, 1: 0.7, 2: 0.7, 3: 0.7})
    twist: Dict[int, float] = field(default_factory=lambda: {0: 0, 1: 0, 2: 0, 3: 0})

@dataclass
class LeafOptions:
    type: LeafType = LeafType.Oak
    billboard: Billboard = Billboard.Double
    angle: float = 10
    count: int = 1
    start: float = 0
    size: float = 2.5
    sizeVariance: float = 0.7
    tint: int = 0xffffff
    alphaTest: float = 0.5

class TreeOptions:
    def __init__(self):
        self.seed = 0
        self.type = TreeType.Deciduous
        self.bark = BarkOptions()
        self.branch = BranchOptions()
        self.leaves = LeafOptions()

    def copy(self, source, target=None):
        if target is None:
            target = self
        
        # If source is a dictionary (like from JSON or kwargs)
        source_dict = source if isinstance(source, dict) else source.__dict__

        for key, value in source_dict.items():
            if hasattr(target, key):
                target_attr = getattr(target, key)
                
                # Check if we need to recurse (if target attribute is one of our option classes)
                if isinstance(target_attr, (BarkOptions, BranchOptions, LeafOptions)):
                     self.copy(value, target_attr)
                else:
                    setattr(target, key, value)
