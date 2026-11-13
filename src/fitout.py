"""Step 2 - furniture, joinery, sanitaryware, planting and light fittings.
Run:  blender -b -P src/fitout.py
In:   build/shell.blend      Out: build/house.blend

Furniture positions are taken from the plan (sofas, armchairs, coffee table,
slat screen + console, dining table for 8, island, kitchen run, bed, wardrobe,
vanity, WC, shower, terrace seating).
"""
import bpy, sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

bpy.ops.wm.open_mainfile(filepath=os.path.join(BUILD, "shell.blend"))
M = get_materials()
F = "Fitout"
random.seed(7)


def bx(n, lo, hi, mat, bevel=0.0, **kw):
    return box(n, lo, hi, M[mat] if isinstance(mat, str) else mat, F, bevel=bevel, **kw)


def cy(n, c, r, z0, z1, mat, **kw):
    return cyl(n, c, r, z0, z1, M[mat], F, **kw)


# ------------------------------------------------------------------ generic furniture
def sofa(n, x0, y0, x1, y1, back, mat="sofa", seat_h=0.42, arm=0.16):
    """back = side the backrest is on: 'N','S','E','W'."""
    bx(n + ".base", (x0, y0, 0.08), (x1, y1, 0.26), mat, 0.03)
    for i, (px, py) in enumerate(((x0 + .06, y0 + .06), (x1 - .06, y0 + .06), (x0 + .06, y1 - .06), (x1 - .06, y1 - .06))):
        cy(f"{n}.leg{i}", (px, py), 0.02, 0, 0.08, "black", seg=12)
    bd = 0.2
    sx0, sx1, sy0, sy1 = x0, x1, y0, y1
    if back == "N":
        bx(n + ".back", (x0, y1 - bd, 0.2), (x1, y1, 0.78), mat, 0.06); sy1 -= bd
        bx(n + ".armL", (x0, y0, 0.2), (x0 + arm, sy1, 0.6), mat, 0.05); bx(n + ".armR", (x1 - arm, y0, 0.2), (x1, sy1, 0.6), mat, 0.05)
        sx0 += arm; sx1 -= arm
    elif back == "S":
        bx(n + ".back", (x0, y0, 0.2), (x1, y0 + bd, 0.78), mat, 0.06); sy0 += bd
        bx(n + ".armL", (x0, sy0, 0.2), (x0 + arm, y1, 0.6), mat, 0.05); bx(n + ".armR", (x1 - arm, sy0, 0.2), (x1, y1, 0.6), mat, 0.05)
        sx0 += arm; sx1 -= arm
    elif back == "W":
        bx(n + ".back", (x0, y0, 0.2), (x0 + bd, y1, 0.78), mat, 0.06); sx0 += bd
        bx(n + ".armL", (sx0, y0, 0.2), (x1, y0 + arm, 0.6), mat, 0.05); bx(n + ".armR", (sx0, y1 - arm, 0.2), (x1, y1, 0.6), mat, 0.05)
        sy0 += arm; sy1 -= arm
    else:
        bx(n + ".back", (x1 - bd, y0, 0.2), (x1, y1, 0.78), mat, 0.06); sx1 -= bd
        bx(n + ".armL", (x0, y0, 0.2), (sx1, y0 + arm, 0.6), mat, 0.05); bx(n + ".armR", (x0, y1 - arm, 0.2), (sx1, y1, 0.6), mat, 0.05)
        sy0 += arm; sy1 -= arm
    # seat cushions (split along the long axis)
    long_x = (sx1 - sx0) > (sy1 - sy0)
    L = (sx1 - sx0) if long_x else (sy1 - sy0)
    k = max(1, round(L / 0.8))
    for i in range(k):
        if long_x:
            a, b = sx0 + L * i / k, sx0 + L * (i + 1) / k
            bx(f"{n}.seat{i}", (a + .005, sy0, 0.26), (b - .005, sy1, seat_h + 0.02), mat, 0.05, seg=4)
        else:
            a, b = sy0 + L * i / k, sy0 + L * (i + 1) / k
            bx(f"{n}.seat{i}", (sx0, a + .005, 0.26), (sx1, b - .005, seat_h + 0.02), mat, 0.05, seg=4)
    return (sx0, sy0, sx1, sy1)


def armchair(n, x0, y0, x1, y1, back, mat="armchair"):
    sofa(n, x0, y0, x1, y1, back, mat=mat, arm=0.12)


