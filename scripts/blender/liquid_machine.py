# 0027 "This machine runs on liquid" - motion test (owner pick Nov 17 2026, after the chip reel was rejected).
# A magnetic machine in a BRIGHT white studio: matte white ceramic base, a clear glass ring-channel, black glossy
# ferrofluid inside it, a polished steel hub turning four arms with nickel magnet pods that pass over the channel.
# Every magnet that passes pulls the liquid up into smooth glossy cones (Rosensweig spikes) - no crystals, no crowns.
# Test beats: 0-0.5 HOOK low on the channel, a spiked wave races at the lens, at 0.4 s a magnet passes and pulls it up
# into a tall column; 0.5-4.5 the camera pulls back, the hub speeds up, each pass lifts the liquid (one thock each).
# Usage: blender -b --factory-startup -P liquid_machine.py -- <outdir> <t0> <t1> <fps> <k> <workers>  (env LM_FAST=1)
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a_ = sys.argv[sys.argv.index("--") + 1:]
OUTDIR = os.path.abspath(a_[0]); T0, T1, FPS = float(a_[1]), float(a_[2]), int(a_[3]); K, NW = int(a_[4]), int(a_[5])
FAST = bool(os.environ.get("LM_FAST"))
TAU = 2 * math.pi


def sm(a, b, x):
    k = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
if FAST:
    for _eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = _eng
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 24
    scene.render.resolution_x, scene.render.resolution_y = 540, 960
else:
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == "OPTIX"
    scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("LM_SAMPLES", "64")); scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
    scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("LM_RES", "1080x1920").split("x")]
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.image_settings.file_format = "PNG"


def pm(name, col, rough, metal=0.0, coat=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    return m


CERAMIC = pm("Ceramic", (0.5, 0.5, 0.5), 0.5, coat=0.15)
# edge check (Instagram "border"): the bare white base read as a flat band at the bottom -> machined concentric grooves
# + a fine ceramic grain, real detail that carries to the frame edge
_cn = CERAMIC.node_tree.nodes; _cl = CERAMIC.node_tree.links
_tc2 = _cn.new("ShaderNodeTexCoord"); _sx = _cn.new("ShaderNodeSeparateXYZ"); _cl.new(_tc2.outputs["Object"], _sx.inputs[0])
_r = _cn.new("ShaderNodeVectorMath"); _r.operation = "LENGTH"
_cxy = _cn.new("ShaderNodeCombineXYZ"); _cl.new(_sx.outputs["X"], _cxy.inputs["X"]); _cl.new(_sx.outputs["Y"], _cxy.inputs["Y"])
_cl.new(_cxy.outputs[0], _r.inputs[0])
_rm = _cn.new("ShaderNodeMath"); _rm.operation = "MULTIPLY"; _rm.inputs[1].default_value = 34.0; _cl.new(_r.outputs["Value"], _rm.inputs[0])
_sn = _cn.new("ShaderNodeMath"); _sn.operation = "SINE"; _cl.new(_rm.outputs[0], _sn.inputs[0])
_nz = _cn.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 400.0
_ad = _cn.new("ShaderNodeMath"); _ad.operation = "MULTIPLY_ADD"; _ad.inputs[1].default_value = 0.35
_cl.new(_nz.outputs["Fac"], _ad.inputs[0]); _cl.new(_sn.outputs[0], _ad.inputs[2])
_bm = _cn.new("ShaderNodeBump"); _bm.inputs["Strength"].default_value = 0.9; _bm.inputs["Distance"].default_value = 0.012
_cl.new(_ad.outputs[0], _bm.inputs["Height"]); _cl.new(_bm.outputs["Normal"], _cn["Principled BSDF"].inputs["Normal"])
_rr = _cn.new("ShaderNodeMapRange"); _rr.inputs["To Min"].default_value = 0.38; _rr.inputs["To Max"].default_value = 0.6
_cl.new(_ad.outputs[0], _rr.inputs["Value"]); _cl.new(_rr.outputs["Result"], _cn["Principled BSDF"].inputs["Roughness"])
STEEL = pm("Steel", (0.92, 0.92, 0.94), 0.06, metal=1.0)
NICKEL = pm("Nickel", (0.78, 0.77, 0.74), 0.14, metal=1.0)
GLASS = pm("Glass", (1.0, 1.0, 1.0), 0.0, trans=1.0, ior=1.47)
FERRO = pm("Ferrofluid", (0.004, 0.004, 0.005), 0.05, metal=0.6, coat=1.0)
FERRO.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.02
FLOOR = pm("Cyc", (0.32, 0.33, 0.35), 0.5)


def mesh(name, V, F, m, smooth=True):
    me = bpy.data.meshes.new(name); me.from_pydata(V.tolist(), [], F)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); o.data.materials.append(m)
    return o


