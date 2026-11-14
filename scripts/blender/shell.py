# 0017 "Obsidian Heart" (owner's reference, Nov 14: a black sphere of cracked plates in space that bursts open on a
# glowing core, gets hit by small black spheres and turns into an urchin - "recreate it, ultra realistic, better
# effects"). Same core idea, our look and effects, ray-traced in Blender Cycles:
#  - shell: ~220 Voronoi plates of polished obsidian (one mesh, per-plate rigid transforms per frame, solidify + bevel)
#  - core: a living violet-white plasma (animated 4D noise emission) + a light inside, so light leaks through the cracks
#  - urchin: a glossy black spike rises from every plate; impacts: black beads with light trails, a light ripple
#    through the cracks and a shockwave ring; signature: the plates swirl around the core like a galaxy, then click home
#  - deep space: black, a faint purple nebula, real star points; slow cinematic orbit, depth of field
# Ends: settles, dims and fades to black (owner, Nov 14). Usage:
#   blender -b --factory-startup -P scripts/blender/shell.py -- <outDir> [samples] [fps] [k] [n] [only]
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

DUR = 18.0  # real length (owner, Nov 14: 20 s is enough; v3 opens on the old 11 s effect)
# v3 edit: real time -> story time. The reel opens on the urchin (story 10.8) and its galaxy swirl, then plays the
# pulses/burst/hits/wave (story 1.0-9.8), then the ending (story 17.3-20). Every join is a closed, still sphere.
SEGS = [(0.0, 6.5, 10.8), (6.5, 15.3, 1.0), (15.3, 18.0, 17.3)]


def story(tr):
    for a, b, s0 in SEGS:
        if tr < b or b == SEGS[-1][1]:
            return s0 + (tr - a)
    return tr
TAU = 2 * math.pi
# story beats (s)
B = dict(
    retract=(0.0, 0.6),      # HOOK: frame 0 is the urchin, its spikes snap back in
    pulses=(1.0, 1.8),       # the cracks pulse with light
    burst=(2.4, 3.8),        # the plates burst open on the galaxy core
    home=(4.0, 5.2),         # ...and click back into place (shockwave)
    hits=(5.8, 6.5, 7.2, 7.8),  # beads fly in and hit, each a light ripple
    wave=(8.3, 9.6),         # a wave lifts the plates around the sphere
    spikes=(9.8, 11.8),      # the urchin
    swirl=(12.2, 16.0),      # SIGNATURE: plates swirl around the blazing galaxy
    click=(16.0, 17.3),      # ...then spiral home and click in, one by one
    end=(17.3, 20.0),        # ENDING (owner: "I want an end"): it settles, a last faint pulse, the light dims, fade to black
)

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
scene.cycles.max_bounces = 10
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.use_persistent_data = True
res = os.environ.get("SHELL_RES", "1080x1920").split("x")
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.image_settings.file_format = "PNG"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.9  # v3: owner - too dark
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass

# ---------------- deep space ----------------
world = bpy.data.worlds.new("Space")
scene.world = world
world.use_nodes = True
wn = world.node_tree.nodes
wl = world.node_tree.links
wn.clear()
wout = wn.new("ShaderNodeOutputWorld")
wbg = wn.new("ShaderNodeBackground")
wtc = wn.new("ShaderNodeTexCoord")
neb = wn.new("ShaderNodeTexNoise")
neb.inputs["Scale"].default_value = 1.6
neb.inputs["Detail"].default_value = 8.0
neb.inputs["Roughness"].default_value = 0.62
nramp = wn.new("ShaderNodeValToRGB")
nramp.color_ramp.elements[0].position = 0.45
nramp.color_ramp.elements[0].color = (0, 0, 0, 1)
nramp.color_ramp.elements[1].position = 0.78
nramp.color_ramp.elements[1].color = (0.16, 0.04, 0.32, 1)  # a faint purple nebula
stars = wn.new("ShaderNodeTexVoronoi")
stars.inputs["Scale"].default_value = 380.0
sramp = wn.new("ShaderNodeValToRGB")
sramp.color_ramp.elements[0].position = 0.0
sramp.color_ramp.elements[0].color = (1.6, 1.5, 1.8, 1)
sramp.color_ramp.elements[1].position = 0.035
sramp.color_ramp.elements[1].color = (0, 0, 0, 1)
smask = wn.new("ShaderNodeTexNoise")  # only some cells hold a star
smask.inputs["Scale"].default_value = 90.0
smr = wn.new("ShaderNodeMath")
smr.operation = "GREATER_THAN"
smr.inputs[1].default_value = 0.62
smul = wn.new("ShaderNodeVectorMath")
smul.operation = "SCALE"
add = wn.new("ShaderNodeMixRGB")
add.blend_type = "ADD"
add.inputs["Fac"].default_value = 1.0
wl.new(wtc.outputs["Generated"], neb.inputs["Vector"])
wl.new(neb.outputs["Fac"], nramp.inputs["Fac"])
wl.new(wtc.outputs["Generated"], stars.inputs["Vector"])
wl.new(stars.outputs["Distance"], sramp.inputs["Fac"])
wl.new(wtc.outputs["Generated"], smask.inputs["Vector"])
wl.new(smask.outputs["Fac"], smr.inputs[0])
wl.new(sramp.outputs["Color"], smul.inputs[0])
wl.new(smr.outputs[0], smul.inputs["Scale"])
wl.new(nramp.outputs["Color"], add.inputs[1])
wl.new(smul.outputs[0], add.inputs[2])
wl.new(add.outputs["Color"], wbg.inputs["Color"])
wbg.inputs["Strength"].default_value = 1.0
wl.new(wbg.outputs[0], wout.inputs[0])


