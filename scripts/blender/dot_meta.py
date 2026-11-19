# 0030 "Dot Metamorphosis" v2 (owner, Nov 18 2026: improve the reel - more realistic, better effects, more life, hold
# everyone to the end). Same idea + story as the owner's v1 (thousands of dots form a body that keeps transforming:
# blob -> peanut -> spiky -> dumbbell -> three spheres -> rejoin -> hourglass -> disc -> dust), rebuilt as a real 3D render:
# every dot is a small glowing glass bead (Cycles, depth of field, bloom), the body breathes and ripples all the time, and
# every transformation is an EVENT (the beads erupt outward and snap back with a shock ripple, sparks fly at splits).
# Usage: blender -b --factory-startup -P dot_meta.py -- <outdir> <t0> <t1> <fps> <k> <workers>   env DM_RES, DM_SAMPLES
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a_ = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a_[0]); T0, T1, FPS = float(a_[1]), float(a_[2]), int(a_[3]); K, NW = int(a_[4]), int(a_[5])
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi
rng = np.random.default_rng(30)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("DM_SAMPLES", "48"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("DM_RES", "540x960").split("x")]
scene.view_settings.view_transform = "Khronos PBR Neutral"; scene.view_settings.look = "None"
scene.render.image_settings.file_format = "PNG"


def sm(a, b, x):
    k = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


# ---- the beads: N points on a Fibonacci sphere (the body's "skin"), instanced as glass beads via geometry nodes ----
N = 9000
i = np.arange(N) + 0.5
phi = np.arccos(1 - 2 * i / N); th = np.pi * (1 + 5 ** 0.5) * i
DIR = np.stack([np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi), np.cos(phi)], -1)   # unit directions
JIT = rng.uniform(0, 1, N)
PAL = os.environ.get("DM_PAL", "orig")
NEB = {"orig": (0.03, 0.008, 0.05), "chameleon": (0.03, 0.008, 0.05), "opal": (0.012, 0.01, 0.05),
       "sapphire": (0.004, 0.012, 0.05), "aurora": (0.006, 0.045, 0.045)}[PAL]
RIMS = {"orig": ((1, 0.2, 0.8), (0.2, 0.8, 1)), "chameleon": ((1, 0.2, 0.8), (0.2, 0.8, 1)),
        "opal": ((1, 0.5, 0.8), (0.4, 1, 0.8)), "sapphire": ((1, 0.85, 0.6), (0.3, 0.6, 1)),
        "aurora": ((0.6, 0.3, 1), (0.2, 1, 0.6))}[PAL]
me = bpy.data.meshes.new("Dots"); me.from_pydata((DIR * 1.0).tolist(), [], [])
dots = bpy.data.objects.new("Dots", me); scene.collection.objects.link(dots)
col_attr = me.attributes.new("dcol", "FLOAT_COLOR", "POINT")
glow_attr = me.attributes.new("dglow", "FLOAT", "POINT")
vel_attr = me.attributes.new("dvel", "FLOAT_VECTOR", "POINT")
size_attr = me.attributes.new("dsize", "FLOAT", "POINT")