# ---- studio: a white seamless sweep ----
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); bpy.context.active_object.data.materials.append(FLOOR)

# ---- the machine ----
R, CH = 2.0, 0.3                     # ring radius, channel half-width
BASE_H = 0.45
bpy.ops.mesh.primitive_cylinder_add(radius=2.9, depth=BASE_H, location=(0, 0, BASE_H / 2), vertices=160)
base = bpy.context.active_object; base.data.materials.append(CERAMIC)
bv = base.modifiers.new("b", "BEVEL"); bv.width = 0.06; bv.segments = 5
# glass U-channel: a torus with the top cut away
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=CH + 0.03, major_segments=256, minor_segments=40, location=(0, 0, BASE_H + CH))
glass = bpy.context.active_object; glass.data.materials.append(GLASS)
sol = glass.modifiers.new("s", "SOLIDIFY"); sol.thickness = 0.025
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, BASE_H + CH + 0.6)); cut = bpy.context.active_object
cut.scale = (6, 6, 1.0); cut.hide_render = True
bo = glass.modifiers.new("cut", "BOOLEAN"); bo.object = cut; bo.operation = "DIFFERENCE"
CH_Z = BASE_H + 0.06                 # channel floor height (the liquid sits on it)
# v2 (owner: "no spinning, it gave me a headache"): nothing rotates. A static polished steel column in the centre carries
# a steel ring frame above the channel; 12 nickel magnet pistons hang from it and slide DOWN towards the liquid and back up.
MAG_Z = BASE_H + CH + 0.62                 # piston pod height when raised
DROP = 0.34                                # how far a piston comes down
NPI = 12
bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=1.9, location=(0, 0, BASE_H + 0.95), vertices=96)
bpy.context.active_object.data.materials.append(STEEL)
bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=0.05, major_segments=256, minor_segments=24, location=(0, 0, MAG_Z + 0.75))
bpy.context.active_object.data.materials.append(STEEL)
for i in range(4):                          # four static spokes from the column to the ring frame
    a0 = i * TAU / 4 + TAU / 8
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a0) * R / 2, math.sin(a0) * R / 2, MAG_Z + 0.75))
    sp_ = bpy.context.active_object; sp_.scale = (R, 0.08, 0.06); sp_.rotation_euler.z = a0; sp_.data.materials.append(STEEL)
PODS = []                                   # (angle, rod object, pod object)
for i in range(NPI):
    a0 = -math.pi / 2 + i * TAU / NPI       # piston 0 sits at the front (theta = -90 deg, the camera side)
    x, y = math.cos(a0) * R, math.sin(a0) * R
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.7, location=(x, y, MAG_Z + 0.4), vertices=24)
    rod = bpy.context.active_object; rod.data.materials.append(STEEL)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.2, location=(x, y, MAG_Z), vertices=64)
    pod = bpy.context.active_object; pod.data.materials.append(NICKEL)
    b2 = pod.modifiers.new("b", "BEVEL"); b2.width = 0.03; b2.segments = 4
    PODS.append((a0, rod, pod))

# ---- the liquid: a band along the ring (theta) x across the channel (w) ----
NA, NWD = 1600, 56
TH = np.linspace(0, TAU, NA, endpoint=False)
WW = np.linspace(-1, 1, NWD)
THg, Wg = np.meshgrid(TH, WW, indexing="ij")
F = []
for i in range(NA):
    for j in range(NWD - 1):
        a0 = i * NWD + j; b0 = ((i + 1) % NA) * NWD + j
        F.append((a0, b0, b0 + 1, a0 + 1))
liq = mesh("Liquid", np.zeros((NA * NWD, 3)), F, FERRO)
# a hexagonal lattice of smooth cones in (arc length, width) space
SP = 0.13
U = THg * R
qx, qy = U / SP, (Wg * CH) / (SP * math.sqrt(3))
d1 = np.hypot((qx - np.round(qx)) * SP, (qy - np.round(qy)) * SP * math.sqrt(3))
d2 = np.hypot((qx - 0.5 - np.round(qx - 0.5)) * SP, (qy - 0.5 - np.round(qy - 0.5)) * SP * math.sqrt(3))
xx = np.clip(1 - np.minimum(d1, d2) / 0.065, 0, 1)
HEX = xx ** 2.4
EDGE = np.clip(1 - np.abs(Wg) ** 6, 0, 1)            # the liquid meets the glass walls smoothly


