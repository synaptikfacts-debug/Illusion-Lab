# 0021 "Cosmic Swarm" (owner, Nov 15 2026: "like 0011 Singing Pins but not identical"; picked all three concept stills
# (glass curtain, pearl cloud, mirror discs) -> "create a preview with all the 3 mixed", in SPACE colours).
# Reference (0011): 4096 pins in a floor grid rise into patterns. Ours: ONE swarm of 4096 elements in deep space that
# changes form three times - glass-bead curtain -> floating pearl cloud -> mirror-disc wall - and changes material with
# it (glass -> pearl -> mirror). Same formula: every element on its own rhythm, patterns emerge and lock.
# Beat sheet (story seconds; real = story + 1.8 after the cold open + rewind):
#   COLD OPEN (real 0-1): the pearl helix spinning (story 9.4-10.4), it BURSTS at real 0.6; real 1-1.8 fast rewind
#   0-2.6     curtain: 64 strands of glass beads, each swinging at its own rhythm (pendulum wave -> waves emerge)
#   2.6-5.0   the strands lock into a SPIRAL in depth, hold, let go
#   4.8-6.6   the beads leave the strands and float up into a cube cloud, glass turns to pearl
#   7.4-10.0  the cloud twists into a double HELIX that spins
#   10.0-12.2 the helix BURSTS into a hollow sphere that catches itself and turns
#   12.2-13.8 the sphere flattens into a wall facing the lens, pearls flatten into MIRROR discs
#   13.8-17.0 waves run across the mirrors, they lock into a SPIRAL, then RINGS (the pattern is the reflected light)
#   17.2-18.8 ENDING: the discs turn edge-on in a wave from the centre - the wall vanishes - one last glint
#   18.0-19.4 fade to black (real 19.8-21.2)
# Usage: blender -b --factory-startup -P scripts/blender/cosmos.py -- <outdir> <samples> <fps> <k> <n> [frames]
#   env COSMOS_RES=WxH (default 1080x1920)
import math
import os
import sys
import time

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 48
FPS = int(argv[2]) if len(argv) > 2 else 30
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi
DUR = 21.7
OPEN, REWIND = 0.75, 2.2  # v3: a 1.45 s rewind (0.8 s and 1.2 s flickered, photosensitivity check)
rng = np.random.default_rng(2121)


def sm(a, b, x):
    k = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


def story(r):
    if r < OPEN:
        return 10.0 + r  # v4: frame 0 = the intact helix, it BURSTS over the first 0.75 s (story 10.0-10.75)
    if r < REWIND:
        k = (r - OPEN) / (REWIND - OPEN)
        return (10.0 + OPEN) * (1 - k * k * (3 - 2 * k))
    return r - REWIND


# ---------------- scene ----------------
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
scene.cycles.max_bounces = 8
scene.cycles.transmission_bounces = 8
scene.cycles.glossy_bounces = 4
scene.cycles.diffuse_bounces = 2
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.use_persistent_data = True
res = os.environ.get("COSMOS_RES", "1080x1920").split("x")
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.5

# deep space: navy base, a blue + gold nebula, a star field
w = bpy.data.worlds.new("Space")
scene.world = w
w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
wn.clear()
# v7 sky, built to the owner's reference image: near-black space, thin WISPY blue nebula filaments (ridged, distorted
# noise) with magenta in places, dense small crisp white stars, a few bright stars (they get 4-point spikes in the
# compositor). No core glow, no flat wash.
wout = wn.new("ShaderNodeOutputWorld")
wbg = wn.new("ShaderNodeBackground")
wtc = wn.new("ShaderNodeTexCoord")


def node(kind, **inputs):
    n_ = wn.new(kind)
    for k_, v_ in inputs.items():
        n_.inputs[k_].default_value = v_
    return n_


def math_(op, a=None, b=None, clamp=False):
    n_ = wn.new("ShaderNodeMath")
    n_.operation = op
    n_.use_clamp = clamp
    if a is not None:
        n_.inputs[0].default_value = a
    if b is not None:
        n_.inputs[1].default_value = b
    return n_


# filaments: ridged noise 1-|2n-1|, sharpened, so the gas forms thin bright strands with dark gaps
fil = node("ShaderNodeTexNoise", Scale=2.2, Detail=12.0, Roughness=0.62, Distortion=1.6)
f1 = math_("MULTIPLY", b=2.0)
f2 = math_("SUBTRACT", b=1.0)
f3 = math_("ABSOLUTE")
f4 = math_("SUBTRACT", a=1.0)
f5 = math_("POWER", b=7.0)
# where the gas is at all: a large soft mask, so whole regions are empty black space like the reference
cloud = node("ShaderNodeTexNoise", Scale=0.9, Detail=4.0, Roughness=0.5)
cm = wn.new("ShaderNodeMapRange")
cm.inputs["From Min"].default_value = 0.52
cm.inputs["From Max"].default_value = 0.72
gas = math_("MULTIPLY")
# colour: deep blue everywhere, magenta where a second slow noise is high
hue = node("ShaderNodeTexNoise", Scale=1.3, Detail=3.0)
hm = wn.new("ShaderNodeMapRange")
hm.inputs["From Min"].default_value = 0.52
hm.inputs["From Max"].default_value = 0.66
col = wn.new("ShaderNodeMixRGB")
col.inputs[1].default_value = (0.03, 0.08, 0.55, 1)   # nebula blue
col.inputs[2].default_value = (0.22, 0.1, 0.6, 1)    # violet wisps (swirl palette)
neb = wn.new("ShaderNodeMixRGB")
neb.blend_type = "MULTIPLY"
neb.inputs["Fac"].default_value = 1.0
glow = math_("MULTIPLY", b=0.2)  # a faint haze under the strands, so they sit in soft blue light
haze = math_("ADD")
for a_, b_ in ((wtc.outputs["Generated"], fil.inputs["Vector"]), (fil.outputs["Fac"], f1.inputs[0]),
               (f1.outputs[0], f2.inputs[0]), (f2.outputs[0], f3.inputs[0]), (f3.outputs[0], f4.inputs[1]),
               (f4.outputs[0], f5.inputs[0]), (wtc.outputs["Generated"], cloud.inputs["Vector"]),
               (cloud.outputs["Fac"], cm.inputs["Value"]), (cm.outputs["Result"], glow.inputs[0]),
               (f5.outputs[0], haze.inputs[0]), (glow.outputs[0], haze.inputs[1]),
               (haze.outputs[0], gas.inputs[0]), (cm.outputs["Result"], gas.inputs[1]),
               (wtc.outputs["Generated"], hue.inputs["Vector"]), (hue.outputs["Fac"], hm.inputs["Value"]),
               (hm.outputs["Result"], col.inputs["Fac"]), (col.outputs["Color"], neb.inputs[1]),
               (gas.outputs[0], neb.inputs[2])):
    wl.new(a_, b_)
