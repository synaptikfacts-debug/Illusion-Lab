# 0031 hexagon columns - CALM ASMR version (owner, Nov 20 2026, confirmed: "yes, this": thousands of columns moving
# smoothly in soft waves, every few seconds they settle into a beautiful abstract shape - each with its own harmonious
# colour story - soft tactile taps on every move, no sparks, no explosions; the 0011 "4096 pins" formula).
#   0.0   the field already drifts in soft waves (ice blue / silver); the chrome sphere glides in from the lens
#   0.6   it settles softly in the centre: one smooth ring spreads
#   2.6   a sweep runs outward and the columns settle one by one into a FLOWER MANDALA (rose quartz -> soft gold)
#   7.6   a sweep runs AROUND the field and re-orders the columns into a SPIRAL (mint -> aqua), slowly turning
# Every column taps once when it moves (events.json -> the sound).
# Usage: blender -b --factory-startup -P hex_calm.py -- <outdir> <seconds> <fps> [first_frame last_frame]
import json
import math
import os
import sys

import numpy as np

_args = sys.argv[sys.argv.index("--") + 1:]
OUTDIR = os.path.abspath(_args[0]); SECS = float(_args[1]); FPS = int(_args[2])
F0 = int(_args[3]) if len(_args) > 3 else 0
F1 = int(_args[4]) if len(_args) > 4 else int(SECS * FPS) - 1
os.makedirs(OUTDIR, exist_ok=True)
sys.argv = sys.argv[:sys.argv.index("--") + 1] + [os.path.join(OUTDIR, "_still.png")]
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hex_columns.py"), encoding="utf-8").read()
exec(_src.split("bpy.ops.render.render(write_still=True)")[0])

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

BASE = 0.18
T_LAND = 0.6
SWEEPS = [  # (start, duration, from-shape, to-shape, mode)
    (2.6, 2.8, "rest", "flower", "out"),
    (7.6, 2.8, "flower", "spiral", "around"),
]
me = bpy.data.objects["Columns"].data
sph = bpy.data.objects["Sphere"]
cam_o = scene.camera
bpy.data.objects["Key"].visible_glossy = False

