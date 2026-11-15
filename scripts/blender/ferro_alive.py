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
LOOK = os.environ.get("FERRO_LOOK", "B")  # 0018 uses B (owner, Nov 15); 0012 was rendered before this existed  # 0018 look options: A lightbox, B liquid lake, C macro low angle
if LOOK == "A":
    # a backlit violet glass panel: the creature reads as a sharp black silhouette, edges glinting
    lb = bpy.data.materials.new("Lightbox")
    lb.use_nodes = True
    ln = lb.node_tree.nodes
    ln.clear()
    lo_ = ln.new("ShaderNodeOutputMaterial")
    le = ln.new("ShaderNodeEmission")
    ltc = ln.new("ShaderNodeTexCoord")
    lg = ln.new("ShaderNodeTexGradient")
    lg.gradient_type = "SPHERICAL"
    lmap = ln.new("ShaderNodeMapping")
    lmap.inputs["Scale"].default_value = (7.0, 7.0, 7.0)
    lr = ln.new("ShaderNodeValToRGB")
    lr.color_ramp.elements[0].color = (0.02, 0.005, 0.06, 1)
    lr.color_ramp.elements[1].color = (0.55, 0.2, 1.0, 1)
    lb.node_tree.links.new(ltc.outputs["Object"], lmap.inputs["Vector"])
    lb.node_tree.links.new(lmap.outputs["Vector"], lg.inputs["Vector"])
    lb.node_tree.links.new(lg.outputs["Fac"], lr.inputs["Fac"])
    lb.node_tree.links.new(lr.outputs["Color"], le.inputs["Color"])
    le.inputs["Strength"].default_value = 3.0
    lb.node_tree.links.new(le.outputs[0], lo_.inputs["Surface"])
    fl.data.materials.clear()
    fl.data.materials.append(lb)
elif LOOK == "B":
    # a glossy violet liquid lake with slow ripples and a glow from below
    lake = bpy.data.materials.new("Lake")
    lake.use_nodes = True
    kn = lake.node_tree.nodes
    kb = kn["Principled BSDF"]
    kb.inputs["Base Color"].default_value = (0.05, 0.01, 0.12, 1)
    kb.inputs["Roughness"].default_value = 0.03
    kb.inputs["Coat Weight"].default_value = 1.0
    kb.inputs["Emission Color"].default_value = (0.35, 0.08, 0.8, 1)
    kb.inputs["Emission Strength"].default_value = 0.25
    kw = kn.new("ShaderNodeTexWave")
    kw.wave_type = "RINGS"
    kw.inputs["Scale"].default_value = 18.0
    kw.inputs["Distortion"].default_value = 3.0
    kbump = kn.new("ShaderNodeBump")
    kbump.inputs["Strength"].default_value = 0.12
    lake.node_tree.links.new(kw.outputs["Fac"], kbump.inputs["Height"])
    lake.node_tree.links.new(kbump.outputs["Normal"], kb.inputs["Normal"])
    fl.data.materials.clear()
    fl.data.materials.append(lake)
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
NEON_EM = []
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
    NEON_EM.append(em_)
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


JUMP = []
for i in range(26):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    jd = bpy.context.active_object
    jd.data.materials.append(ferro)
    bpy.ops.object.shade_smooth()
    lit.objects.link(jd)
    jd.scale = (0, 0, 0)
    JUMP.append(jd)


def place_jumpers(fr):
    js = fr.get("jumpers", [])
    for i, jd in enumerate(JUMP):
        if i < len(js):
            x, y, z, rad, st, yaw, pitch = js[i]
            jd.location = (x, y, z)
            jd.rotation_euler = (0, -pitch, yaw)
            jd.scale = (rad * st, rad / math.sqrt(st), rad / math.sqrt(st))
        else:
            jd.scale = (0, 0, 0)
            jd.location = (0, 0, -1)


# 0018: polished steel beads the creature eats
chrome = principled("Chrome", (0.92, 0.92, 0.95), metal=1.0, rough=0.06)
if LOOK == "A":  # glowing glass marbles on the lightbox
    chrome = principled("GlassMarble", (0.85, 0.75, 1.0), rough=0.0)
    chrome.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
    chrome.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.4, 0.85, 1.0, 1)
    chrome.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.6
BEADS = []
for i in range(14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0)
    bo = bpy.context.active_object
    bo.data.materials.append(chrome)
    bpy.ops.object.shade_smooth()
    lit.objects.link(bo)
    bo.scale = (0, 0, 0)
    BEADS.append(bo)


def place_beads(fr):
    bl = fr.get("beads", [])
    for i, bo in enumerate(BEADS):
        if i < len(bl):
            x, y, z, r = bl[i]
            bo.location = (x, y, z)
            bo.scale = (r, r, r)
        else:
            bo.scale = (0, 0, 0)
            bo.location = (0, 0, -1)