def principled(name, color, metal=0.0, rough=0.1, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.015
    return m


obsidian = principled("SmokedGlass", (0.75, 0.6, 1.0), metal=0.0, rough=0.04, coat=0.6)
_ob = obsidian.node_tree.nodes
_ob["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
_ob["Principled BSDF"].inputs["IOR"].default_value = 1.52
_oabs = _ob.new("ShaderNodeVolumeAbsorption")
_oabs.inputs["Color"].default_value = (0.55, 0.3, 0.9, 1)
_oabs.inputs["Density"].default_value = 9.0  # smoked: dark violet, but the crystals glow through
obsidian.node_tree.links.new(_oabs.outputs[0], _ob["Material Output"].inputs["Volume"])
# micro surface detail: faint scratches/waviness so the plates read as real polished stone
on = obsidian.node_tree.nodes
bump = on.new("ShaderNodeBump")
bump.inputs["Strength"].default_value = 0.08
nz = on.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 60.0
nz.inputs["Detail"].default_value = 6.0
obsidian.node_tree.links.new(nz.outputs["Fac"], bump.inputs["Height"])
obsidian.node_tree.links.new(bump.outputs["Normal"], on["Principled BSDF"].inputs["Normal"])
spike_m = principled("SpikeGloss", (0.006, 0.006, 0.009), metal=0.3, rough=0.05, coat=1.0)
# v3 urchin remake: each spike glows violet toward its tip, like light running out of the core along it
_sn = spike_m.node_tree.nodes
_attr = _sn.new("ShaderNodeAttribute")
_attr.attribute_name = "tip"
_pw = _sn.new("ShaderNodeMath")
_pw.operation = "POWER"
_pw.inputs[1].default_value = 4.0
_sc = _sn.new("ShaderNodeMath")
_sc.operation = "MULTIPLY"
_sc.inputs[1].default_value = 3.5
spike_m.node_tree.links.new(_attr.outputs["Fac"], _pw.inputs[0])
spike_m.node_tree.links.new(_pw.outputs[0], _sc.inputs[0])
_sn["Principled BSDF"].inputs["Emission Color"].default_value = (0.55, 0.22, 1.0, 1)
spike_m.node_tree.links.new(_sc.outputs[0], _sn["Principled BSDF"].inputs["Emission Strength"])
bead_m = principled("Bead", (0.008, 0.008, 0.012), metal=0.6, rough=0.06, coat=1.0)

# ---------------- the shell: Voronoi plates ----------------
R = 1.0
NPL = 220
rng = np.random.default_rng(1717)
gold = math.pi * (3 - math.sqrt(5))
seeds = []
for i in range(NPL):
    y = 1 - (i + 0.5) / NPL * 2
    rr = math.sqrt(1 - y * y)
    a = gold * i
    v = np.array([math.cos(a) * rr, y, math.sin(a) * rr]) + rng.normal(0, 0.06, 3)
    seeds.append(v / np.linalg.norm(v))
SEEDS = np.array(seeds)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=8, radius=R)
ico = bpy.context.active_object
me = ico.data
nverts = len(me.vertices)
P = np.empty(nverts * 3)
me.vertices.foreach_get("co", P)
P = P.reshape(-1, 3)
tri = np.empty(len(me.polygons) * 3, dtype=np.int64)
me.polygons.foreach_get("vertices", tri)
tri = tri.reshape(-1, 3)
fc = P[tri].mean(1)
fc /= np.linalg.norm(fc, axis=1, keepdims=True)
owner = np.argmax(fc @ SEEDS.T, axis=1)
bpy.data.objects.remove(ico, do_unlink=True)
# separate plates: every plate gets its own vertices; shrink a little toward its centre (the cracks)
verts, faces, vplate = [], [], []
PC = np.zeros((NPL, 3))
for p in range(NPL):
    ft = tri[owner == p]
    if len(ft) == 0:
        continue
    used, inv = np.unique(ft, return_inverse=True)
    pv = P[used].copy()
    # smooth the plate outline: the triangle-staircase boundary becomes a clean cut (relax boundary loop, keep on sphere)
    lf = inv.reshape(-1, 3)
    e = np.sort(np.concatenate([lf[:, [0, 1]], lf[:, [1, 2]], lf[:, [2, 0]]]), axis=1)
    ue, cnt = np.unique(e, axis=0, return_counts=True)
    be = ue[cnt == 1]
    if len(be):
        nb = {}
        for a_, b_ in be:
            nb.setdefault(a_, []).append(b_)
            nb.setdefault(b_, []).append(a_)
        bv = np.array([k for k, v in nb.items() if len(v) == 2])
        n1 = np.array([nb[k][0] for k in bv])
        n2 = np.array([nb[k][1] for k in bv])
        for _ in range(3):
            pv[bv] = 0.6 * pv[bv] + 0.2 * (pv[n1] + pv[n2])
            pv[bv] /= np.linalg.norm(pv[bv], axis=1, keepdims=True)
    c = pv.mean(0)
    c = c / np.linalg.norm(c) * R
    PC[p] = c
    pv = c + (pv - c) * 0.965
    base = len(verts)
    verts.extend(pv.tolist())
    vplate.extend([p] * len(pv))
    faces.extend((inv.reshape(-1, 3) + base).tolist())
mesh = bpy.data.meshes.new("Shell")
mesh.from_pydata(verts, [], faces)
mesh.update()
shell = bpy.data.objects.new("Shell", mesh)
scene.collection.objects.link(shell)
shell.data.materials.append(obsidian)
for poly in mesh.polygons:
    poly.use_smooth = True
sol = shell.modifiers.new("Thick", "SOLIDIFY")
sol.thickness = 0.07
sol.offset = -1
sol.use_even_offset = True
bev = shell.modifiers.new("Edge", "BEVEL")
bev.show_render = False  # the notched highlights on the plate sides came from this
bev.width = 0.012
bev.segments = 2
bev.limit_method = "ANGLE"
V0 = np.array(verts)
VP = np.array(vplate)
NRM = PC / np.linalg.norm(PC, axis=1, keepdims=True)
LAT = NRM[:, 2]
RAND = rng.uniform(0.6, 1.4, NPL)
AXES = rng.normal(0, 1, (NPL, 3))
AXES /= np.linalg.norm(AXES, axis=1, keepdims=True)
BASE_TILT = rng.uniform(-0.055, 0.055, NPL)  # each plate sits a hair off true: it catches light on its own (faceted, jewel-like)
ORDER = np.argsort(np.arctan2(NRM[:, 1], NRM[:, 0]) + 3 * NRM[:, 2])  # the click-home order (a spiral)
CLICK_T = np.empty(NPL)
CLICK_T[ORDER] = np.linspace(0, 1, NPL)

# ---------------- the core: living plasma ----------------
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.83)
core = bpy.context.active_object
cm = bpy.data.materials.new("Plasma")
cm.use_nodes = True
cn = cm.node_tree.nodes
cn.clear()
cout = cn.new("ShaderNodeOutputMaterial")
cem = cn.new("ShaderNodeEmission")
cnz = cn.new("ShaderNodeTexNoise")
cnz.noise_dimensions = "4D"
cnz.inputs["Scale"].default_value = 2.6
cnz.inputs["Detail"].default_value = 10.0
cnz.inputs["Distortion"].default_value = 2.2
cramp = cn.new("ShaderNodeValToRGB")
cramp.color_ramp.elements[0].position = 0.42
cramp.color_ramp.elements[0].color = (0.03, 0.005, 0.09, 1)
mid = cramp.color_ramp.elements.new(0.6)
mid.color = (0.62, 0.32, 1.0, 1)
cramp.color_ramp.elements[1].position = 0.86
cramp.color_ramp.elements[1].color = (0.85, 0.95, 1.0, 1)  # white-hot with a cyan edge
ctc = cn.new("ShaderNodeTexCoord")
cm.node_tree.links.new(ctc.outputs["Object"], cnz.inputs["Vector"])
cm.node_tree.links.new(cnz.outputs["Fac"], cramp.inputs["Fac"])
cm.node_tree.links.new(cramp.outputs["Color"], cem.inputs["Color"])
cm.node_tree.links.new(cem.outputs[0], cout.inputs["Surface"])
core.data.materials.append(cm)
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=0.925)
crackglow = bpy.context.active_object
gm = bpy.data.materials.new("CrackGlow")
gm.use_nodes = True
gn = gm.node_tree.nodes
gn.clear()
gout = gn.new("ShaderNodeOutputMaterial")
gem = gn.new("ShaderNodeEmission")
gem.inputs["Color"].default_value = (0.42, 0.1, 1.0, 1)  # deep violet light in the cracks
gm.node_tree.links.new(gem.outputs[0], gout.inputs["Surface"])
crackglow.data.materials.append(gm)
crackglow.visible_shadow = False
# --- v2 core (owner, Nov 14: "the core looks pretty bad, replace it with something much cooler"): a living GALAXY
# inside the sphere - volumetric spiral arms (violet -> cyan) around a white-hot bulge, dust breakup and star sparkles,
# turning slowly, tilted toward the camera. Every burst reveals a tiny universe.
core.hide_render = True
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.86)
galaxy = bpy.context.active_object
galaxy.rotation_mode = "ZXY"  # spin about its own axis, then tilt toward the camera
gx = bpy.data.materials.new("Galaxy")
gx.use_nodes = True
xn = gx.node_tree.nodes
xl = gx.node_tree.links
xn.clear()
xo = xn.new("ShaderNodeOutputMaterial")