def lattice(shift):
    """hex lattice of smooth cones in (arc length, width) space, carried along the ring by `shift` (radians)"""
    U_ = (THg - shift) * R
    qx_, qy_ = U_ / SP, (Wg * CH) / (SP * math.sqrt(3))
    e1 = np.hypot((qx_ - np.round(qx_)) * SP, (qy_ - np.round(qy_)) * SP * math.sqrt(3))
    e2 = np.hypot((qx_ - 0.5 - np.round(qx_ - 0.5)) * SP, (qy_ - 0.5 - np.round(qy_ - 0.5)) * SP * math.sqrt(3))
    return np.clip(1 - np.minimum(e1, e2) / 0.065, 0, 1) ** 2.4


# a pool of small black droplets thrown up when a column lets go (ballistic arcs back into the liquid)
DROPLETS = []
for i in range(90):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, -5), segments=16, ring_count=10)
    o = bpy.context.active_object; o.data.materials.append(FERRO); o.hide_render = True
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    DROPLETS.append(o)


# ---- story (20 s), v2: nothing spins - the pistons drop in patterns ----
#  0-0.45   HOOK: a spiked wave races along the channel at the lens; at 0.42 the front piston drops -> a column
#  0.6-4.0  the pistons drop one after another round the ring: the columns RUN round (the machine stays still)
#  4.0-8.2  rhythmic patterns, one per beat: every other, opposite pairs, every third, both halves
#  8.5-13.2 CLIMAX: all twelve drop together -> a crown of columns round the whole ring, it breathes three times
#  13.4-14.4 all rise, the liquid relaxes (a settle thock)
#  14.6-17.2 the front piston lowers slowly: the liquid runs along the channel and gathers under it into one bulb
#  17.3-18.3 the piston lifts away: the bulb relaxes into a perfect mirror dome (last soft thock)
#  18.3-20  the camera eases back, fade
DUR = 20.0
FRONT = -math.pi / 2
HOOK = 0.42
DROPS = []                                  # (piston, time of the drop, hold seconds)
DROPS.append((0, HOOK, 0.35))
for k in range(1, 12):                       # the chase, accelerating a little
    DROPS.append((k % NPI, 0.75 + 0.27 * k - 0.004 * k * k, 0.22))
pat_t = 4.1
for pattern in ([0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11], [0, 6], [3, 9], [1, 7], [4, 10], [0, 3, 6, 9], [1, 4, 7, 10], [2, 5, 8, 11], list(range(6)), list(range(6, 12))):
    for k in pattern:
        DROPS.append((k, pat_t, 0.22))
    pat_t += 0.38
ALL = [8.6, 10.0, 11.4]                      # the crown: all twelve, three breaths
for tb in ALL:
    for k in range(NPI):
        DROPS.append((k, tb, 1.0))
GATHER, LIFT = 14.6, 17.3


def piston_amt(k, t):
    """0 = raised, 1 = fully down; fast down (0.07 s), held, eased up (0.18 s)"""
    v = 0.0
    for (kk, td, hold) in DROPS:
        if kk != k or t < td - 0.08 or t > td + hold + 0.25:
            continue
        down = float(sm(td - 0.07, td, t))
        up = 1.0 - float(sm(td + hold, td + hold + 0.18, t))
        v = max(v, down * up)
    if k == 0:                               # the ending: the front piston lowers slowly, gathers, then lifts away
        v = max(v, 0.85 * float(sm(GATHER - 0.2, GATHER + 1.4, t)) * (1.0 - float(sm(LIFT, LIFT + 0.9, t))))
    return v


def flow_angle(t):
    """calm continuous flow round the channel: ~one lap per 16 s, a little faster at the crown, slowing for the end"""
    w = 0.32 + 0.18 * float(sm(7.5, 9.0, t)) - 0.4 * float(sm(13.4, 15.0, t))
    return 0.32 * t + 0.18 * max(0.0, t - 8.25) * float(sm(7.5, 9.0, t)) - 0.4 * max(0.0, t - 14.2) * float(sm(13.4, 15.0, t))


RELEASES = sorted([(k, td + hold + 0.18) for (k, td, hold) in DROPS if hold < 0.9] + [(k, td + hold + 0.18) for (k, td, hold) in DROPS if hold >= 0.9 and k % 2 == 0], key=lambda x: x[1])