def dining_chair(n, cx, cy_, face, mat="leather"):
    """face = direction the sitter looks: 'N','S','E','W'."""
    w = 0.23
    for i, (dx, dy) in enumerate(((-.19, -.19), (.19, -.19), (-.19, .19), (.19, .19))):
        cy(f"{n}.leg{i}", (cx + dx, cy_ + dy), 0.014, 0, 0.44, "black", seg=10)
    bx(n + ".seat", (cx - w, cy_ - w, 0.44), (cx + w, cy_ + w, 0.50), mat, 0.02)
    d = {"N": (0, -1), "S": (0, 1), "E": (-1, 0), "W": (1, 0)}[face]
    if d[0] == 0:
        y = cy_ + d[1] * (w - 0.02)
        bx(n + ".back", (cx - w, y - 0.025, 0.5), (cx + w, y + 0.025, 0.86), mat, 0.02)
    else:
        x = cx + d[0] * (w - 0.02)
        bx(n + ".back", (x - 0.025, cy_ - w, 0.5), (x + 0.025, cy_ + w, 0.86), mat, 0.02)


def blob(n, c, r, mat="leaf", scale=(1, 1, 1), strength=0.35):
    ob = sphere(n, c, r, M[mat], F, scale=scale, sub=4)
    tex = bpy.data.textures.get("leafnoise") or bpy.data.textures.new("leafnoise", "CLOUDS")
    tex.noise_scale = 0.35
    d = ob.modifiers.new("d", "DISPLACE")
    d.texture = tex
    d.strength = strength * r * 2
    d.texture_coords = "GLOBAL"
    return ob


def plant(n, x, y, z=0.0, h=1.3, pot_r=0.2, pot_h=0.42):
    cy(n + ".pot", (x, y), pot_r, z, z + pot_h, "pot", r2=pot_r * 1.15)
    cy(n + ".soil", (x, y), pot_r * 1.05, z + pot_h - 0.03, z + pot_h - 0.02, "soil")
    cy(n + ".stem", (x, y), 0.015, z + pot_h, z + h * 0.7, "trunk", seg=8)
    for i in range(5):
        a = i * 2.4
        blob(f"{n}.leaf{i}", (x + math.cos(a) * 0.14, y + math.sin(a) * 0.14, z + h * (0.6 + 0.08 * i)),
             0.2 + 0.03 * (i % 3), "leaf" if i % 2 else "leaf2", scale=(1, 1, 1.2))


def tree(n, x, y, h=5.0, r=1.6):
    cyl(n + ".trunk", (x, y), 0.12, -0.05, h * 0.6, M["trunk"], F, seg=12, r2=0.07)
    for i in range(6):
        a = i * 1.1 + x
        blob(f"{n}.c{i}", (x + math.cos(a) * r * 0.45, y + math.sin(a) * r * 0.45, h * (0.62 + 0.07 * (i % 4))),
             r * (0.55 + 0.08 * (i % 3)), "leaf" if i % 2 else "leaf2", strength=0.3)


def downlight(n, x, y, z=H, watts=9.0, c="Lights", spread=110):
    """Recessed downlight: small glowing disc + area lamp. Power set per variant in render.py."""
    cyl(n + ".trim", (x, y), 0.05, z - 0.004, z + 0.0, M["cabinet_white"], F, seg=20)
    cyl(n + ".lens", (x, y), 0.035, z - 0.006, z - 0.004, M["lamp"], F, seg=20)
    ld = bpy.data.lights.new(n, "AREA")
    ld.shape = "DISK"
    ld.size = 0.07
    ld.energy = watts
    ld.color = (1.0, 0.84, 0.66)
    try:
        ld.spread = math.radians(spread)
    except Exception:
        pass
    ob = bpy.data.objects.new(n, ld)
    ob.location = (x, y, z - 0.012)
    ob["base_watts"] = watts
    coll(c).objects.link(ob)


def pendant(n, x, y, z, r=0.11, watts=12.0, c="Lights"):
    cy(n + ".cord", (x, y), 0.004, z + r, H, "black", seg=8)
    sphere(n + ".globe", (x, y, z), r, M["lamp"], F)
    cy(n + ".cap", (x, y), 0.03, z + r - 0.01, z + r + 0.05, "brass", seg=16)
    ld = bpy.data.lights.new(n, "POINT")
    ld.shadow_soft_size = r
    ld.energy = watts
    ld.color = (1.0, 0.82, 0.62)
    ob = bpy.data.objects.new(n, ld)
    ob.location = (x, y, z - r - 0.02)
    ob["base_watts"] = watts
    coll(c).objects.link(ob)