def M(op, a=None, b=None, va=None, vb=None):
    n = xn.new("ShaderNodeMath")
    n.operation = op
    if a is not None:
        xl.new(a, n.inputs[0])
    elif va is not None:
        n.inputs[0].default_value = va
    if b is not None:
        xl.new(b, n.inputs[1])
    elif vb is not None:
        n.inputs[1].default_value = vb
    return n.outputs[0]


xtc = xn.new("ShaderNodeTexCoord")
xsep = xn.new("ShaderNodeSeparateXYZ")
xl.new(xtc.outputs["Object"], xsep.inputs[0])
X_, Y_, Z_ = xsep.outputs["X"], xsep.outputs["Y"], xsep.outputs["Z"]
r = M("SQRT", M("ADD", M("MULTIPLY", X_, X_), M("MULTIPLY", Y_, Y_)))
theta = M("ARCTAN2", Y_, X_)
logr = M("LOGARITHM", M("ADD", r, vb=0.03), vb=2.718)
phase = M("SUBTRACT", M("MULTIPLY", theta, vb=2.0), M("MULTIPLY", logr, vb=4.2))
arm_n = xn.new("ShaderNodeMath")
arm_n.operation = "MULTIPLY_ADD"
xl.new(M("COSINE", phase), arm_n.inputs[0])
arm_n.inputs[1].default_value = 0.5
arm_n.inputs[2].default_value = 0.5
arm = M("POWER", arm_n.outputs[0], vb=3.0)
disk = M("EXPONENT", M("MULTIPLY", M("POWER", M("DIVIDE", Z_, vb=0.075), vb=2.0), vb=-1.0))
radial = M("EXPONENT", M("MULTIPLY", M("POWER", M("DIVIDE", r, vb=0.44), vb=2.0), vb=-1.0))
noise = xn.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 7.0
noise.inputs["Detail"].default_value = 10.0
noise.inputs["Roughness"].default_value = 0.6
xl.new(xtc.outputs["Object"], noise.inputs["Vector"])
dust = M("POWER", noise.outputs["Fac"], vb=2.2)
arm_s = M("POWER", arm, vb=2.0)  # sharper, more defined arms
arms = M("MULTIPLY", M("MULTIPLY", disk, radial), M("ADD", M("MULTIPLY", M("MULTIPLY", arm_s, dust), vb=7.0), vb=0.0))
bulge = M("MULTIPLY", M("EXPONENT", M("MULTIPLY", M("ADD", M("MULTIPLY", r, r), M("MULTIPLY", Z_, Z_)), vb=-140.0)), vb=5.0)
vor = xn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 45.0
xl.new(xtc.outputs["Object"], vor.inputs["Vector"])
starpt = M("MAXIMUM", M("SUBTRACT", va=0.07, b=vor.outputs["Distance"]), vb=0.0)  # bright points at the cell centres
stars = M("MULTIPLY", M("MULTIPLY", starpt, vb=420.0), M("EXPONENT", M("MULTIPLY", M("POWER", M("DIVIDE", Z_, vb=0.18), vb=2.0), vb=-1.0)))
density = M("ADD", M("ADD", arms, bulge), M("MULTIPLY", stars, radial))
xramp = xn.new("ShaderNodeValToRGB")
cr_ = xramp.color_ramp
cr_.elements[0].position = 0.0
cr_.elements[0].color = (1.0, 0.92, 1.0, 1)
e1 = cr_.elements.new(0.12)
e1.color = (0.95, 0.5, 1.0, 1)
e2 = cr_.elements.new(0.32)
e2.color = (0.5, 0.16, 1.0, 1)
cr_.elements[1].position = 0.62
cr_.elements[1].color = (0.15, 0.7, 1.0, 1)  # the cyan accent on the outer arms
xl.new(M("DIVIDE", r, vb=0.86), xramp.inputs["Fac"])
xem = xn.new("ShaderNodeEmission")
xl.new(xramp.outputs["Color"], xem.inputs["Color"])
GAL_GAIN = xn.new("ShaderNodeValue")
GAL_GAIN.outputs[0].default_value = 3.0
xl.new(M("MULTIPLY", density, GAL_GAIN.outputs[0]), xem.inputs["Strength"])
xl.new(xem.outputs[0], xo.inputs["Volume"])
galaxy.data.materials.append(gx)
scene.cycles.volume_step_rate = 2.0
# light spikes (owner: 'add spikes or something'): thin blades of light shoot out of the galaxy when the shell opens
NRAY = 18
ray_v, ray_f = [], []
rdirs = rng.normal(0, 1, (NRAY, 3))
rdirs /= np.linalg.norm(rdirs, axis=1, keepdims=True)
for i in range(NRAY):
    b0 = len(ray_v)
    ray_v.append((0.0, 0.0, 1.0))
    for s_ in range(6):
        a = TAU * s_ / 6
        ray_v.append((math.cos(a), math.sin(a), 0.0))
    for s_ in range(6):
        ray_f.append((b0, b0 + 1 + s_, b0 + 1 + (s_ + 1) % 6))