BEAD = bpy.data.materials.new("Bead"); BEAD.use_nodes = True
bn, bl = BEAD.node_tree.nodes, BEAD.node_tree.links
bsdf = bn["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 1.0, 1); bsdf.inputs["Roughness"].default_value = 0.04
bsdf.inputs["Transmission Weight"].default_value = 0.6; bsdf.inputs["IOR"].default_value = 1.5
bsdf.inputs["Coat Weight"].default_value = 0.6
ac = bn.new("ShaderNodeAttribute"); ac.attribute_type = "INSTANCER"; ac.attribute_name = "dcol"
ag = bn.new("ShaderNodeAttribute"); ag.attribute_type = "INSTANCER"; ag.attribute_name = "dglow"
bl.new(ac.outputs["Color"], bsdf.inputs["Emission Color"]); bl.new(ac.outputs["Color"], bsdf.inputs["Base Color"])
bl.new(ag.outputs["Fac"], bsdf.inputs["Emission Strength"])

gn = dots.modifiers.new("Beads", "NODES")
tree = bpy.data.node_groups.new("Beads", "GeometryNodeTree")
tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = tree.nodes.new("NodeGroupInput"); go = tree.nodes.new("NodeGroupOutput")
iop = tree.nodes.new("GeometryNodeInstanceOnPoints")
ico = tree.nodes.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 0.013; ico.inputs["Subdivisions"].default_value = 3
sm_ = tree.nodes.new("GeometryNodeSetShadeSmooth")
setm = tree.nodes.new("GeometryNodeSetMaterial"); setm.inputs["Material"].default_value = BEAD
tree.links.new(gi.outputs[0], iop.inputs["Points"]); tree.links.new(ico.outputs["Mesh"], sm_.inputs["Geometry"])
_va = tree.nodes.new("GeometryNodeInputNamedAttribute"); _va.data_type = "FLOAT_VECTOR"; _va.inputs["Name"].default_value = "dvel"
_al = tree.nodes.new("FunctionNodeAlignEulerToVector"); _al.axis = "Z"
tree.links.new(_va.outputs["Attribute"], _al.inputs["Vector"]); tree.links.new(_al.outputs["Rotation"], iop.inputs["Rotation"])
_ln = tree.nodes.new("ShaderNodeVectorMath"); _ln.operation = "LENGTH"; tree.links.new(_va.outputs["Attribute"], _ln.inputs[0])
_st = tree.nodes.new("ShaderNodeMath"); _st.operation = "MULTIPLY_ADD"; _st.inputs[1].default_value = 0.0; _st.inputs[2].default_value = 1.0
tree.links.new(_ln.outputs["Value"], _st.inputs[0])
_sc = tree.nodes.new("ShaderNodeCombineXYZ"); _sc.inputs["X"].default_value = 1.0; _sc.inputs["Y"].default_value = 1.0
_sz = tree.nodes.new("GeometryNodeInputNamedAttribute"); _sz.data_type = "FLOAT"; _sz.inputs["Name"].default_value = "dsize"
_sm = tree.nodes.new("ShaderNodeMath"); _sm.operation = "MULTIPLY"; tree.links.new(_st.outputs[0], _sm.inputs[0]); tree.links.new(_sz.outputs["Attribute"], _sm.inputs[1])
tree.links.new(_sz.outputs["Attribute"], _sc.inputs["X"]); tree.links.new(_sz.outputs["Attribute"], _sc.inputs["Y"])
tree.links.new(_sm.outputs[0], _sc.inputs["Z"]); tree.links.new(_sc.outputs[0], iop.inputs["Scale"])
tree.links.new(sm_.outputs["Geometry"], iop.inputs["Instance"]); tree.links.new(iop.outputs["Instances"], setm.inputs["Geometry"])
tree.links.new(setm.outputs["Geometry"], go.inputs[0])
gn.node_group = tree

# ---- space: black with a faint violet nebula + a far star field (detail to the frame edges) ----
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn["Background"]
tc = wn.new("ShaderNodeTexCoord"); nz = wn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.8; nz.inputs["Detail"].default_value = 8
wl.new(tc.outputs["Generated"], nz.inputs["Vector"])
ramp = wn.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.001, 0.001, 0.003, 1)
ramp.color_ramp.elements[1].position = 0.78; ramp.color_ramp.elements[1].color = (*NEB, 1)
wl.new(nz.outputs["Fac"], ramp.inputs["Fac"]); wl.new(ramp.outputs["Color"], bg.inputs["Color"])
if PAL == "aurora":
    # a faint aurora curtain far behind the body: soft green low, violet high, wavy vertical bands (detail to the frame edges)
    sx = wn.new("ShaderNodeSeparateXYZ"); wl.new(tc.outputs["Generated"], sx.inputs[0])
    wv = wn.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 2.6; wv.inputs["Distortion"].default_value = 7.0; wv.inputs["Detail"].default_value = 3
    wl.new(tc.outputs["Generated"], wv.inputs["Vector"])
    wp = wn.new("ShaderNodeMath"); wp.operation = "POWER"; wp.inputs[1].default_value = 3.0; wl.new(wv.outputs["Fac"], wp.inputs[0])
    n2 = wn.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 2.2; n2.inputs["Detail"].default_value = 2
    wl.new(tc.outputs["Generated"], n2.inputs["Vector"])
    n2m = wn.new("ShaderNodeMapRange"); n2m.inputs["From Min"].default_value = 0.4; n2m.inputs["From Max"].default_value = 0.7
    wl.new(n2.outputs["Fac"], n2m.inputs["Value"])
    wq = wn.new("ShaderNodeMath"); wq.operation = "MULTIPLY"; wl.new(wp.outputs["Value"], wq.inputs[0]); wl.new(n2m.outputs["Result"], wq.inputs[1])
    hz = wn.new("ShaderNodeMapRange"); hz.inputs["From Min"].default_value = -0.45; hz.inputs["From Max"].default_value = 0.35
    wl.new(sx.outputs["Z"], hz.inputs["Value"])
    ar = wn.new("ShaderNodeValToRGB"); els = ar.color_ramp.elements
    els[0].position = 0.0; els[0].color = (0, 0, 0, 1); els[1].position = 1.0; els[1].color = (0.004, 0.0, 0.008, 1)
    for pos, col in ((0.18, (0.0, 0.05, 0.02, 1)), (0.42, (0.0, 0.032, 0.03, 1)), (0.7, (0.022, 0.006, 0.04, 1))):
        e = els.new(pos); e.color = col
    wl.new(hz.outputs["Result"], ar.inputs["Fac"])
    vs = wn.new("ShaderNodeVectorMath"); vs.operation = "SCALE"; wl.new(ar.outputs["Color"], vs.inputs[0]); wl.new(wq.outputs["Value"], vs.inputs["Scale"])
    va = wn.new("ShaderNodeVectorMath"); va.operation = "ADD"; wl.new(ramp.outputs["Color"], va.inputs[0]); wl.new(vs.outputs["Vector"], va.inputs[1])
    wl.new(va.outputs["Vector"], bg.inputs["Color"])
