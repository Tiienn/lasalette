"""Shared helpers: geometry primitives and procedural materials.
All dimensions in metres. Origin = outer south-west corner of the house,
+X east, +Y north, +Z up. Floor finish level = 0.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
os.makedirs(BUILD, exist_ok=True)

H = 2.7          # ceiling height
SLAB = 0.4       # floor slab / structure zone
TOP = 5.9        # top of upper storey walls


# ---------------------------------------------------------------- collections
def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def _link(ob, c):
    coll(c).objects.link(ob)
    return ob


def _smooth(me, ob, bevel, segments):
    for p in me.polygons:
        p.use_smooth = True
    if hasattr(me, "use_auto_smooth"):
        me.use_auto_smooth = True
    b = ob.modifiers.new("Bevel", "BEVEL")
    b.width = bevel
    b.segments = segments
    b.limit_method = "ANGLE"
    w = ob.modifiers.new("WN", "WEIGHTED_NORMAL")
    w.keep_sharp = True


# ---------------------------------------------------------------- primitives
def box(name, lo, hi, mat, c="Arch", bevel=0.0, seg=3, rot_z=0.0, pivot=None):
    """Axis aligned box from corner lo to corner hi. Optional rotation about
    a vertical axis through `pivot` (x, y)."""
    lo, hi = Vector(lo), Vector(hi)
    lo2 = Vector((min(lo.x, hi.x), min(lo.y, hi.y), min(lo.z, hi.z)))
    hi2 = Vector((max(lo.x, hi.x), max(lo.y, hi.y), max(lo.z, hi.z)))
    size, cen = hi2 - lo2, (lo2 + hi2) / 2
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = cen
    if rot_z:
        p = Vector((pivot[0], pivot[1], cen.z)) if pivot else cen
        R = Matrix.Rotation(rot_z, 4, "Z")
        ob.matrix_world = Matrix.Translation(p) @ R @ Matrix.Translation(cen - p)
    if mat:
        me.materials.append(mat)
    if bevel > 0:
        _smooth(me, ob, bevel, seg)
    return _link(ob, c)


def cyl(name, center, r, z0, z1, mat, c="Arch", seg=48, r2=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=z1 - z0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = abs(p.normal.z) < 0.9
    ob = bpy.data.objects.new(name, me)
    ob.location = (center[0], center[1], (z0 + z1) / 2)
    if mat:
        me.materials.append(mat)
    if bevel > 0:
        _smooth(me, ob, bevel, 3)
    return _link(ob, c)


def sphere(name, center, r, mat, c="Arch", scale=(1, 1, 1), sub=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = center
    ob.scale = scale
    if mat:
        me.materials.append(mat)
    return _link(ob, c)


def beam(name, p0, p1, w, h, mat, c="Arch"):
    """Rectangular bar between two points (w horizontal, h vertical)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(d.length, w, h), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    x = d.normalized()
    y = Vector((0, 0, 1)).cross(x)
    y = y.normalized() if y.length > 1e-6 else Vector((0, 1, 0))
    z = x.cross(y)
    M = Matrix((x, y, z)).transposed().to_4x4()
    M.translation = (p0 + p1) / 2
    ob.matrix_world = M
    if mat:
        me.materials.append(mat)
    return _link(ob, c)


