# 0012 v7 "This liquid came alive" renderer (Blender Cycles, OptiX). A free puddle of ferrofluid on black mirror glass
# that behaves like a creature: its body is a metaball outline (one or two lobes) that reaches, crawls, splits and
# merges; the Rosensweig spike lattice rides WITH the body (a local hex lattice per lobe, computed analytically per
# frame); heartbeat rings rush outward; spikes lean where it goes and sway as they grow.
# Usage: blender -b --factory-startup -P scripts/blender/ferro_alive.py -- <dataDir> <outDir> [samples] [k] [n] [only]
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
import mathutils  # noqa: E402

scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_adaptive_sampling = True
scene.render.use_persistent_data = True
cd.dof.aperture_fstop = 16.0
if os.environ.get("FERRO_RES"):  # e.g. 2160x3840 for sharp thumbnails
    scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ["FERRO_RES"].split("x")]

# --- stage: no dish, black mirror glass ---
for o in (sur, rim, body):
    o.hide_render = True
mirror = principled("BlackMirror", (0.003, 0.003, 0.005), rough=0.11, coat=0.5)
fl.data.materials.clear()
fl.data.materials.append(mirror)
fl.location.z = -0.0003
fl.hide_render = False

# --- a bigger, finer fluid sheet so the creature can travel ---
bpy.data.objects.remove(fluid, do_unlink=True)
HALF = 0.095
NG = 1250
bpy.ops.mesh.primitive_grid_add(x_subdivisions=NG, y_subdivisions=NG, size=2 * HALF)
fluid = bpy.context.active_object
fluid.data.materials.append(ferro)
bpy.ops.object.shade_smooth()
nv = len(fluid.data.vertices)
co0 = np.empty(nv * 3, dtype=np.float32)
fluid.data.vertices.foreach_get("co", co0)
co0 = co0.reshape(-1, 3)
X, Y = co0[:, 0].astype(np.float64), co0[:, 1].astype(np.float64)

# the studio lights light the fluid only (a clean black mirror)
lit = bpy.data.collections.new("LitByStudio")
lit.objects.link(fluid)
LIGHTS = {}
for o in scene.objects:
    if o.type == "LIGHT":
        o.light_linking.receiver_collection = lit
        o.data.energy *= 0.85
        LIGHTS[o.name] = (o, mathutils.Vector(o.location))

# --- BRILLIANT colour (owner, Nov 11: "rich, colourful, brilliant"): the ferrofluid is a black mirror, so its colour is
# what it reflects - a ring of big neon panels, hidden from the camera, mirrored in every spike and droplet ---
NEON = [
    ((0.0, 1.0, 0.95), 0), ((1.0, 0.05, 0.65), 1), ((0.55, 0.15, 1.0), 2), ((0.1, 0.35, 1.0), 3),
    ((1.0, 0.2, 0.95), 4), ((0.0, 0.8, 1.0), 5), ((0.75, 0.0, 1.0), 6), ((1.0, 0.1, 0.4), 7),
]
for col, i in NEON:
    ang = i / len(NEON) * 2 * math.pi + 0.2
    bpy.ops.mesh.primitive_plane_add(size=1.0)
    pnl = bpy.context.active_object
    pnl.scale = (0.16, 0.07, 1)
    pnl.location = (0.2 * math.cos(ang), 0.2 * math.sin(ang), 0.05 + 0.03 * (i % 2))
    pnl.rotation_euler = (mathutils.Vector((0, 0, 0.0)) - pnl.location).to_track_quat("Z", "Y").to_euler()
    pm_ = bpy.data.materials.new(f"Neon{i}")
    pm_.use_nodes = True
    pn_ = pm_.node_tree.nodes
    pn_.clear()
    em_ = pn_.new("ShaderNodeEmission")
    em_.inputs["Color"].default_value = (*col, 1)
    em_.inputs["Strength"].default_value = 12.0
    out_ = pn_.new("ShaderNodeOutputMaterial")
    pm_.node_tree.links.new(em_.outputs["Emission"], out_.inputs["Surface"])
    pnl.data.materials.append(pm_)
    pnl.visible_camera = False
    pnl.light_linking.receiver_collection = lit  # glow on the ferrofluid only, never on the mirror floor