STAR = bpy.data.materials.new("Star"); STAR.use_nodes = True
sn = STAR.node_tree.nodes; sn.clear(); se = sn.new("ShaderNodeEmission"); se.inputs["Strength"].default_value = 6.0
so = sn.new("ShaderNodeOutputMaterial"); STAR.node_tree.links.new(se.outputs[0], so.inputs["Surface"])
sp = rng.normal(0, 1, (7000, 3)); sp /= np.linalg.norm(sp, axis=1, keepdims=True); sp *= rng.uniform(14, 30, (7000, 1))
sme = bpy.data.meshes.new("Stars"); sme.from_pydata(sp.tolist(), [], [])
stars = bpy.data.objects.new("Stars", sme); scene.collection.objects.link(stars)
sg = stars.modifiers.new("S", "NODES"); st = bpy.data.node_groups.new("S", "GeometryNodeTree")
st.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
st.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
a1 = st.nodes.new("NodeGroupInput"); a2 = st.nodes.new("NodeGroupOutput"); ip = st.nodes.new("GeometryNodeInstanceOnPoints")
ic = st.nodes.new("GeometryNodeMeshIcoSphere"); ic.inputs["Radius"].default_value = 0.02
smt = st.nodes.new("GeometryNodeSetMaterial"); smt.inputs["Material"].default_value = STAR
st.links.new(a1.outputs[0], ip.inputs["Points"]); st.links.new(ic.outputs["Mesh"], ip.inputs["Instance"])
st.links.new(ip.outputs["Instances"], smt.inputs["Geometry"]); st.links.new(smt.outputs["Geometry"], a2.inputs[0])
sg.node_group = st
# a soft key from upper left (catches the glass), a magenta rim, a cyan rim
for name, loc, size, pw, col in (("Key", (-4, -4, 5), 3.0, 260, (1, 0.95, 1)), ("RimM", (4, 3, 1), 1.0, 500, RIMS[0]), ("RimC", (-4, 3, -1), 1.0, 450, RIMS[1])):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = pw; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); scene.collection.objects.link(o)
# bloom
ct = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare")
gl.inputs["Type"].default_value = "Bloom"; gl.inputs["Threshold"].default_value = 2.0; gl.inputs["Strength"].default_value = 0.3; gl.inputs["Size"].default_value = 0.7
co = ct.nodes.new("NodeGroupOutput"); ct.links.new(rl.outputs["Image"], gl.inputs["Image"]); ct.links.new(gl.outputs["Image"], co.inputs[0])
scene.compositing_node_group = ct; scene.render.use_compositing = True


# ---- shapes: radius of the skin along each direction (and a few special arrangements) ----
def blob(t):
    x, y, z = DIR.T
    return 1.0 + 0.12 * np.sin(3 * x + 2.1 * t) * np.cos(2 * y - 1.3 * t) + 0.08 * np.sin(4 * z + 1.7 * t)


def peanut(t):
    x, y, z = DIR.T
    return 1.0 + 0.45 * z * z - 0.35 * np.exp(-(z / 0.35) ** 2) + 0.06 * np.sin(5 * x + t)


RET0, RET1 = 0.8, 2.6                          # regather window (also used by the chameleon palette)
MORPH = 1.6                                    # every change of shape: 1.6 s smootherstep (+0.4 s per-bead stagger)
DUST_T = 26.0                                  # the ending: the body dissolves into dust, right to left, fade to black


def _smoother(q):
    return q * q * q * (q * (q * 6 - 15) + 10)


def _rotx(P, a):
    c, s_ = math.cos(a), math.sin(a)
    return np.stack([P[:, 0], P[:, 1] * c - P[:, 2] * s_, P[:, 1] * s_ + P[:, 2] * c], -1)


def _roty(P, a):
    c, s_ = math.cos(a), math.sin(a)
    return np.stack([P[:, 0] * c + P[:, 2] * s_, P[:, 1], -P[:, 0] * s_ + P[:, 2] * c], -1)


ZERO = np.zeros((N, 3))
_XY = DIR[:, :2] / np.maximum(np.linalg.norm(DIR[:, :2], axis=1, keepdims=True), 1e-6)
_PHI = np.arctan2(DIR[:, 1], DIR[:, 0])
_srng = np.random.default_rng(77)
JIT2 = _srng.uniform(0, 1, N)
_BUMPS = _srng.normal(0, 1, (14, 3)); _BUMPS /= np.linalg.norm(_BUMPS, axis=1, keepdims=True)


def s_blob(t):
    return DIR * blob(t)[:, None], ZERO


