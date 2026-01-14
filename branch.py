from mathutils import Vector, Euler

class Branch:
    def __init__(
        self,
        origin=None,
        orientation=None,
        length=0,
        radius=0,
        level=0,
        sectionCount=0,
        segmentCount=0,
    ):
        self.origin = origin.copy() if origin else Vector((0, 0, 0))
        self.orientation = orientation.copy() if orientation else Euler((0, 0, 0))
        self.length = length
        self.radius = radius
        self.level = level
        self.sectionCount = sectionCount
        self.segmentCount = segmentCount