RV = np.array(ray_v)
RAYP = np.repeat(np.arange(NRAY), 7)
rmesh = bpy.data.meshes.new("Rays")
rmesh.from_pydata(ray_v, [], ray_f)
rays = bpy.data.objects.new("Rays", rmesh)
scene.collection.objects.link(rays)
rays.visible_shadow = False
raym = bpy.data.materials.new("RayLight")
raym.use_nodes = True
rnn = raym.node_tree.nodes
rnn.clear()
rro = rnn.new("ShaderNodeOutputMaterial")
rre = rnn.new("ShaderNodeEmission")
rre.inputs["Color"].default_value = (0.55, 0.3, 1.0, 1)
rre.inputs["Strength"].default_value = 5.0
raym.node_tree.links.new(rre.outputs[0], rro.inputs["Surface"])
rays.data.materials.append(raym)
RLEN = rng.uniform(0.9, 1.7, NRAY)
RTX = np.cross(np.where(np.abs(rdirs[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]])), rdirs)
RTX /= np.linalg.norm(RTX, axis=1, keepdims=True)
RTY = np.cross(rdirs, RTX)
scene.cycles.volume_max_steps = 160

ld = bpy.data.lights.new("CoreLight", "POINT")
ld.shadow_soft_size = 0.7
ld.color = (0.62, 0.42, 1.0)
corelight = bpy.data.objects.new("CoreLight", ld)
scene.collection.objects.link(corelight)

# ---------------- spikes: one per plate ----------------
CONE_SEG = 18
cone_v, cone_f, cone_p = [], [], []
for p in range(NPL):
    base = len(cone_v)
    cone_v.append((0, 0, 1))
    for s in range(CONE_SEG):
        a = TAU * s / CONE_SEG
        cone_v.append((math.cos(a), math.sin(a), 0))
    cone_p.extend([p] * (CONE_SEG + 1))
    for s in range(CONE_SEG):
        cone_f.append((base, base + 1 + s, base + 1 + (s + 1) % CONE_SEG))
CV = np.array(cone_v, dtype=np.float64)
CP = np.array(cone_p)
smesh = bpy.data.meshes.new("Spikes")
smesh.from_pydata(cone_v, [], cone_f)
tipa = smesh.attributes.new("tip", "FLOAT", "POINT")
tipa.data.foreach_set("value", [v[2] for v in cone_v])  # 1 at the tip, 0 at the base
spikes = bpy.data.objects.new("Spikes", smesh)
scene.collection.objects.link(spikes)
spikes.data.materials.append(spike_m)
for poly in smesh.polygons:
    poly.use_smooth = True
