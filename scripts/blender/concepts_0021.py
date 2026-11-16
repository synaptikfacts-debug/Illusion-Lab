# Concept stills for reel 0021 (owner, Nov 15 2026: "something like 0011 Singing Pins, but not identical - show me
# examples first"). Same FORMULA as 0011 - thousands of identical objects, each with its own rhythm, that freeze into a
# crisp pattern - but a different object, stage, camera and palette per concept. One still each, frozen on a spiral.
#   A  MIRROR DISCS: a vertical wall of 3000 polished discs on pivots, each tilted to its own angle; the pattern appears
#      in the REFLECTIONS (rose-gold / sunset-red light sweeping across the wall), seen head-on.
#   B  PEARL CLOUD: 4096 pearls floating in mid-air in a cube lattice that flows into a 3D double helix - a shape you
#      orbit in depth, not a floor. Pearl white + coral light.
#   C  GLASS CURTAIN: 64 hanging strands of clear glass beads; every strand swings forward/back on its own, so the
#      beads draw a spiral in depth; warm white-gold backlight through glass.
# Usage: blender -b --factory-startup -P scripts/blender/concepts_0021.py -- <out.png> <A|B|C> [samples] [WxH]
import math
import os
import sys

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
MODE = argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 32
W, H = (int(x) for x in (argv[3] if len(argv) > 3 else "540x960").split("x"))
TAU = 2 * math.pi
rng = np.random.default_rng(2121)

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
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 8
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = OUT


def world(top, bottom, strength=1.0):
    w = bpy.data.worlds.new("W")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs[0])


def mat(name, color, metal=0.0, rough=0.1, coat=0.0, trans=0.0, ior=1.5, sheen=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = es
    return m


def area(loc, size, power, color, target=(0, 0, 0), shape="DISK", sy=None):
    l = bpy.data.lights.new("L", "AREA")
    l.shape = shape
    l.size = size
    if sy:
        l.size_y = sy
    l.energy = power
    l.color = color
    o = bpy.data.objects.new("L", l)
    o.location = loc
    o.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return o


def camera(loc, target, lens=50, fstop=None, focus=None):
    cd = bpy.data.cameras.new("C")
    cd.lens = lens
    cam = bpy.data.objects.new("C", cd)
    cam.location = loc
    cam.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = focus or (mathutils.Vector(target) - mathutils.Vector(loc)).length
    return cam


def instances(name, proto_v, proto_f, centers, rots, scales, material, smooth=True):
    """one mesh holding many copies of a small prototype (rot: per-instance 3x3, scale: per-instance)"""
    pv = np.asarray(proto_v, dtype=np.float64)
    n = len(centers)
    v = np.einsum("nij,kj->nki", rots, pv) * scales[:, None, None] + centers[:, None, :]
    m = len(pv)
    f = [tuple(i * m + k for k in face) for i in range(n) for face in proto_f]  # faces may differ in vertex count
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.reshape(-1, 3).tolist(), [], f)
    me.update()
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(material)
    return o


