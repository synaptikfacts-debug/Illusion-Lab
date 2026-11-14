# 0016 "Urchin Heart" (Blender Cycles, OptiX): a clear purple jelly sphere on black glass with a black ferrofluid heart
# inside. The heart twitches, beats, crawls, turns into an urchin that pushes the jelly skin out, splits in two with the
# jelly, merges back, then its spikes BREACH the skin (the gel heals around them) and pull back; the sphere settles into
# the same wobble as frame 0 (seamless loop). Timeline: src/scenes/urchin/timeline.json.
#  - jelly: a metaball (smooth split/merge, soft bumps where spikes press the skin), refractive gel + purple absorption
#  - heart: two displaced icospheres (one shows when it splits), Rosensweig-like cone spikes along fixed directions
# Usage: blender -b --factory-startup -P scripts/blender/urchin.py -- <outDir> [samples] [fps] [k] [n] [only]
import json
import math
import os
import sys
import time

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
FPS = int(argv[2]) if len(argv) > 2 else 60
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(here, "..", "..", "src", "scenes", "urchin", "timeline.json")))
R = TL["R"]
DUR = TL["duration"]

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.015
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 16
scene.cycles.transmission_bounces = 14
scene.cycles.glossy_bounces = 8
scene.cycles.volume_bounces = 1
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.use_persistent_data = True
res = os.environ.get("URCHIN_RES", "1080x1920").split("x")
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)