neb_s = wn.new("ShaderNodeVectorMath")
neb_s.operation = "SCALE"
neb_s.inputs["Scale"].default_value = 0.22  # owner: "only the black is missing" - mostly black space
wl.new(neb.outputs["Color"], neb_s.inputs[0])


def starfield(scale, size, mask_scale, thresh, bright):
    v = wn.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = scale
    r_ = wn.new("ShaderNodeValToRGB")
    r_.color_ramp.elements[0].position = 0.0
    r_.color_ramp.elements[0].color = (bright, bright, bright, 1)
    r_.color_ramp.elements[1].position = size
    r_.color_ramp.elements[1].color = (0, 0, 0, 1)
    m_ = wn.new("ShaderNodeTexWhiteNoise")  # random per Voronoi cell: only some cells hold a star
    m_.noise_dimensions = "3D"
    g_ = math_("GREATER_THAN", b=thresh)
    sc = wn.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    wl.new(wtc.outputs["Generated"], v.inputs["Vector"])
    wl.new(v.outputs["Distance"], r_.inputs["Fac"])
    wl.new(v.outputs["Position"], m_.inputs["Vector"])
    wl.new(m_.outputs["Value"], g_.inputs[0])
    wl.new(r_.outputs["Color"], sc.inputs[0])
    wl.new(g_.outputs[0], sc.inputs["Scale"])
    return sc


stars_a = starfield(620.0, 0.085, 0, 0.5, 3.0)    # v8: dense field, visible at phone size
stars_b = starfield(240.0, 0.08, 0, 0.55, 9.0)    # medium, dense: keeps the black sky textured at the edges (Instagram border check)
stars_c = starfield(70.0, 0.018, 0, 0.93, 40.0)   # a few very bright ones -> 4-point spikes in the compositor
acc = neb_s.outputs[0]
for st in (stars_a, stars_b, stars_c):
    ad = wn.new("ShaderNodeVectorMath")
    ad.operation = "ADD"
    wl.new(acc, ad.inputs[0])
    wl.new(st.outputs[0], ad.inputs[1])
    acc = ad.outputs[0]
wl.new(acc, wbg.inputs["Color"])
wbg.inputs["Strength"].default_value = 1.0
wl.new(wbg.outputs[0], wout.inputs[0])

# 4-point star spikes on the brightest points only (the bright stars and the sharpest chrome glints), as in the reference
try:
    if os.environ.get("COSMOS_COMP", "1") != "1":
        raise RuntimeError("compositor disabled by COSMOS_COMP=0")
    if hasattr(scene, "compositing_node_group"):
        ctree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        scene.compositing_node_group = ctree
        c_in = ctree.nodes.new("CompositorNodeRLayers")
        c_out = ctree.nodes.new("NodeGroupOutput")
        ctree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    else:
        scene.use_nodes = True
        ctree = scene.node_tree
        ctree.nodes.clear()
        c_in = ctree.nodes.new("CompositorNodeRLayers")
        c_out = ctree.nodes.new("CompositorNodeComposite")
    gl = ctree.nodes.new("CompositorNodeGlare")
    for attr, val in (("glare_type", "STREAKS"), ("streaks", 4), ("angle_offset", math.radians(45)),
                      ("threshold", 6.0), ("mix", 0.0), ("fade", 0.86), ("quality", "HIGH")):
        if hasattr(gl, attr):
            setattr(gl, attr, val)
    for name, val in (("Type", "Streaks"), ("Streaks", 4), ("Streaks Angle", math.radians(45)), ("Threshold", 6.0),
                      ("Fade", 0.86), ("Strength", 1.0), ("Quality", "High")):
        if name in gl.inputs:
            try:
                gl.inputs[name].default_value = val
            except Exception:
                pass
    try:
        ld_ = ctree.nodes.new("CompositorNodeLensdist")
        if "Dispersion" in ld_.inputs:
            ld_.inputs["Dispersion"].default_value = 0.012
        elif hasattr(ld_, "dispersion"):
            ld_.dispersion = 0.012
        ctree.links.new(c_in.outputs["Image"], ld_.inputs["Image"])
        ctree.links.new(ld_.outputs["Image"], gl.inputs["Image"])
        print("compositor: lens dispersion on")
    except Exception as e_:
        print("compositor: lens dispersion unavailable:", e_)
        ctree.links.new(c_in.outputs["Image"], gl.inputs["Image"])
    ctree.links.new(gl.outputs["Image"], c_out.inputs[0])
    print("compositor: star spikes on")
except Exception as e:  # never block a render on the compositor
    print("compositor: star spikes unavailable:", e)


def principled(name, color, metal=0.0, rough=0.1, coat=0.0, trans=0.0, ior=1.5, sheen=0.0, emit=None, es=0.0):
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


# the swarm material: glass -> pearl -> mirror, blended by two factors set every frame
swarm_m = bpy.data.materials.new("Swarm")
swarm_m.use_nodes = True
sn, sl = swarm_m.node_tree.nodes, swarm_m.node_tree.links
sn.clear()
sout = sn.new("ShaderNodeOutputMaterial")
glass = sn.new("ShaderNodeBsdfPrincipled")
glass.inputs["Base Color"].default_value = (0.92, 0.97, 1.0, 1)
glass.inputs["Transmission Dispersion Scale"].default_value = 1.0
glass.inputs["Transmission Dispersion Abbe Number"].default_value = 18.0
glass.inputs["Transmission Weight"].default_value = 0.0  # v8: clear glass only showed white highlights in space
glass.inputs["Metallic"].default_value = 1.0  # -> polished anodized metal like the other stages
glass.inputs["Roughness"].default_value = 0.06
glass.inputs["IOR"].default_value = 1.52
pearl = sn.new("ShaderNodeBsdfPrincipled")
pearl.inputs["Base Color"].default_value = (0.62, 0.62, 0.68, 1)  # v5: iridescent chrome, not white pearl
pearl.inputs["Metallic"].default_value = 1.0
pearl.inputs["Roughness"].default_value = 0.16
pearl.inputs["Thin Film Thickness"].default_value = 420.0
pearl.inputs["Thin Film IOR"].default_value = 1.38
mirror = sn.new("ShaderNodeBsdfPrincipled")
mirror.inputs["Base Color"].default_value = (0.5, 0.52, 0.58, 1)  # v5: dark chrome that reflects the cosmos
mirror.inputs["Metallic"].default_value = 1.0
mirror.inputs["Roughness"].default_value = 0.025
mirror.inputs["Thin Film Thickness"].default_value = 260.0
mirror.inputs["Thin Film IOR"].default_value = 1.33
mix1 = sn.new("ShaderNodeMixShader")
mix2 = sn.new("ShaderNodeMixShader")
sl.new(glass.outputs[0], mix1.inputs[1])
sl.new(pearl.outputs[0], mix1.inputs[2])
sl.new(mix1.outputs[0], mix2.inputs[1])
sl.new(mirror.outputs[0], mix2.inputs[2])
sl.new(mix2.outputs[0], sout.inputs["Surface"])
# v12 REAL: no two beads alike - per-bead polish jitter (attribute "rj") and fine micro-scratches on all the metal
_rj = sn.new("ShaderNodeAttribute")
_rj.attribute_name = "rj"
for _b, _base in ((glass, 0.05), (pearl, 0.14), (mirror, 0.02)):
    _add = sn.new("ShaderNodeMath")
    _add.operation = "ADD"
    _add.inputs[1].default_value = _base
    sl.new(_rj.outputs["Fac"], _add.inputs[0])
    sl.new(_add.outputs[0], _b.inputs["Roughness"])
