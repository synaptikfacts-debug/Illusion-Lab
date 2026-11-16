# 0023 concept stills - "Mercury learned to dance" (pitched Nov 16 2026). Liquid-chrome drops on a black glass drum,
# magenta + lime light. Three looks: A the cold open (drops thrown into the air), B a spiral pattern of drops of
# growing size, C the payoff (one big mirror sphere). Quick look only, not the animation.
# Usage: blender -b --factory-startup -P scripts/blender/concepts_0023.py -- <outdir> <samples> [A,B,C]
import math
import os
import sys

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 48
WHICH = (argv[2] if len(argv) > 2 else "A,B,C").split(",")
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi
rng = np.random.default_rng(2323)

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
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.glossy_bounces = 8
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.resolution_percentage = int(os.environ.get("C23_PCT", "50"))
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.4

w = bpy.data.worlds.new("W")
scene.world = w
w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
wn.clear()
wo = wn.new("ShaderNodeOutputWorld")
wb = wn.new("ShaderNodeBackground")
tc = wn.new("ShaderNodeTexCoord")
nz = wn.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 2.2
nz.inputs["Detail"].default_value = 5.0
cr = wn.new("ShaderNodeValToRGB")
cr.color_ramp.elements[0].position = 0.4
cr.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
cr.color_ramp.elements.new(0.62).color = (0.012, 0.0, 0.008, 1)   # faint magenta haze (black stage)
cr.color_ramp.elements[-1].position = 0.85
cr.color_ramp.elements[-1].color = (0.004, 0.012, 0.0, 1)         # faint lime haze
wl.new(tc.outputs["Generated"], nz.inputs["Vector"])
wl.new(nz.outputs["Fac"], cr.inputs["Fac"])
wl.new(cr.outputs["Color"], wb.inputs["Color"])
wl.new(wb.outputs[0], wo.inputs[0])


