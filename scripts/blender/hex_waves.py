# 0031 hexagon columns - "beautiful and powerful, no flower/star shapes" (owner, Nov 20 2026, after the calm test: "no star
# or flower shapes, they look bad - use more beautiful, brutal effects"). The CLAUDE.md line for the channel: pure,
# mesmerizing physical phenomena one after another, each more striking - ripples, interference, vortex, a giant wave.
# Smooth and pleasant: no sparks, no bouncing.
#   0.0-2.6  three chrome spheres glide in and settle; their smooth ripples cross into interference patterns (ice/silver)
#   4.0-7.4  the field winds into a deep whirlpool with spiral grooves; the spheres orbit down into it (violet/cyan)
#   7.6      the funnel rebounds: a huge smooth ring wave rolls across the whole field (magenta -> gold crest)
#   9.5-12   everything settles
# The colour travels with each wave, column by column (w1 = into the vortex, w2 = the giant wave has passed).
# Usage: blender -b --factory-startup -P hex_waves.py -- <outdir> <seconds> <fps> [first_frame last_frame]
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
DROPS = [(0.6, np.array([0.0, 0.0])), (1.7, np.array([-0.8, 0.55])), (2.6, np.array([0.75, -0.35]))]
TV0, TV1, TV2 = 4.0, 5.5, 7.4         # the vortex forms, is full, lets go
TB = 7.6                              # the rebound + the giant ring wave
me = bpy.data.objects["Columns"].data
sph0 = bpy.data.objects["Sphere"]
cam_o = scene.camera
bpy.data.objects["Key"].visible_glossy = False
spheres = [sph0]
for k in range(2):                                   # two more chrome spheres
    o = sph0.copy(); o.data = sph0.data; scene.collection.objects.link(o); spheres.append(o)

