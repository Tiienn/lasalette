"""Step 3 - render with Blender Cycles.

  blender -b -P src/render.py -- --mode pano                    # all views, day + dusk, 2048 px, 128 spp
  blender -b -P src/render.py -- --mode pano --nodes living,pool --variant day
  blender -b -P src/render.py -- --mode top                     # plan view (also used for the mini map)
  blender -b -P src/render.py -- --mode test --nodes living     # quick flat check images

Out: build/raw/<variant>/<node>/<face>.png   (faces n e s w u d, 90 deg each)
     build/top.png, build/test/<variant>_<node>.png
Finished faces are skipped, so an interrupted render can simply be restarted
(use --force to re-render).
"""
import bpy, sys, os, math, json, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import BUILD, ROOT
from mathutils import Vector, Matrix

ap = argparse.ArgumentParser()
ap.add_argument("--mode", default="pano", choices=["pano", "top", "test"])
ap.add_argument("--variant", default="both", choices=["day", "dusk", "both"])
ap.add_argument("--nodes", default="")
ap.add_argument("--size", type=int, default=2048)
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--device", default="auto", choices=["auto", "cpu"])
ap.add_argument("--force", action="store_true")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

bpy.ops.wm.open_mainfile(filepath=os.path.join(BUILD, "house.blend"))
T = json.load(open(os.path.join(ROOT, "src", "nodes.json")))
S = bpy.context.scene
EYE = T["eye"]

# ------------------------------------------------------------------ lighting variants
# North is +Y. Sun azimuth is a compass bearing (0 = north, 90 = east).
# The living room, terrace and pool face north, so the sun sits in the northern sky.
VARIANTS = {
    "day":  dict(sun_el=52.0, sun_az=330.0, sky=1.0, exposure=-1.8, lamps=2.4, always=5.0, glow=1.5,
                 dusk_lamps=False, ev_scale=1.0),
    "dusk": dict(sun_el=-1.0, sun_az=292.0, sky=1.0, exposure=3.6, lamps=0.13, always=0.13, glow=0.045,
                 dusk_lamps=True, ev_scale=1.0),
}

# ------------------------------------------------------------------ cycles
S.render.engine = "CYCLES"
C = S.cycles
C.samples = a.samples
C.use_adaptive_sampling = True
C.adaptive_threshold = 0.015
C.use_denoising = True
try:
    C.denoiser = "OPENIMAGEDENOISE"
    C.denoising_input_passes = "RGB_ALBEDO_NORMAL"
except Exception:
    pass
C.max_bounces, C.diffuse_bounces, C.glossy_bounces = 10, 5, 4
C.transmission_bounces, C.transparent_max_bounces = 8, 24
C.caustics_reflective = C.caustics_refractive = False
C.sample_clamp_indirect = 8.0
C.blur_glossy = 1.0
S.render.film_transparent = False
S.render.image_settings.file_format = "PNG"
S.render.image_settings.color_depth = "16"
S.render.use_persistent_data = True
try:
    S.view_settings.view_transform = "AgX"
    S.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    try:
        S.view_settings.view_transform = "Filmic"
    except Exception:
        pass


def use_gpu():
    if a.device == "cpu":
        return "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except Exception:
        return "CPU"
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == kind]
            if devs:
                for d in prefs.devices:
                    d.use = d.type == kind
                C.device = "GPU"
                return kind
        except Exception:
            continue
    C.device = "CPU"
    return "CPU"


print("Render device:", use_gpu())

# ------------------------------------------------------------------ world + sun
W = bpy.data.worlds.new("World")
S.world = W
W.use_nodes = True
nt = W.node_tree
nt.nodes.clear()
sky = nt.nodes.new("ShaderNodeTexSky")
for kind in ("MULTIPLE_SCATTERING", "NISHITA"):
    try:
        sky.sky_type = kind
        break
    except Exception:
        pass
bg = nt.nodes.new("ShaderNodeBackground")
flat = nt.nodes.new("ShaderNodeBackground")
mix = nt.nodes.new("ShaderNodeMixShader")
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(sky.outputs[0], bg.inputs[0])
nt.links.new(bg.outputs[0], mix.inputs[1])
nt.links.new(flat.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs[0])
mix.inputs[0].default_value = 0.0

sun_data = bpy.data.lights.new("TopSun", "SUN")       # only used for the plan view
sun_ob = bpy.data.objects.new("TopSun", sun_data)
S.collection.objects.link(sun_ob)
sun_ob.hide_render = True

lamp_mat = bpy.data.materials["Lamp glow"]
lamp_em = next(n for n in lamp_mat.node_tree.nodes if n.type == "EMISSION")
LAMPS = [o for o in bpy.data.objects if o.type == "LIGHT" and "base_watts" in o]


