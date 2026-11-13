"""Step 4 - colour grade the raw renders and write the web images.

  python3 src/grade.py                 # needs: pip install pillow numpy
  python3 src/grade.py --size 1536     # smaller faces for faster loading

In:  build/raw/<variant>/<node>/<face>.png, build/top.png, src/nodes.json
Out: web/pano/<variant>/<node>/<face>.jpg, web/thumb/<node>.jpg, web/map.jpg, web/tour.json

Only per-pixel operations are used (no vignette, no local contrast), so the
six faces of a panorama still match exactly at their edges.
"""
import os, json, argparse, math
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, WEB = os.path.join(ROOT, "build", "raw"), os.path.join(ROOT, "web")
ap = argparse.ArgumentParser()
ap.add_argument("--size", type=int, default=2048)
ap.add_argument("--quality", type=int, default=86)
a = ap.parse_args()

GRADE = {  # contrast (S-curve strength), saturation, RGB gain, lift
    "day":  dict(contrast=0.12, sat=1.06, gain=(1.015, 1.0, 0.975), lift=0.0),
    "dusk": dict(contrast=0.10, sat=1.08, gain=(1.02, 1.0, 0.99), lift=0.0),
}


def grade(im, g):
    x = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    x = x * np.array(g["gain"], dtype=np.float32) + g["lift"]
    x = np.clip(x, 0, 1)
    s = x * x * (3 - 2 * x)                       # smoothstep S-curve
    x = x + (s - x) * g["contrast"] * 2
    lum = (x * np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)).sum(-1, keepdims=True)
    x = lum + (x - lum) * g["sat"]
    return Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))


T = json.load(open(os.path.join(ROOT, "src", "nodes.json")))
FACE_DIR = {"n": (0, 1), "e": (1, 0), "s": (0, -1), "w": (-1, 0)}
variants_done, missing = [], []
for v in T["variants"]:
    ok = True
    for n in T["nodes"]:
        for f in "neswud":
            src = os.path.join(RAW, v["id"], n["id"], f + ".png")
            if not os.path.exists(src):
                missing.append(os.path.relpath(src, ROOT)); ok = False
                continue
            dst = os.path.join(WEB, "pano", v["id"], n["id"], f + ".jpg")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im = grade(Image.open(src), GRADE[v["id"]])
            if im.width > a.size:
                im = im.resize((a.size, a.size), Image.LANCZOS)
            im.save(dst, quality=a.quality, optimize=True, progressive=True)
            face_size = im.width
    if ok:
        variants_done.append(v)

# thumbnails: the face closest to each node's opening direction (first finished variant)
os.makedirs(os.path.join(WEB, "thumb"), exist_ok=True)
for n in T["nodes"]:
    dx, dy = n["look"][0] - n["pos"][0], n["look"][1] - n["pos"][1]
    f = max(FACE_DIR, key=lambda k: FACE_DIR[k][0] * dx + FACE_DIR[k][1] * dy)
    for v in T["variants"]:
        src = os.path.join(WEB, "pano", v["id"], n["id"], f + ".jpg")
        if os.path.exists(src):
            im = Image.open(src)
            s = im.width
            im = im.crop((0, int(s * 0.22), s, int(s * 0.78))).resize((320, 180), Image.LANCZOS)
            im.save(os.path.join(WEB, "thumb", n["id"] + ".jpg"), quality=80)
            break

top = os.path.join(ROOT, "build", "top.png")
if os.path.exists(top):
    im = grade(Image.open(top), dict(contrast=0.08, sat=1.05, gain=(1, 1, 1), lift=0.0))
    im.resize((900, round(900 * im.height / im.width)), Image.LANCZOS).save(os.path.join(WEB, "map.jpg"), quality=86)

tour = dict(T)
tour["variants"] = variants_done or T["variants"]
for n in tour["nodes"]:
    dx, dy = n["look"][0] - n["pos"][0], n["look"][1] - n["pos"][1]
    n["yaw"] = round(math.degrees(math.atan2(dy, dx)), 1)
json.dump(tour, open(os.path.join(WEB, "tour.json"), "w"), indent=1)
print(f"web images written. variants ready: {[v['id'] for v in variants_done]}")
if missing:
    print(f"WARNING: {len(missing)} raw faces missing, e.g. {missing[:3]}")