# ================================================================== LIVING
bx("rug", (5.1, 1.7, 0.0), (7.6, 4.1, 0.012), "rug", 0.004)
sofa("sofaA", 5.39, 3.75, 7.39, 4.62, "N")               # 2.0 m sofa, back to the terrace
sofa("sofaB", 4.02, 1.88, 4.86, 3.87, "W")               # 2.0 m sofa on the hall side
armchair("arm1", 5.29, 1.03, 6.07, 1.83, "S")
armchair("arm2", 6.65, 1.03, 7.43, 1.83, "S")
bx("cushA1", (5.6, 4.22, 0.44), (6.0, 4.38, 0.78), "cushion", 0.06, seg=4)
bx("cushA2", (6.9, 4.22, 0.44), (7.2, 4.38, 0.74), "throw", 0.06, seg=4)
bx("cushB1", (4.24, 3.25, 0.44), (4.40, 3.65, 0.78), "throw", 0.06, seg=4)
cy("coffee.top", (6.31, 2.88), 0.45, 0.33, 0.37, "oak_flat", bevel=0.008)
cy("coffee.base", (6.31, 2.88), 0.18, 0.0, 0.33, "black")
cy("coffee.bowl", (6.2, 2.95), 0.12, 0.37, 0.42, "ceramic", r2=0.16)
bx("coffee.books", (6.38, 2.7, 0.37), (6.62, 2.88, 0.42), "book", 0.004)
# full-height walnut slat screen between living and dining + low console and TV
ys, n_sl = 1.03, 0
while ys < 4.47:
    bx(f"slat{n_sl}", (8.31, ys, 0), (8.40, ys + 0.04, H), "walnut"); ys += 0.085; n_sl += 1
bx("slat_plinth", (8.31, 1.03, 0), (8.40, 4.49, 0.04), "black")
bx("slat_head", (8.31, 1.03, H - 0.04), (8.40, 4.49, H), "black")
bx("console", (7.79, 1.85, 0.12), (8.25, 3.85, 0.5), "oak", 0.006)
bx("console.plinth", (7.85, 1.9, 0), (8.2, 3.8, 0.12), "black")
for i in range(1, 4):
    bx(f"console.gap{i}", (7.788, 1.85 + i * 0.5 - 0.002, 0.14), (7.79, 1.85 + i * 0.5 + 0.002, 0.48), "black")
bx("tv", (8.22, 2.15, 0.75), (8.26, 3.55, 1.55), "screen", 0.004)
bx("tv.back", (8.26, 2.5, 0.9), (8.31, 3.2, 1.4), "black")
cy("vase", (8.02, 2.0), 0.07, 0.5, 0.78, "ceramic", r2=0.04)
bx("console.books", (7.86, 3.5, 0.5), (8.12, 3.72, 0.58), "book", 0.004)
plant("plant_living", 3.45, 0.62, h=1.7, pot_r=0.22)
# art on the wall between the two slider sets and on the east wall
bx("art_n", (7.75, 5.66, 1.0), (8.42, 5.69, 1.9), "art1"); bx("art_n.frame", (7.72, 5.685, 0.97), (8.45, 5.70, 1.93), "black")
# floor lamp beside sofa B
cy("flamp.base", (4.3, 4.3), 0.14, 0, 0.02, "black"); cy("flamp.pole", (4.3, 4.3), 0.012, 0.02, 1.45, "black", seg=10)
cy("flamp.shade", (4.3, 4.3), 0.17, 1.38, 1.62, "outdoor", r2=0.13)
ld = bpy.data.lights.new("flamp", "POINT"); ld.energy = 8; ld.color = (1, 0.8, 0.6); ld.shadow_soft_size = 0.08
ob = bpy.data.objects.new("flamp", ld); ob.location = (4.3, 4.3, 1.5); ob["base_watts"] = 8.0; coll("Lights").objects.link(ob)

# ================================================================== DINING
bx("dtable.top", (9.40, 3.69, 0.72), (11.97, 4.59, 0.76), "oak_flat", 0.006)
for i, (px, py) in enumerate(((9.55, 3.82), (11.82, 3.82), (9.55, 4.46), (11.82, 4.46))):
    bx(f"dtable.leg{i}", (px - .035, py - .035, 0), (px + .035, py + .035, 0.72), "black")