def set_variant(name):
    v = VARIANTS[name]
    mix.inputs[0].default_value = 0.0
    sky.sun_elevation = math.radians(v["sun_el"])
    sky.sun_rotation = math.radians(v["sun_az"])
    try:
        sky.sun_disc = True
        sky.sun_intensity = 1.0
        sky.sun_size = math.radians(0.545)
    except Exception:
        pass
    bg.inputs[1].default_value = v["sky"]
    for o in LAMPS:
        on = v["dusk_lamps"] or not o.get("dusk_only")
        o.hide_render = not on
        o.data.energy = o["base_watts"] * (v["always"] if o.get("always_on") else v["lamps"])
    lamp_em.inputs[1].default_value = v["glow"] * 200
    sun_ob.hide_render = True
    return v


# ------------------------------------------------------------------ camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
S.collection.objects.link(cam)
S.camera = cam
cam_data.clip_start, cam_data.clip_end = 0.03, 400

FACES = {  # name: (forward, up)   -- the viewer uses the same table
    "n": ((0, 1, 0), (0, 0, 1)), "e": ((1, 0, 0), (0, 0, 1)),
    "s": ((0, -1, 0), (0, 0, 1)), "w": ((-1, 0, 0), (0, 0, 1)),
    "u": ((0, 0, 1), (0, 1, 0)), "d": ((0, 0, -1), (0, 1, 0)),
}


def aim(pos, fwd, up):
    f, u = Vector(fwd).normalized(), Vector(up)
    r = f.cross(u).normalized()
    u = r.cross(f)
    M = Matrix((r, u, -f)).transposed().to_4x4()
    M.translation = Vector(pos)
    cam.matrix_world = M


def render(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    S.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"  wrote {os.path.relpath(path, ROOT)}  ({time.time() - t:.0f}s)", flush=True)


nodes = T["nodes"]
if a.nodes:
    want = a.nodes.split(",")
    nodes = [n for n in nodes if n["id"] in want]
variants = ["day", "dusk"] if a.variant == "both" else [a.variant]

# ------------------------------------------------------------------ modes
if a.mode == "top":
    for cname in ("Upper",):
        for o in bpy.data.collections[cname].objects:
            o.hide_render = True
    for o in bpy.data.objects:
        if o.name.startswith(("tree_", "pend_", "dl_", "nb_")) or o.type == "LIGHT":
            o.hide_render = True
    mix.inputs[0].default_value = 1.0
    flat.inputs[0].default_value = (1, 1, 1, 1)
    flat.inputs[1].default_value = 1.1
    sun_ob.hide_render = False
    sun_data.energy = 2.2
    sun_data.angle = math.radians(8)
    sun_ob.rotation_euler = (math.radians(18), math.radians(-14), 0)
    m = T["map"]
    w, h = m["x1"] - m["x0"], m["y1"] - m["y0"]
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = max(w, h)
    aim(((m["x0"] + m["x1"]) / 2, (m["y0"] + m["y1"]) / 2, 30), (0, 0, -1), (0, 1, 0))
    px = a.size if a.size != 2048 else 2400
    S.render.resolution_x, S.render.resolution_y = int(px * w / max(w, h)), int(px * h / max(w, h))
    S.view_settings.exposure = -0.4
    C.samples = min(a.samples, 96)
    render(os.path.join(BUILD, "top.png"))

elif a.mode == "test":
    cam_data.type = "PERSP"
    cam_data.sensor_width = 36
    cam_data.lens = 15
    S.render.resolution_x, S.render.resolution_y = (a.size, int(a.size * 9 / 16)) if a.size != 2048 else (1600, 900)
    for vn in variants:
        v = set_variant(vn)
        for n in nodes:
            p = Vector((n["pos"][0], n["pos"][1], EYE))
            look = Vector((n["look"][0], n["look"][1], EYE - 0.25))
            S.view_settings.exposure = v["exposure"] + n.get("ev", 0) * v["ev_scale"]
            aim(p, look - p, (0, 0, 1))
            render(os.path.join(BUILD, "test", f"{vn}_{n['id']}.png"))

else:
    cam_data.type = "PERSP"
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.angle = math.pi / 2
    S.render.resolution_x = S.render.resolution_y = a.size
    total = len(variants) * len(nodes) * 6
    done, t0 = 0, time.time()
    for vn in variants:
        v = set_variant(vn)
        for n in nodes:
            S.view_settings.exposure = v["exposure"] + n.get("ev", 0) * v["ev_scale"]
            for face, (f, u) in FACES.items():
                path = os.path.join(BUILD, "raw", vn, n["id"], face + ".png")
                done += 1
                if os.path.exists(path) and not a.force:
                    continue
                aim((n["pos"][0], n["pos"][1], EYE), f, u)
                print(f"[{done}/{total}] {vn} {n['id']} {face}  elapsed {(time.time() - t0) / 60:.1f} min", flush=True)
                render(path)
print("DONE")