def s_peanut(t):                                # long peanut, gently twisted and tilted
    P = DIR * peanut(t)[:, None]
    a = 0.55 * P[:, 2]; c, s_ = np.cos(a), np.sin(a)
    P = np.stack([P[:, 0] * c - P[:, 1] * s_, P[:, 0] * s_ + P[:, 1] * c, P[:, 2]], -1)
    return _roty(P, 0.3), ZERO


def s_bumpy(t):                                 # round, soft bumps that pulse (never sharp spikes)
    b = sum(np.exp(-(1 - DIR @ d) / 0.03) * (0.8 + 0.2 * math.sin(t * 1.3 + i)) for i, d in enumerate(_BUMPS))
    r = 1.05 + 0.24 * b + 0.04 * np.sin(5 * DIR[:, 0] + t)
    return DIR * r[:, None], ZERO


def s_dumbbell(t):                              # two round bulbs on a thin neck, tilted
    z = DIR[:, 2]
    bulb = 0.74 * np.sqrt(np.clip(1 - ((np.abs(z) - 0.56) / 0.44) ** 2, 0, 1))
    neck = 0.2 * np.exp(-(z / 0.28) ** 2)
    w = np.sqrt(bulb ** 2 + neck ** 2) * (1 + 0.04 * math.sin(t * 2.0))
    P = np.concatenate([_XY * w[:, None], (1.6 * z)[:, None]], 1)
    return _roty(P, -0.55 + 0.05 * math.sin(t * 0.5)), ZERO


_GRP = np.clip(np.floor((_PHI + math.pi) / (2 * math.pi) * 3), 0, 2).astype(int)
_PHI_LOC = ((_PHI + math.pi) - _GRP * (2 * math.pi / 3)) * 3 - math.pi     # each 120 deg sector unfolds into a whole sphere
_SXY = np.sqrt(np.clip(1 - DIR[:, 2] ** 2, 0, 1))
_LOC = np.stack([np.cos(_PHI_LOC) * _SXY, np.sin(_PHI_LOC) * _SXY, DIR[:, 2]], -1)


def s_three(t):                                 # the body splits into three spheres in a slowly turning triangle
    ang = np.array([90.0, 210.0, 330.0]) * math.pi / 180 + 0.12 * (t - 13.2)
    cen = np.stack([0.98 * np.cos(ang), np.zeros(3), 0.98 * np.sin(ang)], -1)
    C = cen[_GRP]
    r = 0.58 * (1 + 0.03 * np.sin(t * 2.4 + _GRP * 2.1))
    return C + _LOC * r[:, None], C


_STR = (DIR[:, 2] > 0.35) & (JIT2 < 0.12)      # ~4% of the beads: the grains that pour through the neck
_STR_T0 = 17.4 + 2.4 * JIT2[_STR] / 0.12       # one after another, each falls once (no teleport)
_STR_PILE = np.stack([0.28 * np.sqrt(_srng.uniform(0, 1, _STR.sum())) * np.cos(JIT2[_STR] * 80),
                      0.28 * np.sqrt(_srng.uniform(0, 1, _STR.sum())) * np.sin(JIT2[_STR] * 80),
                      -1.22 + 0.22 * JIT2[_STR] / 0.12], -1)


def s_hourglass(t):                             # two cones meeting at a narrow neck, a stream of beads pouring down
    z = DIR[:, 2]; az = np.abs(z)
    w = (0.1 + 0.85 * az ** 0.85) * np.sqrt(np.clip(1 - az ** 10, 0, 1))
    P = np.concatenate([_XY * w[:, None], (1.55 * z)[:, None]], 1)
    C = ZERO.copy()
    Ps = P[_STR]
    u = np.clip((t - _STR_T0) / 1.0, 0, 1)
    a = _smoother(np.clip(u / 0.3, 0, 1))[:, None]                     # slide down the glass to the neck
    top = np.array([0.0, 0.0, 0.12])
    b = (np.clip((u - 0.3) / 0.7, 0, 1) ** 1.6)[:, None]              # then fall (accelerating) onto the pile
    G = Ps + (top - Ps) * a
    G = G + (_STR_PILE - top) * b
    P[_STR] = G; C[_STR] = G
    return _rotx(P, 0.12), _rotx(C, 0.12)


def s_disc(t):                                  # flattens into a wavy disc that slowly turns
    th = np.arccos(np.clip(DIR[:, 2], -1, 1)); rho = 1.85 * np.sin(th / 2)
    ph = _PHI + 0.3 * (t - 20.0)
    wav = (0.12 * np.sin(3 * ph + 1.2 * t) + 0.04 * np.sin(6 * ph - t)) * np.clip(rho / 1.2, 0, 1)   # calm centre (no cross at the pole)
    P = np.stack([rho * np.cos(ph), rho * np.sin(ph), wav], -1)
    return _rotx(P, 0.42), ZERO


SHAPES = [(0.0, s_blob), (3.0, s_peanut), (6.4, s_bumpy), (9.8, s_dumbbell), (13.2, s_three), (16.6, s_hourglass),
          (20.0, s_disc), (23.4, s_blob)]
