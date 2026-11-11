# Singing Pins: The Show - ray-traced (Cycles) render of the pin wall, frame by frame, from the data written by
# scripts/gen-pinshow-frames.ts. Brushed-steel shafts, glossy coated tips coloured by height (with a soft inner glow),
# a black glass floor, soft studio area lights + two coloured rim lights that follow the palette, real depth of field.
# Usage: blender -b --factory-startup -P scripts/blender/pinshow.py -- <dataDir> <outDir> [samples] [k] [n] [only]
#   k/n: render every n-th frame starting at k (parallel instances); only: comma list of frames (test stills)
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
DATA, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
SAMPLES = int(argv[2]) if len(argv) > 2 else 48
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)

spec = json.load(open(os.path.join(DATA, "frames.json")))
P = np.array(spec["pins"], dtype=np.float32)  # three.js x, z
NP = len(P)
H = np.memmap(os.path.join(DATA, "heights.bin"), dtype=np.uint16, mode="r").reshape(spec["n"], NP)
MAXH, SP = spec["maxHeight"], spec["spacing"]
# three.js (x, y, z) -> Blender (x, -z, y)
BX, BY = P[:, 0], -P[:, 1]

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
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = int(os.environ.get("PINSHOW_BOUNCES", "8"))
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.use_persistent_data = True
RES = [int(v) for v in os.environ.get("PINSHOW_RES", "1440x2560").split("x")]  # 1440x2560 supersampled (slow), 1080x1920 native (fast)
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "8"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass

# --- world: very dark violet studio ---
scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
wn = scene.world.node_tree.nodes
wn["Background"].inputs["Color"].default_value = (0.006, 0.004, 0.016, 1)
wn["Background"].inputs["Strength"].default_value = 1.0


def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes["Principled BSDF"]


def setp(b, key, v):
    if key in b.inputs:
        b.inputs[key].default_value = v


# shafts: brushed steel
m_shaft, b = mat("Steel")
setp(b, "Base Color", (0.56, 0.58, 0.64, 1))
setp(b, "Metallic", 1.0)
setp(b, "Roughness", 0.3)
setp(b, "Anisotropic", 0.6)
# tips: glossy coated beads, coloured by height, soft inner glow
m_tip, b = mat("Tip")
attr = m_tip.node_tree.nodes.new("ShaderNodeAttribute")
attr.attribute_name = "col"
m_tip.node_tree.links.new(attr.outputs["Color"], b.inputs["Base Color"])
setp(b, "Metallic", 0.35)
setp(b, "Roughness", 0.16)
setp(b, "Coat Weight", 1.0)
setp(b, "Coat Roughness", 0.04)
m_tip.node_tree.links.new(attr.outputs["Color"], b.inputs["Emission Color"])
setp(b, "Emission Strength", 0.9)
# floor: matte black (any gloss mirrored the softboxes or turned grey at grazing angles)
m_floor = bpy.data.materials.new("MatteBlack")
m_floor.use_nodes = True
fn = m_floor.node_tree.nodes
fn.remove(fn["Principled BSDF"])
dif = fn.new("ShaderNodeBsdfDiffuse")
dif.inputs["Color"].default_value = (0.004, 0.004, 0.007, 1)
# a soft violet pool of light on the floor around the wall (studio glow, no dead black)
tc = fn.new("ShaderNodeTexCoord")
mp = fn.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (0.11, 0.11, 0.11)
gr = fn.new("ShaderNodeTexGradient")
gr.gradient_type = "SPHERICAL"
em = fn.new("ShaderNodeEmission")
em.inputs["Color"].default_value = (0.22, 0.1, 0.55, 1)
mul = fn.new("ShaderNodeMath")
mul.operation = "POWER"
mul.inputs[1].default_value = 2.2
ad = fn.new("ShaderNodeAddShader")
L = m_floor.node_tree.links
L.new(tc.outputs["Object"], mp.inputs["Vector"])
L.new(mp.outputs["Vector"], gr.inputs["Vector"])
L.new(gr.outputs["Fac"], mul.inputs[0])
L.new(mul.outputs[0], em.inputs["Strength"])
L.new(dif.outputs[0], ad.inputs[0])
L.new(em.outputs[0], ad.inputs[1])
L.new(ad.outputs[0], fn["Material Output"].inputs["Surface"])
# base plate under the pins: dark anodised metal
m_plate, b = mat("Plate")
setp(b, "Base Color", (0.05, 0.05, 0.07, 1))
setp(b, "Metallic", 1.0)
setp(b, "Roughness", 0.18)


def obj_from(name, verts, faces, material, smooth):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    if smooth:
        me.shade_smooth()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob, me


# --- shafts: 4096 cylinders in one mesh (12 sides); top ring z follows the pin height ---
R = SP * 0.33
SEG = 12
ang = np.linspace(0, 2 * np.pi, SEG, endpoint=False)
ring = np.stack([np.cos(ang) * R * 0.7, np.sin(ang) * R * 0.7], 1)
sv = np.zeros((NP, 2 * SEG, 3), np.float32)
sv[:, :SEG, 0] = BX[:, None] + ring[:, 0]
sv[:, :SEG, 1] = BY[:, None] + ring[:, 1]
sv[:, SEG:, 0] = sv[:, :SEG, 0]
sv[:, SEG:, 1] = sv[:, :SEG, 1]
sf = []
for i in range(NP):
    o = i * 2 * SEG
    for s in range(SEG):
        a, b2 = s, (s + 1) % SEG
        sf.append([o + a, o + b2, o + SEG + b2, o + SEG + a])