cxs, cys = [], []
for q in range(-NQ // 2, NQ // 2):
    for rr in range(-NR // 2, NR // 2):
        cxs.append(math.sqrt(3) * RH * (q + rr / 2)); cys.append(1.5 * RH * rr)
cx, cy = np.array(cxs), np.array(cys)
NC = len(cx)
r0 = np.hypot(cx, cy); th0 = np.arctan2(cy, cx)
rd = [np.hypot(cx - P[0], cy - P[1]) for _, P in DROPS]
co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co)
co = co.reshape(NC, 24, 3)
arng = np.random.default_rng(11)
W_I = arng.uniform(1.5, 3.0, NC); P_I = arng.uniform(0, 2 * math.pi, NC)
jit = arng.uniform(-0.03, 0.03, NC)


def ss(a, b, x):
    k = np.clip((x - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


# ---- soft glow + three palettes mixed per column ----
_rim = bpy.data.materials["Rim"]; _nt = _rim.node_tree; _N, _L = _nt.nodes, _nt.links
for n_ in _N:
    if n_.bl_idname == "ShaderNodeMath" and n_.operation == "POWER":
        n_.inputs[1].default_value = 1.8
    if n_.bl_idname == "ShaderNodeMath" and n_.operation == "MULTIPLY_ADD":
        n_.inputs[1].default_value = 10.0; n_.inputs[2].default_value = 0.1
STORIES = {
    "ice": [(0.01, 0.02, 0.07), (0.04, 0.16, 0.38), (0.25, 0.55, 0.95), (0.55, 0.78, 1.0), (0.82, 0.9, 1.0), (0.95, 0.97, 1.0)],
    "violet": [(0.01, 0.0, 0.06), (0.12, 0.03, 0.36), (0.45, 0.14, 0.95), (0.3, 0.62, 1.0), (0.62, 0.92, 1.0), (0.9, 0.97, 1.0)],
    "warm": [(0.05, 0.0, 0.04), (0.34, 0.03, 0.22), (0.95, 0.2, 0.52), (1.0, 0.48, 0.5), (1.0, 0.78, 0.38), (1.0, 0.94, 0.82)],
}
_heat = _N["Attribute"]; _bsdf = _N["Principled BSDF"]


def _make_ramp(cols):
    rn = _N.new("ShaderNodeValToRGB"); el = rn.color_ramp.elements
    el[0].position = 0.0; el[1].position = 1.0
    for pos in (0.22, 0.42, 0.6, 0.8):
        el.new(pos)
    for e_, c_ in zip(sorted(el, key=lambda z: z.position), cols):
        e_.color = (*c_, 1)
    _L.new(_heat.outputs["Fac"], rn.inputs["Fac"])
    return rn


def _mix(a_col, b_col, fac_attr):
    at_ = _N.new("ShaderNodeAttribute"); at_.attribute_name = fac_attr
    mx = _N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    ci = [x for x in mx.inputs if x.type == "RGBA"]
    _L.new(at_.outputs["Fac"], [x for x in mx.inputs if x.name == "Factor" and x.type == "VALUE"][0])
    _L.new(a_col, ci[0]); _L.new(b_col, ci[1])
    return [x for x in mx.outputs if x.type == "RGBA"][0]


_c = _mix(_mix(_make_ramp(STORIES["ice"]).outputs["Color"], _make_ramp(STORIES["violet"]).outputs["Color"], "w1"),
          _make_ramp(STORIES["warm"]).outputs["Color"], "w2")
_L.new(_c, _bsdf.inputs["Emission Color"])
me.attributes.new("w1", "FLOAT", "FACE"); me.attributes.new("w2", "FLOAT", "FACE")


# ---- the field ----
def ripples(rr_, u):
    A = 0.14 * (1 - math.exp(-u * 8)) * math.exp(-u / 3.0)
    q = rr_ + jit
    return A * np.cos(np.clip((q - (0.15 + 0.6 * u)), -3, 0) * 9.0) * np.exp(-((q - (0.15 + 0.6 * u)) / 0.9) ** 2) * (q < 0.15 + 0.6 * u + 0.25)


def vortex_w(t):
    return float(ss(TV0, TV1, t) * (1 - ss(TV2, TV2 + 0.5, t)))


def bloom(t):
    u = t - TB
    if u < 0:
        return 0.0
    dome = 0.42 * (1 - math.exp(-u * 6)) * math.exp(-u / 0.7) * np.exp(-(r0 / 0.6) ** 2)
    wave = 0.42 * (1 - math.exp(-u * 5)) * math.exp(-u / 2.6) * np.exp(-((r0 - (0.35 + 1.05 * u)) / 0.34) ** 2)
    return dome + wave


def field(t):
    h = BASE + 0.04 * np.sin(2.0 * cx + 1.0 * t) * np.sin(1.6 * cy - 0.7 * t + 0.6) + 0.018 * np.sin(3.6 * (cx + cy) - 1.2 * t)
    h = h + 0.008 * np.sin(W_I * t + P_I)
    fade_r = 1 - ss(TV0, TV1, t)                                 # the ripples give way to the vortex
    for (T, _), rr_ in zip(DROPS, rd):
        if t >= T:
            h = h + fade_r * ripples(rr_, t - T)
    w = vortex_w(t)
    if w > 0:                                                    # a deep whirlpool with turning spiral grooves
        funnel = -0.7 * np.exp(-(r0 / 1.15) ** 2) + 0.08 * np.exp(-((r0 - 1.6) / 0.28) ** 2)
        grooves = 0.12 * np.sin(4 * th0 + 9.0 * r0 - 2.6 * (t - TV0)) * np.exp(-r0 / 1.5) * ss(0.12, 0.35, r0)
        h = h + w * (funnel + grooves)
    return h + bloom(t)


def h_at(h, p):
    return float(h[np.argmin((cx - p[0]) ** 2 + (cy - p[1]) ** 2)])


ENTRY = [Vector((0.42, -0.75, 1.75)), Vector((-1.6, 1.6, 2.4)), Vector((1.9, 0.6, 2.2))]


def sphere_pos(i, t):
    T, P = DROPS[i]
    h = field(t)
    if t < T - 0.6:
        if i == 0:
            return ENTRY[0].copy()                                            # on frame 0: right there
        return Vector((ENTRY[i].x, ENTRY[i].y, ENTRY[i].z + 3.0))           # still out of sight
    if t < T:                                                                 # glides in and settles softly
        k = float(ss(T - 0.6, T, t))
        return ENTRY[i].lerp(Vector((P[0], P[1], h_at(h, P) + 0.26)), k)
    k = float(ss(TV0, TV1 + 0.6, t))                                         # drawn into an even orbit round the vortex
    ph = 2 * math.pi * i / 3 + 2.6 * max(0.0, t - TV0) * (1 - 0.6 * float(ss(TV2, TB + 1.5, t)))
    orb = 0.72
    p = np.array(P) * (1 - k) + np.array([orb * math.cos(ph), orb * math.sin(ph)]) * k
    rho = math.hypot(*p)
    if t > TB:                                                                # the giant wave carries them a little outward
        u = t - TB; push = 0.35 * (1 - math.exp(-u * 2.5))
        p = p * (1 + push / max(rho, 0.05))
    return Vector((p[0], p[1], h_at(h, p) + 0.26))


def cam_at(t):
    keys = [(0.0, 1.2, -2.15, 3.3, 0.0, 0.3, -0.7), (3.6, 1.5, -1.9, 3.0, -0.05, 0.2, -0.6),
            (6.8, 1.05, -1.45, 3.05, 0.0, 0.1, -0.55), (9.0, 1.9, -2.55, 3.4, 0.0, 0.3, -0.6), (12.0, 2.0, -2.7, 3.6, 0.0, 0.35, -0.65)]
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if t <= tb:
            k = float(ss(ta, tb, t)); v = [x * (1 - k) + y * k for x, y in zip(a, b)]
            return Vector(v[:3]), Vector(v[3:])
    return Vector(keys[-1][1:4]), Vector(keys[-1][4:])


scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.5
for i, o in enumerate(spheres):
    for _f in range(-1, int(SECS * FPS) + 2):
        o.location = sphere_pos(i, _f / FPS); o.keyframe_insert("location", frame=_f)

events = []
hprev = field(-1.0 / FPS); prev = hprev.copy()
heat_s = np.zeros(NC)
w1 = np.zeros(NC); w2 = np.zeros(NC)
for f in range(int(SECS * FPS)):
    t = f / FPS
    h = field(t)
    crossed = ((prev < BASE + 0.1) & (h >= BASE + 0.1)) | ((prev > BASE - 0.12) & (h <= BASE - 0.12))
    events.append({"t": t, "n": int(crossed.sum()), "x": float(cx[crossed].mean()) if crossed.any() else 0.0})
    prev = h
    vel = (h - hprev) * FPS; hprev = h.copy()
    depth = np.clip((BASE - h) / 0.5, 0, 1)                         # the vortex glows in its grooves and its throat
    gpat = np.sin(4 * th0 + 9.0 * r0 - 2.6 * (t - TV0)) * np.exp(-r0 / 1.5) * ss(0.12, 0.35, r0)
    groove_glow = np.clip(gpat, 0, 1) * 0.85 * vortex_w(t) * np.exp(-(r0 / 1.3) ** 2)   # the spiral grooves glow as lines
    heat_raw = np.clip((h - 0.12) / 0.55 + np.clip(np.abs(vel) * 0.12, 0, 0.15) + 0.7 * depth * vortex_w(t) + groove_glow, 0, 1)
    heat_s = np.minimum(np.maximum(heat_raw, heat_s * 0.95), heat_s + 0.04)
    w1 = np.maximum(w1, np.clip(vortex_w(t) * 1.4 - (r0 / 2.6), 0, 1))  # the violet runs in with the vortex
    if t > TB:
        w2 = np.maximum(w2, ss(0.0, 0.25, (0.35 + 1.05 * (t - TB)) - r0))   # the warm colour follows the giant wave
    if f < F0 or f > F1:
        continue
    co[:, 6:12, 2] = h[:, None] - CH; co[:, 12:18, 2] = h[:, None]; co[:, 18:24, 2] = h[:, None] + 0.002
    me.vertices.foreach_set("co", co.ravel()); me.update()
    me.attributes["hn"].data.foreach_set("value", np.repeat(heat_s.astype(np.float32), 19))
    me.attributes["w1"].data.foreach_set("value", np.repeat(w1.astype(np.float32), 19))
    me.attributes["w2"].data.foreach_set("value", np.repeat(w2.astype(np.float32), 19))
    for i, o in enumerate(spheres):
        o.rotation_euler = (0.15 * math.sin(0.5 * t + i), 0.0, 0.6 * t + i)
    scene.frame_set(f)
    loc, tgt = cam_at(t)
    cam_o.location = loc; cam_o.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam_o.data.dof.focus_distance = (Vector((0, 0, 0.1)) - loc).length
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("frame", f, flush=True)
beats = [{"t": T, "kind": "land", "x": float(P[0]), "amp": 0.6} for T, P in DROPS]
beats += [{"t": TV0, "kind": "swirl", "x": 0.0, "amp": 0.7}, {"t": TB, "kind": "wave", "x": 0.0, "amp": 1.0}]
json.dump({"fps": FPS, "secs": SECS, "t_hit": DROPS[0][0], "beats": beats, "frames": events}, open(os.path.join(OUTDIR, "events.json"), "w"))
print("done")