cxs, cys = [], []
for q in range(-NQ // 2, NQ // 2):
    for rr in range(-NR // 2, NR // 2):
        cxs.append(math.sqrt(3) * RH * (q + rr / 2)); cys.append(1.5 * RH * rr)
cx, cy = np.array(cxs), np.array(cys)
NC = len(cx)
r0 = np.hypot(cx, cy); th0 = np.arctan2(cy, cx)
co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co)
co = co.reshape(NC, 24, 3)
arng = np.random.default_rng(11)
W_I = arng.uniform(1.5, 3.0, NC); P_I = arng.uniform(0, 2 * math.pi, NC)
jit = arng.uniform(-0.05, 0.05, NC)

# softer, pleasant light: gentle glow, never white-hot
rim_nodes = bpy.data.materials["Rim"].node_tree.nodes
for n_ in rim_nodes:
    if n_.bl_idname == "ShaderNodeMath" and n_.operation == "POWER":
        n_.inputs[1].default_value = 1.8
    if n_.bl_idname == "ShaderNodeMath" and n_.operation == "MULTIPLY_ADD":
        n_.inputs[1].default_value = 9.0; n_.inputs[2].default_value = 0.12
STORIES = {   # 6 stops: calm -> crest
    "ice": [(0.01, 0.02, 0.07), (0.04, 0.16, 0.38), (0.25, 0.55, 0.95), (0.55, 0.78, 1.0), (0.82, 0.9, 1.0), (0.95, 0.97, 1.0)],
    "rose": [(0.05, 0.01, 0.04), (0.3, 0.06, 0.2), (0.92, 0.32, 0.52), (1.0, 0.58, 0.6), (1.0, 0.76, 0.4), (1.0, 0.9, 0.75)],
    "mint": [(0.0, 0.03, 0.04), (0.0, 0.2, 0.22), (0.08, 0.66, 0.7), (0.38, 0.94, 0.72), (0.72, 1.0, 0.86), (0.92, 1.0, 0.95)],
}
_rim = bpy.data.materials["Rim"]; _nt = _rim.node_tree; _N, _L = _nt.nodes, _nt.links
_ramp0 = _N["Color Ramp"]; _heat = _N["Attribute"]
_bsdf = _N["Principled BSDF"]


def _make_ramp(cols):
    rn = _N.new("ShaderNodeValToRGB"); el = rn.color_ramp.elements
    el[0].position = 0.0; el[1].position = 1.0
    for pos in (0.22, 0.42, 0.6, 0.8):
        el.new(pos)
    for e_, c_ in zip(sorted(el, key=lambda z: z.position), cols):
        e_.color = (*c_, 1)
    _L.new(_heat.outputs["Fac"], rn.inputs["Fac"])
    return rn


_r_ice, _r_rose, _r_mint = _make_ramp(STORIES["ice"]), _make_ramp(STORIES["rose"]), _make_ramp(STORIES["mint"])


def _mix(a_col, b_col, fac_attr):
    at_ = _N.new("ShaderNodeAttribute"); at_.attribute_name = fac_attr
    mx = _N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    ci = [x for x in mx.inputs if x.type == "RGBA"]
    _L.new(at_.outputs["Fac"], [x for x in mx.inputs if x.name == "Factor" and x.type == "VALUE"][0])
    _L.new(a_col, ci[0]); _L.new(b_col, ci[1])
    return [x for x in mx.outputs if x.type == "RGBA"][0]


_c1 = _mix(_r_ice.outputs["Color"], _r_rose.outputs["Color"], "w1")
_c2 = _mix(_c1, _r_mint.outputs["Color"], "w2")
_L.new(_c2, _bsdf.inputs["Emission Color"])
me.attributes.new("w1", "FLOAT", "FACE"); me.attributes.new("w2", "FLOAT", "FACE")


def ss(a, b, x):
    k = np.clip((x - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


def shape(name, t):
    if name == "rest":
        return BASE + 0.045 * np.sin(2.0 * cx + 1.0 * t) * np.sin(1.6 * cy - 0.7 * t + 0.6) + 0.02 * np.sin(3.6 * (cx + cy) - 1.2 * t)
    if name == "flower":                                     # a six-petal mandala that fits the honeycomb
        petal = (0.5 + 0.5 * np.cos(6 * th0)) ** 1.5 * np.exp(-((r0 - 0.78) / 0.36) ** 2)
        inner = 0.6 * np.exp(-((r0 - 0.32) / 0.1) ** 2) * (0.6 + 0.4 * np.cos(6 * th0 + math.pi))
        outer = 0.45 * np.exp(-((r0 - 1.5) / 0.1) ** 2) * (0.55 + 0.45 * np.cos(12 * th0))
        return BASE + 0.3 * (petal + inner + outer) + 0.008 * np.sin(W_I * t + P_I)
    if name == "spiral":                                     # three soft arms, slowly turning
        return BASE + 0.26 * (0.5 + 0.5 * np.sin(3 * th0 + 6.0 * r0 - 0.35 * t)) * np.exp(-r0 / 2.0) * ss(0.22, 0.55, r0) + 0.008 * np.sin(W_I * t + P_I)
    raise ValueError(name)


def landing_ring(t):
    u = t - T_LAND
    if u < 0:
        return 0.0
    A = 0.16 * (1 - math.exp(-u * 8)) * math.exp(-u / 1.8)
    R = 0.2 + 0.55 * u
    return A * (np.exp(-((r0 + jit - R) / 0.2) ** 2) + 0.45 * np.exp(-((r0 + jit - R + 0.6) / 0.18) ** 2))


def progress(sw, t):
    T, D, _, _, mode = sw
    if mode == "out":                                        # the sweep runs outward from the centre
        delay = (r0 / r0.max()) * 0.62 * D + jit
    else:                                                    # the sweep runs around the field
        delay = ((th0 + math.pi) / (2 * math.pi)) * 0.62 * D + 0.15 * (r0 / r0.max()) * D + jit
    return ss(T + delay, T + delay + 0.38 * D, t)


def field(t):
    h = shape("rest", t)
    for sw in SWEEPS:
        if t < sw[0]:
            break
        p = progress(sw, t)
        h = h * (1 - p) + shape(sw[3], t) * p + 0.07 * np.sin(np.pi * p)   # each column lifts softly as it moves
    return h + landing_ring(t) - 0.12 * (1 - math.exp(-max(0.0, t - T_LAND) * 6)) * np.exp(-(r0 / 0.3) ** 2) * (t >= T_LAND)


def sphere_at(t):
    h = field(t)
    near = np.argsort(r0)[:7]; rest = float(h[near].mean()) + 0.26
    if t < T_LAND:                                           # glides in from the lens and settles (eases into the landing)
        k = float(ss(0.0, T_LAND, max(0.0, t)))
        P0 = Vector((0.5, -1.15, 2.2)); Pe = Vector((0.0, 0.0, rest))
        return P0.lerp(Pe, k)
    return Vector((0.0, 0.0, rest))


def cam_at(t):
    a = math.radians(-14.0 * t / SECS)
    b = Vector((1.15, -2.1, 3.3 - 0.35 * t / SECS))
    loc = Vector((b.x * math.cos(a) - b.y * math.sin(a), b.x * math.sin(a) + b.y * math.cos(a), b.z))
    return loc, Vector((0.0, 0.35, -0.7))


scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.5
DUSTM = bpy.data.materials.new("Mote"); DUSTM.use_nodes = True
dmb = DUSTM.node_tree.nodes["Principled BSDF"]; dmb.inputs["Base Color"].default_value = (0.95, 0.92, 1.0, 1)
dmb.inputs["Emission Color"].default_value = (0.9, 0.85, 1.0, 1); dmb.inputs["Emission Strength"].default_value = 0.5
drng = np.random.default_rng(29); ND = 260
d_p0 = np.column_stack([drng.uniform(-2.2, 2.2, ND), drng.uniform(-1.6, 2.6, ND), drng.uniform(0.35, 1.9, ND)])
d_ph = drng.uniform(0, 2 * math.pi, (ND, 3)); d_w = drng.uniform(0.15, 0.4, (ND, 3))
dme = bpy.data.meshes.new("Motes"); dme.from_pydata(d_p0.tolist(), [], [])
dust_obj = bpy.data.objects.new("Motes", dme); scene.collection.objects.link(dust_obj)
dg_ = dust_obj.modifiers.new("M", "NODES"); dgt = bpy.data.node_groups.new("Motes", "GeometryNodeTree")
dgt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
dgt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
di = dgt.nodes.new("NodeGroupInput"); do_ = dgt.nodes.new("NodeGroupOutput"); dip = dgt.nodes.new("GeometryNodeInstanceOnPoints")
dico = dgt.nodes.new("GeometryNodeMeshIcoSphere"); find(dico.inputs, "Radius").default_value = 0.0035
dsm = dgt.nodes.new("GeometryNodeSetMaterial"); find(dsm.inputs, "Material").default_value = DUSTM
dgt.links.new(di.outputs[0], dip.inputs["Points"]); dgt.links.new(dico.outputs["Mesh"], dip.inputs["Instance"])
dgt.links.new(dip.outputs["Instances"], dsm.inputs["Geometry"]); dgt.links.new(dsm.outputs["Geometry"], do_.inputs[0])
dg_.node_group = dgt

for _f in range(-1, int(SECS * FPS) + 2):
    sph.location = sphere_at(_f / FPS); sph.keyframe_insert("location", frame=_f)
events = []
hprev = field(-1.0 / FPS)
heat_s = np.zeros(NC)
pprev = [np.zeros(NC) for _ in SWEEPS]
for f in range(int(SECS * FPS)):
    t = f / FPS
    h = field(t)
    moved = np.zeros(NC, dtype=bool)                          # every column taps once, the moment it moves
    for i, sw in enumerate(SWEEPS):
        p = progress(sw, t) if t >= sw[0] else np.zeros(NC)
        moved |= (pprev[i] < 0.5) & (p >= 0.5); pprev[i] = p
    events.append({"t": t, "n": int(moved.sum()), "x": float(cx[moved].mean()) if moved.any() else 0.0})
    vel = (h - hprev) * FPS; hprev = h.copy()
    heat_raw = np.clip((h - 0.12) / 0.55 + np.clip(vel * 0.15, 0, 0.12), 0, 1)
    heat_s = np.minimum(np.maximum(heat_raw, heat_s * 0.95), heat_s + 0.04)
    if f < F0 or f > F1:
        continue
    co[:, 6:12, 2] = h[:, None] - CH; co[:, 12:18, 2] = h[:, None]; co[:, 18:24, 2] = h[:, None] + 0.002
    me.vertices.foreach_set("co", co.ravel()); me.update()
    me.attributes["hn"].data.foreach_set("value", np.repeat(heat_s.astype(np.float32), 19))
    w1 = progress(SWEEPS[0], t) if t >= SWEEPS[0][0] else np.zeros(NC)
    w2 = progress(SWEEPS[1], t) if t >= SWEEPS[1][0] else np.zeros(NC)
    me.attributes["w1"].data.foreach_set("value", np.repeat(w1.astype(np.float32), 19))
    me.attributes["w2"].data.foreach_set("value", np.repeat(w2.astype(np.float32), 19))
    P = d_p0 + 0.1 * np.sin(d_w * t + d_ph); dme.vertices.foreach_set("co", P.astype(np.float32).ravel()); dme.update()
    sph.rotation_euler = (0.15 * math.sin(0.5 * t), 0.0, 0.5 * t)
    scene.frame_set(f)
    loc, tgt = cam_at(t)
    cam_o.location = loc; cam_o.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam_o.data.dof.focus_distance = (Vector((0, 0, 0.3)) - loc).length
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("frame", f, flush=True)
beats = [{"t": T_LAND, "kind": "land", "x": 0.0, "amp": 0.6}]
json.dump({"fps": FPS, "secs": SECS, "t_hit": T_LAND, "beats": beats, "frames": events}, open(os.path.join(OUTDIR, "events.json"), "w"))
print("done")