def plane(name, lo, hi, z, mat, c="Arch"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(lo[0], lo[1], z), (hi[0], lo[1], z), (hi[0], hi[1], z), (lo[0], hi[1], z)],
                   [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    if mat:
        me.materials.append(mat)
    return _link(ob, c)


# ---------------------------------------------------------------- walls
def wall(name, axis, a0, a1, b0, b1, z0, z1, mat, openings=(), c="Arch"):
    """Wall running along `axis` ('x' or 'y') from a0..a1, occupying b0..b1 in
    the other axis, between z0..z1. openings = [(start, end, sill, head)]."""
    def seg(s, e, za, zb, i):
        if e - s < 1e-4 or zb - za < 1e-4:
            return
        if axis == "x":
            box(f"{name}.{i}", (s, b0, za), (e, b1, zb), mat, c)
        else:
            box(f"{name}.{i}", (b0, s, za), (b1, e, zb), mat, c)
    cur, i = a0, 0
    for (s, e, sill, head) in sorted(openings):
        seg(cur, s, z0, z1, i); i += 1
        seg(s, e, z0, max(z0, sill), i); i += 1
        seg(s, e, min(z1, head), z1, i); i += 1
        cur = e
    seg(cur, a1, z0, z1, i)


def window(name, axis, a0, a1, b, sill, head, M, mullions=(), transoms=(),
           fw=0.05, fd=0.08, c="Arch", glass=True):
    """Framed glazing in a wall along `axis`; b = wall centre line."""
    def bx(n, s, e, za, zb, d, mat):
        if axis == "x":
            box(n, (s, b - d / 2, za), (e, b + d / 2, zb), mat, c)
        else:
            box(n, (b - d / 2, s, za), (b + d / 2, e, zb), mat, c)
    fr = M["frame"]
    bx(name + ".fl", a0, a0 + fw, sill, head, fd, fr)
    bx(name + ".fr", a1 - fw, a1, sill, head, fd, fr)
    bx(name + ".ft", a0, a1, head - fw, head, fd, fr)
    bx(name + ".fb", a0, a1, sill, sill + (fw if sill > 0.05 else 0.03), fd, fr)
    for i, m in enumerate(mullions):
        bx(f"{name}.m{i}", m - fw / 2, m + fw / 2, sill, head, fd, fr)
    for i, t in enumerate(transoms):
        bx(f"{name}.t{i}", a0, a1, t - fw / 2, t + fw / 2, fd, fr)
    if glass:
        bx(name + ".glass", a0 + fw / 2, a1 - fw / 2, sill + 0.02, head - fw / 2, 0.008, M["glass"])


# ---------------------------------------------------------------- materials
def _new(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_fake_user = True      # keep even if not used yet (fitout.py needs it)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    return m, nt, nt.nodes, nt.links


def _out(nodes):
    return nodes.new("ShaderNodeOutputMaterial")


def _set(bsdf, **kw):
    names = {"base": "Base Color", "rough": "Roughness", "metal": "Metallic",
             "spec": "Specular IOR Level", "coat": "Coat Weight",
             "coat_rough": "Coat Roughness", "sheen": "Sheen Weight",
             "trans": "Transmission Weight", "ior": "IOR", "alpha": "Alpha",
             "emit": "Emission Color", "emit_str": "Emission Strength",
             "sss": "Subsurface Weight"}
    for k, v in kw.items():
        key = names[k]
        if key in bsdf.inputs:
            if isinstance(v, tuple) and len(v) == 3:
                v = (*v, 1.0)
            bsdf.inputs[key].default_value = v


def simple(name, color, rough=0.5, noise_bump=0.0, noise_scale=40.0, **kw):
    m, nt, N, L = _new(name)
    b = N.new("ShaderNodeBsdfPrincipled")
    _set(b, base=color, rough=rough, **kw)
    L.new(b.outputs[0], _out(N).inputs[0])
    if noise_bump > 0:
        geo = N.new("ShaderNodeNewGeometry")
        n = N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise_scale
        n.inputs["Detail"].default_value = 6
        L.new(geo.outputs["Position"], n.inputs["Vector"])
        bp = N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = noise_bump
        bp.inputs["Distance"].default_value = 0.01
        L.new(n.outputs[0], bp.inputs["Height"])
        L.new(bp.outputs[0], b.inputs["Normal"])
    return m


def _plan_vector(N, L, mode):
    """World-space 2D texture vector. mode 'floor' = XY, 'wall' = (x+y, z)."""
    geo = N.new("ShaderNodeNewGeometry")
    if mode == "floor":
        return geo.outputs["Position"]
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(geo.outputs["Position"], sep.inputs[0])
    add = N.new("ShaderNodeMath")
    L.new(sep.outputs[0], add.inputs[0])
    L.new(sep.outputs[1], add.inputs[1])
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(add.outputs[0], comb.inputs[0])
    L.new(sep.outputs[2], comb.inputs[1])
    return comb.outputs[0]


def bricks(name, c1, c2, mortar, bw, bh, gap, rough=0.4, offset=0.5,
           mode="floor", grain=0.0, grain_axis="x", bump=0.3, coat=0.0, speckle=0.0):
    """Planks / tiles from the brick texture in world space (metres)."""
    m, nt, N, L = _new(name)
    vec = _plan_vector(N, L, mode)
    br = N.new("ShaderNodeTexBrick")
    br.offset = offset
    br.inputs["Color1"].default_value = (*c1, 1)
    br.inputs["Color2"].default_value = (*c2, 1)
    br.inputs["Mortar"].default_value = (*mortar, 1)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = gap
    br.inputs["Mortar Smooth"].default_value = 0.1
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = bw
    br.inputs["Row Height"].default_value = bh
    L.new(vec, br.inputs["Vector"])
    col = br.outputs["Color"]
    b = N.new("ShaderNodeBsdfPrincipled")
    _set(b, rough=rough, coat=coat, coat_rough=0.15)
    height = None
    if grain > 0 or speckle > 0:
        mp = N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (2, 60, 60) if grain_axis == "x" else (60, 2, 60)
        if speckle > 0:
            mp.inputs["Scale"].default_value = (25, 25, 25)
        L.new(vec, mp.inputs[0])
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 1.0
        nz.inputs["Detail"].default_value = 8
        nz.inputs["Roughness"].default_value = 0.65
        L.new(mp.outputs[0], nz.inputs["Vector"])
        mix = N.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        ramp = N.new("ShaderNodeValToRGB")
        k = grain if grain > 0 else speckle
        ramp.color_ramp.elements[0].position = 0.3
        ramp.color_ramp.elements[0].color = (1 - k, 1 - k, 1 - k, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(nz.outputs[0], ramp.inputs[0])
        mix.inputs[0].default_value = 1.0
        L.new(col, mix.inputs[1])
        L.new(ramp.outputs[0], mix.inputs[2])
        col = mix.outputs[0]
        height = nz.outputs[0]
    L.new(col, b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.002
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L.new(br.outputs["Fac"], inv.inputs[1])
    L.new(inv.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    L.new(b.outputs[0], _out(N).inputs[0])
    return m


def glass(name, tint=(0.93, 0.97, 0.96), ior=1.5, bump=0.0, bump_scale=3.0, reflect=1.0):
    """Cheap architectural glass / water: transparent + fresnel reflection.
    Lets sun and sky light straight through (no caustic noise)."""
    m, nt, N, L = _new(name)
    tr = N.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (*tint, 1)
    gl = N.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.0
    # Schlick fresnel from the facing angle (works from both sides of a pane,
    # unlike the Fresnel node which goes fully reflective on back faces)
    r0 = ((ior - 1) / (ior + 1)) ** 2
    fr = N.new("ShaderNodeLayerWeight")
    fr.inputs["Blend"].default_value = 0.5
    pw = N.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 5.0
    L.new(fr.outputs["Facing"], pw.inputs[0])
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY_ADD"
    mul.inputs[1].default_value = (1 - r0) * reflect
    mul.inputs[2].default_value = r0 * reflect
    L.new(pw.outputs[0], mul.inputs[0])
    mx = N.new("ShaderNodeMixShader")
    L.new(mul.outputs[0], mx.inputs[0])
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(gl.outputs[0], mx.inputs[2])
    if bump > 0:
        geo = N.new("ShaderNodeNewGeometry")
        nz = N.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = bump_scale
        nz.inputs["Detail"].default_value = 3
        L.new(geo.outputs["Position"], nz.inputs["Vector"])
        bp = N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.05
        L.new(nz.outputs[0], bp.inputs["Height"])
        L.new(bp.outputs[0], gl.inputs["Normal"])
        L.new(bp.outputs[0], fr.inputs["Normal"])
    L.new(mx.outputs[0], _out(N).inputs[0])
    if hasattr(m, "use_transparent_shadow"):
        m.use_transparent_shadow = True
    return m


def sheer(name, color=(0.95, 0.94, 0.9), opacity=0.55):
    m, nt, N, L = _new(name)
    tr = N.new("ShaderNodeBsdfTransparent")
    df = N.new("ShaderNodeBsdfDiffuse")
    df.inputs[0].default_value = (*color, 1)
    tl = N.new("ShaderNodeBsdfTranslucent")
    tl.inputs[0].default_value = (*color, 1)
    a = N.new("ShaderNodeMixShader")
    a.inputs[0].default_value = 0.5
    L.new(df.outputs[0], a.inputs[1])
    L.new(tl.outputs[0], a.inputs[2])
    mx = N.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = opacity
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(a.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], _out(N).inputs[0])
    return m


def emissive(name, color=(1.0, 0.82, 0.62), strength=1.0):
    m, nt, N, L = _new(name)
    e = N.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*color, 1)
    e.inputs[1].default_value = strength
    L.new(e.outputs[0], _out(N).inputs[0])
    return m


def lawn(name):
    m, nt, N, L = _new(name)
    geo = N.new("ShaderNodeNewGeometry")
    n1 = N.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 1.2
    n1.inputs["Detail"].default_value = 4
    n2 = N.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 180
    n2.inputs["Detail"].default_value = 2
    L.new(geo.outputs["Position"], n1.inputs["Vector"])
    L.new(geo.outputs["Position"], n2.inputs["Vector"])
    r = N.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (0.035, 0.085, 0.012, 1)
    r.color_ramp.elements[1].color = (0.10, 0.19, 0.03, 1)
    L.new(n1.outputs[0], r.inputs[0])
    mix = N.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 0.6
    L.new(r.outputs[0], mix.inputs[1])
    L.new(n2.outputs[0], mix.inputs[2])
    b = N.new("ShaderNodeBsdfPrincipled")
    _set(b, rough=0.9, sheen=0.3)
    L.new(mix.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.8
    bp.inputs["Distance"].default_value = 0.03
    L.new(n2.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    L.new(b.outputs[0], _out(N).inputs[0])
    return m


def foliage(name, c1=(0.02, 0.07, 0.01), c2=(0.07, 0.16, 0.03)):
    m, nt, N, L = _new(name)
    geo = N.new("ShaderNodeNewGeometry")
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 25
    n.inputs["Detail"].default_value = 5
    L.new(geo.outputs["Position"], n.inputs["Vector"])
    r = N.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position = 0.35
    r.color_ramp.elements[0].color = (*c1, 1)
    r.color_ramp.elements[1].position = 0.7
    r.color_ramp.elements[1].color = (*c2, 1)
    L.new(n.outputs[0], r.inputs[0])
    b = N.new("ShaderNodeBsdfPrincipled")
    _set(b, rough=0.6, sheen=0.2)
    L.new(r.outputs[0], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 1.0
    bp.inputs["Distance"].default_value = 0.06
    L.new(n.outputs[0], bp.inputs["Height"])
    L.new(bp.outputs[0], b.inputs["Normal"])
    L.new(b.outputs[0], _out(N).inputs[0])
    # leafy displacement on the mesh itself is added by fitout.blob()
    return m


def make_materials():
    M = {}
    M["paint"] = simple("Paint white", (0.86, 0.85, 0.82), 0.55, noise_bump=0.03, noise_scale=300)
    M["render"] = simple("Exterior render", (0.80, 0.79, 0.76), 0.8, noise_bump=0.15, noise_scale=120)
    M["ceiling"] = simple("Ceiling", (0.88, 0.88, 0.86), 0.6)
    M["concrete"] = simple("Concrete", (0.42, 0.42, 0.41), 0.7, noise_bump=0.2, noise_scale=30)
    # warm oak laminate, 1220 x 195 planks running east-west
    M["laminate"] = bricks("Laminate oak", (0.52, 0.36, 0.21), (0.44, 0.29, 0.16), (0.10, 0.06, 0.03),
                           1.22, 0.195, 0.0015, rough=0.38, offset=0.37, grain=0.28, bump=0.15, coat=0.15)
    M["tile_floor"] = bricks("Bath floor tile", (0.50, 0.48, 0.45), (0.47, 0.45, 0.42), (0.25, 0.25, 0.24),
                             0.6, 0.6, 0.003, rough=0.45, offset=0.0, speckle=0.10, bump=0.4)
    M["tile_wall"] = bricks("Bath wall tile", (0.66, 0.63, 0.58), (0.63, 0.60, 0.55), (0.42, 0.41, 0.39),
                            0.6, 0.3, 0.002, rough=0.22, offset=0.5, mode="wall", speckle=0.05, bump=0.4)
    M["terrace"] = bricks("Terrace porcelain", (0.50, 0.47, 0.42), (0.46, 0.43, 0.39), (0.22, 0.21, 0.20),
                          0.6, 0.6, 0.004, rough=0.6, offset=0.0, speckle=0.15, bump=0.5)
    M["paver"] = bricks("Pool paver", (0.62, 0.59, 0.53), (0.57, 0.54, 0.49), (0.3, 0.29, 0.27),
                        0.9, 0.45, 0.005, rough=0.75, offset=0.5, speckle=0.2, bump=0.6)
    M["pool_tile"] = bricks("Pool mosaic", (0.10, 0.42, 0.50), (0.07, 0.35, 0.45), (0.5, 0.65, 0.68),
                            0.05, 0.05, 0.004, rough=0.2, offset=0.0, bump=0.2)
    M["pool_wall"] = bricks("Pool mosaic wall", (0.10, 0.42, 0.50), (0.07, 0.35, 0.45), (0.5, 0.65, 0.68),
                            0.05, 0.05, 0.004, rough=0.2, offset=0.0, mode="wall", bump=0.2)
    M["water"] = glass("Water", tint=(0.72, 0.93, 0.95), ior=1.33, bump=0.25, bump_scale=2.5)
    M["glass"] = glass("Glass")
    M["shower_glass"] = glass("Shower glass", tint=(0.9, 0.97, 0.95))
    M["mirror"] = simple("Mirror", (0.9, 0.9, 0.9), 0.02, metal=1.0)
    M["frame"] = simple("Frame black", (0.02, 0.02, 0.022), 0.4, metal=0.6)
    M["steel"] = simple("Brushed steel", (0.55, 0.55, 0.55), 0.3, metal=1.0)
    M["black"] = simple("Matt black", (0.015, 0.015, 0.015), 0.5)
    M["brass"] = simple("Brass", (0.75, 0.55, 0.28), 0.3, metal=1.0)
    M["oak"] = bricks("Oak veneer", (0.50, 0.35, 0.20), (0.47, 0.32, 0.18), (0.4, 0.28, 0.15),
                      3.0, 0.6, 0.0, rough=0.45, grain=0.3, mode="wall", bump=0.0)
    M["oak_flat"] = bricks("Oak top", (0.50, 0.35, 0.20), (0.47, 0.32, 0.18), (0.4, 0.28, 0.15),
                           3.0, 0.6, 0.0, rough=0.4, grain=0.3, bump=0.0)
    M["walnut"] = simple("Walnut slat", (0.16, 0.09, 0.05), 0.45)
    M["soffit"] = bricks("Timber soffit", (0.40, 0.25, 0.13), (0.34, 0.21, 0.11), (0.05, 0.03, 0.02),
                         3.6, 0.09, 0.006, rough=0.5, offset=0.3, grain=0.25, bump=0.5)
    M["fence"] = bricks("Fence timber", (0.20, 0.15, 0.10), (0.17, 0.12, 0.08), (0.02, 0.02, 0.02),
                        0.12, 3.0, 0.01, rough=0.75, offset=0.0, mode="wall", bump=0.8)
    M["stone"] = simple("Quartz benchtop", (0.82, 0.81, 0.78), 0.25, noise_bump=0.0)
    M["cabinet"] = simple("Cabinet sage", (0.33, 0.37, 0.32), 0.45)
    M["cabinet_white"] = simple("Cabinet white", (0.84, 0.83, 0.80), 0.4)
    M["ceramic"] = simple("Ceramic", (0.9, 0.9, 0.88), 0.12, coat=0.5)
    M["sofa"] = simple("Sofa linen", (0.60, 0.56, 0.48), 0.9, noise_bump=0.4, noise_scale=500, sheen=0.5)
    M["armchair"] = simple("Armchair boucle", (0.23, 0.26, 0.24), 0.95, noise_bump=0.6, noise_scale=350, sheen=0.6)
    M["cushion"] = simple("Cushion rust", (0.50, 0.22, 0.10), 0.9, noise_bump=0.4, noise_scale=500, sheen=0.5)
    M["bed"] = simple("Bed linen", (0.85, 0.84, 0.80), 0.9, noise_bump=0.3, noise_scale=400, sheen=0.4)
    M["throw"] = simple("Throw", (0.32, 0.38, 0.36), 0.95, noise_bump=0.5, noise_scale=300, sheen=0.5)
    M["rug"] = simple("Rug wool", (0.66, 0.62, 0.54), 1.0, noise_bump=0.8, noise_scale=250, sheen=0.6)
    M["leather"] = simple("Leather tan", (0.42, 0.22, 0.10), 0.5)
    M["outdoor"] = simple("Outdoor fabric", (0.70, 0.69, 0.65), 0.9, noise_bump=0.4, noise_scale=400)
    M["curtain"] = sheer("Sheer curtain")
    M["lawn"] = lawn("Lawn")
    M["leaf"] = foliage("Foliage")
    M["leaf2"] = foliage("Foliage light", (0.04, 0.10, 0.01), (0.14, 0.24, 0.05))
    M["trunk"] = simple("Trunk", (0.12, 0.08, 0.05), 0.9, noise_bump=0.8, noise_scale=40)
    M["soil"] = simple("Soil", (0.05, 0.035, 0.025), 0.95, noise_bump=0.8, noise_scale=60)
    M["pot"] = simple("Planter", (0.25, 0.24, 0.23), 0.8, noise_bump=0.2, noise_scale=80)
    M["asphalt"] = simple("Asphalt", (0.06, 0.06, 0.065), 0.85, noise_bump=0.5, noise_scale=200)
    M["drive"] = simple("Driveway concrete", (0.48, 0.47, 0.45), 0.8, noise_bump=0.3, noise_scale=90)
    M["lamp"] = emissive("Lamp glow", strength=1.0)      # strength set per variant in render.py
    M["screen"] = simple("TV screen", (0.01, 0.01, 0.012), 0.08, coat=1.0)
    M["art1"] = simple("Art warm", (0.62, 0.40, 0.25), 0.8)
    M["art2"] = simple("Art sage", (0.38, 0.45, 0.40), 0.8)
    M["book"] = simple("Books", (0.55, 0.50, 0.42), 0.8)
    return M


def get_materials():
    """Materials dict from an already built .blend."""
    names = {"paint": "Paint white", "render": "Exterior render", "ceiling": "Ceiling", "concrete": "Concrete",
             "laminate": "Laminate oak", "tile_floor": "Bath floor tile", "tile_wall": "Bath wall tile",
             "terrace": "Terrace porcelain", "paver": "Pool paver", "pool_tile": "Pool mosaic",
             "pool_wall": "Pool mosaic wall", "water": "Water", "glass": "Glass", "shower_glass": "Shower glass",
             "mirror": "Mirror", "frame": "Frame black", "steel": "Brushed steel", "black": "Matt black",
             "brass": "Brass", "oak": "Oak veneer", "oak_flat": "Oak top", "walnut": "Walnut slat",
             "soffit": "Timber soffit", "fence": "Fence timber", "stone": "Quartz benchtop",
             "cabinet": "Cabinet sage", "cabinet_white": "Cabinet white", "ceramic": "Ceramic",
             "sofa": "Sofa linen", "armchair": "Armchair boucle", "cushion": "Cushion rust", "bed": "Bed linen",
             "throw": "Throw", "rug": "Rug wool", "leather": "Leather tan", "outdoor": "Outdoor fabric",
             "curtain": "Sheer curtain", "lawn": "Lawn", "leaf": "Foliage", "leaf2": "Foliage light",
             "trunk": "Trunk", "soil": "Soil", "pot": "Planter", "asphalt": "Asphalt",
             "drive": "Driveway concrete", "lamp": "Lamp glow", "screen": "TV screen", "art1": "Art warm",
             "art2": "Art sage", "book": "Books"}
    return {k: bpy.data.materials[v] for k, v in names.items()}