for i, cx in enumerate((9.95, 10.685, 11.42)):
    dining_chair(f"dch_n{i}", cx, 4.72, "S")
    dining_chair(f"dch_s{i}", cx, 3.56, "N")
dining_chair("dch_w", 9.25, 4.14, "E")
dining_chair("dch_e", 12.12, 4.14, "W")
cy("dtable.vase", (10.7, 4.14), 0.09, 0.76, 0.98, "ceramic", r2=0.05)
blob("dtable.flowers", (10.7, 4.14, 1.12), 0.17, "leaf2")
for i, px in enumerate((10.0, 10.685, 11.37)):
    pendant(f"pend_dining{i}", px, 4.14, 1.75 + 0.08 * (i % 2), r=0.09, watts=10)
bx("art_e", (12.77, 3.4, 0.95), (12.795, 4.9, 1.95), "art2"); bx("art_e.frame", (12.785, 3.37, 0.92), (12.80, 4.93, 1.98), "black")

# ================================================================== KITCHEN
# island 2.8 x 0.8 with waterfall stone ends, induction hob, three stools on the dining side
bx("island.body", (9.32, 1.85, 0.1), (12.05, 2.57, 0.88), "cabinet")
bx("island.kick", (9.36, 1.9, 0), (12.01, 2.52, 0.1), "black")
bx("island.top", (9.28, 1.81, 0.88), (12.09, 2.61, 0.92), "stone", 0.003)
bx("island.endW", (9.28, 1.81, 0), (9.32, 2.61, 0.88), "stone", 0.003)
bx("island.endE", (12.05, 1.81, 0), (12.09, 2.61, 0.88), "stone", 0.003)
bx("hob", (10.3, 1.98, 0.92), (11.1, 2.44, 0.925), "screen")
for i in range(1, 5):
    bx(f"island.gap{i}", (9.32 + i * 0.546 - 0.002, 1.848, 0.12), (9.32 + i * 0.546 + 0.002, 1.85, 0.86), "black")
for i, sx in enumerate((9.85, 10.685, 11.52)):
    cy(f"stool{i}.seat", (sx, 2.86), 0.17, 0.63, 0.67, "oak_flat", bevel=0.008)
    for q in range(4):
        a = q * math.pi / 2 + 0.78
        beam(f"stool{i}.leg{q}", (sx + math.cos(a) * 0.11, 2.86 + math.sin(a) * 0.11, 0.63),
             (sx + math.cos(a) * 0.19, 2.86 + math.sin(a) * 0.19, 0), 0.02, 0.02, M["black"], F)
    cy(f"stool{i}.ring", (sx, 2.86), 0.165, 0.22, 0.235, "black")
# back run: tall fridge / pantry block, then base units with sink under the window
bx("tall.body", (8.81, 0.2, 0.1), (9.55, 0.8, 2.4), "oak")
bx("tall.kick", (8.81, 0.2, 0), (9.55, 0.77, 0.1), "black")
bx("tall.gap", (9.178, 0.8, 0.1), (9.182, 0.802, 2.4), "black")
bx("tall.fill", (8.81, 0.2, 2.4), (9.55, 0.8, H), "paint")
bx("tall.h1", (9.12, 0.80, 0.9), (9.14, 0.83, 1.5), "black"); bx("tall.h2", (9.22, 0.80, 0.9), (9.24, 0.83, 1.5), "black")
bx("run.body", (9.55, 0.2, 0.1), (12.8, 0.78, 0.88), "cabinet")
bx("run.kick", (9.55, 0.2, 0), (12.8, 0.74, 0.1), "black")
bx("run.top", (9.55, 0.2, 0.88), (12.8, 0.8, 0.92), "stone", 0.003)
bx("run.splash", (9.55, 0.2, 0.92), (12.8, 0.215, 1.1), "stone")
bx("run.splashE", (12.785, 0.2, 0.92), (12.8, 0.8, 1.1), "stone")
for i in range(1, 6):
    bx(f"run.gap{i}", (9.55 + i * 0.542 - 0.002, 0.78, 0.12), (9.55 + i * 0.542 + 0.002, 0.782, 0.86), "black")