_scr = sn.new("ShaderNodeTexNoise")
_scr.inputs["Scale"].default_value = 420.0
_scr.inputs["Detail"].default_value = 6.0
_bmp = sn.new("ShaderNodeBump")
_bmp.inputs["Strength"].default_value = 0.05
sl.new(_scr.outputs["Fac"], _bmp.inputs["Height"])
for _b in (glass, pearl, mirror):
    sl.new(_bmp.outputs["Normal"], _b.inputs["Normal"])
glass.inputs["Thin Film Thickness"].default_value = 320.0
glass.inputs["Thin Film IOR"].default_value = 1.35

# v6 ANODIZED COLOUR (owner: "why is the material white"): every bead is real metal/glass carrying colour - anodized
# titanium graded teal -> blue -> magenta -> gold across the swarm (attribute "hue", set per bead below)
_hue = sn.new("ShaderNodeAttribute")
_hue.attribute_name = "hue"
_hr = sn.new("ShaderNodeValToRGB")
# owner, Nov 15: "I don't see green" -> emerald added: emerald -> blue -> magenta -> gold
# owner, Nov 15 (swirl reference, "for the colors"): mint green -> aqua -> blue -> violet, no magenta/gold
_hstops = ((0.0, (0.45, 1.0, 0.62)), (0.33, (0.08, 0.82, 0.88)), (0.66, (0.12, 0.3, 1.0)), (1.0, (0.42, 0.24, 1.0)))
_hr.color_ramp.elements[0].position, _hr.color_ramp.elements[0].color = _hstops[0][0], (*_hstops[0][1], 1)
_hr.color_ramp.elements[1].position, _hr.color_ramp.elements[1].color = _hstops[-1][0], (*_hstops[-1][1], 1)
for _pos, _col in _hstops[1:-1]:
    _e = _hr.color_ramp.elements.new(_pos)
    _e.color = (*_col, 1)
sl.new(_hue.outputs["Fac"], _hr.inputs["Fac"])
sl.new(_hr.outputs["Color"], pearl.inputs["Base Color"])
sl.new(_hr.outputs["Color"], mirror.inputs["Base Color"])
_gt = sn.new("ShaderNodeMixRGB")  # glass: a light tint of the same colour, so it is coloured glass, not white
_gt.inputs["Fac"].default_value = 1.0
_gt.inputs[1].default_value = (1, 1, 1, 1)
sl.new(_hr.outputs["Color"], _gt.inputs[2])
sl.new(_gt.outputs["Color"], glass.inputs["Base Color"])


def area(name, loc, size, power, color, target=(0, 0, 0), shape="DISK", sy=None):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = shape
    l.size = size
    if sy:
        l.size_y = sy
    l.energy = power
    l.color = color
    o = bpy.data.objects.new(name, l)
    o.location = loc
    o.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False
    scene.collection.objects.link(o)
    return l


area("Key", (-4.5, -6.0, 5.0), 2.0, 450, (0.6, 0.75, 1.0))             # v5: a weak cool starlight fill only
area("VioletRim", (5.5, 2.5, 2.5), 3.0, 1700, (0.5, 0.3, 1.0))         # violet, back right
area("TealRim", (-5.5, 2.5, -1.5), 3.0, 1500, (0.05, 0.75, 1.0))       # teal gas, back left
area("MintCore", (0.0, 6.0, 0.8), 4.0, 1400, (0.5, 1.0, 0.75))         # mint glow straight behind
ORBIT = [(bpy.data.objects[n_], mathutils.Vector(bpy.data.objects[n_].location), bpy.data.objects[n_].data.energy)
         for n_ in ("VioletRim", "TealRim", "MintCore")]
strip = area("Strip", (0.0, -7.5, 3.2), 9.0, 0, (0.4, 0.95, 1.0), shape="RECTANGLE", sy=0.6)  # mirrors catch it
backl = area("Back", (0.0, 4.5, 0.0), 7.0, 0, (0.3, 0.85, 1.0), shape="RECTANGLE", sy=9.0)  # glows through the glass


# v5 STAGE (every approved reel stands on a real surface - 0020 black stone, 0019 smoked glass, 0018 a liquid lake):
# a black mirror-water surface far below the swarm, gently rippled, reflecting the swarm and the nebula sky.
lake = bpy.data.meshes.new("Lake")
lake.from_pydata([(-40, -40, -4.6), (40, -40, -4.6), (40, 60, -4.6), (-40, 60, -4.6)], [], [(0, 1, 2, 3)])
lake_o = bpy.data.objects.new("Lake", lake)
scene.collection.objects.link(lake_o)
lake_m = principled("BlackWater", (0.004, 0.005, 0.008), rough=0.03, coat=0.0)
_ln = lake_m.node_tree.nodes
_bump = _ln.new("ShaderNodeBump")
_bump.inputs["Strength"].default_value = 0.06
_wave = _ln.new("ShaderNodeTexNoise")
_wave.inputs["Scale"].default_value = 2.5
_wave.inputs["Detail"].default_value = 3.0
lake_m.node_tree.links.new(_wave.outputs["Fac"], _bump.inputs["Height"])
lake_m.node_tree.links.new(_bump.outputs["Normal"], _ln["Principled BSDF"].inputs["Normal"])
lake_o.data.materials.append(lake_m)
lake_o.hide_render = True  # v7: open space like the reference, no floor

# distant glowing stars with real depth (bokeh), so no frame edge is ever a flat colour band
bk_m = principled("StarGlow", (0, 0, 0), emit=(1.0, 0.85, 0.6), es=7.0)
bk_b = principled("StarGlowBlue", (0, 0, 0), emit=(0.55, 0.7, 1.0), es=8.0)


def uv_sphere(seg, ring):
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
    return np.array(v), f


def static_instances(name, centers, radii, material):
    pv, pf = uv_sphere(10, 6)
    v = pv[None] * radii[:, None, None] + centers[:, None, :]
    m = len(pv)
    f = [tuple(i * m + k for k in face) for i in range(len(centers)) for face in pf]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.reshape(-1, 3).tolist(), [], f)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(material)
    return o