def uv_sphere(seg=16, ring=10):
    v, f = [], []
    for i in range(ring + 1):
        th = math.pi * i / ring
        for j in range(seg):
            ph = TAU * j / seg
            v.append((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
    for i in range(ring):
        for j in range(seg):
            a, b = i * seg + j, i * seg + (j + 1) % seg
            f.append((a, b, b + seg, a + seg))
    return v, f


def disc(seg=24, thick=0.08):
    v = [(math.cos(TAU * s / seg), math.sin(TAU * s / seg), z) for z in (thick / 2, -thick / 2) for s in range(seg)]
    f = [tuple(range(seg)), tuple(range(2 * seg - 1, seg - 1, -1))]
    f += [(s, (s + 1) % seg, seg + (s + 1) % seg, seg + s) for s in range(seg)]
    return v, f


def rot_axis(axis, ang):
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / np.linalg.norm(axis, axis=-1, keepdims=True)
    c, s = np.cos(ang)[:, None, None], np.sin(ang)[:, None, None]
    k = axis
    K = np.zeros((len(ang), 3, 3))
    K[:, 0, 1], K[:, 0, 2], K[:, 1, 0] = -k[:, 2], k[:, 1], k[:, 2]
    K[:, 1, 2], K[:, 2, 0], K[:, 2, 1] = -k[:, 0], -k[:, 1], k[:, 0]
    return np.eye(3)[None] + s * K + (1 - c) * (K @ K)


def bokeh(n, color, z0, z1, x=6.0, y=(4.0, 9.0), r=(0.05, 0.16), strength=6.0):
    """soft glowing spheres far behind the subject - real depth instead of a flat background band"""
    m = mat("Bokeh", (0, 0, 0), emit=color, es=strength)
    c = np.stack([rng.uniform(-x, x, n), rng.uniform(*y, n), rng.uniform(z0, z1, n)], 1)
    v, f = uv_sphere(10, 6)
    instances("Bokeh", v, f, c, np.repeat(np.eye(3)[None], n, 0), rng.uniform(*r, n), m)


def spiral_field(x, y, arms=3, k=1.6):
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    return np.sin(arms * th - k * TAU * r) * np.exp(-0.15 * r * r)


if MODE == "A":
    # MIRROR DISCS: a wall of polished discs, each tilted by a spiral field; the reflection of a warm sunset sky draws it
    world((1.0, 0.06, 0.16), (0.02, 0.0, 0.01), 1.4)
    nx, ny = 26, 46
    gx, gz = np.meshgrid(np.linspace(-1, 1, nx) * 2.3, np.linspace(-1, 1, ny) * 4.1)
    gx[1::2] += 2.3 / (nx - 1)  # hex offset rows
    gx, gz = gx.ravel(), gz.ravel()
    s = spiral_field(gx / 1.2, gz / 1.2, 3, 1.1)
    tilt = 0.85 * s
    axis = np.stack([np.cos(np.arctan2(gz, gx) + 1.2), np.zeros_like(gx), np.sin(np.arctan2(gz, gx) + 1.2)], 1)
    face_cam = np.repeat(np.array([[[1, 0, 0], [0, 0, -1], [0, 1, 0]]], dtype=float), len(gx), 0)  # disc normal -> -Y
    rots = rot_axis(axis, tilt) @ face_cam
    v, f = disc(28, 0.06)
    instances("Discs", v, f, np.stack([gx, np.zeros_like(gx), gz], 1), rots, np.full(len(gx), 0.082),
              mat("Mirror", (0.97, 0.97, 0.98), metal=1.0, rough=0.04))
    plate = bpy.data.meshes.new("Back")
    plate.from_pydata([(-3, 0.12, -5), (3, 0.12, -5), (3, 0.12, 5), (-3, 0.12, 5)], [], [(0, 1, 2, 3)])
    bo = bpy.data.objects.new("Back", plate)
    scene.collection.objects.link(bo)
    bo.data.materials.append(mat("BackPlate", (0.02, 0.012, 0.015), metal=0.6, rough=0.35))
    area((-3.5, -4.5, 3.5), 3.0, 1400, (1.0, 0.96, 0.95))
    area((3.8, -3.5, -2.0), 2.5, 900, (1.0, 0.08, 0.2))
    area((0, -6, 2.5), 9, 600, (1.0, 1.0, 1.0), shape="RECTANGLE", sy=0.5)
    bokeh(70, (1.0, 0.12, 0.25), -6, 6, x=7, y=(3, 7))
    camera((1.3, -7.6, 0.6), (0, 0, 0), lens=46, fstop=4.0)

elif MODE == "B":
    # PEARL CLOUD: a cube lattice of pearls flowing into a double helix, floating in a coral-lit space
    world((0.06, 0.004, 0.02), (0.06, 0.004, 0.02), 1.0)
    n = 16
    lat = np.stack(np.meshgrid(*(np.linspace(-1, 1, n),) * 3, indexing="ij"), -1).reshape(-1, 3) * 1.6
    i = np.arange(len(lat))
    t = (i % 2048) / 2048
    strand = (i // 2048).astype(float)
    ang = t * TAU * 3.2 + strand * math.pi
    rad = 1.05 + 0.35 * rng.standard_normal(len(i)) * 0.25
    helix = np.stack([np.cos(ang) * rad, np.sin(ang) * rad, (t - 0.5) * 6.4], 1)
    helix += rng.normal(0, 0.035, helix.shape)
    k = 0.82 + 0.18 * np.clip((helix[:, 2] + 3.2) / 6.4, 0, 1)  # lower part fully formed, top still flowing in
    c = lat * (1 - k)[:, None] + helix * k[:, None]
    v, f = uv_sphere(18, 12)
    instances("Pearls", v, f, c, np.repeat(np.eye(3)[None], len(c), 0), np.full(len(c), 0.066),
              mat("Pearl", (0.96, 0.93, 0.9), rough=0.22, coat=1.0, sheen=0.6))
    area((-3, -4, 4), 3.5, 1100, (1.0, 0.92, 0.86))
    area((4, -2, -1), 3.0, 1000, (1.0, 0.35, 0.45))
    area((0, 5, 2), 4.0, 900, (1.0, 0.45, 0.55))
    bokeh(140, (1.0, 0.3, 0.42), -7, 7, x=8, y=(4, 10), strength=9)
    camera((0, -9.5, 0.8), (0, 0, 0.1), lens=50, fstop=5.6)

elif MODE == "C":
    # GLASS CURTAIN: hanging strands of glass beads, each strand swung forward/back so the beads draw a spiral in depth
    world((0.02, 0.02, 0.025), (0.02, 0.02, 0.025), 1.0)
    ns, nb = 64, 96
    sx = np.linspace(-2.4, 2.4, ns)
    sz = np.linspace(4.3, -4.3, nb)
    X, Z = np.meshgrid(sx, sz, indexing="ij")
    d = spiral_field(X / 1.3, Z / 1.3, 2, 0.9)
    Y = -0.9 * d * np.clip((4.3 - Z) / 1.2, 0, 1)  # strands hang from the top bar, swing more lower down
    c = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    v, f = uv_sphere(14, 10)
    instances("Beads", v, f, c, np.repeat(np.eye(3)[None], len(c), 0), np.full(len(c), 0.04),
              mat("Glass", (1.0, 1.0, 1.0), rough=0.0, trans=1.0, ior=1.52))
    thread = mat("Thread", (0.9, 0.85, 0.7), metal=1.0, rough=0.2)
    bar = bpy.data.meshes.new("Bar")
    bar.from_pydata([(-2.7, -0.03, 4.45), (2.7, -0.03, 4.45), (2.7, 0.03, 4.45), (-2.7, 0.03, 4.45)], [], [(0, 1, 2, 3)])
    bo = bpy.data.objects.new("Bar", bar)
    scene.collection.objects.link(bo)
    bo.data.materials.append(thread)
    area((0, 4, 0), 7, 5000, (1.0, 0.9, 0.35), shape="RECTANGLE", sy=10)  # lemon-gold backlight through the glass
    area((-4, -5, 3), 2.5, 500, (1.0, 0.97, 0.92))
    area((4, -4, -2), 2.5, 300, (1.0, 0.75, 0.55))
    bokeh(150, (1.0, 0.88, 0.3), -6, 6, x=7, y=(5, 9), strength=10)
    camera((2.6, -8.2, -0.4), (0, 0, 0), lens=48, fstop=4.0)

bpy.ops.render.render(write_still=True)
print("saved", OUT)
