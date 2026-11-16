# 0023 "Mercury learned to dance" (owner, Nov 16 2026: "make it incredible, with effects that keep everyone to the end").
# Liquid-chrome (mercury) drops on a black glass drum, magenta + lime light, white strip panels for reflections
# (look approved on the concept stills, scripts/blender/concepts_0023.py). The drops are METABALLS, so when two touch
# they fuse with a real liquid neck. Real-time story (s):
#  0-0.6    HOOK: a bass hit has thrown 64 drops into the air - frozen mid-flight, close and low
#  0.6-1.6  fast rewind: they fall back onto the glass (time runs backwards)
#  2.0-6.0  every bass pulse makes them tremble and hop on the drum
#  6.0-12   the vibration sorts them: a RING (6-8) -> neighbours merge -> a SPIRAL (8-10) -> merge -> a STAR (10-12)
#  12-15.6  the last 8 orbit faster and faster, merging 8 -> 4 -> 2 -> 1 with a splash crown of droplets
#  15.6-20  ONE big mirror sphere wobbles, the splash droplets roll back into it, it settles, fade
# Usage: blender -b --factory-startup -P scripts/blender/mercury_dance.py -- <outDir> [samples] [fps] [k] [n] [only]
#        MD_EVENTS=1 writes src/scenes/mercury/events.json (merges, beats, splash) for the sound and quits.
import json
import math
import os
import sys
import time

import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 48
FPS = int(argv[2]) if len(argv) > 2 else 60
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TAU = 2 * math.pi
DUR = 20.0

N0 = 32                      # drops at the start (32 bigger drops read better than 64 dots - swipe test)
R0 = 0.11                    # radius of one drop
GROW = 1.42                  # radius growth per merge (a little more than volume, so the payoff sphere is big)
MERGE_T = [8.0, 10.0, 12.0, 13.9, 15.6]         # level L -> L+1 (pairs merge): 32 -> 16 -> 8 -> 4 -> 2 -> 1
NL = len(MERGE_T)
BEATS = [2.0, 2.8, 3.6, 4.4, 5.2]               # bass pulses: the drops hop
VIB = [6.4, 7.2, 8.6, 9.4, 10.6, 11.4]          # gentle pulses during the patterns (a ripple through the drops)
NSPL = 14                                        # splash droplets at the final merge

rng = np.random.default_rng(2323)


