# Ferrofluid Labyrinth - renders the reel frame by frame with exactly the approved still's scene (labyrinth_still.py,
# built once), swapping the labyrinth maps and the camera distance per frame. Fast settings: adaptive sampling +
# OptiX denoiser, persistent data. Several instances can share the GPU (stride k/n), and a frame is rendered as soon
# as its maps exist (rendering overlaps with map generation).
# Usage: blender -b --factory-startup -P scripts/blender/labyrinth_anim.py -- <framesDir> <outDir> [samples] [k] [n]
import json
import math
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
FRAMES, OUTDIR = argv[0], argv[1]
SAMPLES = argv[2] if len(argv) > 2 else "48"
K = int(argv[3]) if len(argv) > 3 else 0
N = int(argv[4]) if len(argv) > 4 else 1
still = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labyrinth_still.py")
first = os.path.join(FRAMES, f"_first_{K}")
os.makedirs(first, exist_ok=True)
for n in ("height", "mask"):
    with open(os.path.join(FRAMES, f"{n}_0000.png"), "rb") as a, open(os.path.join(first, f"{n}.png"), "wb") as b:
        b.write(a.read())
sys.argv = [sys.argv[0], "--", first.replace("\\", "/"), "unused.png", SAMPLES]
g = {"NO_RENDER": True, "__name__": "labyrinth_still"}
exec(compile(open(still, encoding="utf8").read(), still, "exec"), g)

scene = bpy.context.scene
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.03
scene.cycles.denoiser = "OPTIX"
scene.render.use_persistent_data = True
height_img, mask_img = g["height_img"], g["mask_img"]
cam, cd, tilt = g["cam"], g["cd"], g["tilt"]
spec = json.load(open(os.path.join(FRAMES, "frames.json")))
os.makedirs(OUTDIR, exist_ok=True)
t0 = time.time()
done = 0
for fr in spec["frames"]:
    f = fr["frame"]
    if f % N != K:
        continue
    out = os.path.join(OUTDIR, f"f_{f:04d}.png")
    if os.path.exists(out):
        continue
    mp = os.path.join(FRAMES, f"mask_{f:04d}.png")
    while not os.path.exists(mp):  # the map generator is still on its way
        time.sleep(1.0)
    time.sleep(0.3)
    height_img.filepath = os.path.join(FRAMES, f"height_{f:04d}.png")
    mask_img.filepath = mp
    height_img.reload()
    mask_img.reload()
    d = fr["dist"]
    cam.location = (0, -d * math.sin(tilt), d * math.cos(tilt))
    cd.dof.focus_distance = d
    bpy.context.view_layer.update()
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    done += 1
    print(f"FRAME {f} ({(time.time() - t0) / done:.1f} s/frame)", flush=True)
print("DONE", done)