for nm, mt, n in (("BokehGold", bk_m, 60), ("BokehBlue", bk_b, 80)):
    c = np.stack([rng.uniform(-9, 9, n), rng.uniform(5, 14, n), rng.uniform(-9, 9, n)], 1)
    static_instances(nm, c, rng.uniform(0.04, 0.14, n), mt).hide_render = True  # v7: no bokeh balls

# ---------------- the swarm: 4096 elements in one mesh ----------------
N = 4096
PV, PF = uv_sphere(12, 8)
NV = len(PV)
faces = [tuple(i * NV + k for k in face) for i in range(N) for face in PF]
smesh = bpy.data.meshes.new("Swarm")
smesh.from_pydata(np.zeros((N * NV, 3)).tolist(), [], faces)
smesh.polygons.foreach_set("use_smooth", [True] * len(smesh.polygons))
swarm = bpy.data.objects.new("Swarm", smesh)
scene.collection.objects.link(swarm)
swarm.data.materials.append(swarm_m)
# a zero-strength modifier marks the mesh as deforming, so Cycles also motion-blurs the beads (not only the camera)
_dm = swarm.modifiers.new("DeformTag", "DISPLACE")
_dm.strength = 0.0

# v6 LIGHT LINKING: every lamp lights only the swarm (the water reflects the nebula and the swarm, never a lamp)
_swarm_only = bpy.data.collections.new("SwarmOnly")
_swarm_only.objects.link(swarm)
for _o in scene.objects:
    if _o.type == "LIGHT":
        _o.light_linking.receiver_collection = _swarm_only
        _o.light_linking.blocker_collection = _swarm_only

idx = np.arange(N)
S_, B_ = idx // 64, idx % 64            # strand, bead
# curtain
CX = (S_ / 63 - 0.5) * 4.0
CZ = 3.4 - B_ / 63 * 6.8
HANG = (3.4 - CZ) / 6.8
W_S = TAU * (0.30 + 0.0065 * S_)        # every strand its own rhythm (pendulum wave across the curtain)
PH_S = 0.4 * ((S_ * 0.6180339887) % 1.0)  # one phase per strand (same formula in gen-cosmos-audio.ts)
# cube cloud (x from the strand, z from the bead, so the curtain flows into it without crossing)
IX, IY, IZ = S_ // 4, (S_ % 4) * 4 + B_ % 4, B_ // 4
LAT = np.stack([(IX - 7.5), (IY - 7.5), (7.5 - IZ)], 1) * 0.19
REL_T = 4.8 + 1.2 * rng.random(N)
# helix
U = (IZ * 256 + IY * 16 + IX) / 4096.0
STRAND = ((IX + IY) % 2).astype(float)

_hue_attr = smesh.attributes.new("hue", "FLOAT", "POINT")
_hue_attr.data.foreach_set("value", np.repeat(U, NV).astype(np.float32))
_vr = np.random.default_rng(777)
SIZE_J = _vr.uniform(0.86, 1.14, N)                        # v12: no two beads the same size
_rj_attr = smesh.attributes.new("rj", "FLOAT", "POINT")
_rj_attr.data.foreach_set("value", np.repeat(_vr.uniform(0.0, 0.07, N), NV).astype(np.float32))
DRIFT_F = _vr.uniform(0.35, 0.9, (N, 3)) * TAU             # v12: every bead drifts on its own rhythm
DRIFT_P = _vr.uniform(0, TAU, (N, 3))
BEAT = 2.4                                                 # v12: the swarm's heartbeat (story seconds)


def heartbeat(t):
    ph = (t % BEAT) / BEAT
    return math.exp(-ph * 7.0) * (1 - math.exp(-ph * 45.0))
TUBE = rng.normal(0, 1, (N, 2)) * 0.085
# hollow sphere (Fibonacci, ordered like the helix)
KK = np.argsort(np.argsort(U))
FZ = 1 - 2 * (KK + 0.5) / N
FR = np.sqrt(1 - FZ ** 2)
FPH = KK * math.pi * (3 - math.sqrt(5))
SPH = np.stack([FR * np.cos(FPH), FR * np.sin(FPH), FZ], 1) * 2.05
# mirror wall: rows by latitude, columns by longitude inside each row
COLS = 48
order = np.argsort(-SPH[:, 2], kind="stable")
WALL = np.zeros((N, 3))
for row in range(math.ceil(N / COLS)):
    blk = order[row * COLS:(row + 1) * COLS]
    blk = blk[np.argsort(np.arctan2(SPH[blk, 1], SPH[blk, 0]))]
    for col, e in enumerate(blk):
        WALL[e] = ((col - (COLS - 1) / 2) * 0.086 + 0.043 * (row % 2), 0.0, 3.65 - row * 0.086)
WROW = (3.65 - WALL[:, 2]) / 0.086
WR = np.hypot(WALL[:, 0], WALL[:, 2])
WTH = np.arctan2(WALL[:, 2], WALL[:, 0])
AXIS = np.stack([np.cos(WTH + math.pi / 2), np.zeros(N), np.sin(WTH + math.pi / 2)], 1)  # tangential tilt axis
W_W = TAU * (0.5 + 0.012 * (WALL[:, 0] + 2.1) / 0.086)  # mirror rhythm per column
FACE = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=float)  # local flat axis (z) -> -Y (towards the lens)


def spiral_field(x, z, arms, k):
    r = np.hypot(x, z)
    return np.sin(arms * np.arctan2(z, x) - k * TAU * r) * np.exp(-0.12 * r * r)


def rot_axis(axis, ang):
    k = axis
    c, s = np.cos(ang)[:, None, None], np.sin(ang)[:, None, None]
    Km = np.zeros((len(ang), 3, 3))
    Km[:, 0, 1], Km[:, 0, 2], Km[:, 1, 0] = -k[:, 2], k[:, 1], k[:, 2]
    Km[:, 1, 2], Km[:, 2, 0], Km[:, 2, 1] = -k[:, 0], -k[:, 1], k[:, 0]
    return np.eye(3)[None] + s * Km + (1 - c) * (Km @ Km)


def rotz(p, a):
    c, s = math.cos(a), math.sin(a)
    return np.stack([p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c, p[:, 2]], 1)


def lerp(a, b, k):
    k = np.asarray(k)
    return a * (1 - k)[..., None] + b * k[..., None] if np.ndim(k) else a * (1 - k) + b * k