def place_drops(fr, t):
    if fr.get("noDrops"):
        for dr in DROPS:
            dr["o"].scale = (0, 0, 0)
        return
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
    if os.environ.get("FERRO_DOME", "1") == "1":
        # 0018 (owner: "it looks like a biscuit"): a round, domed body - a living spiky sphere sitting on the surface
        rb = bl[owner, 2]
        dd = np.hypot(X - bl[owner, 0], Y - bl[owner, 1]) / np.maximum(rb, 1e-6)
        dome = 0.62 * rb * np.clip(1 - (dd / 0.95) ** 2, 0, 1) ** 0.8  # a rounded spiky hill, smooth into its edge
        pool = pool + dome * e
    cx, cy = bl[owner, 0], bl[owner, 1]
    sx, sy, dmin = hex_nearest(X - cx, Y - cy)
    sr = np.hypot(sx, sy)
    w = A * 0.62
    prof = np.clip(1 - dmin / w, 0, 1)
    shape = (prof ** 2.2) * (3 - 2 * prof) * 0.5 + prof ** 6 * 0.5
    amp = np.full(X.shape, fr["base"])
    mx = (bl[:, 0] * bl[:, 2]).sum() / bl[:, 2].sum()
    my = (bl[:, 1] * bl[:, 2]).sum() / bl[:, 2].sum()
    for ring in fr["rings"]:
        idx, radius, ra = ring[0], ring[1], ring[2]
        if len(ring) == 5:  # a splash ring around a point (a droplet landing)
            rr = np.hypot(cx + sx - ring[3], cy + sy - ring[4])
        elif idx < 0 or idx >= len(bl):
            rr = np.hypot(cx + sx - mx, cy + sy - my)
        else:
            rr = np.hypot(cx + sx - bl[int(idx), 0], cy + sy - bl[int(idx), 1])
        amp += ra * np.exp(-(((rr - radius) / 0.007) ** 2))
    dx, dy, k, ph, wa = fr["wave"]
    if wa > 1e-5:
        amp += wa * (0.5 + 0.5 * np.cos(k * (sx * dx + sy * dy) + ph)) ** 3
    sw = fr.get("swirl", [0, 3, 0])
    if sw[0] > 1e-5:  # a spiral wave running over the spikes
        ang = np.arctan2(sy, sx)
        amp += sw[0] * (0.5 + 0.5 * np.cos(sw[1] * ang - 120 * sr + sw[2])) ** 3
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


# ---------------- 0018 SPHERE MODE (owner, Nov 15: "it looks like a biscuit" -> a full spiky sphere) ----------------
# The creature is a floating ball of ferrofluid covered in Rosensweig spikes (an icosphere displaced along its own
# normals). It ROLLS as it moves (spikes ride round with it), shoots a spike-arm at the bead it wants, ripples with a
# heartbeat wave over its surface, bristles with long spikes for the crown, and splits into two smaller spheres.
SPHERE = os.environ.get("FERRO_SPHERE", "0") == "1"
if SPHERE:
    fluid.hide_render = True
    SPH = []
    for _ in range(2):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1.0)
        so = bpy.context.active_object
        so.data.materials.append(ferro)
        bpy.ops.object.shade_smooth()
        lit.objects.link(so)
        SPH.append(so)
    _nv = len(SPH[0].data.vertices)
    SU = np.empty(_nv * 3)
    SPH[0].data.vertices.foreach_get("co", SU)
    SU = SU.reshape(-1, 3)
    SU /= np.linalg.norm(SU, axis=1, keepdims=True)
    # spike sites: a fibonacci lattice on the sphere
    NS = 420
    _g = math.pi * (3 - math.sqrt(5))
    SITES = []
    for i in range(NS):
        yy = 1 - (i + 0.5) / NS * 2
        rr_ = math.sqrt(1 - yy * yy)
        SITES.append((math.cos(_g * i) * rr_, math.sin(_g * i) * rr_, yy))
    SITES = np.array(SITES)
    _dots = SU @ SITES.T
    S_NEAR = np.argmax(_dots, axis=1)
    S_ANG = np.arccos(np.clip(_dots[np.arange(_nv), S_NEAR], -1, 1))
    del _dots
    S_W = 0.115  # angular half-width of a spike base
    _c = np.clip(1 - S_ANG / S_W, 0, 1)
    S_PROF = _c ** 2.4 * (3 - 2 * _c) * 0.55 + _c ** 7 * 0.45
    S_VAR = 0.7 + 0.6 * np.mod(np.sin(np.arange(NS) * 12.9898) * 43758.5453, 1.0)

    # rolling: integrate the body's motion into a rotation (deterministic, from the frame data)
    ROT = []
    q = mathutils.Quaternion()
    prev = None
    for fr_ in spec["frames"]:
        b0 = fr_["blobs"][0]
        p = np.array(b0[:2])
        if prev is not None:
            v = p - prev
            d = float(np.linalg.norm(v))
            if d > 1e-7:
                ax = mathutils.Vector((-v[1], v[0], 0.0)).normalized()
                q = mathutils.Quaternion(ax, d / max(b0[2], 1e-4)) @ q
        prev = p
        ROT.append(q.copy())

    def sphere_frame(fr, f, t):
        bl = np.array(fr["blobs"], dtype=np.float64)
        Rmax = float(np.max(bl[:, 2]))
        bodies = [b for b in bl if b[2] >= 0.72 * Rmax][:2]
        arms = [b for b in bl if b[2] < 0.72 * Rmax]
        rot = np.array(ROT[f].to_matrix())
        # heartbeat: a wave that runs from the top of the ball to the bottom
        theta = np.arccos(np.clip(SITES[:, 2], -1, 1))
        amp = np.full(NS, 0.16)
        for ring in fr["rings"]:
            if ring[0] == -1:
                front = ring[1] / 0.06 * math.pi
                amp += (ring[2] / 0.012) * 0.55 * np.exp(-((theta - front) / 0.35) ** 2)
        amp += 0.12 * np.sin(np.arange(NS) * 1.7 + t * 2.3) ** 2 * 0.5  # never perfectly still
        amp += 0.75 * fr["crown"] * (0.6 + 0.4 * SITES[:, 2])  # the crown: it bristles all over, longest on top
        amp *= S_VAR
        for i, so in enumerate(SPH):
            if i >= len(bodies):
                so.scale = (0, 0, 0)
                continue
            cx, cy, R = bodies[i]
            dirs = SU @ rot.T  # the spikes roll with the ball
            rad = 1.0 + (amp[S_NEAR] * S_PROF) * 0.55
            # spike-arm: a long tentacle of fluid toward the bead it wants
            for a in arms:
                v = np.array([a[0] - cx, a[1] - cy, -0.08 * R])  # the arm reaches out, low over the lake
                L = np.linalg.norm(v)
                if L < 1e-6:
                    continue
                v /= L
                reach = a[2] / (0.55 * R)
                ang = np.arccos(np.clip(dirs @ v, -1, 1))
                rad = rad + 1.1 * reach * np.exp(-(ang / 0.32) ** 2)
            co = dirs * rad[:, None]
            so.data.vertices.foreach_set("co", co.astype(np.float32).ravel())
            so.data.update()
            so.location = (cx, cy, R * 1.02 + 0.002 + (fr.get("hop", 0.0) if i == 0 else 0.0))
            so.scale = (R, R, R)
            so.rotation_euler = (0, 0, 0)