def principled(name, color, metal=0.0, rough=0.1, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.02
    return m


# --- materials ---
jelly = bpy.data.materials.new("PurpleJelly")
jelly.use_nodes = True
jn = jelly.node_tree.nodes
jb = jn["Principled BSDF"]
jb.inputs["Base Color"].default_value = (0.78, 0.6, 1.0, 1)
jb.inputs["Transmission Weight"].default_value = 1.0
jb.inputs["IOR"].default_value = 1.36
jb.inputs["Roughness"].default_value = 0.025
jb.inputs["Coat Weight"].default_value = 0.4
jb.inputs["Coat Roughness"].default_value = 0.01
absorb = jn.new("ShaderNodeVolumeAbsorption")
absorb.inputs["Color"].default_value = (0.7, 0.35, 1.0, 1)
absorb.inputs["Density"].default_value = 16.0
scat = jn.new("ShaderNodeVolumeScatter")
scat.inputs["Color"].default_value = (0.75, 0.55, 1.0, 1)
scat.inputs["Density"].default_value = 2.2
scat.inputs["Anisotropy"].default_value = 0.4
vadd = jn.new("ShaderNodeAddShader")
jelly.node_tree.links.new(absorb.outputs[0], vadd.inputs[0])
jelly.node_tree.links.new(scat.outputs[0], vadd.inputs[1])
jelly.node_tree.links.new(vadd.outputs[0], jn["Material Output"].inputs["Volume"])

ferro = principled("Ferrofluid", (0.006, 0.006, 0.008), metal=0.25, rough=0.05, coat=1.0)
glass = principled("BlackGlass", (0.004, 0.004, 0.006), rough=0.06, coat=0.6)

# --- black glass floor ---
bpy.ops.mesh.primitive_plane_add(size=3.0)
floor = bpy.context.active_object
floor.data.materials.append(glass)

# --- jelly: a metaball ---
mb = bpy.data.metaballs.new("Jelly")
mb.resolution = 0.004
mb.render_resolution = 0.0011
mb.threshold = 0.6
jobj = bpy.data.objects.new("Jelly", mb)
scene.collection.objects.link(jobj)
jobj.data.materials.append(jelly)
MAIN = [mb.elements.new(type="ELLIPSOID") for _ in range(2)]
NSP = TL["spikes"]
BUMPS = [mb.elements.new(type="BALL") for _ in range(NSP)]
COLLARS = [mb.elements.new(type="BALL") for _ in range(NSP)]

# spike directions: fibonacci sphere, keep the ones that are not pointing into the floor
dirs = []
i = 0
while len(dirs) < NSP:
    y = 1 - (i + 0.5) / (NSP * 1.6) * 2
    rr = math.sqrt(max(0.0, 1 - y * y))
    th = math.pi * (3 - math.sqrt(5)) * i
    v = np.array([math.cos(th) * rr, math.sin(th) * rr, y])
    if v[2] > -0.35:
        dirs.append(v / np.linalg.norm(v))
    i += 1
DIRS = np.array(dirs)
rng = np.random.default_rng(1616)
SPK_GAIN = rng.uniform(0.75, 1.15, NSP)
SPK_PHASE = rng.uniform(0, 0.6, NSP)
TWITCH_K = int(np.argmax(DIRS @ np.array([-0.92, -0.1, 0.38])))  # the first spike pokes out on the left side (reads in silhouette)

# --- heart: two displaced icospheres ---
RH = 0.017
MBK = 1 / 0.5707  # a metaball BALL with stiffness 2 has its surface at 0.5707 x its radius (measured)
HEARTS = []
for _ in range(2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
    h = bpy.context.active_object
    h.data.materials.append(ferro)
    bpy.ops.object.shade_smooth()
    HEARTS.append(h)
nv = len(HEARTS[0].data.vertices)
U = np.empty(nv * 3, dtype=np.float32)
HEARTS[0].data.vertices.foreach_get("co", U)
U = U.reshape(-1, 3).astype(np.float64)
U /= np.linalg.norm(U, axis=1, keepdims=True)
COS = U @ DIRS.T  # (nv, NSP) angle cosines to every spike direction
ANG = np.arccos(np.clip(COS, -1, 1))

# --- light: one clear key, a small cyan rim, a soft purple glow far behind ---
def area(name, loc, size, power, color, target=(0, 0, 0.045), shape="RECTANGLE"):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size, ld.size_y = size
    ld.energy = power
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    lo.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    lo.visible_camera = False
    return lo


area("Key", (-0.3, -0.2, 0.42), (0.22, 0.22), 34, (1.0, 0.97, 0.95), shape="DISK")
area("RimCyan", (0.2, 0.22, 0.09), (0.02, 0.2), 7, (0.15, 0.85, 1.0))
area("FillPurple", (0.3, -0.05, 0.12), (0.2, 0.2), 6, (0.6, 0.25, 1.0))
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0.75, 0.12), rotation=(math.radians(90), 0, 0))
bk = bpy.context.active_object
bk.scale = (0.7, 0.4, 1)
bm = bpy.data.materials.new("Glow")
bm.use_nodes = True
bnn = bm.node_tree.nodes
bnn.clear()
bo = bnn.new("ShaderNodeOutputMaterial")
be = bnn.new("ShaderNodeEmission")
bg = bnn.new("ShaderNodeTexGradient")
bg.gradient_type = "SPHERICAL"
bmap = bnn.new("ShaderNodeMapping")
bmap.inputs["Scale"].default_value = (1.4, 2.4, 1.4)
btc = bnn.new("ShaderNodeTexCoord")
bcr = bnn.new("ShaderNodeValToRGB")
bcr.color_ramp.elements[0].color = (0, 0, 0, 1)
bcr.color_ramp.elements[1].color = (0.35, 0.08, 0.75, 1)
bl_ = bm.node_tree.links
bl_.new(btc.outputs["Object"], bmap.inputs["Vector"])
bl_.new(bmap.outputs["Vector"], bg.inputs["Vector"])
bl_.new(bg.outputs["Fac"], bcr.inputs["Fac"])
bl_.new(bcr.outputs["Color"], be.inputs["Color"])
be.inputs["Strength"].default_value = 0.35
bl_.new(be.outputs["Emission"], bo.inputs["Surface"])
bk.data.materials.append(bm)