def state(t):
    """positions (N,3), radius, flatten, tilt angle (N,) and material mix for story time t"""
    # act 1: curtain (pendulum wave, then lock into a spiral in depth)
    swing = 0.75 * HANG * np.sin(W_S * t + PH_S)
    lock = float(sm(2.6, 3.2, t) * (1 - sm(4.4, 5.0, t)))
    target = -1.25 * HANG * spiral_field(CX / 1.2, CZ / 1.2, 2, 0.85)
    cur = np.stack([CX + 0.04 * np.sin(W_S * 0.7 * t), swing * (1 - lock) + target * lock, CZ], 1)
    # act 2a: cube cloud, slowly turning
    lat = rotz(LAT, 0.45 * (t - 5.0))
    k_r = sm(REL_T, REL_T + 1.4, t)
    pos = lerp(cur, lat, k_r)
    pos[:, 2] += 0.7 * np.sin(math.pi * k_r)  # the beads lift as they let go
    # act 2b: double helix, spinning
    spin = 1.7 * (t - 7.4)
    a = U * TAU * 3.0 + STRAND * math.pi + spin
    hel = np.stack([np.cos(a) * 1.0, np.sin(a) * 1.0, (0.5 - U) * 7.0], 1)
    hel[:, 0] += TUBE[:, 0] * np.cos(a)
    hel[:, 1] += TUBE[:, 0] * np.sin(a)
    hel[:, 2] += TUBE[:, 1]
    k_h = sm(7.4 + 0.8 * U, 8.2 + 0.8 * U, t)
    pos = lerp(pos, hel, k_h)
    # act 2c: BURST into a hollow sphere that catches itself and turns
    k_b = sm(10.0, 10.75, t)  # v2: slower burst (0.45 s flickered)
    over = 1 + 0.4 * np.exp(-((t - 10.8) / 0.45) ** 2)
    sph = rotz(SPH, 0.35 * (t - 10.0)) * over
    pos = lerp(pos, sph, k_b)
    # act 3: the sphere flattens into a wall facing the lens; pearls flatten into mirror discs
    k_w = sm(12.2 + 0.012 * WROW, 13.0 + 0.012 * WROW, t)
    pos = lerp(pos, WALL, k_w)
    flat = 1 - 0.82 * float(sm(12.8, 13.8, t))
    rad = 0.04 + 0.022 * float(sm(4.8, 6.4, t)) - 0.019 * float(sm(12.8, 13.8, t))  # v5: bigger, readable beads
    # mirror tilts: waves, then a spiral, then rings; ending: edge-on in a wave from the centre
    wave = 0.55 * np.sin(W_W * t)
    k_sp = float(sm(14.6, 15.2, t) * (1 - sm(15.8, 16.2, t)))
    k_rg = float(sm(16.0, 16.5, t))
    spi = 0.8 * spiral_field(WALL[:, 0] / 1.1, WALL[:, 2] / 1.1, 3, 1.0)
    rng_f = 0.8 * np.sin(2.4 * TAU * WR - 2.0 * (t - 16.0))
    ang = wave * (1 - k_sp) * (1 - k_rg) + spi * k_sp + rng_f * k_rg
    ang *= float(sm(13.4, 13.9, t))
    k_e = sm(17.2 + 0.32 * WR, 17.65 + 0.32 * WR, t)
    ang = ang * (1 - k_e) + (math.pi / 2) * k_e
    mats = (float(sm(5.0, 6.4, t)), float(sm(12.8, 13.8, t)))
    return pos, rad, flat, ang, mats


CAM_KEYS = [  # story t, yaw deg, elevation deg, distance
    (0.0, 22, 4, 9.8), (2.4, 34, 7, 9.8), (4.6, 30, 6, 9.8), (6.6, -18, 12, 9.4), (9.4, 18, 8, 9.6), (11.0, 10, 6, 10.2),
    (12.2, 4, 4, 9.6), (13.8, 3, 2, 9.3), (17.2, 0, 1, 9.3), (19.5, 0, 0, 10.8),
]


def cam_at(t):
    ks = CAM_KEYS
    if t <= ks[0][0]:
        return ks[0][1:]
    for (t0, *a), (t1, *b) in zip(ks, ks[1:]):
        if t <= t1:
            k = float(sm(t0, t1, t))
            return tuple(x + (y - x) * k for x, y in zip(a, b))
    return ks[-1][1:]


cd = bpy.data.cameras.new("Cam")
cd.lens = 40
cd.dof.use_dof = True
cd.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


def apply(r):
    t = story(r)
    pos, rad, flat, ang, (m1, m2) = state(t)
    # v12 ALIVE: each bead drifts on its own rhythm (smaller once it is a mirror disc), the swarm swells on a heartbeat
    pos = pos + (0.009 - 0.005 * m2) * np.sin(DRIFT_F * t + DRIFT_P)  # subtle shimmer, keeps the structure crisp
    hb = heartbeat(t)
    pos = pos * (1 + 0.022 * hb)
    R = rot_axis(AXIS, ang) @ FACE[None]
    local = PV[None] * np.array([rad, rad, rad * flat])[None, None]
    v = np.einsum("nij,kj->nki", R, local[0]) * SIZE_J[:, None, None] + pos[:, None, :]
    for _o, _home, _e in ORBIT:  # the coloured lights circle slowly -> reflections slide over the metal; pulse on the beat
        _a = 0.5 * math.sin(0.25 * t)  # swing +-30 deg, never round to the front (v12 test blew out the sphere)
        _o.location = (_home.x * math.cos(_a) - _home.y * math.sin(_a), _home.x * math.sin(_a) + _home.y * math.cos(_a), _home.z)
        _o.rotation_euler = (mathutils.Vector((0, 0, 0)) - _o.location).to_track_quat("-Z", "Y").to_euler()
        _o.data.energy = _e * (1 + 0.3 * hb)
    smesh.vertices.foreach_set("co", v.astype(np.float32).ravel())
    smesh.update()
    mix1.inputs["Fac"].default_value = m1
    mix2.inputs["Fac"].default_value = m2
    strip.energy = 700 * m2           # the mirrors need a long light to flash
    backl.energy = 600 * (1 - m1)    # backlight glowing through the glass curtain
    yaw, elv, dist = cam_at(t)
    if r < OPEN:  # v5 hook: the camera right beside the helix - the burst flies at and past the lens
        dist = 7.2 + 0.8 * float(sm(0.0, OPEN, r))  # the whole helix in shot, crisp on frame 0; it bursts mid-frame
        elv = 6.0
    yaw += 0.9 * math.sin(0.6 * t)          # v12: a gentle camera drift, never locked off
    elv += 0.5 * math.sin(0.45 * t + 1.0)
    yaw, elv = math.radians(yaw), math.radians(elv)
    look = mathutils.Vector((0, 0, 0))
    p = look + mathutils.Vector((math.sin(yaw) * math.cos(elv), -math.cos(yaw) * math.cos(elv), math.sin(elv))) * dist
    cam.location = p
    cam.rotation_euler = (look - p).to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = (look - p).length
    cd.dof.aperture_fstop = 5.6
    # v3 tape-rewind look: the picture dims smoothly while time runs backwards (also keeps the fast rewind under
    # the photosensitivity limit - smaller brightness steps per cell)
    dim = float(sm(OPEN - 0.15, OPEN + 0.25, r) * (1 - sm(REWIND - 0.35, REWIND + 0.1, r)))
    scene.view_settings.exposure = 0.5 - 1.4 * dim


def on_frame(scn, *_):
    apply((scn.frame_current + scn.frame_subframe) / FPS)


