from enum import Enum

class BarkType(Enum):
    Birch = 'birch'
    Oak = 'oak'
    Pine = 'pine'
    Willow = 'willow'

class Billboard(Enum):
    Single = 'single'
    Double = 'double'

class LeafType(Enum):
    Ash = 'ash'
    Aspen = 'aspen'
    Pine = 'pine'
    Oak = 'oak'

class TreeType(Enum):
    Deciduous = 'deciduous'
    Evergreen = 'evergreen'