bx("run.rail", (9.57, 0.78, 0.84), (12.78, 0.784, 0.85), "black")
bx("sink", (10.45, 0.3, 0.9), (11.15, 0.7, 0.922), "steel")
bx("sink.well", (10.48, 0.33, 0.921), (11.12, 0.67, 0.923), "black")
cy("tap.riser", (10.8, 0.27), 0.012, 0.92, 1.25, "black", seg=12)
beam("tap.spout", (10.8, 0.27, 1.25), (10.8, 0.46, 1.25), 0.024, 0.024, M["black"], F)
beam("tap.drop", (10.8, 0.46, 1.25), (10.8, 0.46, 1.19), 0.024, 0.024, M["black"], F)
bx("board", (11.6, 0.3, 0.92), (11.95, 0.55, 0.94), "oak_flat", 0.003)
cy("kettle", (12.4, 0.5), 0.08, 0.92, 1.12, "steel", r2=0.06)
plant("herb", 12.55, 0.38, z=0.92, h=0.32, pot_r=0.06, pot_h=0.12)
# shelf with cups on the east wall above the run
bx("shelf", (12.55, 0.3, 1.5), (12.8, 1.9, 1.53), "oak_flat")
for i in range(5):
    cy(f"cup{i}", (12.68, 0.5 + i * 0.28), 0.045, 1.53, 1.63, "ceramic")
for i, px in enumerate((9.9, 10.685, 11.47)):
    pendant(f"pend_island{i}", px, 2.21, 1.85, r=0.07, watts=8)

# ================================================================== HALL / ENTRY / STAIR
bx("bench", (2.52, 0.24, 0.38), (3.95, 0.62, 0.44), "oak_flat", 0.006)          # entry bench
for i, px in enumerate((2.6, 3.87)):
    bx(f"bench.leg{i}", (px - .02, 0.26, 0), (px + .02, 0.60, 0.38), "black")
bx("bench.cushion", (2.6, 0.27, 0.44), (3.2, 0.59, 0.5), "throw", 0.02)
bx("mirror_entry", (3.0, 0.205, 1.0), (3.6, 0.215, 1.9), "mirror"); bx("mirror_entry.fr", (2.98, 0.2, 0.98), (3.62, 0.208, 1.92), "black")
bx("doormat", (4.2, 0.3, 0), (5.1, 0.85, 0.012), "armchair", 0.004)
plant("plant_stair", 1.95, 2.0, h=1.9, pot_r=0.24, pot_h=0.5)
bx("art_hall", (3.795, 3.9, 1.0), (3.8, 4.9, 1.8), "art1") if False else None

# ================================================================== STORE (behind closed door: shelving)
for i in range(4):
    bx(f"store.shelf{i}", (2.05, 3.93, 0.4 + i * 0.5), (2.85, 4.35, 0.42 + i * 0.5), "cabinet_white")

# ================================================================== BEDROOM
# bed 1.8 x 2.2 with headboard on the west wall
bx("bed.base", (0.3, 7.82, 0.1), (2.42, 9.56, 0.3), "oak", 0.01)
bx("bed.mattress", (0.32, 7.84, 0.3), (2.4, 9.54, 0.54), "bed", 0.05, seg=4)
bx("bed.duvet", (0.95, 7.81, 0.5), (2.43, 9.57, 0.6), "bed", 0.05, seg=4)
bx("bed.throw", (1.95, 7.80, 0.52), (2.44, 9.58, 0.615), "throw", 0.04, seg=4)
bx("bed.head", (0.2, 7.6, 0.0), (0.28, 9.78, 1.15), "sofa", 0.03)
for i, py in enumerate((8.27, 9.11)):
    bx(f"pillow{i}", (0.36, py - 0.33, 0.54), (0.82, py + 0.33, 0.70), "bed", 0.07, seg=4)
    bx(f"pillowb{i}", (0.80, py - 0.25, 0.56), (1.0, py + 0.25, 0.80), "cushion" if i else "throw", 0.07, seg=4,
       rot_z=0)
for i, py in enumerate((7.42, 9.96)):                                  # bedside tables + lamps
    bx(f"bedside{i}", (0.22, py - 0.2, 0.18), (0.62, py + 0.2, 0.5), "oak", 0.006)
    cy(f"bedside{i}.leg", (0.42, py), 0.03, 0, 0.18, "black")
    cy(f"blamp{i}.base", (0.38, py), 0.05, 0.5, 0.68, "ceramic", r2=0.03)
    cy(f"blamp{i}.shade", (0.38, py), 0.1, 0.68, 0.84, "outdoor", r2=0.075)
    ld = bpy.data.lights.new(f"blamp{i}", "POINT"); ld.energy = 4; ld.color = (1, 0.8, 0.6); ld.shadow_soft_size = 0.05
    ob = bpy.data.objects.new(f"blamp{i}", ld); ob.location = (0.38, py, 0.76); ob["base_watts"] = 4.0
    coll("Lights").objects.link(ob)