def frame(f):
    fr = spec["frames"][f]
    t = f / spec["fps"]
    if SPHERE:
        sphere_frame(fr, f, t)
    else:
        frame_fluid(fr, f, t)
    frame_rest(fr, f, t)


def frame_fluid(fr, f, t):
    z, spike, amp, sx, sy, sr, shape, prof = heights(fr, t)
    # sway: compare with the heights a moment ago (deterministic: computed, not remembered)
    _, _, amp_prev, _, _, _, _, _ = heights(spec["frames"][max(0, f - 2)], (f - 2) / spec["fps"])
    sway = np.clip((amp - amp_prev) * 2.0, -0.004, 0.004)
    ux = np.where(sr > 1e-6, sx / np.maximum(sr, 1e-6), 0)
    uy = np.where(sr > 1e-6, sy / np.maximum(sr, 1e-6), 0)
    lean_r = 0.05 + 0.12 * np.clip(sr / 0.04, 0, 1) ** 2
    if os.environ.get("FERRO_DOME", "1") == "1":
        lean_r = lean_r + 0.75 * np.clip(sr / (0.95 * np.max(np.array(fr["blobs"])[:, 2])), 0, 1) ** 1.5  # spikes follow the curve of the dome
    lx, ly = fr["lean"]
    c = co0.copy()
    c[:, 0] = X + (lean_r * ux + lx) * spike + sway * shape * prof ** 2 * ux
    c[:, 1] = Y + (lean_r * uy + ly) * spike + sway * shape * prof ** 2 * uy
    c[:, 2] = z
    fluid.data.vertices.foreach_set("co", c.astype(np.float32).ravel())
    fluid.data.update()


def frame_rest(fr, f, t):
    place_drops(fr, t)
    place_jumpers(fr)
    place_beads(fr)
    for em_ in NEON_EM:  # the creature glows a little on every heartbeat
        em_.inputs["Strength"].default_value = 12.0 * fr.get("glow", 1.0)
    for name, (o, p0) in LIGHTS.items():
        a = 0.35 * math.sin(2 * math.pi * t / 14 + len(name)) + (0.25 * t / 30 if name == "Top" else 0)
        p = mathutils.Matrix.Rotation(a, 4, "Z") @ p0
        o.location = p
        o.rotation_euler = (mathutils.Vector((0, 0, 0.004)) - p).to_track_quat("-Z", "Y").to_euler()
    LIGHTS["Cyan"][0].data.color = fr["lightA"]
    LIGHTS["Magenta"][0].data.color = fr["lightB"]
    yaw, d, tilt = fr["yaw"], fr["dist"], fr["tilt"]
    if LOOK == "A":
        tilt, d = math.radians(12), d * 1.15  # nearly top-down over the lightbox
    elif LOOK == "C":
        tilt, d = math.radians(72), d * 0.85  # table-height macro
        cd.dof.aperture_fstop = 8.0
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