BURSTS = [(ts - 0.05, 0.45) for ts, _ in SHAPES[1:]]   # a gentle exhale drives every change
SPLIT_T = 13.2

# ---------------- OPENING: the 0021 "One Hit" formula, our look (owner Nov 18 2026: "an opening like One Hit Broke 2000
# Beads Into a Planet Ring"; picked: a heavy dark-glass sphere). A REAL SIMULATION, not formulas: the sphere streaks in
# from the lower-right foreground and hits the body at 0.35 s; time slows to 0.25x; beads struck by the sphere bounce
# off it (restitution), the impact shock bursts the whole shell open, ejecta splash back at and past the lens; from
# ~2.3 s the body's pull (a damped spring to each bead's home) draws every bead back along its own curved path.
T_IMP = 0.35


def op_speed(r):
    return 1.0 - 0.55 * float(sm(0.33, 0.46, r)) * (1 - float(sm(2.0, 2.7, r)))      # ~0.45x slow motion, ramps back as they regather


_ort = np.arange(0, 14.0, 0.001); _osp = np.array([op_speed(x) for x in _ort])
_ost = np.concatenate([[0.0], np.cumsum(_osp[:-1]) * 0.001])


def sim_t(r):
    return float(np.interp(r, _ort, _ost))


def real_of(sv):
    return float(np.interp(sv, _ost, _ort))


S_IMP = sim_t(T_IMP)
BALL_R, BALL_V = 0.3, 5.0
BALL_DIR = np.array([-0.3, 1.0, 0.2]); BALL_DIR /= np.linalg.norm(BALL_DIR)
_hp = np.array([0.35, -1.0, -0.22]); _hp /= np.linalg.norm(_hp)
HOME = DIR * blob(T_IMP)[:, None]
HIT = _hp * float(np.mean(np.linalg.norm(HOME[DIR @ _hp > 0.97], axis=1)))
BEAD_R = 0.013


def ball_at(sv):
    return HIT + BALL_DIR * (BALL_V * (sv - S_IMP) - BALL_R)


def _bake_opening():
    ds, keep = 1.0 / 480.0, 4
    s_end = sim_t(7.0)
    off = np.zeros((N, 3)); vel = np.zeros((N, 3))
    OFF, hits, shocked = [], [], False
    srng = np.random.default_rng(3030)
    jit = srng.normal(0, 1, (N, 3))
    nstep = int(s_end / ds) + 1
    for k in range(nstep):
        sv = k * ds
        if k % keep == 0:
            OFF.append(off.astype(np.float32))
        c = ball_at(sv)
        pos = HOME + off
        if sv >= S_IMP and not shocked:
            shocked = True
            d = np.linalg.norm(HOME - HIT, axis=1, keepdims=True)
            ur = (HOME - HIT) / np.maximum(d, 1e-6)
            vel += ur * 3.0 * np.exp(-d / 1.1)                  # the shock bursts the whole shell open
            vel += (-BALL_DIR * 0.8 + ur * 0.6) * 4.5 * np.exp(-d / 0.55)   # ejecta splash back at and past the lens
            vel += jit * 0.35 * np.exp(-d / 1.2)                # every bead a little different
        # the heavy sphere: beads in its way bounce off it (restitution 0.6), the sphere barely slows
        dc = pos - c; dist = np.linalg.norm(dc, axis=1)
        hit = dist < (BALL_R + BEAD_R)
        if hit.any():
            n_ = dc[hit] / np.maximum(dist[hit, None], 1e-6)
            rv = vel[hit] - BALL_DIR * BALL_V
            vn = (rv * n_).sum(1)
            app = vn < 0
            vh = vel[hit]; vh[app] -= (1.6 * vn[app])[:, None] * n_[app]; vel[hit] = vh
            off[hit] = c + n_ * (BALL_R + BEAD_R) - HOME[hit]
            hits.append((real_of(sv), int(app.sum())))
        # the body's pull: a damped spring home, eased in (no snap); a touch of drag before it
        kk = 18.0 * float(sm(RET0, RET0 + 0.5, real_of(sv)))
        cc = 0.9 + 2.0 * math.sqrt(kk) * 1.0                  # a soft drag: beads glide to a stop, never hang
        vel += (-kk * off - cc * vel) * ds
        off += vel * ds
    return np.stack(OFF), ds * keep, hits


OP_OFF, OP_DS, OP_HITS = _bake_opening()


def opening_off(t):
    sv = sim_t(t); x = sv / OP_DS
    i = int(x); f = x - i
    if i >= len(OP_OFF) - 1:
        return OP_OFF[-1]
    return OP_OFF[i] * (1 - f) + OP_OFF[i + 1] * f




def shape_state(t):
    i0 = 0
    for i in range(len(SHAPES)):
        if t >= SHAPES[i][0] + MORPH + 0.45:
            i0 = i
    P, C = SHAPES[i0][1](t)
    for i in range(i0 + 1, len(SHAPES)):
        ts = SHAPES[i][0]
        if t < ts:
            break
        w = _smoother(np.clip((t - ts - 0.4 * JIT) / MORPH, 0, 1))[:, None]
        P2, C2 = SHAPES[i][1](t)
        P = P + (P2 - P) * w; C = C + (C2 - C) * w
    return P, C