bx("bed.rug", (1.2, 7.5, 0), (3.5, 9.9, 0.012), "rug", 0.004)
# built-in wardrobe 2.34 x 0.5, four oak doors facing the room
bx("robe.carcass", (0.2, 6.71, 0), (2.54, 7.20, 2.4), "cabinet_white")
bx("robe.fill", (0.2, 6.71, 2.4), (2.54, 7.22, H), "paint")
for i in range(4):
    a = 0.2 + i * 0.585
    bx(f"robe.door{i}", (a + 0.003, 7.20, 0.05), (a + 0.582, 7.22, 2.4), "oak")
    bx(f"robe.pull{i}", (a + (0.52 if i % 2 == 0 else 0.04), 7.22, 0.95), (a + (0.54 if i % 2 == 0 else 0.06), 7.245, 1.25), "black")
bx("robe.kick", (0.2, 6.71, 0), (2.54, 7.19, 0.05), "black")
# sheer curtain across the north window (wavy plane) + track
def curtain(n, x0, x1, y, z0, z1, waves=14):
    seg = waves * 8
    vs, fs = [], []
    for i in range(seg + 1):
        t = i / seg
        x = x0 + (x1 - x0) * t
        yy = y + 0.035 * math.sin(t * waves * 2 * math.pi)
        vs += [(x, yy, z0), (x, yy, z1)]
    for i in range(seg):
        fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    me = bpy.data.meshes.new(n); me.from_pydata(vs, [], fs)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(n, me); me.materials.append(M["curtain"]); coll(F).objects.link(ob)
curtain("curtain_bedL", 1.2, 1.95, 10.24, 0.03, 2.62, waves=7)
curtain("curtain_bedR", 2.9, 3.65, 10.24, 0.03, 2.62, waves=7)
bx("curtain_track", (1.1, 10.22, 2.62), (3.75, 10.26, 2.64), "black")
bx("art_bed", (3.775, 8.2, 1.1), (3.795, 9.3, 1.9), "art2"); bx("art_bed.fr", (3.785, 8.17, 1.07), (3.80, 9.33, 1.93), "black")
plant("plant_bed", 3.4, 9.95, h=1.4)

# ================================================================== BATHROOM
bx("vanity", (0.21, 5.76, 0.45), (0.70, 6.48, 0.82), "oak", 0.004)               # wall-hung vanity
bx("vanity.top", (0.21, 5.74, 0.82), (0.72, 6.50, 0.85), "stone", 0.003)
cy("basin", (0.46, 6.12), 0.19, 0.85, 0.97, "ceramic", r2=0.2)
cy("basin.in", (0.46, 6.12), 0.165, 0.965, 0.972, "paint")
cy("basin.tap", (0.27, 6.12), 0.012, 0.85, 1.1, "black", seg=12)
beam("basin.spout", (0.27, 6.12, 1.1), (0.40, 6.12, 1.1), 0.02, 0.02, M["black"], F)
bx("bath.mirror", (0.212, 5.78, 1.1), (0.22, 6.46, 1.95), "mirror"); bx("bath.mirror.fr", (0.21, 5.76, 1.08), (0.216, 6.48, 1.97), "black")
bx("wc.cistern", (0.21, 5.19, 0.0), (0.36, 5.57, 0.85), "ceramic", 0.02)         # back-to-wall WC
bx("wc.pan", (0.34, 5.2, 0.0), (0.72, 5.56, 0.40), "ceramic", 0.09, seg=5)
bx("wc.seat", (0.34, 5.19, 0.40), (0.73, 5.57, 0.43), "ceramic", 0.012)
bx("wc.flush", (0.36, 5.33, 1.0), (0.365, 5.43, 1.07), "steel")
bx("roll", (0.215, 4.98, 0.65), (0.30, 5.10, 0.75), "paint", 0.03)
# walk-in shower 1.65 x 0.97: fixed glass screen on the line drawn in the plan
bx("shower.glass", (0.21, 4.895, 0.0), (1.2, 4.905, 2.1), "shower_glass")
bx("shower.channel", (0.21, 4.89, 0.0), (1.2, 4.91, 0.02), "black")
bx("shower.tray", (0.21, 3.94, 0.0), (1.84, 4.89, 0.004), "tile_floor")
cy("shower.arm", (1.0, 4.0), 0.012, 2.15, 2.17, "black", seg=10)
beam("shower.pipe", (1.0, 3.95, 2.16), (1.0, 4.35, 2.16), 0.02, 0.02, M["black"], F)
cy("shower.rose", (1.0, 4.38), 0.12, 2.13, 2.15, "black")
cy("shower.mixer", (1.0, 3.95), 0.05, 1.1, 1.1 + 0.001, "black")
bx("shower.mix", (0.95, 3.94, 1.05), (1.05, 3.96, 1.15), "black")
bx("shower.niche", (0.4, 3.94, 1.1), (0.75, 3.945, 1.4), "tile_floor")
bx("towel.rail", (1.835, 4.1, 1.15), (1.80, 4.7, 1.17), "black")
bx("towel", (1.79, 4.2, 0.7), (1.83, 4.6, 1.17), "bed", 0.01)