# a glowing, saturated backdrop instead of a dim one
_bd = bpy.data.materials["Backdrop"].node_tree.nodes
for n_ in _bd:
    if n_.type == "VALTORGB":
        n_.color_ramp.elements[1].color = (0.55, 0.06, 1.0, 1)
    if n_.type == "EMISSION":
        n_.inputs["Strength"].default_value = 2.2

LIGHTS["Top"][0].data.color = (0.7, 0.45, 1.0)  # no white highlights: every highlight carries colour
LIGHTS["Top"][0].data.energy *= 0.6

spec = json.load(open(os.path.join(DATA, "frames.json")))

# --- satellite droplets: small beads of ferrofluid on the mirror that the creature pulls in and swallows ---
rng = np.random.default_rng(1212)
DROPS = []
for i in range(34):
    a = rng.uniform(0, 2 * math.pi)
    r0 = rng.uniform(0.055, 0.1)
    rad = rng.uniform(0.0012, 0.0032)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    d = bpy.context.active_object
    d.data.materials.append(ferro)
    bpy.ops.object.shade_smooth()
    lit.objects.link(d)
    DROPS.append({"o": d, "p0": np.array([r0 * math.cos(a), r0 * math.sin(a)]), "rad": rad, "wake": rng.uniform(0.5, 24.0), "pull": rng.uniform(0.6, 1.4)})


def place_drops(fr, t):
    bl = np.array(fr["blobs"], dtype=np.float64)
    mx = (bl[:, 0] * bl[:, 2]).sum() / bl[:, 2].sum()
    my = (bl[:, 1] * bl[:, 2]).sum() / bl[:, 2].sum()
    for dr in DROPS:
        age = max(0.0, t - dr["wake"])
        # once awake, a drop slides toward the creature, faster and faster, and is swallowed at its edge
        k = min(1.0, (age * dr["pull"] / 2.6) ** 2)
        p = dr["p0"] + (np.array([mx, my]) - dr["p0"]) * k
        dist = np.hypot(p[0] - mx, p[1] - my)
        gone = dist < 0.85 * max(b[2] for b in bl) or k >= 1.0
        sc = 0.0 if gone else dr["rad"]
        stretch = 1.0 + 0.6 * min(1.0, age * dr["pull"]) * (1 - k)  # it stretches toward the pull
        ang = math.atan2(my - p[1], mx - p[0])
        dr["o"].location = (p[0], p[1], sc * 0.45 - 0.0003)
        dr["o"].rotation_euler = (0, 0, ang)
        dr["o"].scale = (sc * stretch, sc, sc * 0.6)

A = SPACING
HROW = A * 0.8660254


def hex_nearest(qx, qy):
    """nearest hex-lattice site (local coords) for every point: site x, y and the distance"""
    best_d = np.full(qx.shape, 1e9)
    bx = np.zeros_like(qx)
    by = np.zeros_like(qy)
    j0 = np.floor(qy / HROW)
    for dj in (0, 1):
        j = j0 + dj
        off = 0.5 * np.mod(j, 2)
        i = np.round(qx / A - off)
        sx = (i + off) * A
        sy = j * HROW
        d = np.hypot(qx - sx, qy - sy)
        c = d < best_d
        best_d = np.where(c, d, best_d)
        bx = np.where(c, sx, bx)
        by = np.where(c, sy, by)
    return bx, by, best_d


