# "Ferrofluid vs Music" (0012) animation renderer: the approved look scene (ferro_speaker_look.py) driven per frame by
# the score (scripts/gen-ferromusic-frames.ts -> amps.bin + frames.json).
# Realism: spikes are Rosensweig cones with rounded bases on a domed pool; they lean outward along the field lines
# (more near the rim), and their tips sway slightly as they wobble.
# Usage: blender -b --factory-startup -P scripts/blender/ferro_music.py -- <dataDir> <outDir> [samples] [k] [n] [only]
import json
import math
import os
import sys
import time

import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
DATA, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
SAMPLES = int(argv[2]) if len(argv) > 2 else 24
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)

here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["blender", "--", OUT, str(SAMPLES)]
NO_RENDER = True
exec(open(os.path.join(here, "ferro_speaker_look.py"), encoding="utf-8").read())
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_adaptive_sampling = True
scene.render.use_persistent_data = True
if os.environ.get("FERRO_ENGINE") == "EEVEE":  # fast raster engine with screen-space ray tracing
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    scene.eevee.use_raytracing = True
    scene.eevee.ray_tracing_options.resolution_scale = "1"
    scene.eevee.use_shadows = True
cd.dof.aperture_fstop = 18.0  # macro: focused on the action, foreground spikes softly out of focus (owner: "inside the screen")

# --- v6 stage (owner, Nov 11: "why a dish? replace it, ultra realistic"): no container - a free puddle of ferrofluid
# sitting on a polished black mirror-glass slab, its edge a living, slowly wobbling outline
for o in (sur, rim, body):
    o.hide_render = True
mirror = principled("BlackMirror", (0.003, 0.003, 0.005), rough=0.11, coat=0.5)
# light linking: the studio lights light the ferrofluid only, so the mirror floor never shows them as bright bands
_lit = bpy.data.collections.new("LitByStudio")
_lit.objects.link(fluid)
for _o in scene.objects:
    if _o.type == "LIGHT":
        _o.light_linking.receiver_collection = _lit
for _o in scene.objects:
    if _o.type == "LIGHT":
        _o.data.energy *= 0.85
fl.data.materials.clear()
fl.data.materials.append(mirror)
fl.location.z = -0.0003
fl.hide_render = False

spec = json.load(open(os.path.join(DATA, "frames.json")))
S = np.array(spec["sites"], dtype=np.float64)
NS = len(S)
A = np.fromfile(os.path.join(DATA, "amps.bin"), dtype=np.float32).reshape(spec["n"], NS)

# per vertex: nearest site + spike profile (computed once)
near = np.zeros(len(X), dtype=np.int32)
dmin = np.full(len(X), 1e9)
for k in range(NS):
    d = np.hypot(X - S[k, 0], Y - S[k, 1])
    c = d < dmin
    dmin[c] = d[c]
    near[c] = k
w = SPACING * 0.62
prof = np.clip(1 - dmin / w, 0, 1)
shape = (prof ** 2.2) * (3 - 2 * prof) * 0.5 + prof ** 6 * 0.5
theta = np.arctan2(Y, X)


def blob(t):
    """the free puddle: a softly wobbling outline, a domed body, a rounded meniscus edge"""
    Rb = R_POOL * (0.95 + 0.025 * np.sin(3 * theta + 0.6 * t) + 0.02 * np.sin(5 * theta - 0.9 * t + 1.0))
    e = np.clip((Rb - r) / 0.007, 0, 1)
    p = 0.0028 * (1 - (r / Rb) ** 2 * 0.35) * np.sqrt(e) - 0.0012 * (1 - e)
    return e, p


edge, pool = blob(0.0)
sr = np.hypot(S[near, 0], S[near, 1])
ux = np.where(sr > 1e-6, S[near, 0] / np.maximum(sr, 1e-6), 0)
uy = np.where(sr > 1e-6, S[near, 1] / np.maximum(sr, 1e-6), 0)
lean = 0.05 + 0.14 * (sr / R_POOL) ** 2  # outward lean along the field lines, stronger at the rim
co0 = co.copy()
import mathutils
LIGHTS = {o.name: (o, mathutils.Vector(o.location)) for o in scene.objects if o.type == "LIGHT"}


def move_lights(t):
    # the studio lights drift slowly around the dish so highlights glide over the wet spikes (alive, touchable)
    for name, (o, p0) in LIGHTS.items():
        a = 0.35 * math.sin(2 * math.pi * t / 14 + len(name)) + (0.25 * t / 32 if name == "Top" else 0)
        p = mathutils.Matrix.Rotation(a, 4, "Z") @ p0
        o.location = p
        o.rotation_euler = (mathutils.Vector((0, 0, 0.004)) - p).to_track_quat("-Z", "Y").to_euler()



def frame(f):
    global edge, pool
    edge, pool = blob(f / spec["fps"])
    amp = A[f, near].astype(np.float64)
    prev = A[max(0, f - 2), near].astype(np.float64)
    spike = amp * shape * edge
    dh, ds = spec["cams"][f].get("dome", [0, 0.014])
    dome = dh * np.exp(-((r / ds) ** 2)) * edge  # v4: the tower rises on a dome of fluid
    zt = pool + dome + spike
    # tips lean outward and sway with their growth speed (wobble)
    sway = np.clip((amp - prev) * 2.5, -0.004, 0.004)
    off = (lean * spike + sway * shape * prof ** 2)
    c = co0.copy()
    c[:, 0] = X + ux * off
    c[:, 1] = Y + uy * off
    c[:, 2] = zt
    fluid.data.vertices.foreach_set("co", c.astype(np.float32).ravel())
    fluid.data.update()
    fluid.rotation_euler.z = spec["cams"][f].get("rot", 0.0)  # the pool physically turns
    move_lights(f / spec["fps"])
    la, lb = spec["cams"][f].get("lightA"), spec["cams"][f].get("lightB")
    if la: LIGHTS["Cyan"][0].data.color = la
    if lb: LIGHTS["Magenta"][0].data.color = lb
    cm = spec["cams"][f]
    yaw, d, tilt = cm["yaw"], cm["dist"], cm["tilt"]
    lx, ly, lz = cm["look"]
    cam.location = (lx + math.sin(yaw) * d * math.sin(tilt), ly - math.cos(yaw) * d * math.sin(tilt), lz + d * math.cos(tilt))
    cam.rotation_euler = (tilt, 0, yaw)
    cd.dof.focus_distance = d
    scene.render.filepath = os.path.join(OUT, f"f_{f:04d}.png")
    bpy.ops.render.render(write_still=True)


todo = ONLY if ONLY is not None else list(range(K, spec["n"], NN))
t0 = time.time()
for i, f in enumerate(todo):
    if (ONLY is None or os.environ.get("SKIP_DONE")) and os.path.exists(os.path.join(OUT, f"f_{f:04d}.png")):
        continue
    frame(f)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t0) / (i + 1):.2f} s/frame", flush=True)
print(f"done {len(todo)} frames in {time.time() - t0:.0f} s", flush=True)