cd = bpy.data.cameras.new("Cam")
cd.lens = 85
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 5.0
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


# ---------------- the story ----------------
def sm(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def ring(t, t0, amp, freq=3.2, decay=3.0):
    """a damped wobble that starts at t0"""
    a = t - t0
    if a < 0:
        return 0.0
    return amp * math.exp(-a * decay) * math.sin(2 * math.pi * freq * a) * min(1.0, a / 0.03)


def pulse(t, t0, w=0.09, decay=5.0):
    a = t - t0
    if a < 0:
        return 0.0
    return (1 - math.exp(-a / w)) * math.exp(-a * decay)


def state(t):
    tw = TL["twitch"]
    # wobble (squash) of the jelly: a living idle, plus a ring on every event
    sq = 0.012 * math.sin(2 * math.pi * 1.1 * t) * (1 - sm(TL["settle"][0], TL["settle"][1], t)) + 0.012 * math.sin(2 * math.pi * 1.1 * (t - DUR)) * sm(TL["settle"][0], TL["settle"][1], t)
    sq += ring(t, tw, 0.05)
    for b in TL["beats"]:
        sq += ring(t, b, 0.035)
    sq += ring(t, TL["split"][0] + 1.2, 0.07) + ring(t, TL["merge"], 0.11, 2.6, 2.2)
    sq += ring(t, TL["breach"][1] - 0.6, 0.06) + ring(t, TL["urchin"][0] + 0.6, 0.04)
    # crawl: out and back (the heart leads, the jelly follows)
    cu = sm(TL["crawl"][0], TL["crawl"][1], t)
    cx = 0.022 * math.sin(math.pi * cu)
    lead = 0.01 * math.cos(math.pi * cu) * math.sin(math.pi * cu) * 2
    # split / merge
    s0, s1 = TL["split"]
    sep = sm(s0 + 0.4, s0 + 2.0, t) * (1 - sm(TL["merge"] - 0.8, TL["merge"], t))
    pres = sm(s0, s0 + 0.5, t) * (1 - sm(TL["merge"] - 0.3, TL["merge"] + 0.2, t))
    ang = 0.55 * max(0.0, t - (s0 + 2.0)) + 0.2
    d = 0.037 * sep
    cA = np.array([cx + d * math.cos(ang), d * math.sin(ang)])
    cB = np.array([cx - d * math.cos(ang), -d * math.sin(ang)])
    rA = R * (1 - 0.21 * sep)
    rB = R * 0.79 * pres
    # spike heights of the heart (m, beyond the heart radius)
    amp = np.zeros(NSP)
    amp[TWITCH_K] += 0.04 * pulse(t, tw, 0.08, 2.4)
    for b in TL["beats"]:
        amp += 0.006 * pulse(t, b, 0.05, 6.0)
    u0, u1 = TL["urchin"]
    for k in range(NSP):
        uk = sm(u0 + SPK_PHASE[k], u0 + 1.4 + SPK_PHASE[k], t) * (1 - sm(u1 - 0.8, u1, t))
        amp[k] += 0.022 * SPK_GAIN[k] * uk * (1 + 0.12 * math.sin(2 * math.pi * 1.6 * t + k))
        b0, b1 = TL["breach"]
        bk_ = sm(b0 + 0.5 * SPK_PHASE[k], b0 + 0.6 + 0.5 * SPK_PHASE[k], t) * (1 - sm(b1 - 1.0 + 0.3 * SPK_PHASE[k], b1 - 0.1 + 0.3 * SPK_PHASE[k], t))
        amp[k] += 0.046 * SPK_GAIN[k] * bk_
    hs = 1 - 0.21 * sep  # heart shrinks when it splits (two smaller hearts)
    return dict(sq=sq, cA=cA, cB=cB, rA=rA, rB=rB, lead=lead, amp=amp, hs=hs, pres=pres)


def heart_mesh(h, center, scale, amp, show):
    if not show:
        h.scale = (0, 0, 0)
        return
    w = 0.2
    c = np.clip(1 - ANG / w, 0, 1)
    prof = c ** 2.4 * (3 - 2 * c) * 0.6 + c ** 7 * 0.4
    rad = RH * (1 + 0.04 * np.sin(U[:, 0] * 9 + U[:, 2] * 7)) + prof @ amp
    co = (U * rad[:, None]).astype(np.float32)
    h.data.vertices.foreach_set("co", co.ravel())
    h.data.update()
    h.location = (center[0], center[1], center[2])
    h.scale = (scale, scale, scale)


def frame(f):
    t = f / FPS
    st = state(t)
    zc = R * 0.93
    sq = st["sq"]
    for el, c, r in ((MAIN[0], st["cA"], st["rA"]), (MAIN[1], st["cB"], st["rB"])):
        el.co = (c[0], c[1], zc * (r / R) * (1 - sq * 0.6))
        el.radius = max(r * MBK, 1e-5)
        el.size_x = el.size_y = 1 + sq * 0.5
        el.size_z = 1 - sq
        el.stiffness = 2.0
    hc = np.array([st["cA"][0] + st["lead"], st["cA"][1], zc * (st["rA"] / R) * (1 - sq * 0.6)])
    amp = st["amp"]
    # skin bumps where a spike presses the jelly, collars where a spike breaks through
    reach = RH + amp
    for k in range(NSP):
        dk = DIRS[k]
        press = np.clip((reach[k] - (R * 0.62)) / 0.02, 0, 1) if st["pres"] < 0.5 else 0.0
        through = np.clip((reach[k] - R * 0.98) / 0.012, 0, 1)
        p = hc + dk * min(reach[k], R * 0.9) * 0.92
        BUMPS[k].co = tuple(p)
        BUMPS[k].radius = 0.0135 * MBK * press * (1 - through) + 1e-5
        BUMPS[k].stiffness = 2.0
        q = hc + dk * R * 0.97
        COLLARS[k].co = tuple(q)
        COLLARS[k].radius = 0.0045 * MBK * through + 1e-5
        COLLARS[k].stiffness = 2.0
    heart_mesh(HEARTS[0], hc, st["hs"], amp, True)
    hb = np.array([st["cB"][0], st["cB"][1], zc * (max(st["rB"], 1e-4) / R) * (1 - sq * 0.6)])
    heart_mesh(HEARTS[1], hb, st["hs"], amp * 0.85, st["pres"] > 0.02)
    # camera: low 3/4 macro view, a slow drift that returns to its start (loop)
    yaw = math.radians(8 * math.sin(2 * math.pi * t / DUR))
    el_ = math.radians(15 + 3 * math.sin(2 * math.pi * t / DUR + 1.0))
    dist = 0.74 + 0.16 * sm(TL["split"][0], TL["split"][0] + 2, t) * (1 - sm(TL["merge"] - 1, TL["merge"], t))
    look = mathutils.Vector((0.012 * math.sin(math.pi * sm(TL["crawl"][0], TL["crawl"][1], t)), 0, 0.042))
    pos = look + mathutils.Vector((math.sin(yaw) * math.cos(el_), -math.cos(yaw) * math.cos(el_), math.sin(el_))) * dist
    cam.location = pos
    cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = (look - pos).length
    scene.render.filepath = os.path.join(OUT, f"f_{f:04d}.png")
    bpy.ops.render.render(write_still=True)


N = int(round(DUR * FPS))
todo = ONLY if ONLY is not None else list(range(K, N, NN))
t0 = time.time()
for i, f in enumerate(todo):
    if ONLY is None and os.path.exists(os.path.join(OUT, f"f_{f:04d}.png")):
        continue
    frame(f)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t0) / (i + 1):.2f} s/frame", flush=True)
print(f"done {len(todo)} frames in {time.time() - t0:.0f} s", flush=True)