shafts, shaft_me = obj_from("Shafts", sv.reshape(-1, 3), np.array(sf), m_shaft, True)

# --- tips: 4096 UV spheres in one mesh, with a per-point colour attribute ---
UL, VL = 18, 10
tv, tfs = [], []
for vi in range(VL + 1):
    th = math.pi * vi / VL
    for ui in range(UL):
        ph = 2 * math.pi * ui / UL
        tv.append([R * math.sin(th) * math.cos(ph), R * math.sin(th) * math.sin(ph), R * math.cos(th)])
tv = np.array(tv, np.float32)
for vi in range(VL):
    for ui in range(UL):
        a = vi * UL + ui
        b2 = vi * UL + (ui + 1) % UL
        tfs.append([a, b2, b2 + UL, a + UL])
tfs = np.array(tfs)
nv = len(tv)
tip_v = np.zeros((NP, nv, 3), np.float32)
tip_v[:, :, 0] = BX[:, None] + tv[None, :, 0]
tip_v[:, :, 1] = BY[:, None] + tv[None, :, 1]
tip_f = (tfs[None, :, :] + (np.arange(NP) * nv)[:, None, None]).reshape(-1, 4)
tips, tip_me = obj_from("Tips", tip_v.reshape(-1, 3), tip_f, m_tip, True)
col_attr = tip_me.color_attributes.new("col", "FLOAT_COLOR", "POINT")

# --- floor + plate ---
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -0.002))
bpy.context.object.data.materials.append(m_floor)
half = (64 * SP) / 2 + 0.25
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.03))
plate = bpy.context.object
plate.scale = (half * 2, half * 2, 0.06)
plate.data.materials.append(m_plate)


# --- lights ---
def area(name, loc, size, power, color):
    d = bpy.data.lights.new(name, "AREA")
    d.size = size
    d.energy = power
    d.color = color
    ob = bpy.data.objects.new(name, d)
    ob.location = loc
    scene.collection.objects.link(ob)
    ob.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    ob.visible_camera = False  # softboxes light the pins but never show in the shot
    return d


area("Key", (-5, 5, 15), 8, 4200, (1.0, 0.96, 0.92))
area("Fill", (8, 8, 7), 9, 700, (0.75, 0.8, 1.0))
rimA = area("RimA", (6.5, -6.5, 2.6), 4, 1400, (0.4, 0.6, 1.0))
rimB = area("RimB", (-7, 2.0, 2.2), 4, 1100, (0.7, 0.3, 1.0))

# --- camera ---
cd = bpy.data.cameras.new("Cam")
cd.sensor_fit = "VERTICAL"
cd.angle_y = math.radians(30)
cd.clip_start, cd.clip_end = 0.5, 200
cd.dof.use_dof = True
cd.dof.aperture_fstop = 1.6
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam

STOPS = None


def grad(stops, x):
    f = np.clip(x, 0, 0.9999) * (len(stops) - 1)
    i = np.floor(f).astype(int)
    w = (f - i)[:, None]
    s = np.array(stops, np.float32)
    return s[i] * (1 - w) + s[i + 1] * w


def srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def frame(f):
    fr = spec["frames"][f]
    h = H[f].astype(np.float32) / 65535.0 * MAXH
    hh = 0.03 + h
    v = sv.copy()
    v[:, SEG:, 2] = hh[:, None]
    shaft_me.vertices.foreach_set("co", v.reshape(-1))
    shaft_me.update()
    t = tip_v.copy()
    t[:, :, 2] = hh[:, None] + tv[None, :, 2]
    tip_me.vertices.foreach_set("co", t.reshape(-1))
    x = h / MAXH
    c = srgb_to_lin(grad(fr["stops"], x)) * (0.5 + 0.45 * x)[:, None]
    rgba = np.concatenate([c, np.ones((NP, 1), np.float32)], 1)
    rgba = np.repeat(rgba[:, None, :], nv, 1).reshape(-1)
    col_attr.data.foreach_set("color", rgba)
    tip_me.update()
    s = fr["stops"]
    rimA.color = tuple(srgb_to_lin(np.array(s[2], np.float32)).tolist())
    rimB.color = tuple(srgb_to_lin(np.array(s[1], np.float32)).tolist())
    px, py, pz = fr["cam"]
    lx, ly, lz = fr["look"]
    pos, look = Vector((px, -pz, py)), Vector((lx, -lz, ly))
    cam.location = pos
    cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = (look - pos).length
    scene.render.filepath = os.path.join(OUT, f"f_{f:04d}.png")
    bpy.ops.render.render(write_still=True)


todo = ONLY if ONLY is not None else list(range(K, spec["n"], NN))
t0 = time.time()
for i, f in enumerate(todo):
    if ONLY is None and os.path.exists(os.path.join(OUT, f"f_{f:04d}.png")):
        continue
    frame(f)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t0) / (i + 1):.2f} s/frame", flush=True)
print(f"done {len(todo)} frames in {time.time() - t0:.0f} s", flush=True)