def positions(t):
    P, C = shape_state(t)
    dv = P - C; rn = np.linalg.norm(dv, axis=1, keepdims=True); nrm = dv / np.maximum(rn, 1e-6)
    # breathing + travelling ripples (life)
    P = P + nrm * (rn * 0.03 * math.sin(t * 2.2) + 0.022 * np.sin(14 * DIR[:, 2] - 5.0 * t + 6 * DIR[:, 0])[:, None])
    global P_REST; P_REST = P.copy()                   # colour is pinned to the bead on the calm shape
    glow = np.full(N, 0.9)
    global SIZE; SIZE = np.ones(N)
    for (tb, s) in BURSTS:
        u = t - tb
        if -0.02 < u < 2.5:
            # a gentle exhale: the shape blooms out over 0.7 s and settles; beads swell into soft orbs (no flicker)
            amp = s * (0.15 + 0.15 * JIT); uu = max(u, 0.0); TP = 0.7
            A = math.sin(0.5 * math.pi * uu / TP) ** 2 if uu < TP else math.exp(-(uu - TP) * 1.6)
            ang = np.arccos(np.clip(DIR @ np.array([0.3, -0.85, 0.42]), -1, 1))
            shock = 0.09 * s * np.exp(-((ang - 2.6 * u) / 0.25) ** 2) * math.exp(-u * 1.5)
            P = P + nrm * (amp * A + shock)[:, None]
            glow = glow + 1.0 * s * math.sin(0.5 * math.pi * min(1.0, uu / 0.3)) ** 2 * math.exp(-max(u - 0.3, 0.0) * 1.6) * (0.6 + 0.4 * JIT)
            grow = 1.0 + 1.2 * A * (0.7 + 0.6 * JIT) / 1.3
            SIZE = SIZE * grow; glow = glow / grow ** 2
    # sparks at the split: beads glow and swell while they travel to their new sphere
    if SPLIT_T < t < SPLIT_T + MORPH + 0.5:
        ws = _smoother(np.clip((t - SPLIT_T - 0.4 * JIT) / MORPH, 0, 1))
        sp = np.sin(math.pi * ws)
        glow = glow + 0.7 * sp; SIZE = SIZE * (1 + 0.4 * sp)
    if t < 7.0:
        oo = opening_off(t); P = P + oo
        # flying beads swell into soft glowing orbs (light spread over them): readable debris, no pixel flicker
        grow = 1.0 + 1.1 * np.clip(np.linalg.norm(oo, axis=1) / 1.2, 0, 1)
        SIZE = SIZE * grow; glow = glow / grow ** float(os.environ.get("DM_GP", "3.5"))
        u = t - T_IMP
        if u > 0:
            glow = glow * (1 + 0.3 * float(sm(0.0, 0.25, u)) * (1 - float(sm(0.4, 1.6, u))))   # a soft swell, no pop
    if t > DUST_T:
        # the ending: the body dissolves into drifting dust from right to left, every bead fading as it goes
        xr = P_REST[:, 0]; xn = (xr - xr.min()) / max(float(np.ptp(xr)), 1e-6)
        pd = _smoother(np.clip((t - DUST_T - 1.4 * (1 - xn) - 0.3 * JIT) / 1.8, 0, 1))
        drift = (nrm * 0.8 + np.array([0.3, 0.0, 0.45])) * (0.6 + 0.8 * JIT)[:, None]          # outward and gently up, like embers
        P = P + drift * (pd * 0.8)[:, None]
        glow = glow * (1 - pd) ** 1.5
        SIZE = SIZE * np.maximum(1 - pd, 0.0) ** 0.8        # each bead shrinks to nothing as it drifts: real dust, then gone
    return P, glow, np.zeros((N, 3))


def _ramp(stops, h):
    S = np.array(stops, float); n = len(S) - 1
    x = np.clip(h, 0, 1) * n; i = np.minimum(x.astype(int), n - 1); f = (x - i)[:, None]
    return S[i] * (1 - f) + S[i + 1] * f


def _cyc(stops, h):
    S = np.array(list(stops) + [stops[0]], float); n = len(S) - 1
    x = (h % 1.0) * n; i = np.minimum(x.astype(int), n - 1); f = (x - i)[:, None]
    return S[i] * (1 - f) + S[i + 1] * f


def _sm(a, b, x):
    k = np.clip((x - a) / (b - a), 0, 1); return k * k * (3 - 2 * k)