def sm(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ---------------- layouts ----------------
# scattered resting positions (well spaced, so metaballs don't fuse by accident)
SCAT = []
while len(SCAT) < N0:
    a, rr = rng.uniform(0, TAU), 2.1 * math.sqrt(rng.uniform(0.02, 1))
    p = np.array([rr * math.cos(a), rr * math.sin(a)])
    if all(np.linalg.norm(p - q) > 0.45 for q in SCAT):
        SCAT.append(p)
SCAT = np.array(SCAT)
# ring order by angle so each drop slides to the nearest ring slot (no crossings)
ORDER = list(np.argsort(np.arctan2(SCAT[:, 1], SCAT[:, 0])))
for _k in range(0, N0, 2):  # in each angular pair the farther drop takes the outer slot
    if np.hypot(*SCAT[ORDER[_k]]) < np.hypot(*SCAT[ORDER[_k + 1]]):
        ORDER[_k], ORDER[_k + 1] = ORDER[_k + 1], ORDER[_k]
SLOT = np.empty(N0, int)
SLOT[ORDER] = np.arange(N0)
HOP_H = rng.uniform(0.25, 0.75, N0)
HOP_D = rng.uniform(0.0, 0.12, N0)
FLY_H = rng.uniform(0.6, 2.4, N0)


def radius(level):
    return R0 * GROW ** level


def layout(level, j, t):
    """where drop j of a merge level sits at time t (x, y)"""
    rot = 0.08 * t
    if level == 0:   # a double ring of 32: slot 2k outer, 2k+1 inner at the same angle (radial pairs merge)
        a = TAU * (j // 2) / (N0 // 2) + rot
        rr = 1.75 if j % 2 == 0 else 1.08
        return np.array([rr * math.cos(a), rr * math.sin(a)])
    if level == 1:   # a two-arm spiral of 16
        arm, k = j // 8, j % 8   # consecutive drops are neighbours on the same arm (they merge in pairs)
        rr = 0.85 + 1.25 * (k / 7)
        a = arm * math.pi + k * 0.72 + rot * 1.4
        return np.array([rr * math.cos(a), rr * math.sin(a)])
    if level == 2:   # a 4-point star of 8 (tips and valleys alternate)
        a = TAU * j / 8 - rot * 1.2
        rr = 1.6 if j % 2 == 0 else 0.95
        return np.array([rr * math.cos(a), rr * math.sin(a)])
    # levels 3..: orbit, faster and tighter until they all meet
    n = N0 >> level
    shrink = 1 - sm(12.0, 15.6, t)
    rr = (0.25 + 1.2 * shrink) if n > 1 else 0.0
    spin = 0.6 * (t - 12) + 0.55 * max(0.0, t - 12) ** 2
    a = TAU * j / n + spin
    return np.array([rr * math.cos(a), rr * math.sin(a)])


def level_at(t):
    lv = 0
    for m in MERGE_T:
        if t >= m:
            lv += 1
    return lv


def pos(level, j, t):
    """position of drop j at merge level `level`, including the convergence before its merge and the
    blend from its children's meeting point after its own birth"""
    p = layout(level, j, t)
    if level < NL:
        tm = MERGE_T[level]
        # converge with its partner just before the merge (they roll into each other)
        if tm - 0.55 < t < tm:
            partner = j ^ 1
            c = 0.5 * (layout(level, j, t) + layout(level, partner, t))
            k = sm(tm - 0.55, tm, t)
            p = p * (1 - k) + c * k
    if level > 0:
        tb = MERGE_T[level - 1]
        if t < tb + 0.9:   # just born from two children: glide from their meeting point to its own slot
            c = 0.5 * (layout(level - 1, 2 * j, tb) + layout(level - 1, 2 * j + 1, tb))
            k = sm(tb, tb + 0.9, t)
            p = c * (1 - k) + p * k
    return p


def leaf_state(i, t):
    """leaf i (0..63): returns (x, y, z, radius, squash) or None when this leaf is not the visible drop of its group"""
    if t < 6.0:
        # scattered: cold open in the air, rewind down, hops on the beats, slide to the ring from 6.0
        x, y = SCAT[i]
        z, sq = 0.0, 0.62
        if t < 0.6:
            z = FLY_H[i] * (0.92 + 0.08 * t / 0.6)
            sq = 1.25
        elif t < 1.6:
            k = (t - 0.6) / 1.0
            k = k * k * (3 - 2 * k)
            z = FLY_H[i] * (1 - k)
            sq = 1.25 - 0.63 * k
        else:
            for b in BEATS:
                a = t - b - HOP_D[i]
                if 0 < a < 0.5:
                    z += HOP_H[i] * 4 * (a / 0.5) * (1 - a / 0.5)
                    sq = 0.62 + 0.5 * math.sin(math.pi * a / 0.5)
            # tremble between hops
            sq += 0.04 * math.sin(TAU * 7 * t + i)
        return (x, y, z, R0, sq)
    lv = level_at(t)
    j = SLOT[i] >> lv if lv < NL else 0
    group = 1 << lv
    if lv < NL and (SLOT[i] % group) != 0:
        return None
    if lv == NL and SLOT[i] != 0:
        return None
    if lv == 0:
        p = pos(0, SLOT[i], t)
        k = sm(6.0, 7.4, t)
        x, y = SCAT[i] * (1 - k) + p * k
    else:
        x, y = pos(lv, j, t)
    r = radius(lv)
    # wobble after its birth (a real liquid oscillation that decays)
    sq = 0.7 if lv < NL else 0.82
    if lv > 0:
        a = t - MERGE_T[lv - 1]
        if a > 0:
            sq += 0.22 * math.exp(-a * (2.2 if lv == NL else 3.5)) * math.sin(TAU * (2.6 if lv == NL else 4.0) * a)
    # gentle vibration pulses during the patterns
    z = 0.0
    for v in VIB:
        a = t - v - 0.06 * (math.hypot(x, y))
        if 0 < a < 0.35:
            z += 0.1 * 4 * (a / 0.35) * (1 - a / 0.35)
    return (x, y, z, r, sq)


# the splash crown: droplets thrown out by the final merge, they arc, land and roll back into the sphere
SPL = [dict(a=TAU * k / NSPL + rng.uniform(-0.15, 0.15), v=rng.uniform(1.2, 2.0), h=rng.uniform(0.6, 1.3),
            r=rng.uniform(0.04, 0.075)) for k in range(NSPL)]


def splash_state(k, t):
    s = SPL[k]
    t0 = MERGE_T[-1] + 0.05
    a = t - t0
    if a < 0 or a > 3.2:
        return None
    fly = 0.7
    if a < fly:
        d = s["v"] * a
        z = 0.35 + s["h"] * 4 * (a / fly) * (1 - a / fly) * 0.8 - 0.35 * a / fly
        return (d * math.cos(s["a"]), d * math.sin(s["a"]), max(0.0, z), s["r"], 1.2)
    back = sm(fly + 0.4, 3.0, a)
    d = s["v"] * fly * (1 - back) + 0.3 * back
    return (d * math.cos(s["a"]), d * math.sin(s["a"]), 0.0, s["r"] * (1 - 0.6 * back), 0.62)


if os.environ.get("MD_EVENTS"):
    merges = []
    for lv, tm in enumerate(MERGE_T):
        merges.append(dict(t=tm, level=lv + 1, count=N0 >> (lv + 1)))
    ev = dict(duration=DUR, open=[0, 0.6], rewind=[0.6, 1.6], beats=BEATS, vib=VIB, merges=merges,
              ring=[6.0, 8.0], spiral=[8.0, 10.0], star=[10.0, 12.0], orbit=[12.0, 15.6], splash=MERGE_T[-1],
              splashLand=[MERGE_T[-1] + 0.75 + 0.05 * k for k in range(NSPL)], settle=[15.6, 18.6], fade=[18.4, 19.9])
    os.makedirs(os.path.join(ROOT, "src", "scenes", "mercury"), exist_ok=True)
    json.dump(ev, open(os.path.join(ROOT, "src", "scenes", "mercury", "events.json"), "w"), indent=1)
    print("wrote events.json")
    sys.exit(0)

# ---------------- the scene (look from concepts_0023.py) ----------------
import bpy  # noqa: E402
import mathutils  # noqa: E402

os.makedirs(OUT, exist_ok=True)
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
scene.cycles.glossy_bounces = 8
scene.render.use_persistent_data = True
res = os.environ.get("MD_RES", "1080x1920").split("x")
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.75  # brighter silver (swipe test: dark drops read as black dots)

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
cr.color_ramp.elements.new(0.62).color = (0.012, 0.0, 0.008, 1)
cr.color_ramp.elements[-1].position = 0.85
cr.color_ramp.elements[-1].color = (0.004, 0.012, 0.0, 1)
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


mercury = principled("Mercury", (0.92, 0.92, 0.95), metal=1.0, rough=0.025, film=120.0)
glass = principled("BlackGlass", (0.003, 0.003, 0.004), rough=0.03, coat=0.35)
glass.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.14  # satin: the panels blur into soft glows, no white bars

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


S = 1.35  # the stage is bigger than in the concept stills (64 drops spread wider)
area("KeyMagenta", (-3.5 * S, -2.5 * S, 3.5 * S), (0, 0, 0.3), 2.5 * S, 1500 * S * S, (1.0, 0.1, 0.6))
area("RimLime", (3.0 * S, 3.5 * S, 2.5 * S), (0, 0, 0.4), 2.2 * S, 1400 * S * S, (0.5, 1.0, 0.1))
# area("Strip", (2.2 * S, -3.0 * S, 2.0 * S), (0, 0, 0.3), 0.25 * S, 500 * S * S, (1.0, 1.0, 1.0), sy=4.0 * S)
area("Top", (0.0, 0.0, 5.0 * S), (0, 0, 0), 3.0 * S, 250 * S * S, (0.9, 0.9, 1.0))
bpy.data.objects["Top"].visible_glossy = False  # its mirror image in the floor showed as a white bar
bpy.data.objects["RimLime"].visible_glossy = False  # a harsh lime glare at the frame edge


PANELS = []


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
    PANELS.append(ob)


for _k in range(3):
    # behind and above the camera: the drops mirror them, but their image in the floor falls behind the lens
    panel(f"PWhite{_k}", ((-1.2 + 1.2 * _k) * S, -11.0, 7.5), (0, 0, 0.3), 0.22 * S, 3.4 * S, (1.0, 1.0, 1.0), 40.0)
panel("PSoftbox", (0.0, -12.0, 9.0), (0, 0, 0.3), 4.5, 2.2, (1.0, 1.0, 1.0), 14.0)  # a big softbox behind the lens: silver drops
for _k in range(8):
    _a = TAU * _k / 8 + 0.2
    panel(f"PRing{_k}", (11 * math.cos(_a), 11 * math.sin(_a), 1.6), (0, 0, 0.6), 2.4, 1.0, [(1, 1, 1), (1.0, 0.25, 0.7), (1, 1, 1), (0.6, 1.0, 0.25)][_k % 4], 5.0)
panel("PSideL", (-7.0, -6.0, 4.0), (0, 0, 0.3), 0.2, 2.5, (1.0, 1.0, 1.0), 30.0)  # side strips: more silver, images fall outside the frame
panel("PSideR", (7.0, -6.0, 4.0), (0, 0, 0.3), 0.2, 2.5, (1.0, 1.0, 1.0), 30.0)
panel("PMag", (-4.0 * S, 1.0 * S, 1.6 * S), (0, 0, 0.5), 1.0 * S, 2.5 * S, (1.0, 0.08, 0.55), 8.0)
panel("PLime", (4.0 * S, 1.5 * S, 1.4 * S), (0, 0, 0.5), 1.0 * S, 2.5 * S, (0.45, 1.0, 0.08), 7.0)
# panel("PBack", (0.0, 5.0 * S, 2.0 * S), (0, 0, 0.5), 3.0 * S, 0.06 * S, (1.0, 1.0, 1.0), 20.0)


def ico_sphere(sub):
    t_ = (1 + math.sqrt(5)) / 2
    vs = [(-1, t_, 0), (1, t_, 0), (-1, -t_, 0), (1, -t_, 0), (0, -1, t_), (0, 1, t_), (0, -1, -t_), (0, 1, -t_),
          (t_, 0, -1), (t_, 0, 1), (-t_, 0, -1), (-t_, 0, 1)]
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
brng = np.random.default_rng(99)
for i in range(110):
    p = np.array([brng.uniform(-12, 12), brng.uniform(7, 20), brng.uniform(-2.0, 10.0)])
    me = bpy.data.meshes.new(f"Bk{i}")
    me.from_pydata((BV * brng.uniform(0.15, 0.4) + p).tolist(), [], BF.tolist())
    o = bpy.data.objects.new(f"Bk{i}", me)
    scene.collection.objects.link(o)
    o.data.materials.append(bms[[0, 1, 0, 1, 2][i % 5]])
    o.visible_shadow = False

# the drops: one metaball object, one ellipsoid element per leaf + splash droplets
mb = bpy.data.metaballs.new("Mercury")
mb.resolution = 0.02
mb.render_resolution = float(os.environ.get("MD_MBRES", "0.006"))
mb.threshold = 0.6
mobj = bpy.data.objects.new("Mercury", mb)
scene.collection.objects.link(mobj)
mobj.data.materials.append(mercury)
MBK = 1 / 0.5707   # a stiffness-2 element's surface sits at 0.5707 x its radius (measured)
ELS = [mb.elements.new(type="ELLIPSOID") for _ in range(N0 + NSPL)]
# the white/colour panels are only for the mercury to reflect - never mirrored as white bars in the glass floor
_lit = bpy.data.collections.new("MercuryOnly")
_lit.objects.link(mobj)
for _p in PANELS:
    _p.light_linking.receiver_collection = _lit
for e in ELS:
    e.stiffness = 2.0

cd = bpy.data.cameras.new("Cam")
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 4.0
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam

# camera keys (t, location, look-at, lens)
CK = [
    (0.0, (1.5, -3.3, 1.0), (0, 0, 1.15), 34),     # cold open: low, among the flying drops
    (0.6, (1.7, -3.7, 1.0), (0, 0, 1.0), 34),
    (1.6, (2.8, -6.8, 2.5), (0, 0, 0.1), 28),     # the drum
    (5.6, (2.4, -7.2, 2.8), (0, 0, 0.1), 28),
    (7.2, (1.0, -5.2, 5.0), (0, 0.3, 0), 26),     # high and closer: the patterns read from above
    (11.6, (-0.9, -5.0, 5.2), (0, 0.3, 0), 26),
    (13.4, (1.8, -5.0, 4.2), (0, 0, 0.3), 30),    # the orbit tightens
    (15.8, (2.3, -4.6, 1.6), (0, 0, 0.5), 38),    # the big sphere, low
    (20.0, (2.6, -5.6, 1.9), (0, 0, 0.5), 38),
]


def cam_at(t):
    for (t0, l0, k0, f0), (t1, l1, k1, f1) in zip(CK, CK[1:]):
        if t <= t1:
            k = sm(t0, t1, t)
            lerp = lambda a, b: np.array(a) * (1 - k) + np.array(b) * k  # noqa: E731
            return lerp(l0, l1), lerp(k0, k1), f0 + (f1 - f0) * k
    return np.array(CK[-1][1]), np.array(CK[-1][2]), CK[-1][3]


def frame(f):
    t = f / FPS
    i_el = 0
    for i in range(N0):
        st = leaf_state(i, t)
        e = ELS[i]
        if st is None:
            e.radius = 1e-5
            e.co = (0, 0, -5)
            continue
        x, y, z, r, sq = st
        e.co = (x, y, z + r * sq)
        e.radius = r * MBK
        e.size_x = e.size_y = 1.0 / math.sqrt(max(sq, 0.2)) * (1 if sq < 1 else 1)
        e.size_z = sq
    for k in range(NSPL):
        e = ELS[N0 + k]
        st = splash_state(k, t)
        if st is None:
            e.radius = 1e-5
            e.co = (0, 0, -5)
            continue
        x, y, z, r, sq = st
        e.co = (x, y, z + r * sq)
        e.radius = r * MBK
        e.size_x = e.size_y = 1.0
        e.size_z = sq
    loc, look, lens = cam_at(t)
    yaw = 0.18 * math.sin(TAU * t / 26)
    c, s_ = math.cos(yaw), math.sin(yaw)
    loc = np.array([loc[0] * c - loc[1] * s_, loc[0] * s_ + loc[1] * c, loc[2]])
    cam.location = loc.tolist()
    d = mathutils.Vector(look.tolist()) - mathutils.Vector(loc.tolist())
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.dof.focus_distance = d.length
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