def principled(name, color, metal=0.0, rough=0.1, coat=0.0, film=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if film:
        b.inputs["Thin Film Thickness"].default_value = film
    return m


def ico_sphere(sub):
    t = (1 + math.sqrt(5)) / 2
    vs = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
          (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    fs = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
          (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
          (8, 6, 7), (9, 8, 1)]
    vs = [np.array(v) / np.linalg.norm(v) for v in vs]
    for _ in range(sub):
        cache, nf = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m_ = vs[a] + vs[b]
                vs.append(m_ / np.linalg.norm(m_))
                cache[key] = len(vs) - 1
            return cache[key]
        for a, b, c in fs:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        fs = nf
    return np.array(vs), np.array(fs)


SV, SF = ico_sphere(5)
mercury = principled("Mercury", (0.92, 0.92, 0.95), metal=1.0, rough=0.025, film=120.0)
glass = principled("BlackGlass", (0.003, 0.003, 0.004), rough=0.03, coat=1.0)


def drop(name, p, r, squash=1.0):
    """a drop of liquid metal: flattened when resting (a sessile drop), round in the air"""
    v = SV.copy()
    v[:, 2] *= squash
    v[:, 2] = np.where(v[:, 2] < -0.82 * squash, -0.82 * squash + (v[:, 2] + 0.82 * squash) * 0.2, v[:, 2])
    me = bpy.data.meshes.new(name)
    me.from_pydata((v * r + np.array(p)).tolist(), [], SF.tolist())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(mercury)
    return o


fv = [(0, 0, 0)] + [(30 * math.cos(a), 30 * math.sin(a), 0) for a in np.linspace(0, TAU, 128, endpoint=False)]
fme = bpy.data.meshes.new("Floor")
fme.from_pydata(fv, [], [(0, i + 1, (i + 1) % 128 + 1) for i in range(128)])
floor = bpy.data.objects.new("Floor", fme)
scene.collection.objects.link(floor)
floor.data.materials.append(glass)


def area(name, loc, look, size, energy, color, sy=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size = size
    if sy is not None:
        ld.size_y = sy
    ld.energy = energy
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (mathutils.Vector(look) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    lo.visible_camera = False


area("KeyMagenta", (-3.5, -2.5, 3.5), (0, 0, 0.3), 2.5, 1500, (1.0, 0.1, 0.6))
area("RimLime", (3.0, 3.5, 2.5), (0, 0, 0.4), 2.2, 1400, (0.5, 1.0, 0.1))
area("Strip", (2.2, -3.0, 2.0), (0, 0, 0.3), 0.25, 500, (1.0, 1.0, 1.0), sy=4.0)
area("Top", (0.0, 0.0, 5.0), (0, 0, 0), 3.0, 250, (0.9, 0.9, 1.0))
# big soft panels the chrome reflects (mercury is a mirror: it needs bright shapes around it to look silver)
def panel(name, loc, look, sx, sy, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nn = m.node_tree.nodes
    nn.clear()
    e = nn.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    o_ = nn.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(e.outputs[0], o_.inputs["Surface"])
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(m)
    ob.location = loc
    ob.rotation_euler = (mathutils.Vector(look) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    ob.visible_camera = False
    ob.visible_shadow = False


for _k in range(3):  # thin white strips (a big panel showed as a white slab in the glass floor)
    panel(f"PWhite{_k}", (-0.9 + 0.9 * _k, 0.0, 4.5), (-0.9 + 0.9 * _k, 0, 0), 0.08, 2.2, (1.0, 1.0, 1.0), 25.0)
panel("PMag", (-4.0, 1.0, 1.6), (0, 0, 0.5), 1.0, 2.5, (1.0, 0.08, 0.55), 8.0)
panel("PLime", (4.0, 1.5, 1.4), (0, 0, 0.5), 1.0, 2.5, (0.45, 1.0, 0.08), 7.0)
panel("PBack", (0.0, 5.0, 2.0), (0, 0, 0.5), 3.0, 0.06, (1.0, 1.0, 1.0), 20.0)


# soft bokeh orbs far behind, magenta / lime / white
def bokeh_mat(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l_ = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = n.new("ShaderNodeBsdfTransparent")
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 0.35
    mx = n.new("ShaderNodeMixShader")
    l_.new(lw.outputs["Facing"], pw.inputs[0])
    l_.new(pw.outputs[0], mx.inputs["Fac"])
    l_.new(em.outputs[0], mx.inputs[1])
    l_.new(tr.outputs[0], mx.inputs[2])
    l_.new(mx.outputs[0], out.inputs["Surface"])
    return m


BV, BF = ico_sphere(3)
bms = [bokeh_mat("B0", (1.0, 0.1, 0.6), 1.8), bokeh_mat("B1", (0.55, 1.0, 0.1), 1.6), bokeh_mat("B2", (1, 1, 1), 0.9)]
for i in range(70):
    p = np.array([rng.uniform(-9, 9), rng.uniform(6, 15), rng.uniform(-1.0, 7.0)])
    me = bpy.data.meshes.new(f"Bk{i}")
    me.from_pydata((BV * rng.uniform(0.12, 0.3) + p).tolist(), [], BF.tolist())
    o = bpy.data.objects.new(f"Bk{i}", me)
    scene.collection.objects.link(o)
    o.data.materials.append(bms[[0, 1, 0, 1, 2][i % 5]])
    o.visible_shadow = False

cd = bpy.data.cameras.new("Cam")
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 2.2
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


def place(loc, look, lens):
    cam.location = loc
    d = mathutils.Vector(look) - mathutils.Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.dof.focus_distance = d.length


def clear_drops():
    for o in list(bpy.data.objects):
        if o.name.startswith("Drop"):
            bpy.data.objects.remove(o, do_unlink=True)


def look_a():
    """cold open: a bass hit throws every drop into the air - frozen mid-flight, some stretched upward"""
    for i in range(70):
        a = rng.uniform(0, TAU)
        rr = math.sqrt(rng.uniform(0, 1)) * 1.6
        h = rng.uniform(0.05, 1.6) * (1.2 - rr / 2)
        r = rng.uniform(0.03, 0.11)
        drop(f"Drop{i}", (rr * math.cos(a), rr * math.sin(a), h + r), r, squash=rng.uniform(1.0, 1.5))
    place((1.6, -3.4, 0.7), (0, 0, 0.7), 40)


def look_b():
    """the vibration sorts them: a spiral of drops growing in size towards the centre"""
    n = 46
    for i in range(n):
        k = i / n
        a = i * 0.62
        rr = 0.25 + 1.55 * k
        r = 0.16 - 0.12 * k
        drop(f"Drop{i}", (rr * math.cos(a), rr * math.sin(a), r * 0.62), r, squash=0.62)
    place((1.2, -2.6, 3.2), (0, 0.1, 0.0), 35)


def look_c():
    """the payoff: everything merged into one big mirror sphere resting on the glass"""
    drop("Drop0", (0, 0, 0.62 * 0.9), 0.75, squash=0.9)
    for i in range(6):  # a few tiny last droplets around it
        a = i / 6 * TAU + 0.3
        drop(f"Drop{i + 1}", (1.25 * math.cos(a), 1.25 * math.sin(a), 0.025), 0.04, squash=0.62)
    place((2.2, -4.6, 1.3), (0, 0, 0.55), 45)


for key, fn in (("A", look_a), ("B", look_b), ("C", look_c)):
    if key not in WHICH:
        continue
    clear_drops()
    fn()
    scene.render.filepath = os.path.join(OUT, f"concept_{key}.png")
    bpy.ops.render.render(write_still=True)