# ================================================================== TERRACE
armchair("t_arm1", 4.59, 7.30, 5.42, 8.08, "W", mat="outdoor")
armchair("t_arm2", 7.82, 7.30, 8.65, 8.08, "E", mat="outdoor")
armchair("t_ch1", 5.83, 6.10, 6.57, 6.93, "S", mat="outdoor")
armchair("t_ch2", 6.63, 6.10, 7.37, 6.93, "S", mat="outdoor")
cy("t_table.top", (6.61, 7.67), 0.45, 0.36, 0.40, "concrete", bevel=0.008)
cy("t_table.base", (6.61, 7.67), 0.3, 0.0, 0.36, "concrete")
cy("t_table.bowl", (6.61, 7.67), 0.1, 0.40, 0.46, "ceramic", r2=0.15)
plant("t_plant1", 11.7, 6.4, z=-0.02, h=1.6, pot_r=0.26, pot_h=0.55)
plant("t_plant2", 4.4, 9.0, z=-0.02, h=1.3, pot_r=0.22, pot_h=0.45)
# two sun loungers on the paving west of the pool, facing east
for i, ly in enumerate((11.0, 12.3)):
    bx(f"lounger{i}.frame", (4.25, ly - 0.32, 0.18), (5.55, ly + 0.32, 0.24), "oak_flat", 0.01)
    bx(f"lounger{i}.pad", (4.27, ly - 0.30, 0.24), (5.53, ly + 0.30, 0.31), "outdoor", 0.02)
    beam(f"lounger{i}.back", (4.25, ly, 0.27), (3.85 + 0.2, ly, 0.62), 0.6, 0.06, M["outdoor"], F)
    for q, lx in enumerate((4.35, 5.45)):
        bx(f"lounger{i}.leg{q}", (lx - .02, ly - 0.3, -0.02), (lx + .02, ly + 0.3, 0.18), "black")

# ================================================================== GARDEN
for i in range(9):                                  # hedge along the rear fence
    blob(f"hedge_n{i}", (-0.3 + i * 1.75, 14.15, 0.6), 0.75, "leaf", scale=(1.25, 0.5, 1.0), strength=0.2)
for i in range(6):                                  # shrubs along the east fence
    blob(f"hedge_e{i}", (13.5, 6.6 + i * 1.3, 0.5), 0.6, "leaf2" if i % 2 else "leaf", scale=(0.6, 1.1, 1.0), strength=0.25)
for i in range(4):                                  # low planting by the bedroom wall
    blob(f"shrub_w{i}", (4.5 + 0.02 * i, 9.9 + 0.0 * i, 0.3), 0.01, "leaf")   # (placeholder kept tiny)
for i in range(5):
    blob(f"front_hedge{i}", (0.2 + i * 0.75, -0.55, 0.4), 0.5, "leaf", scale=(1.0, 0.6, 0.9), strength=0.2)
for i in range(3):
    blob(f"front_shrub{i}", (6.6 + i * 0.55, -0.5, 0.3), 0.38, "leaf2", strength=0.25)