def liquid(t):
    gather = float(sm(GATHER, GATHER + 2.6, t))
    lift = float(sm(LIFT, LIFT + 1.0, t))
    crown = max(float(np.exp(-((t - (tb + 0.5)) / 0.75) ** 2)) for tb in ALL)
    base_lvl = 0.1 * (1.0 - gather)
    h = np.full(THg.shape, base_lvl)
    fa = flow_angle(t)
    hexf = lattice(fa)                                      # the resting spike texture drifts with the flow
    calm = 1.0 - float(sm(14.2, 15.2, t))
    # gentle flowing ripples along the channel + a faint cross ripple (life on the surface between the columns)
    h = h + calm * (0.012 * np.sin(22 * R * (THg - fa) + 1.3 * np.sin(3 * THg)) + 0.007 * np.sin(9 * Wg + 40 * (THg - fa)))
    h = h + calm * 0.05 * hexf * (0.6 + 0.4 * np.sin(2 * (THg - fa) + t))    # a low drifting spike field everywhere
    # release ripples: when a column lets go, rings of waves run away from that spot along the channel
    for (k, tr) in RELEASES:
        age = t - tr
        if age < 0 or age > 1.6:
            continue
        a0 = PODS[k][0] + fa * 0.0
        dd = np.abs(np.angle(np.exp(1j * (THg - a0)))) * R
        h = h + calm * 0.05 * math.exp(-age * 2.2) * np.cos(18 * (dd - 0.9 * age)) * np.exp(-((dd - 0.9 * age) / 0.35) ** 2)
    th_w = FRONT - 1.2 * (0.4 - t) if t < 0.6 else FRONT
    dw = np.angle(np.exp(1j * (THg - th_w)))
    wave = np.exp(-(dw / 0.18) ** 2) * (1.0 - float(sm(0.45, 1.2, t)))
    h = h + 0.1 * wave + 0.42 * wave * HEX
    grow = 1.0 + 0.3 * float(sm(2.0, 8.5, t)) + 0.25 * crown
    for k, (a0, rod, pod) in enumerate(PODS):
        amt = piston_amt(k, t)
        pod.location.z = MAG_Z - DROP * amt + 0.9 * lift * (k == 0)
        rod.location.z = MAG_Z + 0.4 - DROP * amt + 0.9 * lift * (k == 0)
        if k == 0 and t > GATHER:
            continue                             # the ending piston drives the gather, not spikes
        if amt < 0.01:
            continue
        hb = 1.0 + 1.8 * float(np.exp(-((t - HOOK) / 0.12) ** 2)) * (k == 0)
        d = np.angle(np.exp(1j * (THg - a0)))
        infl = np.exp(-(d / 0.15) ** 2)
        h = h + amt * (infl * (0.05 + 0.5 * np.maximum(HEX, hexf) * grow * hb) + 0.36 * np.exp(-(d / 0.075) ** 2) * np.exp(-(Wg / 0.45) ** 2) * grow * hb)
    if gather > 0.0:
        dg = np.angle(np.exp(1j * (THg - FRONT)))
        width = 0.55 - 0.36 * gather
        bulb = np.exp(-(dg / width) ** 2) * np.exp(-(Wg / 0.9) ** 2)
        peak = (0.3 + 0.55 * gather) * (1.0 - 0.5 * lift)
        h = h + gather * peak * bulb
    z = CH_Z + h * EDGE
    rr = R + Wg * CH * 0.9
    V = np.stack([rr * np.cos(THg), rr * np.sin(THg), z], -1).reshape(-1, 3)
    liq.data.vertices.foreach_set("co", V.reshape(-1).astype(np.float32)); liq.data.update()
    # droplets: 4 per release, thrown from the column top, falling back in under gravity
    used = 0
    for n_, (k, tr) in enumerate(RELEASES):
        age = t - tr
        if age < 0 or age > 0.55 or used >= len(DROPLETS) - 4:
            continue
        a0 = PODS[k][0]
        for j in range(4):
            ph = (n_ * 7 + j * 3) % 11 / 11.0
            ang = a0 + (ph - 0.5) * 0.22
            v_up = 1.3 + 0.7 * ph
            zz = CH_Z + 0.45 + v_up * age - 4.9 * age * age
            if zz < CH_Z + 0.08:
                continue
            rad = R + (ph - 0.5) * 0.25 * CH
            o = DROPLETS[used]; used += 1
            o.hide_render = False
            o.location = (rad * math.cos(ang), rad * math.sin(ang), zz)
            sc = 0.018 + 0.016 * ph
            o.scale = (sc, sc, sc * (1.0 + 0.6 * min(1.0, abs(v_up - 9.8 * age))))      # stretched while fast
    for o in DROPLETS[used:]:
        o.hide_render = True