# MOTION BLUR (photosensitivity: thousands of small fast beads flickered cell by cell). Cycles' own motion blur only
# blurred the camera - the swarm is rebuilt by script each frame, so it never saw the beads move (tested, v3). Instead,
# fast frames are ACCUMULATED: rendered at several moments across a full-frame shutter and averaged, exactly what a real
# shutter does. The number of sub-frames follows how far the beads travel during the frame; calm frames render once.
scene.render.fps = FPS
scene.render.use_motion_blur = False
scene.frame_start, scene.frame_end = 0, int(round(DUR * FPS))
SUB_STEP = float(os.environ.get("COSMOS_SUBSTEP", "0.035"))  # max bead travel (world units) per sub-frame
SUB_MAX = int(os.environ.get("COSMOS_SUBMAX", "12"))


def travel(r):
    """largest bead displacement across one frame centred on real time r (world units)"""
    a, b = state(story(r - 0.5 / FPS))[0], state(story(r + 0.5 / FPS))[0]
    return float(np.percentile(np.linalg.norm(b - a, axis=1), 95))


def render_to(path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def frame(f):
    r = f / FPS
    subs = int(np.clip(math.ceil(travel(r) / SUB_STEP), 1, SUB_MAX))
    span = 1.0  # shutter, in frames
    if r < OPEN + 0.1:  # cold-open burst on black flickered: a long exposure (3 frames) draws it as smooth light streaks
        subs, span = 16, 1.5
    if os.environ.get("COSMOS_MODE", "reel2") in ("impact", "reel2") and r < T_HIT + 0.05:  # the meteor streaks in: full shutter
        subs = max(subs, 10)
    if "span_at" in globals():  # reel2: longer exposure on the fast beats (flash-safe light streaks)
        _sp = span_at(r)
        if _sp > span:
            span, subs = _sp, max(subs, int(8 * _sp))
    out = os.path.join(OUT, f"f_{f:04d}.png")
    if subs == 1:
        apply(r)
        render_to(out)
        return
    scene.cycles.samples = max(12, int(SAMPLES * 2 / subs))  # averaging the sub-frames cleans up the rest of the noise
    acc = None
    for j in range(subs):
        apply(r + ((j + 0.5) / subs - 0.5) * span / FPS)
        tmp = os.path.join(OUT, f"_sub_{f:04d}_{j}.png")
        render_to(tmp)
        img = bpy.data.images.load(tmp)
        px = np.empty(len(img.pixels), dtype=np.float32)
        img.pixels.foreach_get(px)
        acc = px if acc is None else acc + px
        bpy.data.images.remove(img)
        os.remove(tmp)
    scene.cycles.samples = SAMPLES
    res_img = bpy.data.images.new(f"acc_{f}", scene.render.resolution_x, scene.render.resolution_y)
    res_img.pixels.foreach_set(acc / subs)
    res_img.filepath_raw = out
    res_img.file_format = "PNG"
    res_img.save()
    bpy.data.images.remove(res_img)
    print(f"frame {f}: {subs} sub-frames", flush=True)


# ---------------- IMPACT TEST (owner, Nov 15 2026: v12 preview was "boring as hell" - a chain of morphs, nothing HAPPENS)
# COSMOS_MODE=impact renders the proposed new opening as a ~2.5 s motion test: the mirror wall (locked in its spiral),
# a chrome meteor flies in past the lens and SLAMS into it -> a crater punches in, a shockwave ring ripples outward
# through all 4096 mirror discs (their tilt makes the reflections flash in a ring), discs near the hit are flung at the
# camera, the camera shakes. Same look, materials and accumulated motion blur as the reel.
MODE = os.environ.get("COSMOS_MODE", "reel2")  # reel2 = the impact-driven reel (owner, Nov 15); story = the retired morph story
if MODE in ("impact", "reel2"):
    DUR = 2.5
    T_HIT = 0.42
    HIT = np.array([0.35, 0.0, 0.55])
    M_FROM = np.array([4.5, -3.0, 5.5])            # upper right, diagonally across the frame - you see it coming
    _hd = np.hypot(WALL[:, 0] - HIT[0], WALL[:, 2] - HIT[2])
    _hth = np.arctan2(WALL[:, 2] - HIT[2], WALL[:, 0] - HIT[0])
    _hax = np.stack([np.cos(_hth + math.pi / 2), np.zeros(N), np.sin(_hth + math.pi / 2)], 1)  # tilt axis around the hit
    _rad_dir = np.stack([np.cos(_hth), np.zeros(N), np.sin(_hth)], 1)
    _deb = np.clip(1 - _hd / 0.85, 0, 1)            # discs inside the crater rim become debris
    _deb_v = _rad_dir * (3.2 * _deb)[:, None] + np.array([0, -2.0, 0.6]) * _deb[:, None] + rng.normal(0, 0.5, (N, 3)) * _deb[:, None]
    _deb_spin = rng.uniform(6, 14, N)
    _spi = 0.8 * spiral_field(WALL[:, 0] / 1.1, WALL[:, 2] / 1.1, 3, 1.0)
    meteor_m = principled("Meteor", (0.35, 0.36, 0.42), metal=1.0, rough=0.18, coat=0.4)
    meteor_m.node_tree.nodes["Principled BSDF"].inputs["Thin Film Thickness"].default_value = 380.0
    _mv, _mf = uv_sphere(48, 24)
    _mme = bpy.data.meshes.new("Meteor")
    _mme.from_pydata((_mv * 0.5).tolist(), [], _mf)
    _mme.polygons.foreach_set("use_smooth", [True] * len(_mme.polygons))
    meteor = bpy.data.objects.new("Meteor", _mme)
    scene.collection.objects.link(meteor)
    meteor.data.materials.append(meteor_m)
    _swarm_only.objects.link(meteor)  # the lamps light it too

    def story(r):  # noqa: F811 - real time = test time
        return r

    def impact_state(t):
        a = t - T_HIT
        pos = WALL.copy()
        ang = _spi.copy()
        axis = AXIS.copy()
        if a > 0:
            front = 3.0 * a                                        # the shockwave ring rolls outward
            ring = np.exp(-((_hd - front) / 0.45) ** 2) * math.exp(-0.6 * a)
            crater = 0.85 * np.exp(-(_hd / 0.5) ** 2) * math.exp(-1.6 * a) * float(sm(0.0, 0.06, a))
            pos[:, 1] += 1.1 * ring + crater                       # pushed back, away from the lens
            wob = ring * np.sin(TAU * (_hd - front) / 0.8) * 1.8   # alternating tilt -> rings of flashing reflections (front view)
            ang = ang * (1 - np.clip(ring * 2, 0, 1)) + wob
            axis = np.where((ring > 0.05)[:, None], _hax, axis)
            pos += _deb_v * a * _deb[:, None] * (_deb > 0)[:, None]  # debris flung at the camera
            ang = ang + _deb * _deb_spin * a
        return pos, ang, axis

    def state(t):  # noqa: F811 - used by travel() for the motion-blur sub-frame count
        return impact_state(t)[0], None, None, None, None

    def apply(r):  # noqa: F811
        t = r
        pos, ang, axis = impact_state(t)
        pos = pos + 0.004 * np.sin(DRIFT_F * t + DRIFT_P)
        R = rot_axis(axis, ang) @ FACE[None]
        local = PV * np.array([0.043, 0.043, 0.043 * 0.18])[None]
        v = np.einsum("nij,kj->nki", R, local) * SIZE_J[:, None, None] + pos[:, None, :]
        smesh.vertices.foreach_set("co", v.astype(np.float32).ravel())
        smesh.update()
        mix1.inputs["Fac"].default_value = 1.0
        mix2.inputs["Fac"].default_value = 1.0
        strip.energy = 700
        backl.energy = 0
        k = min(1.0, t / T_HIT)
        mp = M_FROM + (HIT - M_FROM) * (k ** 1.15)                  # accelerating in
        if t > T_HIT:                                               # punches through and is gone behind the wall
            mp = HIT + (HIT - M_FROM) / np.linalg.norm(HIT - M_FROM) * 6.0 * (t - T_HIT)
        meteor.location = tuple(mp)
        meteor.rotation_euler = (3.0 * t, 1.7 * t, 0.0)
        meteor.hide_render = t > T_HIT + 0.35
        a = t - T_HIT
        shake = 0.07 * math.exp(-a * 5.0) * (a > 0)
        yaw = math.radians(7 + 1.0 * t + shake * 60 * math.sin(a * 55))    # owner: in FRONT of the wall (a hair off-axis keeps depth)
        elv = math.radians(4 + shake * 40 * math.sin(a * 47 + 1))
        dist = 11.2 - 0.8 * float(sm(0, DUR, t))                    # the whole wall in black space, slow push-in
        look = mathutils.Vector((0.0, 0.0, 0.0))
        p = look + mathutils.Vector((math.sin(yaw) * math.cos(elv), -math.cos(yaw) * math.cos(elv), math.sin(elv))) * dist
        cam.location = p
        cam.rotation_euler = (look - p).to_track_quat("-Z", "Y").to_euler()
        cd.dof.focus_distance = (mathutils.Vector(tuple(HIT)) - p).length
        cd.dof.aperture_fstop = 4.0
        scene.view_settings.exposure = 0.5

    OPEN = 0.0  # no cold open / rewind in the test: frame() gives fast frames the adaptive shutter
    scene.frame_end = int(round(DUR * FPS))

# ---------------- REEL2: the impact-driven reel (owner, Nov 15 2026: "yes, build it" after the front impact test) ----
# Every ~1.5 s an EVENT with a visible cause (the v12 morph story was "boring as hell"). Real time = story time.
#   0-0.42 meteor in   0.42 HIT 1: crater + shockwave ring   1.9 SHATTER: the wall bursts at the camera, discs tumble
#   4-7.5 VORTEX (owner's swirl image): mint outside -> violet inside, spinning faster until the beads draw streaks
#   7.6 HIT 2: a pulse from the centre slams a ring wave through the vortex, beads ricochet out and snap back
#   9.4-11 COLLAPSE: the vortex spirals into one blinding point   11.0 RELEASE: the point bursts into a thin ring
#   12.5-15 the ring turns slowly and settles; the reel fades 13.4-14.9
if MODE == "reel2":
    # owner, Nov 15: "change the opening - NOT a sheet of paper with something exploding into it" -> no wall, no meteor.
    # COLD OPEN on the climax (the vortex spiralling into a blinding star), a fast rewind, then the story from a SEED.
    # Story seconds (real = story + 2.0 after the cold open):
    #   0-0.5 a small glowing seed of beads pulses   0.5 BURST: beads fly out in every direction, some at the lens
    #   2.6-4.0 they whip into the VORTEX (owner's swirl image)   3.6-6.0 it spins up into light streaks
    #   6.2 HIT 2: a ring wave slams through, beads ricochet and snap back   8.0-9.6 COLLAPSE into a blinding point
    #   9.6 RELEASE: the point bursts into a thin ring   11-13.6 it turns slowly and settles (reel fades)
    T_B, T_VX, T_H2, T_CL, T_RL, T_END = 0.5, 2.6, 6.2, 8.0, 9.6, 13.6
    OPEN, REWIND = 0.75, 2.0
    DUR = T_END + REWIND
    meteor.hide_render = True
    _vr2 = np.random.default_rng(2122)
    SEED = SPH * 0.3                                               # a dense ball, radius ~0.6
    _dir = SEED / (np.linalg.norm(SEED, axis=1, keepdims=True) + 1e-6)
    V_B = _dir * _vr2.uniform(1.6, 3.6, N)[:, None] + np.array([0.0, -1.2, 0.0]) * _vr2.uniform(0.0, 1.8, N)[:, None] \
        + _vr2.normal(0, 0.3, (N, 3))
    R_V = 2.55 - 1.55 * U + _vr2.normal(0, 0.07, N)                # colour bands by radius: mint outside, violet inside
    TH0 = np.arctan2(SEED[:, 2], SEED[:, 0]) + _vr2.normal(0, 0.15, N)
    Y_V = _vr2.normal(0, 0.1, N)
    ARM = 0.1 * np.sin(2 * TH0)
    RIC = (_vr2.random(N) < 0.3).astype(float)  # v2c: hit 2 must read - more beads, harder ricochet
    V_RIC = np.stack([_vr2.normal(0, 1.8, N), _vr2.uniform(-4.2, -1.6, N), _vr2.normal(0, 1.8, N)], 1)
    R_RING = 2.3 * _vr2.uniform(0.88, 1.12, N)  # v2c: the release ring stays inside the frame
    _ts = np.arange(0, T_END + 0.5, 0.002)
    _om = 0.7 + 2.6 * sm(3.6, 6.0, _ts) + 4.5 * sm(T_CL, T_RL, _ts) - 6.4 * sm(T_RL, T_RL + 1.6, _ts)
    _om = np.maximum(_om, 0.25)
    _phi = np.cumsum(_om) * 0.002

    def PHI(t):
        return float(np.interp(t, _ts, _phi))

    core_m = principled("Core", (0, 0, 0), emit=(0.7, 1.0, 0.95), es=0.0)
    _cv, _cf = uv_sphere(24, 12)
    _cme = bpy.data.meshes.new("Core")
    _cme.from_pydata((_cv * 0.12).tolist(), [], _cf)
    _cme.polygons.foreach_set("use_smooth", [True] * len(_cme.polygons))
    core_o = bpy.data.objects.new("Core", _cme)
    scene.collection.objects.link(core_o)
    core_o.data.materials.append(core_m)
    core_bsdf = core_m.node_tree.nodes["Principled BSDF"]

    def story(r):  # noqa: F811 - cold open on the collapse (story 8.0 -> 9.6 in 0.75 s), rewind, then the story
        if r < OPEN:
            return 8.0 + (T_RL - 8.0) * (r / OPEN)
        if r < REWIND:
            k = (r - OPEN) / (REWIND - OPEN)
            return T_RL * (1 - k * k * (3 - 2 * k))
        return r - REWIND

    def reel_state(t):
        """positions, radius, core strength"""
        # the seed pulses once, then BURSTS
        pulse = 1 + 0.12 * math.exp(-((t - 0.3) / 0.09) ** 2)
        a = max(0.0, t - T_B)
        fl = (1 - math.exp(-1.25 * a)) / 1.25
        burst = SEED * pulse + V_B * fl
        phi = PHI(t)
        th = TH0 + phi * (1.9 / R_V)                                # inner beads orbit faster -> swirl
        rv = R_V * (1 + ARM * np.cos(th - TH0))
        a2 = t - T_H2
        if a2 > 0:
            front = 0.6 + 3.2 * a2
            rv = rv + 1.0 * np.exp(-((R_V - front) / 0.32) ** 2) * math.exp(-0.9 * a2)  # v2c: twice as strong
        c = 1.0 - float(sm(T_CL, T_RL, t)) ** 0.85
        rv = rv * c + 0.015
        vx = np.stack([rv * np.cos(th), Y_V * c, rv * np.sin(th)], 1)
        if a2 > 0:
            vx = vx + RIC[:, None] * V_RIC * (a2 * math.exp(-2.2 * a2))
        k_v = sm(T_VX + 0.25 * U, T_VX + 1.3 + 0.25 * U, t)
        pos = burst * (1 - k_v)[:, None] + vx * k_v[:, None]
        rad = 0.05
        core = 0.0
        if t > T_CL + 0.6:
            core = 60.0 * float(sm(T_CL + 0.6, T_RL, t)) * (1 - float(sm(T_RL + 0.05, T_RL + 1.4, t)))
        core += 6.0 * math.exp(-((t - 0.3) / 0.12) ** 2)            # the seed's pulse glows
        a3 = t - T_RL
        if a3 > 0:
            rr = 0.02 + R_RING * (1 - math.exp(-2.4 * a3))
            thr = TH0 + phi * 0.3
            ring = np.stack([rr * np.cos(thr), Y_V * 0.2, rr * np.sin(thr)], 1)
            k_g = float(sm(T_RL, T_RL + 0.15, t))
            pos = pos * (1 - k_g) + ring * k_g
            rad = rad * (1 - 0.3 * float(sm(T_RL, T_RL + 1.0, t)))
        rad = rad * (1 - 0.45 * float(sm(T_CL, T_RL, t)) * (1 - float(sm(T_RL, T_RL + 0.6, t))))
        return pos, rad, core

    def state(t):  # noqa: F811 - used by travel() for the adaptive shutter
        return reel_state(t)[0], None, None, None, None

    CAM2 = [  # story t, yaw, elev, dist
        (0.0, 6, 5, 6.2), (0.5, 6, 5, 6.2), (2.4, 8, 8, 9.6), (4.0, 14, 10, 11.0), (6.0, 20, 13, 11.2),
        (8.0, 16, 11, 11.0), (9.6, 12, 10, 7.0), (11.2, 8, 8, 10.6), (13.6, 4, 6, 11.8),  # vortex (~5.2 wide) fully in frame
    ]

    def cam2(t):
        for (t0, *a_), (t1, *b_) in zip(CAM2, CAM2[1:]):
            if t <= t1:
                k = float(sm(t0, t1, t))
                return [x + (y - x) * k for x, y in zip(a_, b_)]
        return CAM2[-1][1:]

    def span_at(r):
        """longer exposure where thousands of beads move fast on black (flash check): rewind, burst, hit 2, collapse"""
        t = story(r)
        rew = 3.0 * float(sm(OPEN - 0.05, OPEN + 0.1, r) * (1 - sm(REWIND - 0.1, REWIND + 0.05, r)))
        if r < REWIND:
            return max(1.0, rew)
        return max(1.0, 2.2 * float(sm(T_B - 0.05, T_B + 0.15, t) * (1 - sm(T_B + 1.2, T_B + 1.8, t))),
                   1.8 * float(sm(T_H2 - 0.05, T_H2 + 0.1, t) * (1 - sm(T_H2 + 0.8, T_H2 + 1.2, t))),
                   2.0 * float(sm(T_CL + 0.6, T_CL + 1.0, t) * (1 - sm(T_RL + 0.6, T_RL + 1.0, t))))

    def apply(r):  # noqa: F811
        t = story(r)
        pos, rad, core = reel_state(t)
        pos = pos + 0.005 * np.sin(DRIFT_F * t + DRIFT_P)
        local = PV * rad
        v = local[None] * SIZE_J[:, None, None] + pos[:, None, :]
        smesh.vertices.foreach_set("co", v.astype(np.float32).ravel())
        smesh.update()
        mix1.inputs["Fac"].default_value = 1.0
        mix2.inputs["Fac"].default_value = 0.0                      # iridescent anodized beads throughout
        strip.energy = 0
        backl.energy = 0
        core_bsdf.inputs["Emission Strength"].default_value = core
        core_o.hide_render = core <= 0.01
        shake = 0.0
        for th_, amp in ((T_B, 0.06), (T_H2, 0.06), (T_RL, 0.05)):
            a_ = t - th_
            if a_ > 0 and r >= REWIND:
                shake += amp * math.exp(-a_ * 5.0) * math.sin(a_ * 55 + th_)
        yaw_, elv_, dist_ = cam2(t)
        yaw = math.radians(yaw_ + shake * 60)
        elv = math.radians(elv_ + shake * 40)
        look = mathutils.Vector((0.0, 0.0, 0.0))
        p = look + mathutils.Vector((math.sin(yaw) * math.cos(elv), -math.cos(yaw) * math.cos(elv), math.sin(elv))) * dist_
        cam.location = p
        cam.rotation_euler = (look - p).to_track_quat("-Z", "Y").to_euler()
        cd.dof.focus_distance = (look - p).length
        cd.dof.aperture_fstop = 4.0
        dim = float(sm(OPEN - 0.1, OPEN + 0.2, r) * (1 - sm(REWIND - 0.3, REWIND + 0.05, r)))  # tape-rewind dim
        scene.view_settings.exposure = 0.5 - 1.4 * dim

    T_HIT = -1.0  # no meteor in reel2 (frame() checks it)
    scene.frame_end = int(round(DUR * FPS))

NF = int(round(DUR * FPS))
todo = ONLY if ONLY is not None else list(range(K, NF, NN))
t0 = time.time()
for i, f in enumerate(todo):
    if ONLY is None and os.path.exists(os.path.join(OUT, f"f_{f:04d}.png")):
        continue
    frame(f)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t0) / (i + 1):.2f} s/frame", flush=True)
