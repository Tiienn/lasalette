"""Step 1 - build the house shell from the floor plan.
Run:  blender -b -P src/build.py        (or: python3 src/build.py with the bpy module)
Out:  build/shell.blend

Collections
  Arch   ground-floor shell (walls, floors, doors, windows, stair)
  Upper  everything above the ground-floor ceiling (hidden for the top view)
  Site   lot, lawn, pool, fences
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

bpy.ops.wm.read_factory_settings(use_empty=True)
M = make_materials()
P, R = M["paint"], M["render"]

# ------------------------------------------------------------------ plan data
# (all read from the plan; see README for the dimension table)
W_EXT = 0.2
X_E = 13.0                       # house width (15.0 m lot less 2 x 1.0 m setback)
Y_MAIN = 5.9                     # outer face of living-room north wall
Y_WING = 10.52                   # outer face of bedroom north wall
X_WING = 4.0                     # outer face of wing east wall
STAIR_X = 2.85                   # east edge of stair void

# openings: (start, end, sill, head)
SOUTH_G = [(0.30, 1.08, 1.2, H), (1.70, 2.48, 1.2, H), (4.08, 6.26, 0, 2.4),
           (6.81, 7.55, 0.9, 2.4), (9.59, 11.98, 1.1, 2.4)]
SOUTH_U = [(0.30, 1.08, H, 4.6), (1.70, 2.48, H, 4.6), (4.6, 6.6, 3.9, 5.3), (9.2, 11.6, 3.9, 5.3)]
NORTH_G = [(4.0, 7.6, 0, 2.4), (8.57, 12.17, 0, 2.4)]
NORTH_U = [(4.6, 7.0, 3.6, 5.3), (9.2, 11.6, 3.6, 5.3)]
BED_WIN = (1.43, 3.38, 0.75, 2.4)

# ------------------------------------------------------------------ exterior walls
for lvl, z0, z1, c in (("g", 0, H, "Arch"), ("u", H, TOP, "Upper")):
    wall(f"ext_S_{lvl}", "x", 0, X_E, 0, W_EXT, z0, z1, R, SOUTH_G if lvl == "g" else SOUTH_U, c)
    wall(f"ext_W_{lvl}", "y", W_EXT, Y_WING - W_EXT, 0, W_EXT, z0, z1, R, (), c)
    wall(f"ext_Nw_{lvl}", "x", 0, X_WING, Y_WING - W_EXT, Y_WING, z0, z1, R,
         [BED_WIN] if lvl == "g" else [(1.4, 3.0, 3.9, 5.3)], c)
    wall(f"ext_Ew_{lvl}", "y", Y_MAIN, Y_WING - W_EXT, X_WING - W_EXT, X_WING, z0, z1, R, (), c)
    wall(f"ext_N_{lvl}", "x", X_WING - W_EXT, X_E, Y_MAIN - W_EXT, Y_MAIN, z0, z1, R,
         NORTH_G if lvl == "g" else NORTH_U, c)
    wall(f"ext_E_{lvl}", "y", W_EXT, Y_MAIN - W_EXT, X_E - W_EXT, X_E, z0, z1, R, (), c)

# blade wall with rounded end at the east side of the terrace (500 thick)
box("blade", (12.2, Y_MAIN, 0), (12.7, 9.05, 2.95), R)
cyl("blade_end", (12.45, 9.05), 0.25, 0, 2.949, R)

# ------------------------------------------------------------------ interior walls
wall("int_stair_bath", "x", W_EXT, 2.93, 3.74, 3.93, 0, H, P)
wall("int_stair_bath_u", "x", W_EXT, STAIR_X + 0.1, 3.74, 3.93, H, TOP, P, (), "Upper")
wall("int_bath_E", "y", 3.93, 6.51, 1.85, 2.05, 0, H, P, [(5.45, 6.30, 0, 2.1)])
wall("int_store_N", "x", 2.05, 2.93, 5.22, 5.41, 0, H, P, [(2.12, 2.82, 0, 2.1)])
wall("int_store_E", "y", 3.93, 5.22, 2.85, 2.93, 0, H, P)
wall("int_bath_bed", "x", W_EXT, X_WING - W_EXT, 6.51, 6.71, 0, H, P, [(2.82, 3.72, 0, 2.1)])
wall("int_robe_end", "y", 6.71, 7.25, 2.54, 2.80, 0, H, P)
wall("int_void_u", "y", W_EXT, 3.74, STAIR_X, STAIR_X + 0.1, H + SLAB, TOP, P, (), "Upper")

# bathroom wall tiling (10 mm lining, full height)
T = M["tile_wall"]
box("tile_W", (0.2, 3.93, 0), (0.21, 6.51, H), T)
box("tile_S", (0.2, 3.93, 0), (1.85, 3.94, H), T)
box("tile_N", (0.2, 6.50, 0), (1.85, 6.51, H), T)
wall("tile_E", "y", 3.93, 6.51, 1.84, 1.85, 0, H, T, [(5.45, 6.30, 0, 2.1)])

# ------------------------------------------------------------------ floors
LAM, e = M["laminate"], 0.0
box("floor_main", (STAIR_X - 0.0, 0.2, -0.15), (12.8, 5.7, 0), LAM)
box("floor_stair", (0.2, 0.2, -0.15), (STAIR_X, 3.74, 0), LAM)
box("floor_hall", (2.05, 5.41, -0.15), (2.85, 6.51, 0), LAM)
box("floor_hall2", (2.85, 5.7, -0.15), (3.8, 6.51, 0), LAM)
box("floor_store", (2.05, 3.93, -0.15), (2.85, 5.22, 0), LAM)
box("floor_store_door", (2.12, 5.22, -0.15), (2.82, 5.41, 0), LAM)
box("floor_bed", (0.2, 6.71, -0.15), (3.8, 10.32, 0), LAM)
box("floor_bed_door", (2.82, 6.51, -0.15), (3.72, 6.71, 0), LAM)
box("floor_bath", (0.2, 3.93, -0.15), (1.85, 6.51, 0), M["tile_floor"])
box("floor_bath_door", (1.85, 5.45, -0.15), (2.05, 6.30, 0), M["tile_floor"])
box("thresh_N1", (4.0, 5.7, -0.15), (7.6, 5.9, 0), M["frame"])
box("thresh_N2", (8.57, 5.7, -0.15), (12.17, 5.9, 0), M["frame"])
box("thresh_entry", (4.08, 0, -0.15), (6.26, 0.2, 0), M["frame"])
# skirting (60 mm) on the long living room walls
for n, lo, hi in (("sk_E", (12.78, 0.8, 0), (12.8, 5.7, 0.06)), ("sk_S1", (2.48, 0.2, 0), (4.08, 0.22, 0.06)),
                  ("sk_S2", (6.26, 0.2, 0), (8.81, 0.22, 0.06)), ("sk_N", (7.6, 5.68, 0), (8.57, 5.7, 0.06))):
    box(n, lo, hi, M["cabinet_white"])

# ------------------------------------------------------------------ slabs / ceilings / roof  (Upper)
C = M["ceiling"]
box("slab_wing", (0, 3.74, H), (X_WING, Y_WING, H + SLAB), C, "Upper")
box("slab_main_s", (STAIR_X, 0, H), (X_E, 3.74, H + SLAB), C, "Upper")
box("slab_main_n", (X_WING, 3.74, H), (X_E, Y_MAIN, H + SLAB), C, "Upper")
box("slab_landing", (2.7, 2.75, H), (STAIR_X, 3.74, H + SLAB), C, "Upper")
box("roof_wing", (-0.1, -0.1, TOP), (X_WING + 0.1, Y_WING + 0.1, TOP + 0.15), M["concrete"], "Upper")
box("roof_main", (X_WING + 0.1, -0.1, TOP), (X_E + 0.1, Y_MAIN + 0.1, TOP + 0.15), M["concrete"], "Upper")
# covered terrace roof with timber soffit
box("terrace_roof", (X_WING, Y_MAIN, 2.74), (12.9, 9.55, 2.98), M["concrete"], "Upper")
box("terrace_soffit", (X_WING, Y_MAIN, H), (12.9, 9.55, 2.74), M["soffit"], "Upper")

# ------------------------------------------------------------------ windows & glazed doors
window("win_stair1", "x", 0.30, 1.08, 0.1, 1.2, 4.6, M)
window("win_stair2", "x", 1.70, 2.48, 0.1, 1.2, 4.6, M)
window("win_slot", "x", 6.81, 7.55, 0.1, 0.9, 2.4, M)
window("win_kitchen", "x", 9.59, 11.98, 0.1, 1.1, 2.4, M, mullions=[10.785])
window("win_bed", "x", 1.43, 3.38, Y_WING - 0.1, 0.75, 2.4, M, mullions=[2.405])
for i, (a, b, s, h) in enumerate(SOUTH_U[2:]):
    window(f"win_up_s{i}", "x", a, b, 0.1, s, h, M, mullions=[(a + b) / 2], c="Upper")
for i, (a, b, s, h) in enumerate(NORTH_U):
    window(f"win_up_n{i}", "x", a, b, Y_MAIN - 0.1, s, h, M, mullions=[(a + b) / 2], c="Upper")
window("win_up_bed", "x", 1.4, 3.0, Y_WING - 0.1, 3.9, 5.3, M, c="Upper")

# entry: glazed pivot door (west leaf, 1.09 m) + fixed sidelight
window("entry", "x", 4.08, 6.26, 0.1, 0, 2.4, M, mullions=[5.17])
box("entry_leaf_l", (4.15, 0.07, 0.03), (4.23, 0.13, 2.33), M["frame"])
box("entry_leaf_r", (5.07, 0.07, 0.03), (5.13, 0.13, 2.33), M["frame"])
box("entry_leaf_t", (4.15, 0.07, 2.25), (5.13, 0.13, 2.33), M["frame"])
box("entry_leaf_b", (4.15, 0.07, 0.03), (5.13, 0.13, 0.12), M["frame"])
box("entry_pull_in", (5.0, 0.15, 0.8), (5.03, 0.18, 1.6), M["brass"])
box("entry_pull_out", (5.0, 0.02, 0.8), (5.03, 0.05, 1.6), M["brass"])

# terrace sliders: 2 x 3.6 m, four 0.9 m panels each. West set has one panel slid open.
def slider(name, x0, open_panel=None):
    y = Y_MAIN - 0.1
    fr, g = M["frame"], M["glass"]
    box(name + ".head", (x0, y - 0.07, 2.34), (x0 + 3.6, y + 0.07, 2.4), fr)
    box(name + ".jl", (x0, y - 0.07, 0), (x0 + 0.05, y + 0.07, 2.4), fr)
    box(name + ".jr", (x0 + 3.55, y - 0.07, 0), (x0 + 3.6, y + 0.07, 2.4), fr)
    box(name + ".track", (x0, y - 0.07, 0), (x0 + 3.6, y + 0.07, 0.015), fr)
    for i in range(4):
        px = x0 + 0.05 + i * 0.875
        py = y - 0.03 if i % 2 == 0 else y + 0.03
        if i == open_panel:
            px -= 0.83           # slid behind its neighbour
            py = y - 0.03 if (i - 1) % 2 else y + 0.03
        for n, lo, hi in (("l", (px, 0.02), (px + 0.045, 2.34)), ("r", (px + 0.83, 0.02), (px + 0.875, 2.34)),
                          ("t", (px, 2.29), (px + 0.875, 2.34)), ("b", (px, 0.02), (px + 0.875, 0.08))):
            box(f"{name}.p{i}{n}", (lo[0], py - 0.02, lo[1]), (hi[0], py + 0.02, hi[1]), fr)
        box(f"{name}.p{i}g", (px + 0.04, py - 0.004, 0.07), (px + 0.84, py + 0.004, 2.30), g)

slider("slide_W", 4.0, open_panel=2)
slider("slide_E", 8.57)

# ------------------------------------------------------------------ internal doors
def door(name, hinge, width, angle, axis, mat=None, t=0.04, h=2.08):
    """Leaf hinged at `hinge` (x, y); closed leaf extends +width along axis
    ('x' or 'y', may be negative width); angle opens it about the hinge."""
    mat = mat or M["cabinet_white"]
    hx, hy = hinge
    if axis == "x":
        lo, hi = (hx, hy - t / 2, 0.01), (hx + width, hy + t / 2, h)
    else:
        lo, hi = (hx - t / 2, hy, 0.01), (hx + t / 2, hy + width, h)
    ob = box(name, lo, hi, mat, rot_z=math.radians(angle), pivot=hinge)
    # lever handle
    s = 1 if width > 0 else -1
    if axis == "x":
        hl, hh = (hx + width - s * 0.12, hy - 0.07, 1.0), (hx + width - s * 0.06, hy + 0.07, 1.03)
    else:
        hl, hh = (hx - 0.07, hy + width - s * 0.12, 1.0), (hx + 0.07, hy + width - s * 0.06, 1.03)
    box(name + ".handle", hl, hh, M["black"], rot_z=math.radians(angle), pivot=hinge)
    return ob

def lining(name, axis, a0, a1, b0, b1, h=2.1):
    """Simple door frame (jambs + head) inside an opening."""
    fr = M["cabinet_white"]
    if axis == "x":
        box(name + ".jl", (a0, b0 - 0.01, 0), (a0 + 0.02, b1 + 0.01, h), fr)
        box(name + ".jr", (a1 - 0.02, b0 - 0.01, 0), (a1, b1 + 0.01, h), fr)
        box(name + ".hd", (a0, b0 - 0.01, h - 0.02), (a1, b1 + 0.01, h), fr)
    else:
        box(name + ".jl", (b0 - 0.01, a0, 0), (b1 + 0.01, a0 + 0.02, h), fr)
        box(name + ".jr", (b0 - 0.01, a1 - 0.02, 0), (b1 + 0.01, a1, h), fr)
        box(name + ".hd", (b0 - 0.01, a0, h - 0.02), (b1 + 0.01, a1, h), fr)

# bedroom door: hinged on the east jamb, opens into the bedroom (as drawn)
lining("dl_bed", "x", 2.82, 3.72, 6.51, 6.71)
door("door_bed", (3.70, 6.69), -0.86, -82, "x")
# bathroom door: hinged at the north jamb, opens into the bathroom (as drawn)
lining("dl_bath", "y", 5.45, 6.30, 1.85, 2.05)
door("door_bath", (1.87, 6.28), -0.81, -75, "y")
# storage door: faces north into the hall, closed
lining("dl_store", "x", 2.12, 2.82, 5.22, 5.41)
door("door_store", (2.14, 5.39), 0.66, 0, "x")

# ------------------------------------------------------------------ stair (U-shaped, 19 risers to 3.1 m)
r = (H + SLAB) / 19
ST, TR = M["paint"], M["oak_flat"]
def tread(n, lo, hi, top, solid):
    z0 = 0 if solid else top - r - 0.10
    box(n + ".body", (lo[0], lo[1], z0), (hi[0], hi[1], top - 0.03), ST)
    box(n + ".tread", (lo[0], lo[1], top - 0.03), (hi[0], hi[1], top), TR)

for i in range(1, 7):                      # flight 1, heading west along the south wall
    x1 = 3.03 - 0.305 * (i - 1)
    tread(f"st1_{i}", (x1 - 0.305, 0.2), (x1, 1.25), i * r, True)
tread("st_land1", (0.2, 0.2), (1.2, 1.25), 7 * r, True)
for j in range(1, 6):                      # flight 2, heading north along the west wall
    y0 = 1.25 + 0.3 * (j - 1)
    tread(f"st2_{j}", (0.2, y0), (1.2, y0 + 0.3), (7 + j) * r, True)
tread("st_land2", (0.2, 2.75), (1.2, 3.74), 13 * r, False)
for k in range(1, 6):                      # flight 3, heading east along the bathroom wall
    x0 = 1.2 + 0.3 * (k - 1)
    tread(f"st3_{k}", (x0, 2.75), (x0 + 0.3, 3.74), (13 + k) * r, False)

# black steel balustrade on the inner edges
BL = M["black"]
def rail(name, pts, posts=True):
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        beam(f"{name}.r{i}", (a[0], a[1], a[2] + 0.95), (b[0], b[1], b[2] + 0.95), 0.04, 0.04, BL)
        n = max(1, int((Vector(b) - Vector(a)).length / 0.12))
        for q in range(n + 1):
            t = q / n
            p = Vector(a).lerp(Vector(b), t)
            beam(f"{name}.b{i}_{q}", (p.x, p.y, p.z), (p.x, p.y, p.z + 0.95), 0.012, 0.012, BL)

rail("rail1", [(3.03, 1.27, r), (1.22, 1.27, 7 * r), (1.22, 2.73, 12 * r)])
rail("rail3", [(1.22, 2.73, 13 * r), (2.7, 2.73, 19 * r)])
rail("rail_up", [(2.7, 2.73, 19 * r), (STAIR_X, 2.73, 19 * r)])

# ------------------------------------------------------------------ site
S = "Site"
LOT = dict(x0=-1.0, x1=14.0, y0=-5.05, y1=14.55)       # 15.0 x ~19.6 m lot
PX0, PX1, PY0, PY1, PD = 5.79, 11.79, 10.32, 13.32, 1.4   # pool 6.0 x 3.0, 0.9 m north of the terrace
LX0, LX1, LY0, LY1 = LOT["x0"] - 14, LOT["x1"] + 14, LOT["y0"] - 14, LOT["y1"] + 14
for n, lo, hi in (("S", (LX0, LY0), (LX1, PY0)), ("N", (LX0, PY1), (LX1, LY1)),
                  ("W", (LX0, PY0), (PX0, PY1)), ("E", (PX1, PY0), (LX1, PY1))):   # lawn with a hole for the pool
    box("lawn_" + n, (lo[0], lo[1], -0.6), (hi[0], hi[1], -0.05), M["lawn"], S)
# covered terrace floor 8.67 x 3.52
box("terrace_floor", (X_WING, Y_MAIN, -0.3), (12.7, 9.42, -0.02), M["terrace"], S)
# pool 6.0 x 3.0, 0.9 m north of the terrace; paved surround
pv = M["paver"]
box("pave_S", (X_WING, 9.42, -0.3), (12.7, PY0, -0.02), pv, S)
box("pave_W", (X_WING, PY0, -0.3), (PX0, 13.95, -0.02), pv, S)
box("pave_E", (PX1, PY0, -0.3), (12.7, 13.95, -0.02), pv, S)
box("pave_N", (PX0, PY1, -0.3), (PX1, 13.95, -0.02), pv, S)
box("pool_floor", (PX0, PY0, -PD - 0.2), (PX1, PY1, -PD), M["pool_tile"], S)
pw = M["pool_wall"]
# pool walls stand 6 mm proud of the paving / lawn edges and run up to the coping
box("pool_wS", (PX0, PY0 - 0.2, -PD), (PX1, PY0 + 0.006, -0.03), pw, S)
box("pool_wN", (PX0, PY1 - 0.006, -PD), (PX1, PY1 + 0.2, -0.03), pw, S)
box("pool_wW", (PX0 - 0.2, PY0, -PD), (PX0 + 0.006, PY1, -0.03), pw, S)
box("pool_wE", (PX1 - 0.006, PY0, -PD), (PX1 + 0.2, PY1, -0.03), pw, S)
plane("pool_water", (PX0, PY0), (PX1, PY1), -0.12, M["water"], S)
for i in range(3):                                         # entry steps at the west end
    box(f"pool_step{i}", (PX0, PY0, -PD), (PX0 + 0.35 * (3 - i), PY0 + 1.2, -0.35 - 0.3 * i), M["pool_tile"], S)

# boundary fences (1.8 m timber) on the sides and rear, low wall + drive at the street
F = M["fence"]
box("fence_W", (LOT["x0"] - 0.05, LOT["y0"] + 4.0, -0.05), (LOT["x0"], LOT["y1"], 1.8), F, S)
box("fence_E", (LOT["x1"], LOT["y0"] + 4.0, -0.05), (LOT["x1"] + 0.05, LOT["y1"], 1.8), F, S)
box("fence_N", (LOT["x0"] - 0.05, LOT["y1"], -0.05), (LOT["x1"] + 0.05, LOT["y1"] + 0.05, 1.8), F, S)
box("path_entry", (4.1, LOT["y0"], -0.3), (5.3, 0.0, -0.02), M["terrace"], S)
box("driveway", (8.2, LOT["y0"], -0.3), (12.6, 0.0, -0.03), M["drive"], S)
box("footpath", (LOT["x0"] - 14, LOT["y0"] - 1.5, -0.3), (LOT["x1"] + 14, LOT["y0"], -0.03), M["drive"], S)
box("street", (LOT["x0"] - 14, LOT["y0"] - 8.5, -0.3), (LOT["x1"] + 14, LOT["y0"] - 1.5, -0.08), M["asphalt"], S)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BUILD, "shell.blend"))
print("OK shell.blend  objects:", len(bpy.data.objects))