# ---- light: big soft boxes, bright world (the black liquid mirrors them as clean highlights) ----
def area(name, loc, size, power, sy=None, target=(0, 0, 0.6)):
    l = bpy.data.lights.new(name, "AREA"); l.shape = "RECTANGLE"; l.size = size; l.size_y = sy or size; l.energy = power
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); scene.collection.objects.link(o)


area("Key", (-5, -4, 7), 3.5, 3200)
area("Strip", (5, -2, 3), 0.8, 900, sy=6)
area("Top", (0, 0, 9), 6.0, 900)
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
_wn, _wl = world.node_tree.nodes, world.node_tree.links
_tc = _wn.new("ShaderNodeTexCoord"); _sp = _wn.new("ShaderNodeSeparateXYZ"); _ramp = _wn.new("ShaderNodeValToRGB")
_wl.new(_tc.outputs["Generated"], _sp.inputs[0]); _wl.new(_sp.outputs["Z"], _ramp.inputs["Fac"])
_ramp.color_ramp.elements[0].position = 0.45; _ramp.color_ramp.elements[0].color = (0.18, 0.18, 0.19, 1)
_ramp.color_ramp.elements[1].position = 0.75; _ramp.color_ramp.elements[1].color = (0.85, 0.85, 0.86, 1)
_wl.new(_ramp.outputs["Color"], _wn["Background"].inputs["Color"])
_wn["Background"].inputs["Strength"].default_value = 0.45

camd = bpy.data.cameras.new("Cam"); camd.sensor_width = 36
cam = bpy.data.objects.new("Cam", camd); scene.collection.objects.link(cam); scene.camera = cam


KEYS = [  # t, position, look-at, lens - slow pushes and pulls, never circling the machine
    (0.0, (0.55, -2.95, CH_Z + 0.32), (-1.2, -1.6, CH_Z + 0.45), 26),
    (0.6, (0.75, -3.1, CH_Z + 0.4), (-0.9, -1.7, CH_Z + 0.5), 26),
    (3.0, (1.3, -3.7, 1.85), (0.0, -0.6, 1.15), 32),
    (6.0, (1.05, -4.0, 2.25), (0.0, -0.4, 1.05), 32),
    (8.4, (1.0, -5.4, 3.9), (0.0, 0.0, 0.55), 34),
    (11.0, (0.8, -5.0, 4.6), (0.0, 0.0, 0.5), 34),
    (13.4, (0.9, -4.4, 3.0), (0.0, -0.8, 0.55), 34),
    (15.0, (1.1, -3.7, 1.5), (0.0, -1.6, 0.95), 36),
    (17.4, (0.9, -3.4, 1.05), (0.0, -1.8, 0.9), 38),
    (20.0, (1.6, -5.4, 2.6), (0.0, -0.8, 0.6), 38),
]


def _cr(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def camera(t):
    ks = KEYS
    i = max(k for k in range(len(ks) - 1) if ks[k][0] <= t) if t >= ks[0][0] else 0
    t1, t2 = ks[i][0], ks[i + 1][0]
    u = min(1.0, max(0.0, (t - t1) / (t2 - t1)))
    u = u * u * (3 - 2 * u) * 0.4 + u * 0.6
    g = lambda k, idx: Vector(ks[max(0, min(len(ks) - 1, k))][idx])
    pos = _cr(g(i - 1, 1), g(i, 1), g(i + 1, 1), g(i + 2, 1), u)
    look = _cr(g(i - 1, 2), g(i, 2), g(i + 1, 2), g(i + 2, 2), u)
    return pos, look, ks[i][3] + (ks[i + 1][3] - ks[i][3]) * u


events = [{"t": td, "kind": "drop", "k": k} for (k, td, hold) in DROPS]
os.makedirs(OUTDIR, exist_ok=True)
json.dump({"events": events, "hook": HOOK, "crown": ALL, "settle": 13.4, "gather": GATHER, "lift": LIFT, "dur": DUR}, open(os.path.join(OUTDIR, "events.json"), "w"))

frames = list(range(int(round(T0 * FPS)), int(round(T1 * FPS))))
for fr in frames[K::NW]:
    t = fr / FPS
    pos, look, lens = camera(t)
    cam.location = pos; cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler(); camd.lens = lens
    camd.dof.use_dof = True; camd.dof.focus_distance = (look - pos).length; camd.dof.aperture_fstop = 9.0
    liquid(t)
    scene.view_settings.exposure = math.log2(max(1e-4, 1.0 - float(sm(18.6, 19.95, t))))
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % fr)
    bpy.ops.render.render(write_still=True)
print("done")