# a frame (tangent basis) per plate
UP = np.where(np.abs(NRM[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
TX = np.cross(UP, NRM)
TX /= np.linalg.norm(TX, axis=1, keepdims=True)
TY = np.cross(NRM, TX)
PLR = np.array([np.max(np.linalg.norm(V0[VP == p] - PC[p], axis=1)) if np.any(VP == p) else 0.1 for p in range(NPL)])

# ---------------- beads with light trails, shockwave ring ----------------
BEADS = []
trail_m = bpy.data.materials.new("Trail")
trail_m.use_nodes = True
tn = trail_m.node_tree.nodes
tn.clear()
tout = tn.new("ShaderNodeOutputMaterial")
tem = tn.new("ShaderNodeEmission")
tem.inputs["Color"].default_value = (0.65, 0.85, 1.0, 1)
tgr = tn.new("ShaderNodeTexGradient")
ttc = tn.new("ShaderNodeTexCoord")
tmix = tn.new("ShaderNodeMixShader")
ttr = tn.new("ShaderNodeBsdfTransparent")
tsep = tn.new("ShaderNodeSeparateXYZ")
tpow = tn.new("ShaderNodeMath")
tpow.operation = "POWER"
tpow.inputs[1].default_value = 2.5
tinv = tn.new("ShaderNodeMath")
tinv.operation = "SUBTRACT"
tinv.inputs[0].default_value = 1.0
trail_m.node_tree.links.new(ttc.outputs["Generated"], tsep.inputs[0])
trail_m.node_tree.links.new(tsep.outputs["Z"], tinv.inputs[1])
trail_m.node_tree.links.new(tinv.outputs[0], tpow.inputs[0])
trail_m.node_tree.links.new(tpow.outputs[0], tmix.inputs["Fac"])  # bright at the bead, fading to nothing
trail_m.node_tree.links.new(ttr.outputs[0], tmix.inputs[1])
trail_m.node_tree.links.new(tem.outputs[0], tmix.inputs[2])
trail_m.node_tree.links.new(tmix.outputs[0], tout.inputs["Surface"])
tem.inputs["Strength"].default_value = 3.0
HIT_DIRS = []
for i, th in enumerate(B["hits"]):
    a = 0.7 + i * 1.9
    d = np.array([math.cos(a) * 0.8, -0.45 + 0.2 * (i % 3), math.sin(a) * 0.6 + 0.2])
    HIT_DIRS.append(d / np.linalg.norm(d))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.16)
    bo = bpy.context.active_object
    bo.data.materials.append(bead_m)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.016, depth=1.0)
    tr = bpy.context.active_object
    tr.data.materials.append(trail_m)
    tr.visible_shadow = False
    BEADS.append((bo, tr))
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, major_segments=160, minor_segments=12)
ringo = bpy.context.active_object
rm = bpy.data.materials.new("Shock")
rm.use_nodes = True
rn = rm.node_tree.nodes
rn.clear()
rout = rn.new("ShaderNodeOutputMaterial")
rem = rn.new("ShaderNodeEmission")
rem.inputs["Color"].default_value = (0.7, 0.55, 1.0, 1)
rmix = rn.new("ShaderNodeMixShader")
rtr = rn.new("ShaderNodeBsdfTransparent")
rm.node_tree.links.new(rtr.outputs[0], rmix.inputs[1])
rm.node_tree.links.new(rem.outputs[0], rmix.inputs[2])
rm.node_tree.links.new(rmix.outputs[0], rout.inputs["Surface"])
ringo.data.materials.append(rm)
ringo.visible_shadow = False

# ---------------- light and camera ----------------
def area(name, loc, size, power, color, target=(0, 0, 0)):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = "DISK"
    l.size = size
    l.energy = power
    l.color = color
    o = bpy.data.objects.new(name, l)
    o.location = loc
    scene.collection.objects.link(o)
    o.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False
    return o


area("Key", (-4.5, -3.5, 4.5), 3.0, 1000, (1.0, 0.97, 0.94))


