bl_info = {
    "name": "EZ-Tree Blender",
    "author": "Antigravity (Port of EZ-Tree by dgreenheck)",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > N-Panel > EZ-Tree",
    "description": "Procedural Tree Generator Port",
    "category": "Add Mesh",
}

import bpy
from . import properties
from . import ui
from . import operators

def register():
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