def heights(fr, t):
    bl = np.array(fr["blobs"], dtype=np.float64)
    contrib = np.stack([np.exp(-((np.hypot(X - b[0], Y - b[1]) / b[2]) ** 4)) for b in bl])
    F = contrib.sum(0)
    owner = np.argmax(contrib, 0)
    wob = 1 + 0.03 * np.sin(np.arctan2(Y, X) * 3 + 0.7 * t)  # a living, slightly uneven outline
    e = np.clip((F * wob - 0.45) / 0.18, 0, 1)
    pool = 0.0028 * np.sqrt(e) * (0.75 + 0.25 * np.clip(F, 0, 1)) - 0.0012 * (1 - e)
    cx, cy = bl[owner, 0], bl[owner, 1]
    sx, sy, dmin = hex_nearest(X - cx, Y - cy)
    sr = np.hypot(sx, sy)
    w = A * 0.62
    prof = np.clip(1 - dmin / w, 0, 1)
    shape = (prof ** 2.2) * (3 - 2 * prof) * 0.5 + prof ** 6 * 0.5
    amp = np.full(X.shape, fr["base"])
    mx = (bl[:, 0] * bl[:, 2]).sum() / bl[:, 2].sum()
    my = (bl[:, 1] * bl[:, 2]).sum() / bl[:, 2].sum()
    for idx, radius, ra in fr["rings"]:
        if idx < 0 or idx >= len(bl):
            rr = np.hypot(cx + sx - mx, cy + sy - my)
        else:
            rr = np.hypot(cx + sx - bl[int(idx), 0], cy + sy - bl[int(idx), 1])
        amp += ra * np.exp(-(((rr - radius) / 0.007) ** 2))
    dx, dy, k, ph, wa = fr["wave"]
    if wa > 1e-5:
        amp += wa * (0.5 + 0.5 * np.cos(k * (sx * dx + sy * dy) + ph)) ** 3
    if fr["crown"] > 1e-4:
        amp = amp * (1 - 0.6 * fr["crown"] * (1 - np.exp(-((sr / 0.02) ** 2)))) + 0.03 * fr["crown"] * np.exp(-((sr / 0.014) ** 2))
    # real spikes are never identical: each site gets its own height (rides with the body)
    hv = np.mod(np.sin(np.round(sx / A * 2) * 12.9898 + np.round(sy / HROW) * 78.233) * 43758.5453, 1.0)
    amp = amp * (0.72 + 0.56 * hv)
    amp = 0.032 * np.tanh(amp / 0.032)
    # a spike stands only where its site is inside the body
    es = np.clip((np.exp(-((sr / bl[owner, 2]) ** 4)) - 0.4) / 0.25, 0, 1)
    spike = amp * shape * e * es
    dome = 0.011 * fr["crown"] * np.exp(-((sr / 0.016) ** 2)) * e
    # fine ripples running over the liquid between the spikes
    rip = 0.00016 * e * (np.sin(820 * (X * 0.8 + Y * 0.6) - 7.0 * t) + np.sin(640 * (X * -0.5 + Y * 0.86) - 5.3 * t + 1.7))
    return pool + dome + spike + rip, spike, amp, sx, sy, sr, shape, prof


def frame(f):
    fr = spec["frames"][f]
    t = f / spec["fps"]
    z, spike, amp, sx, sy, sr, shape, prof = heights(fr, t)
    # sway: compare with the heights a moment ago (deterministic: computed, not remembered)
    _, _, amp_prev, _, _, _, _, _ = heights(spec["frames"][max(0, f - 2)], (f - 2) / spec["fps"])
    sway = np.clip((amp - amp_prev) * 2.0, -0.004, 0.004)
    ux = np.where(sr > 1e-6, sx / np.maximum(sr, 1e-6), 0)
    uy = np.where(sr > 1e-6, sy / np.maximum(sr, 1e-6), 0)
    lean_r = 0.05 + 0.12 * np.clip(sr / 0.04, 0, 1) ** 2
    lx, ly = fr["lean"]
    c = co0.copy()
    c[:, 0] = X + (lean_r * ux + lx) * spike + sway * shape * prof ** 2 * ux
    c[:, 1] = Y + (lean_r * uy + ly) * spike + sway * shape * prof ** 2 * uy
    c[:, 2] = z
    fluid.data.vertices.foreach_set("co", c.astype(np.float32).ravel())
    fluid.data.update()
    place_drops(fr, t)
    for name, (o, p0) in LIGHTS.items():
        a = 0.35 * math.sin(2 * math.pi * t / 14 + len(name)) + (0.25 * t / 30 if name == "Top" else 0)
        p = mathutils.Matrix.Rotation(a, 4, "Z") @ p0
        o.location = p
        o.rotation_euler = (mathutils.Vector((0, 0, 0.004)) - p).to_track_quat("-Z", "Y").to_euler()
    LIGHTS["Cyan"][0].data.color = fr["lightA"]
    LIGHTS["Magenta"][0].data.color = fr["lightB"]
    yaw, d, tilt = fr["yaw"], fr["dist"], fr["tilt"]
    lx_, ly_, lz_ = fr["look"]
    cam.location = (lx_ + math.sin(yaw) * d * math.sin(tilt), ly_ - math.cos(yaw) * d * math.sin(tilt), lz_ + d * math.cos(tilt))
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