def strip(name, loc, sx, sy, power, color):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = "RECTANGLE"
    l.size, l.size_y = sx, sy
    l.energy = power
    l.color = color
    o = bpy.data.objects.new(name, l)
    o.location = loc
    scene.collection.objects.link(o)
    o.rotation_euler = (mathutils.Vector((0, 0, 0)) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False


# two tall strip softboxes: long, elegant reflections that slide across the plates as the camera drifts
strip("StripL", (-4.0, -2.2, 0.5), 0.25, 5.0, 650, (1.0, 0.98, 0.96))
strip("StripR", (3.2, -3.4, 1.2), 0.18, 4.5, 380, (0.85, 0.8, 1.0))
area("RimCyan", (3.5, 4.0, 1.2), 1.0, 380, (0.2, 0.85, 1.0))
area("Fill", (4.0, -2.5, -1.0), 2.5, 120, (0.55, 0.3, 1.0)).visible_glossy = False  # no sticker-like disc reflection
cd = bpy.data.cameras.new("Cam")
cd.lens = 50
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


# ---------------- the story ----------------
def sm(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def spring(x):
    """0 -> 1 with a real overshoot and a settling wobble (click into place)"""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return 1 - math.exp(-6 * x) * math.cos(9 * x) * (1 - x) ** 0.3


def rot_matrices(axes, ang):
    """Rodrigues: rotation matrices for every plate (n, 3, 3)"""
    k = axes
    c, s = np.cos(ang)[:, None, None], np.sin(ang)[:, None, None]
    K_ = np.zeros((len(k), 3, 3))
    K_[:, 0, 1], K_[:, 0, 2], K_[:, 1, 0] = -k[:, 2], k[:, 1], k[:, 2]
    K_[:, 1, 2], K_[:, 2, 0], K_[:, 2, 1] = -k[:, 0], -k[:, 1], k[:, 0]
    I = np.eye(3)[None]
    return I + s * K_ + (1 - c) * (K_ @ K_)


def state(t):
    out = np.zeros(NPL)          # radial offset of each plate
    spin = BASE_TILT.copy()      # tumble angle (a tiny rest tilt per plate)
    swirl = np.zeros(NPL)        # orbit angle around the vertical axis
    glow = 0.25                  # core brightness (cracks)
    # glow pulses
    for tp in B["pulses"] + (18.0,):  # the last, faint pulse in the ending
        a = t - tp
        if a > 0:
            glow += 1.1 * math.exp(-a * 3.5) * min(1, a / 0.08)
    # burst and home
    b0, b1 = B["burst"]
    h0, h1 = B["home"]
    open_ = sm(b0, b1, t) * (1 - spring((t - h0) / (h1 - h0)))
    out += 0.95 * RAND * open_
    spin += 1.4 * RAND * open_
    glow += 3.5 * open_
    # hits: each bead lands on a plate near its direction; the plate dips and rebounds, light ripples through cracks
    for i, th in enumerate(B["hits"]):
        a = t - th
        if a > 0:
            near = NRM @ HIT_DIRS[i]
            w = np.clip((near - 0.55) / 0.45, 0, 1)
            out += -0.12 * w * math.exp(-a * 4) * math.cos(a * 18)
            ring = np.exp(-(((1 - near) - a * 1.6) / 0.08) ** 2) * math.exp(-a * 2)
            out += 0.04 * ring
            glow += 1.4 * math.exp(-a * 3.0) * min(1, a / 0.04)
    # the wave lifting plates around the sphere
    w0, w1 = B["wave"]
    if w0 < t < w1 + 0.6:
        ph = (t - w0) / (w1 - w0) * TAU * 1.0
        out += 0.16 * np.clip(np.cos(np.arctan2(NRM[:, 1], NRM[:, 0]) - ph), 0, 1) ** 4 * (1 - sm(w1, w1 + 0.6, t))
        glow += 0.5
    # the swirl (signature) and the click home
    s0, s1 = B["swirl"]
    c0, c1 = B["click"]
    swirl_amt = sm(s0, s0 + 1.6, t)
    back = np.clip((t - c0) / (c1 - c0) * 1.25 - CLICK_T * 0.25, 0, 1)
    home = np.array([spring(x) for x in back])
    sw_out = swirl_amt * (1 - home)
    out += (1.3 + 0.9 * (1 - np.abs(LAT))) * RAND * sw_out
    spin += 2.2 * RAND * sw_out
    phase = TAU * 0.22 * max(0.0, t - s0) ** 1.2
    swirl += phase * (1.6 - np.abs(LAT)) * (sw_out > 1e-4)
    glow += 5.5 * float(np.mean(sw_out))
    # spikes
    spk = np.zeros(NPL)
    r0, r1 = B["retract"]
    spk += 1 - sm(r0, r1, t)
    k0, k1 = B["spikes"]
    spk += sm(k0, k0 + 0.6, t) * (1 - sm(k1 - 0.5, k1, t)) * (1 + 0.08 * math.sin(TAU * 2 * t))
    glow *= 1 - 0.85 * sm(18.3, 19.8, t)  # the light dims as it rests
    return out, spin, swirl, glow, np.clip(spk, 0, 1.1)


# ================= v4 (owner, Nov 14: "the core looks cheap, the reel is boring - make it go viral") =================
# 16 s. The core is a cluster of REAL amethyst crystals (ray-traced glass: hexagonal prisms with pyramid tips, purple
# absorption, inner light). Story: the cracked sphere peels open plate by plate, BLASTS apart, the plates orbit the
# crystal heart, the crystals grow out into a giant amethyst urchin, light pulses through them base to tip, they pull
# back, the plates spiral home and slam shut, a last glow, fade.
DUR = 18.2


def story4(r):
    """v5 real -> story time: cold open on the pulsing urchin (story 8.6-9.6), a fast rewind to the closed sphere, then the story"""
    if r < 1.0:
        return 8.6 + r
    if r < 2.2:
        k = (r - 1.0) / 1.2
        return 9.6 * (1 - k * k * (3 - 2 * k))
    return r - 2.2
V4 = dict(peel=(0.3, 2.8), blast=(2.8, 3.6), grow=(6.0, 8.3), pulses=(8.6, 9.3, 10.0), retract=(10.5, 11.8),
          slam=(12.0, 13.4), last=14.2, fade=(14.4, 15.9))

amethyst = bpy.data.materials.new("Amethyst")
amethyst.use_nodes = True
an = amethyst.node_tree.nodes
al = amethyst.node_tree.links
ab = an["Principled BSDF"]
ab.inputs["Base Color"].default_value = (0.7, 0.45, 1.0, 1)
ab.inputs["Transmission Weight"].default_value = 1.0
ab.inputs["IOR"].default_value = 1.544
ab.inputs["Roughness"].default_value = 0.02
ab.inputs["Emission Color"].default_value = (0.62, 0.18, 1.0, 1)
aattr = an.new("ShaderNodeAttribute")
aattr.attribute_name = "glow"
al.new(aattr.outputs["Fac"], ab.inputs["Emission Strength"])
aabs = an.new("ShaderNodeVolumeAbsorption")
aabs.inputs["Color"].default_value = (0.66, 0.16, 0.9, 1)
aabs.inputs["Density"].default_value = 22.0
al.new(aabs.outputs[0], an["Material Output"].inputs["Volume"])

NC = 120
cdirs = []
for i in range(NC):
    y = 1 - (i + 0.5) / NC * 2
    rr = math.sqrt(1 - y * y)
    a = gold * i
    v = np.array([math.cos(a) * rr, y, math.sin(a) * rr]) + rng.normal(0, 0.12, 3)
    cdirs.append(v / np.linalg.norm(v))
CD = np.array(cdirs)
CRAD = rng.uniform(0.055, 0.11, NC)
CBASE = rng.uniform(0.28, 0.62, NC)    # resting length (fits inside the shell)
CLONG = rng.uniform(1.5, 2.6, NC)      # grown length (the urchin)
CPH = rng.uniform(0, 0.6, NC)
CTX = np.cross(np.where(np.abs(CD[:, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]])), CD)
CTX /= np.linalg.norm(CTX, axis=1, keepdims=True)
CTY = np.cross(CD, CTX)
# one hexagonal crystal: base ring (6), shoulder ring (6), tip (1)
cv, cf, cpart = [], [], []
for k in range(NC):
    b = len(cv)
    for ring in (0, 1):
        for s_ in range(6):
            a = TAU * s_ / 6 + 0.3 * k
            cv.append((math.cos(a), math.sin(a), ring))
    cv.append((0, 0, 2))
    cpart.extend([k] * 13)
    for s_ in range(6):
        n_ = (s_ + 1) % 6
        cf.append((b + s_, b + n_, b + 6 + n_, b + 6 + s_))
        cf.append((b + 6 + s_, b + 6 + n_, b + 12))
    cf.append(tuple(b + s_ for s_ in range(5, -1, -1)))
CV4 = np.array(cv, dtype=np.float64)
CPART = np.array(cpart)
cmesh = bpy.data.meshes.new("Crystals")
cmesh.from_pydata(cv, [], cf)
crystals = bpy.data.objects.new("Crystals", cmesh)
scene.collection.objects.link(crystals)
crystals.data.materials.append(amethyst)
glow_attr = cmesh.attributes.new("glow", "FLOAT", "POINT")
heart = bpy.data.lights.new("HeartLight", "POINT")
heart.shadow_soft_size = 0.25
heart.color = (0.7, 0.45, 1.0)
heartlight = bpy.data.objects.new("HeartLight", heart)
scene.collection.objects.link(heartlight)
for o in (galaxy, rays, core, spikes):
    o.hide_render = True


def state4(t):
    out = np.zeros(NPL)
    spin = BASE_TILT.copy()
    swirl = np.zeros(NPL)
    glow = 0.6 + 0.4 * sm(0, 0.3, t)  # frame 0: the cracks already glow
    # peel: plates pop one after another, faster and faster
    p0, p1 = V4["peel"]
    tp = p0 + (p1 - p0) * CLICK_T ** 0.55
    a = np.clip(t - tp, 0, None)
    popped = (t > tp).astype(float)
    pop = popped * (0.55 * (1 - np.exp(-a * 7)) + 0.12 * a)
    # blast: everything still on flies out
    bl = sm(V4["blast"][0], V4["blast"][1], t)
    out += pop + bl * (1.25 + 0.9 * RAND)
    spin += popped * a * 2.2 * RAND + bl * 1.6 * RAND
    # orbit around the crystal heart
    orbit = TAU * 0.08 * max(0.0, t - V4["blast"][0]) * (1 + 0.6 * (1 - np.abs(LAT)))
    swirl += orbit
    # slam home: spiral back in order, click into place
    s0, s1 = V4["slam"]
    back = np.clip((t - s0) / (s1 - s0) * 1.25 - CLICK_T * 0.25, 0, 1)
    home = np.array([spring(x) for x in back])
    out *= 1 - home
    spin = BASE_TILT + (spin - BASE_TILT) * (1 - home)
    swirl *= 1 - home
    aa = t - V4["last"]
    if aa > 0:
        glow += 1.2 * math.exp(-aa * 2.5) * min(1, aa / 0.08)
    glow *= 1 - 0.85 * sm(V4["last"] + 0.3, V4["fade"][1], t)
    # crystals: length and visibility
    g0, g1 = V4["grow"]
    r0, r1 = V4["retract"]
    grow = np.array([sm(g0 + CPH[k], g0 + 1.2 + CPH[k], t) for k in range(NC)]) * (1 - sm(r0, r1, t))
    L = CBASE + (CLONG - CBASE) * grow
    show = 1.0  # v5: the crystals are always there, glowing through the smoked glass
    L = L * 0.95
    return out, spin, swirl, glow, L, show


def crystal_mesh(t, L, show):
    base = CD[CPART] * 0.08
    ring = CV4[:, 2]
    rad = CRAD[CPART][:, None]
    tipl = (CRAD * 1.7)[CPART]
    along = np.where(ring == 0, 0.0, np.where(ring == 1, L[CPART] - tipl, L[CPART]))
    width = np.where(ring == 2, 0.0, 1.0)[:, None]
    pos = (base + CD[CPART] * along[:, None]
           + CTX[CPART] * CV4[:, 0:1] * rad * width + CTY[CPART] * CV4[:, 1:2] * rad * width)
    crystals.data.vertices.foreach_set("co", pos.astype(np.float32).ravel())
    crystals.data.update()
    # light pulses run through each crystal from base to tip
    g = np.full(len(CV4), 0.04 * show)
    frac = np.where(ring == 0, 0.0, np.where(ring == 1, 0.8, 1.0))
    for tp_ in V4["pulses"]:
        aa = t - tp_
        if aa > -0.1:
            front = aa * 1.6
            g += 0.85 * np.exp(-((frac - front) / 0.25) ** 2) * math.exp(-max(aa, 0) * 0.8)
    glow_attr.data.foreach_set("value", g.astype(np.float32))
    crystals.hide_render = show < 0.01


def frame(f):
    treal = f / FPS
    t = story4(treal)
    out, spin, swirl, glow, L4, show4 = state4(t)
    spk = np.zeros(NPL)
    crystal_mesh(t, L4, show4)
    heart.energy = 20 + 110 * show4 + 160 * sum(math.exp(-max(0.0, t - p) * 2) * (t > p) for p in V4["pulses"])
    # plates: rotate in place (tumble), push out along the normal, then orbit around the vertical axis
    Rm = rot_matrices(AXES, spin)
    c_out = PC * (1 + out)[:, None]
    ca, sa = np.cos(swirl), np.sin(swirl)
    cx = c_out[:, 0] * ca - c_out[:, 1] * sa
    cy = c_out[:, 0] * sa + c_out[:, 1] * ca
    c_new = np.stack([cx, cy, c_out[:, 2]], 1)
    local = V0 - PC[VP]
    rv = np.einsum("nij,nj->ni", Rm[VP], local)
    # the orbit also turns the plate with it
    oa, ob = ca[VP], sa[VP]
    rx = rv[:, 0] * oa - rv[:, 1] * ob
    ry = rv[:, 0] * ob + rv[:, 1] * oa
    v = np.stack([rx, ry, rv[:, 2]], 1) + c_new[VP]
    shell.data.vertices.foreach_set("co", v.astype(np.float32).ravel())
    shell.data.update()
    # spikes ride on their plates
    h = 0.85 * spk * RAND ** 0.5
    nrm_t = np.einsum("nij,nj->ni", Rm, NRM)
    nx = nrm_t[:, 0] * ca - nrm_t[:, 1] * sa
    ny = nrm_t[:, 0] * sa + nrm_t[:, 1] * ca
    n2 = np.stack([nx, ny, nrm_t[:, 2]], 1)
    tx = np.einsum("nij,nj->ni", Rm, TX)
    tx2 = np.stack([tx[:, 0] * ca - tx[:, 1] * sa, tx[:, 0] * sa + tx[:, 1] * ca, tx[:, 2]], 1)
    ty2 = np.cross(n2, tx2)
    rad = PLR * 0.5
    cv = CV
    pidx = CP
    pos = (c_new[pidx] + n2[pidx] * (cv[:, 2:3] * h[pidx, None] - 0.03)
           + tx2[pidx] * (cv[:, 0:1] * rad[pidx, None] * (h[pidx, None] > 0.02))
           + ty2[pidx] * (cv[:, 1:2] * rad[pidx, None] * (h[pidx, None] > 0.02)))
    spikes.data.vertices.foreach_set("co", pos.astype(np.float32).ravel())
    spikes.hide_render = True
    spikes.data.update()
    # core
    cem.inputs["Strength"].default_value = min(3.2, 0.5 + 0.55 * glow)
    cnz.inputs["W"].default_value = t * 0.35
    closed = 1.0 - min(1.0, float(np.max(np.abs(out))) * 3)
    gem.inputs["Strength"].default_value = (2.5 + 16.0 * min(glow, 2.0)) * closed
    crackglow.scale = (0, 0, 0)  # v5: glass shell - the crystals themselves glow through
    ld.energy = min(2600, 80 + 420 * glow)
    core.scale = (1 + 0.04 * math.sin(TAU * 0.9 * t),) * 3
    # light spikes: length follows how open the shell is, each flickers on its own
    openk = 1 - closed
    L = RLEN * openk * (0.75 + 0.25 * np.sin(TAU * 1.3 * t + np.arange(NRAY) * 1.7))
    w = 0.011 * openk
    rp = (rdirs[RAYP] * (RV[:, 2:3] * L[RAYP, None] + 0.1) + RTX[RAYP] * RV[:, 0:1] * w + RTY[RAYP] * RV[:, 1:2] * w)
    rays.data.vertices.foreach_set("co", rp.astype(np.float32).ravel())
    rays.data.update()
    rays.hide_render = True
    galaxy.hide_render = True
    # beads and trails
    for i, (bo, tr) in enumerate(BEADS):
        th = B["hits"][i]
        a = -1  # v4: no beads
        d = mathutils.Vector(HIT_DIRS[i].tolist())
        if 0 <= a <= 0.9:
            k = a / 0.9
            dist = 1.06 + 5.5 * (1 - k) ** 1.6
            p = d * dist
            bo.location = p
            bo.scale = (1, 1, 1)
            tl_ = 1.6 * (1 - k * 0.3)
            tr.location = d * (dist + tl_ / 2)
            tr.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
            tr.scale = (1, 1, tl_)
        else:
            bo.scale = (0, 0, 0)
            tr.scale = (0, 0, 0)
    # the shockwave ring: on the home click and the last hit
    ra = t - V4["blast"][0]
    rb = t - V4["slam"][1] + 0.15
    age = ra if 0 <= ra < 1.6 else (rb if 0 <= rb < 1.6 else -1)
    if age >= 0:
        s = 1.15 + 2.6 * age
        ringo.scale = (s, s, s)
        ringo.rotation_euler = (math.radians(72), 0, math.radians(15))
        rem.inputs["Strength"].default_value = 8 * math.exp(-age * 2.6)
        rmix.inputs["Fac"].default_value = 1.0
    else:
        ringo.scale = (0, 0, 0)
    # camera: slow orbit, gentle push on the signature, returns to its start (loop)
    yaw = math.radians(14 * math.sin(TAU * treal / DUR))
    elv = math.radians(8 + 5 * math.sin(TAU * treal / DUR + 1.3))
    dist = 6.4 + 0.9 * sm(2.8, 4.0, t) * (1 - sm(11.6, 13.2, t)) + 2.2 * sm(6.0, 8.5, t) * (1 - sm(10.4, 12.0, t)) + 1.2 * sm(14.0, 16.0, t)
    look = mathutils.Vector((0, 0, 0))
    pos = look + mathutils.Vector((math.sin(yaw) * math.cos(elv), -math.cos(yaw) * math.cos(elv), math.sin(elv))) * dist
    cam.location = pos
    cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = (look - pos).length - 0.6
    scene.render.filepath = os.path.join(OUT, f"f_{f:04d}.png")
    bpy.ops.render.render(write_still=True)


N = int(round(DUR * FPS))
todo = ONLY if ONLY is not None else list(range(K, N, NN))
t_start = time.time()
for i, f in enumerate(todo):
    if ONLY is None and os.path.exists(os.path.join(OUT, f"f_{f:04d}.png")):
        continue
    frame(f)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t_start) / (i + 1):.2f} s/frame", flush=True)
print(f"done {len(todo)} frames in {time.time() - t_start:.0f} s", flush=True)