def colours(P, t):
    h = 0.5 + 0.5 * np.tanh(P[:, 2] * 0.9 + 0.6 * np.sin(P[:, 0] * 2 + t * 0.4))
    if PAL == "chameleon":
        # every story beat repaints the body: ice rain -> rose body on landing -> emerald wave from the eruption
        ice = _ramp([(0.3, 0.5, 1.0), (0.55, 0.85, 1.0), (0.9, 0.97, 1.0)], h)
        rose = _ramp([(1.0, 0.1, 0.6), (0.6, 0.15, 1.0), (1.0, 0.55, 0.85)], h)
        emer = _ramp([(0.05, 1.0, 0.55), (0.1, 0.75, 1.0), (0.75, 1.0, 0.9)], h)
        u1 = _sm(RET0, RET1, t - 0.12 * JIT)[:, None]
        u2 = np.clip((t - 2.5 - 0.25 * (P[:, 2] + 1.5)) / 0.3, 0, 1)[:, None]     # colour wave sweeps upward
        c = ice * (1 - u1) + rose * u1
        c = c * (1 - u2) + emer * u2
    elif PAL == "opal":
        # iridescent pearl: hue follows the angle to the camera, so rainbow bands slide over the body as it moves
        cp, _ = camera(t); cp = np.array(cp)
        n = P / np.maximum(np.linalg.norm(P, axis=1, keepdims=True), 1e-6)
        v = cp - P; v /= np.linalg.norm(v, axis=1, keepdims=True)
        cth = np.abs((n * v).sum(1))
        hue = 0.9 * cth + 0.08 * P[:, 2] + 0.08 * t + 0.15 * JIT * (P[:, 2] > 2.2)
        c = _cyc([(0.1, 0.9, 1.0), (0.2, 0.35, 1.0), (0.6, 0.2, 1.0), (1.0, 0.15, 0.75), (1.0, 0.6, 0.85), (0.4, 1.0, 0.75)], hue)
        c = c + (1 - c) * (0.35 * cth ** 6)[:, None]                                   # pearly white sheen where it faces us
    elif PAL == "sapphire":
        # deep sapphire body, champagne glitter waves rippling bottom -> top + scattered twinkles
        c = _ramp([(0.1, 0.25, 1.0), (0.35, 0.15, 1.0), (0.15, 0.6, 1.0)], h)
        zc = ((t * 0.8) % 1.0) * 5 - 2.5
        g = np.exp(-((P[:, 2] - zc) ** 2) / 0.03) + (np.sin(JIT * 517 + t * 5) > 0.985)
        g = np.clip(g, 0, 1)[:, None]
        c = c * (1 - g) + np.array([1.6, 1.4, 0.95]) * g
    elif PAL == "aurora":
        # aurora curtains: emerald / teal / violet / pink bands flowing sideways across the body
        # real aurora: emerald curtains low, teal in the middle, violet-pink crowns on top, fine vertical rays drifting sideways
        sway = 0.7 * np.sin(P[:, 2] * 1.3 + t * 0.5) + 0.3 * np.sin(P[:, 1] * 1.7 - t * 0.35)
        cur = 0.5 + 0.5 * np.sin(P[:, 0] * 1.8 + sway + t * 0.4)                 # broad curtains
        ray = 0.5 + 0.5 * np.sin(P[:, 0] * 11 + 2.0 * sway + t * 0.9)              # fine rays inside them
        top = 0.5 + 0.5 * np.tanh(P[:, 2] * 1.2 - 0.2 + 0.6 * (cur - 0.5))
        c = _ramp([(0.08, 1.0, 0.42), (0.1, 1.0, 0.62), (0.05, 0.75, 0.85), (0.5, 0.25, 1.0), (1.0, 0.35, 0.75)], top)
        c = c * ((0.6 + 0.6 * ray) * (0.75 + 0.35 * cur))[:, None]
    else:
        c = None
    if c is not None:
        return np.concatenate([c, np.ones((N, 1))], 1)
    """magenta -> violet -> cyan across the body, drifting slowly"""
    mag, vio, cya = np.array([1.0, 0.1, 0.75]), np.array([0.45, 0.15, 1.0]), np.array([0.1, 0.85, 1.0])
    c = np.where(h[:, None] < 0.5, mag + (vio - mag) * (h[:, None] * 2), vio + (cya - vio) * ((h[:, None] - 0.5) * 2))
    return np.concatenate([c, np.ones((N, 1))], 1)


camd = bpy.data.cameras.new("C"); camd.lens = 35; camd.sensor_width = 36
cam = bpy.data.objects.new("C", camd); scene.collection.objects.link(cam); scene.camera = cam
camd.dof.use_dof = True; camd.dof.aperture_fstop = 2.2


CAM_D = [(2.0, 4.7), (3.0, 5.1), (6.4, 5.0), (9.8, 5.8), (13.2, 5.7), (16.6, 6.0), (20.0, 7.0), (23.4, 5.2), (26.0, 7.2)]