tree("tree_nw", 1.3, 12.6, h=5.2, r=1.7)
tree("tree_front", 1.5, -3.2, h=4.6, r=1.5)
tree("tree_street1", -6.0, -5.9, h=6.5, r=2.2)
tree("tree_street2", 19.0, -5.9, h=6.0, r=2.0)
tree("tree_back1", 16.5, 17.5, h=7.5, r=2.6)
tree("tree_back2", 5.0, 19.0, h=8.0, r=2.8)
tree("tree_back3", -5.0, 15.0, h=7.0, r=2.4)
# neighbouring houses as simple rendered volumes so the horizon is not empty
for n, lo, hi in (("nb_W", (-13.5, -1.0, -0.05), (-3.2, 9.5, 5.6)), ("nb_E", (16.2, -1.0, -0.05), (26.0, 9.0, 5.8)),
                  ("nb_N", (0.0, 19.5, -0.05), (12.0, 27.5, 5.2)), ("nb_S1", (-6.0, -24.0, -0.05), (5.0, -16.0, 5.5)),
                  ("nb_S2", (9.0, -24.0, -0.05), (20.0, -16.0, 5.9))):
    box(n, lo, hi, M["render"], "Site")
    box(n + ".roof", (lo[0] - 0.3, lo[1] - 0.3, hi[2]), (hi[0] + 0.3, hi[1] + 0.3, hi[2] + 0.2), M["concrete"], "Site")

# ================================================================== LIGHTS (power set per variant in render.py)
for i, (x, y) in enumerate([(5.0, 1.0), (6.9, 1.0), (5.0, 2.9), (6.9, 2.9), (5.0, 4.8), (6.9, 4.8),      # living
                            (8.9, 1.3), (8.9, 3.0), (8.9, 5.0), (10.7, 5.2), (12.3, 5.2),                 # dining edge
                            (10.0, 1.3), (11.4, 1.3), (12.4, 1.3), (12.4, 3.0),                            # kitchen
                            (3.4, 1.2), (3.4, 2.9), (3.4, 4.6), (3.0, 6.0)]):                              # entry / hall
    downlight(f"dl_main{i}", x, y)
for i, (x, y) in enumerate([(1.0, 4.4), (1.0, 5.3), (1.0, 6.1)]):
    downlight(f"dl_bath{i}", x, y, watts=10)
    bpy.data.objects[f"dl_bath{i}"]["always_on"] = 1      # no window in the bathroom
for i, (x, y) in enumerate([(1.3, 7.8), (3.0, 7.8), (1.3, 9.6), (3.0, 9.6)]):
    downlight(f"dl_bed{i}", x, y, watts=7)
for i, (x, y) in enumerate([(5.5, 7.6), (7.8, 7.6), (10.1, 7.6), (5.5, 6.6), (10.1, 6.6)]):
    downlight(f"dl_terrace{i}", x, y, z=H, watts=9)
downlight("dl_store", 2.45, 4.5, watts=5)
bpy.data.objects["dl_store"]["always_on"] = 1
pendant("pend_stair", 1.95, 2.0, 3.6, r=0.14, watts=25)
bpy.data.objects["pend_stair.cord"].scale.z = 1.0
cyl("pend_stair.cord2", (1.95, 2.0), 0.004, H, TOP, M["black"], F, seg=8)
# pool lights (under water, dusk only) and garden uplights
for i, px in enumerate((7.0, 8.8, 10.6)):
    ld = bpy.data.lights.new(f"pool{i}", "POINT"); ld.energy = 30; ld.color = (0.6, 0.95, 1.0); ld.shadow_soft_size = 0.1
    ob = bpy.data.objects.new(f"pool{i}", ld); ob.location = (px, 10.6, -0.9); ob["base_watts"] = 30.0; ob["dusk_only"] = 1
    coll("Lights").objects.link(ob)
for i, (x, y) in enumerate([(1.3, 12.0), (13.3, 8.0), (13.3, 11.5), (2.0, 14.0), (9.0, 14.1), (1.5, -2.6)]):
    ld = bpy.data.lights.new(f"garden{i}", "SPOT"); ld.energy = 25; ld.color = (1.0, 0.85, 0.65); ld.spot_size = 1.4
    ob = bpy.data.objects.new(f"garden{i}", ld); ob.location = (x, y, 0.05); ob.rotation_euler = (math.pi, 0, 0)
    ob["base_watts"] = 25.0; ob["dusk_only"] = 1
    coll("Lights").objects.link(ob)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BUILD, "house.blend"))
print("OK house.blend  objects:", len(bpy.data.objects))
