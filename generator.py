import bpy
import bmesh
import math
from mathutils import Vector, Euler, Quaternion, Matrix
from .rng import RNG
from .branch import Branch
from .enums import BarkType, Billboard, LeafType, TreeType
from .params import TreeOptions

class TreeGenerator:
    def __init__(self, options: TreeOptions):
        self.options = options
        self.rng = None
        self.branch_queue = []
        self.branches_verts = []
        self.branches_normals = [] # Blender calculates normals, but we might want them custom? For now, let's rely on Blender's auto smooth or calc_normals.
        self.branches_indices = []
        self.branches_uvs = []
        self.leaves_verts = []
        self.leaves_normals = []
        self.leaves_indices = []
        self.leaves_uvs = []
        
    def generate(self):
        # Reset geometry data
        self.branches_verts = []
        self.branches_normals = []
        self.branches_indices = []
        self.branches_uvs = []
        
        self.leaves_verts = []
        self.leaves_normals = []
        self.leaves_indices = []
        self.leaves_uvs = []
        
        self.branch_queue = []

        self.rng = RNG(self.options.seed)

        # Create the trunk
        self.branch_queue.append(
            Branch(
                origin=Vector((0, 0, 0)),
                orientation=Euler((0, 0, 0)),
                length=self.options.branch.length[0],
                radius=self.options.branch.radius[0],
                level=0,
                sectionCount=self.options.branch.sections[0],
                segmentCount=self.options.branch.segments[0],
            )
        )

        while len(self.branch_queue) > 0:
            branch = self.branch_queue.pop(0)
            self.generate_branch(branch)

        return self.create_mesh()

    def generate_branch(self, branch: Branch):
        index_offset = len(self.branches_verts) # Vertices are Vectors, so just count of items
        
        section_orientation = branch.orientation.copy() # Euler
        section_origin = branch.origin.copy() # Vector
        
        # Calculate section length
        divisor = (self.options.branch.levels - 1) if self.options.type == TreeType.Deciduous else 1
        # Avoid division by zero if levels is 1 (trunk only)
        if divisor == 0: divisor = 1
        
        section_length = branch.length / branch.sectionCount / divisor

        sections = []

        for i in range(branch.sectionCount + 1):
            section_radius = branch.radius

            # Radius tapering logic
            if i == branch.sectionCount and branch.level == self.options.branch.levels:
                section_radius = 0.001
            elif self.options.type == TreeType.Deciduous:
                taper = self.options.branch.taper.get(branch.level, 0.7)
                section_radius *= (1 - taper * (i / branch.sectionCount))
            elif self.options.type == TreeType.Evergreen:
                section_radius *= (1 - (i / branch.sectionCount))

            # Generate segments
            first_vertex_data = None
            
            # Helper to rotate vector by Euler (Blender specific)
            # Blender Euler rotation order is usually XYZ, Three.js default is XYZ.
            # mathutils Euler can be converted to Matrix or Quaternion for rotation.
            
            # We need a consistent rotation handling.
            # Tree.js: vertex.applyEuler(sectionOrientation)
            # Blender: vector.rotate(sectionOrientation) works if sectionOrientation is Euler? No.
            # vector.rotate(rotation) where rotation is Euler, Quat, or Axis-Angle. 
            
            for j in range(branch.segmentCount):
                angle = (2.0 * math.pi * j) / branch.segmentCount
                
                # Create vertex (in local circle space)
                # Three.js: new THREE.Vector3(Math.cos(angle), 0, Math.sin(angle)).multiplyScalar(sectionRadius)
                # Note: Y-up in Three.js? The cylinder seems to grow along Y?
                # "new THREE.Vector3(0, sectionLength, 0).applyEuler(sectionOrientation)" -> Growing along Y.
                # So the circle is in XZ plane.
                
                vertex = Vector((math.cos(angle), 0, math.sin(angle))) * section_radius
                
                # Apply rotation
                # Logic: vertex.applyEuler(sectionOrientation)
                vertex.rotate(section_orientation)
                
                # Translate
                vertex += section_origin
                
                # Normal (normalized direction from center)
                normal = Vector((math.cos(angle), 0, math.sin(angle)))
                normal.rotate(section_orientation)
                normal.normalize()
                
                uv = Vector((j / branch.segmentCount, 0 if (i % 2 == 0) else 1))
                
                self.branches_verts.append(vertex)
                # self.branches_normals.append(normal) # TODO: Store normals if using custom normals
                self.branches_uvs.append(uv)
                
                if j == 0:
                    first_vertex_data = (vertex, normal, uv)

            # Duplicate first vertex for UV continuity
            if first_vertex_data:
                self.branches_verts.append(first_vertex_data[0])
                # self.branches_normals.append(first_vertex_data[1])
                self.branches_uvs.append(Vector((1.0, first_vertex_data[2].y)))

            # Store section info for children
            sections.append({
                'origin': section_origin.copy(),
                'orientation': section_orientation.copy(), # Euler
                'radius': section_radius
            })

            # Move origin for next section
            # Three.js: new THREE.Vector3(0, sectionLength, 0).applyEuler(sectionOrientation)
            move_step = Vector((0, section_length, 0))
            move_step.rotate(section_orientation)
            section_origin += move_step

            # Perturb orientation (Gnarliness)
            gnarliness_val = self.options.branch.gnarliness.get(branch.level, 0.1)
            # gnarliness math from JS: Math.max(1, 1 / Math.sqrt(sectionRadius)) * gnarliness
            if section_radius > 0:
                gnarliness_scale = max(1.0, 1.0 / math.sqrt(section_radius)) * gnarliness_val
            else:
                gnarliness_scale = gnarliness_val
            
            # Random perturbations
            rx = self.rng.random(gnarliness_scale, -gnarliness_scale)
            rz = self.rng.random(gnarliness_scale, -gnarliness_scale)
            
            # sectionOrientation.x += rx ...
            # Blender Euler is accessible by .x .y .z
            # But direct Euler manipulation can be susceptible to Gimbal lock differently.
            # Three.js does simple addition on Euler components here.
            
            new_x = section_orientation.x + rx
            new_z = section_orientation.z + rz
            section_orientation.x = new_x
            section_orientation.z = new_z

            # Apply forces (Twist and Growth Force)
            # JS: qSection.makeRotationFromEuler(sectionOrientation)
            q_section = section_orientation.to_quaternion()
            
            # Twist
            twist_angle = self.options.branch.twist.get(branch.level, 0)
            q_twist = Quaternion(Vector((0, 1, 0)), twist_angle)
            
            # Force
            force_dir = Vector((
                self.options.branch.force['direction']['x'],
                self.options.branch.force['direction']['y'],
                self.options.branch.force['direction']['z']
            ))
            
            # qForce.setFromUnitVectors(Vector3(0, 1, 0), force_dir)
            # Blender: rotation_difference between two vectors
            # rotation_difference(v1, v2) -> Calculates rotation to transform v1 into v2
            q_force = Vector((0, 1, 0)).rotation_difference(force_dir)
            
            # qSection.multiply(qTwist)
            q_section = q_section @ q_twist
            
            # qSection.rotateTowards(qForce, strength/radius)
            # Emulate rotateTowards
            # Determine angular distance to qForce
            strength = self.options.branch.force['strength']
            step = strength / section_radius if section_radius > 0.0001 else 0
            
            # Slerp towards qForce by step amount?
            # JS rotateTowards logic: step is angle in radians.
            # angle = q.angleTo(target)
            # if angle == 0 return
            # t = min(1, step / angle)
            # slerp(target, t)
            
            # Blender methods
            # diff = q_section.rotation_difference(q_force) -> returns quat representing difference.
            # angle = diff.angle
            
            # Simpler approach: slerp with factor?
            # We need the angle between the two quaternions.
            # There isn't a direct "angle_to" in mathutils.Quaternion (it has .angle which is the w-construct angle)
            # We can use dot product or rotation_difference angle.
            
            # q_section.slerp(q_force, factor)
            # We need to compute factor based on step/total_angle
            
            # Let's approximate or just use slerp with a small fixed factor if hard?
            # No, let's try to match logic. 
            # q_section is current, q_force is target.
            
            # We can just apply the force as a small rotation? 
            # JS: qSection becomes the result.
            
            current_up = Vector((0,1,0))
            current_up.rotate(q_section)
            # Angle between current up and force dir?
            
            # Let's trust Blender's slerp works by t [0,1].
            # We need to know 't'.
            # t = step / total_angle.
            # How to get total_angle between two quaternions?
            # q1.dot(q2) gives cosine of half angle?
            
            dot = q_section.dot(q_force)
            if dot < 0:
                # Use -q_force to take shortest path and ensure positive dot
                # q_force_target = -q_force # Unary negation of quat?
                # mathutils Quaternion supports negation
                 q_force_target = -q_force
                 dot = -dot
            else:
                 q_force_target = q_force

            if dot > 0.9999:
                pass # close enough
            else:
                # angle = 2 * acos(dot)
                theta = 2 * math.acos(min(max(dot, -1), 1))
                if theta > 0.0001:
                    t = min(1, step / theta)
                    q_section.slerp(q_force_target, t)
            
            section_orientation = q_section.to_euler()

        # Generate Indices (Faces)
        self.generate_branch_indices(index_offset, branch)

        # Decide on next steps (Child branches or leaves)
        if self.options.type == TreeType.Deciduous:
            last_section = sections[-1]
            if branch.level < self.options.branch.levels:
                self.branch_queue.append(Branch(
                    origin=last_section['origin'],
                    orientation=last_section['orientation'],
                    length=self.options.branch.length.get(branch.level + 1, 10),
                    radius=last_section['radius'],
                    level=branch.level + 1,
                    sectionCount=branch.sectionCount,
                    segmentCount=branch.segmentCount
                ))
            else:
                self.generate_leaf(last_section['origin'], last_section['orientation'])

        if branch.level == self.options.branch.levels:
            self.generate_leaves(sections)
        elif branch.level < self.options.branch.levels:
             child_count = self.options.branch.children.get(branch.level, 0)
             self.generate_child_branches(child_count, branch.level + 1, sections)

    def generate_branch_indices(self, index_offset, branch):
        # N = segmentCount + 1 (because of duplicated vertex for UVs)
        N = branch.segmentCount + 1
        for i in range(branch.sectionCount):
            for j in range(branch.segmentCount):
                v1 = index_offset + i * N + j
                v2 = index_offset + i * N + (j + 1)
                v3 = v1 + N
                v4 = v2 + N
                
                # Faces: (v1, v3, v2) and (v2, v3, v4) - CCW winding?
                # Blender faces are usually lists of 3 or 4 indices.
                # Three.js: indices.push(v1, v3, v2, v2, v3, v4); 
                # This is triangles. Blender from_pydata handles quads naturally.
                # Let's try quads for cleaner geometry: (v1, v2, v4, v3) or similar.
                # v1-v2 is bottom edge. v3-v4 is top edge.
                # Quad: v1, v2, v4, v3 
                
                self.branches_indices.append((v1, v2, v4, v3))

    def generate_child_branches(self, count, level, sections):
        radial_offset = self.rng.random(1, 0)
        
        for i in range(count):
            start_val = self.options.branch.start.get(level, 0.3)
            # RNG random(max, min)
            # JS: this.rng.random(1.0, this.options.branch.start[level]);
            child_branch_start = self.rng.random(1.0, start_val)
            
            # Interpolation logic
            section_idx = math.floor(child_branch_start * (len(sections) - 1))
            section_idx = max(0, min(section_idx, len(sections) - 2))
            
            sectionA = sections[section_idx]
            sectionB = sections[section_idx + 1]
            
            # Alpha
            denom = (1 / (len(sections) - 1))
            if denom == 0: denom = 1
            alpha = (child_branch_start - (section_idx / (len(sections) - 1))) / denom
            alpha = max(0, min(alpha, 1))

            # Lerp Origin
            origin = sectionA['origin'].lerp(sectionB['origin'], alpha)
            
            # Lerp Radius
            radius_parent = (1 - alpha) * sectionA['radius'] + alpha * sectionB['radius']
            radius = self.options.branch.radius.get(level, 0.5) * radius_parent
            
            # Lerp Orientation
            qA = sectionA['orientation'].to_quaternion()
            qB = sectionB['orientation'].to_quaternion()
            parent_orientation = qB.slerp(qA, alpha).to_euler()
            
            # Calc Child Orientation
            radial_angle = 2.0 * math.pi * (radial_offset + i / count)
            
            # JS Quats: q3 * q2 * q1 (applied in reverse order?? Three.js multiply order is local/global?)
            # JS: q3.multiply(q2.multiply(q1))
            
            # q1: Axis X, angle from settings
            angle_deg = self.options.branch.angle.get(level, 60)
            q1 = Quaternion(Vector((1, 0, 0)), math.radians(angle_deg))
            
            # q2: Axis Y, radial angle
            q2 = Quaternion(Vector((0, 1, 0)), radial_angle)
            
            # q3: Parent orientation
            q3 = parent_orientation.to_quaternion()
            
            # Blender Quat Multiplication: qA @ qB rotates by qB then qA?
            # Or qA @ point? 
            # In Blender, q1 @ q2 means apply q2 first then q1? 
            # "The multiplication of two quaternions corresponds to the composition of rotations (the rotation on the right is applied first)."
            # So A @ B means B then A.
            
            # JS: q3.multiply(q2) -> q3 becomes q3*q2. Applied q2 then q3? 
            # Three.js: a.multiply(b) "Sets this quaternion to a x b."
            # "Rotations are applied to the arguments from right to left." => a * b means b then a.
            # So q3 * (q2 * q1) means apply q1, then q2, then q3.
            
            # So in Blender: q3 @ q2 @ q1
            final_quat = q3 @ q2 @ q1
            child_orientation = final_quat.to_euler()
            
            length = self.options.branch.length.get(level, 5)
            if self.options.type == TreeType.Evergreen:
                length *= (1.0 - child_branch_start)
                
            self.branch_queue.append(Branch(
                origin=origin,
                orientation=child_orientation,
                length=length,
                radius=radius,
                level=level,
                sectionCount=self.options.branch.sections.get(level, 6),
                segmentCount=self.options.branch.segments.get(level, 4)
            ))

    def generate_leaves(self, sections):
        radial_offset = self.rng.random(1, 0)
        
        leaf_count = self.options.leaves.count
        leaf_start_limit = self.options.leaves.start
        
        for i in range(leaf_count):
            leaf_start = self.rng.random(1.0, leaf_start_limit)
            
            # Interpolation (Same as branches roughly)
            section_idx = math.floor(leaf_start * (len(sections) - 1))
            section_idx = max(0, min(section_idx, len(sections) - 2))
            
            sectionA = sections[section_idx]
            sectionB = sections[section_idx + 1]
            
            denom = (1 / (len(sections) - 1))
            if denom == 0: denom = 1
            alpha = (leaf_start - (section_idx / (len(sections) - 1))) / denom
            
            origin = sectionA['origin'].lerp(sectionB['origin'], alpha)
            
            qA = sectionA['orientation'].to_quaternion()
            qB = sectionB['orientation'].to_quaternion()
            parent_orientation = qB.slerp(qA, alpha).to_euler()
            
            # Orientation
            radial_angle = 2.0 * math.pi * (radial_offset + i / leaf_count)
            
            q1 = Quaternion(Vector((1, 0, 0)), math.radians(self.options.leaves.angle))
            q2 = Quaternion(Vector((0, 1, 0)), radial_angle)
            q3 = parent_orientation.to_quaternion()
            
            # q3 @ q2 @ q1
            final_quat = q3 @ q2 @ q1
            leaf_orientation = final_quat.to_euler()
            
            self.generate_leaf(origin, leaf_orientation)

    def generate_leaf(self, origin, orientation):
        # Create a single or double quad
        
        size = self.options.leaves.size
        # Variance
        variance = self.options.leaves.sizeVariance
        # random(var, -var)
        scale = 1 + self.rng.random(variance, -variance)
        leaf_size = size * scale
        
        W = leaf_size
        L = leaf_size
        
        def create_quad_leaf(rot_offset_y):
            # Vertices
            # v0: -W/2, L, 0
            # v1: -W/2, 0, 0
            # v2: W/2, 0, 0
            # v3: W/2, L, 0
            
            local_verts = [
                Vector((-W/2, L, 0)),
                Vector((-W/2, 0, 0)),
                Vector((W/2, 0, 0)),
                Vector((W/2, L, 0))
            ]
            
            # Transform
            rot_offset_quat = Quaternion(Vector((0,1,0)), rot_offset_y)
            base_quat = orientation.to_quaternion()
            
            transformed_verts = []
            for v in local_verts:
                # Apply local rotation then base orientation then add origin
                v_rot = v.copy()
                v_rot.rotate(rot_offset_quat) # Apply Y rotation
                v_rot.rotate(base_quat)       # Apply orientation
                transformed_verts.append(v_rot + origin)
                
            start_idx = len(self.leaves_verts)
            self.leaves_verts.extend(transformed_verts)
            
            # UVs
            # 0: (0, 1)
            # 1: (0, 0)
            # 2: (1, 0)
            # 3: (1, 1)
            self.leaves_uvs.extend([
                Vector((0, 1)),
                Vector((0, 0)),
                Vector((1, 0)),
                Vector((1, 1))
            ])
            
            # Face
            self.leaves_indices.append((start_idx, start_idx+1, start_idx+2, start_idx+3))
            
        create_quad_leaf(0)
        
        if self.options.leaves.billboard == Billboard.Double:
            create_quad_leaf(math.pi / 2)

    def create_mesh(self):
        # Create Blender Mesh for Branches
        mesh_branches = bpy.data.meshes.new("EZTree_Branches")
        mesh_branches.from_pydata(self.branches_verts, [], self.branches_indices)
        mesh_branches.uv_layers.new(name="UVMap")
        
        # Assign UVs
        bm = bmesh.new()
        bm.from_mesh(mesh_branches)
        uv_layer = bm.loops.layers.uv.verify()
        
        # Iterating loops to assign UVs is slow for large meshes, but simplest to implement
        # self.branches_uvs has one per vertex. But standard Blender UVs are per-loop.
        # My implementation of `branches_verts` duplicated vertices on the seam.
        # So number of vertices should equal number of UV coordinates.
        # However, `from_pydata` creates vertices.
        # We need to map vertex index to UV.
        
        bm.loops.layers.uv.verify()
        
        for face in bm.faces:
            for loop in face.loops:
                v_idx = loop.vert.index
                uv = self.branches_uvs[v_idx]
                loop[uv_layer].uv = uv
        
        bm.to_mesh(mesh_branches)
        bm.free()
        
        # Leaves
        mesh_leaves = bpy.data.meshes.new("EZTree_Leaves")
        mesh_leaves.from_pydata(self.leaves_verts, [], self.leaves_indices)
        
        bm_l = bmesh.new()
        bm_l.from_mesh(mesh_leaves)
        uv_layer_l = bm_l.loops.layers.uv.verify()
        
        for face in bm_l.faces:
            for loop in face.loops:
                v_idx = loop.vert.index
                uv = self.leaves_uvs[v_idx]
                loop[uv_layer_l].uv = uv
                
        bm_l.to_mesh(mesh_leaves)
        bm_l.free()
        
        return mesh_branches, mesh_leaves