def camera(t):
    # close, low, 3/4 (the 0021 hook framing) -> then every shape gets the distance that keeps it whole in frame;
    # one continuous glide, no spin; at the end the camera eases away while the body dissolves
    d, prev = 3.9 - 0.3 * float(sm(0.3, 1.4, t)), 3.6
    for tk, dk in CAM_D:
        d += (dk - prev) * float(sm(tk - 0.2, tk + 1.8, t)); prev = dk
    d += 0.08 * math.sin(t * 0.7) + sum(0.3 * bs * float(sm(tb - 0.3, tb + 0.8, t)) * (1 - float(sm(tb + 1.0, tb + 2.4, t))) for tb, bs in BURSTS)
    k = float(sm(1.4, 3.4, t))
    az = 0.42 * (1 - k) + 0.1 * k + 0.1 * math.sin(t * 0.17)
    el = -0.12 * (1 - k) + 0.06 * k + 0.03 * math.sin(t * 0.23)
    pos = Vector((d * math.sin(az), -d * math.cos(az), d * el + 0.1))
    return pos, Vector((0, 0, 0))


_hb = {}
for _t, _n in OP_HITS:
    _hb[round(_t * 20) / 20] = _hb.get(round(_t * 20) / 20, 0) + _n
_mo = np.linalg.norm(OP_OFF, axis=2).mean(1); _home = next((real_of(i * OP_DS) for i in range(len(_mo)) if real_of(i * OP_DS) > RET0 and _mo[i] < 0.03), RET1)
json.dump({"impact": T_IMP, "ret0": RET0, "land": _home, "hits": sorted(_hb.items()), "bursts": [{"t": b, "s": s} for b, s in BURSTS], "shapes": [ts for ts, _ in SHAPES], "split": SPLIT_T, "grains": sorted(float(x) + 1.0 for x in _STR_T0), "dust": DUST_T}, open(os.path.join(OUT, "events.json"), "w"))
frames = list(range(int(round(T0 * FPS)), int(round(T1 * FPS))))
if os.environ.get("DM_TIMES"):
    frames = [int(round(float(x) * FPS)) for x in os.environ["DM_TIMES"].split(",")]
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=0.3)
ball_o = bpy.context.active_object; ball_o.name = "Ball"; bpy.ops.object.shade_smooth()
GLASS = bpy.data.materials.new("DarkGlass"); GLASS.use_nodes = True
_gb = GLASS.node_tree.nodes["Principled BSDF"]
_gb.inputs["Base Color"].default_value = (0.03, 0.06, 0.055, 1); _gb.inputs["Roughness"].default_value = 0.015
_gb.inputs["Transmission Weight"].default_value = 1.0; _gb.inputs["IOR"].default_value = 1.52
_gb.inputs["Coat Weight"].default_value = 1.0; _gb.inputs["Coat Roughness"].default_value = 0.0
ball_o.data.materials.append(GLASS)


def setup(t):
    P, glow, vel = positions(t)
    vel_attr.data.foreach_set("vector", vel.reshape(-1).astype(np.float32))
    size_attr.data.foreach_set("value", SIZE.astype(np.float32))
    me.vertices.foreach_set("co", P.reshape(-1).astype(np.float32))
    col_attr.data.foreach_set("color", colours(P_REST, t).reshape(-1).astype(np.float32))
    glow_attr.data.foreach_set("value", glow.astype(np.float32))
    me.update()
    pos, look = camera(t)
    cam.location = pos; cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    camd.dof.focus_distance = (look - pos).length - 0.6
    bc = ball_at(sim_t(t)); ball_o.location = (float(bc[0]), float(bc[1]), float(bc[2]))
    ball_o.hide_render = bool(np.linalg.norm(bc) > 14.0)


# real motion blur by sub-frame accumulation (env DM_SUB, default 4): each frame = mean of SUB renders spread over a
# SPAN-frame shutter, averaged in linear light. Moving dots smear along their path instead of popping pixel to pixel,
# which reads like a real camera and keeps sparse dot clouds from flickering (photosensitivity check).
SUB = int(os.environ.get("DM_SUB", "4")); SPAN = 0.8
if SUB > 1:
    scene.cycles.samples = max(12, scene.cycles.samples // SUB)
for fr in frames[K::NW]:
    final = os.path.join(OUT, "f_%04d.png" % fr)
    if SUB == 1:
        setup(fr / FPS); scene.render.filepath = final; bpy.ops.render.render(write_still=True)
        continue
    acc = None
    for j in range(SUB):
        setup((fr + SPAN * ((j + 0.5) / SUB - 0.5)) / FPS)
        tmp = os.path.join(OUT, "_sub_%04d_%d.png" % (fr, j))
        scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(tmp); px = np.empty(len(im.pixels), np.float32); im.pixels.foreach_get(px)
        w, h = im.size; bpy.data.images.remove(im); os.remove(tmp)
        lin = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
        acc = lin if acc is None else acc + lin
    lin = acc / SUB
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    oi = bpy.data.images.new("acc", w, h, alpha=True); oi.pixels.foreach_set(np.clip(srgb, 0, 1).astype(np.float32))
    oi.filepath_raw = final; oi.file_format = "PNG"; oi.save(); bpy.data.images.remove(oi)
print("done")
