# 0031 hexagon columns - motion test v3 (owner, Nov 20 2026: "colours are boring, effects too - I see nothing that would
# hold me to the end"). The field is a living light sculpture now (every column top glows on a heat palette: deep indigo
# -> cyan -> violet -> magenta -> gold -> white-hot, by height and speed), and something bigger happens every 1-2 s:
#   0.00  the chrome sphere dives in, huge in front of the lens, over a breathing field of colour
#   0.35  IMPACT 1: crater, a ring of light races out, gold sparks
#   1.35  the sphere BOUNCES out in a high arc ...
#   2.15  IMPACT 2 somewhere else: magenta sparks; the two ring systems cross -> interference patterns
#   3.6   the waves wind into a spinning spiral galaxy that carries the sphere along its arms into the centre
#   6.4   ERUPTION: the centre shoots up into a tower of white-hot columns and lifts the sphere on top; a gold fountain
# Writes PNG frames + events.json (beats + per-frame crest crossings) for the sound.
# Usage: blender -b --factory-startup -P hex_anim.py -- <outdir> <seconds> <fps> [first_frame last_frame]
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
exec(_src.split("bpy.ops.render.render(write_still=True)")[0])          # builds the approved scene (no render)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

BASE = 0.18
T1, TB0, T2 = 0.35, 1.35, 2.15                 # impact 1, the bounce leaves, impact 2
TS0, TS1, TR1 = 3.6, 4.6, 6.2                  # the spiral forms, is full, the ride ends at the centre
TE = 6.4                                       # the eruption
P1 = np.array([0.0, 0.0]); P2 = np.array([0.85, 0.55])
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
r2 = np.hypot(cx - P2[0], cy - P2[1])
jit = np.random.default_rng(7).uniform(-0.03, 0.03, NC)
co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get("co", co)
co = co.reshape(NC, 24, 3)
arng = np.random.default_rng(11)
W_I = arng.uniform(2.0, 4.5, NC); P_I = arng.uniform(0, 2 * math.pi, NC)


def ss(a, b, x):
    k = np.clip((x - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


def rings(rr_, u, amp=0.28, speed=0.72):
    A = amp * (1 - math.exp(-u * 14.0)) * math.exp(-u / 2.2)
    R = 0.25 + speed * u; q = rr_ + jit
    return A * (np.exp(-((q - R) / 0.17) ** 2) + 0.5 * np.exp(-((q - R + 0.55) / 0.15) ** 2) + 0.25 * np.exp(-((q - R + 1.05) / 0.14) ** 2))


def tower_e(t):
    if t < TE:
        return 0.0
    u = t - TE
    return 1.0 - math.exp(-u * 6.0) * (1.0 + 6.0 * u)         # shoots up and settles (no bounce: no flicker)


def field(t):
    h = BASE + 0.05 * np.sin(2.2 * cx + 1.3 * t) * np.sin(1.7 * cy - 0.9 * t + 0.6) + 0.025 * np.sin(4.1 * (cx + cy) - 1.7 * t)
    h = h + 0.011 * np.sin(W_I * t + P_I)
    if t >= T1:                                                 # impact 1: crater (it heals once the sphere bounces out)
        u = t - T1
        heal = math.exp(-max(0.0, t - TB0) * 3.0)
        h = h - 0.32 * (1 - math.exp(-u * 9.0)) * heal * np.exp(-((r0 + jit) / 0.4) ** 2) + rings(r0, u)
    if t >= T2:                                                 # impact 2 (its crater heals when the ride starts)
        u = t - T2
        heal = math.exp(-max(0.0, t - 4.0) * 2.5)
        h = h - 0.3 * (1 - math.exp(-u * 9.0)) * heal * np.exp(-((r2 + jit) / 0.38) ** 2) + rings(r2, u)
    w = float(ss(TS0, TS1, t) * (1 - ss(6.1, 6.6, t)))          # the spinning spiral galaxy
    if w > 0:
        sp = 0.34 * np.sin(3 * th0 + 7.0 * r0 - 3.2 * (t - TS0)) * np.exp(-r0 / 2.2) * ss(0.2, 0.55, r0)
        h = h * (1 - w) + (BASE + sp + 0.011 * np.sin(W_I * t + P_I)) * w
    e = tower_e(t)
    if e != 0.0:                                                # the eruption: a tower + a ring of columns thrown outward
        u = t - TE
        h = h + 1.05 * e * np.exp(-((r0 + 0.5 * jit) / 0.5) ** 3)
        h = h + 0.2 * math.exp(-u / 1.2) * np.exp(-((r0 - (0.65 + 1.7 * u)) / 0.22) ** 2)
    return h


def h_at(h, p):
    return float(h[np.argmin((cx - p[0]) ** 2 + (cy - p[1]) ** 2)])


def sphere_at(t):
    h = field(t)
    if t < T1:
        k = (max(0.0, t) / T1) ** 1.6
        P0 = Vector((0.5, -1.15, 2.2)); Pe = Vector((0.0, 0.0, h_at(h, P1) + 0.27))
        return P0.lerp(Pe, k)
    if t < TB0:
        return Vector((P1[0], P1[1], h_at(h, P1) + 0.27))
    if t < T2:                                                  # the bounce: a high arc to the second spot
        k = (t - TB0) / (T2 - TB0)
        p = P1 + (P2 - P1) * k
        z0 = h_at(h, P1) * (1 - k) + h_at(h, P2) * k + 0.27
        return Vector((p[0], p[1], z0 + 0.9 * 4 * k * (1 - k)))
    if t < 4.0:
        return Vector((P2[0], P2[1], h_at(h, P2) + 0.27))
    if t < TR1:                                                 # carried along the spiral arm into the centre
        k = float(ss(4.0, TR1, t))
        rho = math.hypot(*P2) * (1 - k); phi = math.atan2(P2[1], P2[0]) + 2 * math.pi * 1.25 * k
        p = np.array([rho * math.cos(phi), rho * math.sin(phi)])
        return Vector((p[0], p[1], h_at(h, p) + 0.27))
    near = np.argsort(r0)[:7]                                     # on the centre; the tower lifts it, seated on its top
    return Vector((0.0, 0.0, float(h[near].mean()) + 0.25))


def shock(t):
    s_ = np.zeros(NC)
    for Tk, rr_ in ((T1, r0), (T2, r2)):
        u = t - Tk
        if 0 <= u < 1.4:
            s_ += 0.6 * math.exp(-u / 0.45) * np.exp(-((rr_ - (0.25 + 2.4 * u)) / 0.09) ** 2)
    return s_


def cam_at(t):
    """high 3/4 -> orbit lower over the interference -> low and close on the spiral -> pull back up for the tower"""
    keys = [(0.0, 1.15, -2.1, 3.35, 0.05, 0.45, -0.8), (2.2, 1.6, -1.9, 3.0, 0.3, 0.4, -0.6),
            (4.4, 1.9, -1.2, 2.1, 0.1, 0.3, -0.3), (6.2, 1.5, -1.3, 1.7, 0.0, 0.1, 0.1), (8.0, 1.9, -2.2, 2.6, 0.0, 0.2, 0.55)]
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if t <= tb:
            k = float(ss(ta, tb, t)); v = [x * (1 - k) + y * k for x, y in zip(a, b)]
            return Vector(v[:3]), Vector(v[3:])
    return Vector(keys[-1][1:4]), Vector(keys[-1][4:])


# ---------------- effects ----------------
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.5


def emission_mat(name, col, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    n_ = m.node_tree.nodes; n_.clear(); e_ = n_.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = (*col, 1)
    e_.inputs["Strength"].default_value = strength; o_ = n_.new("ShaderNodeOutputMaterial"); m.node_tree.links.new(e_.outputs[0], o_.inputs["Surface"])
    return m


SPARK_MATS = [emission_mat("SparkGold", (1.0, 0.7, 0.25), 40.0), emission_mat("SparkMagenta", (1.0, 0.2, 0.7), 40.0),
              emission_mat("SparkWhite", (1.0, 0.92, 0.75), 50.0)]
srng = np.random.default_rng(23)


def burst(T, centre, n, vmin, vmax, up_min, up_max, mat, life=(0.45, 1.1), z0=0.12):
    a = srng.uniform(0, 2 * math.pi, n); rr_ = srng.uniform(0.15, 0.35, n)
    pos = np.column_stack([centre[0] + rr_ * np.cos(a), centre[1] + rr_ * np.sin(a), np.full(n, z0)])
    sp_ = srng.uniform(vmin, vmax, n)
    vel = np.column_stack([np.cos(a) * sp_, np.sin(a) * sp_, srng.uniform(up_min, up_max, n)])
    return dict(T=T, pos=pos, vel=vel, life=srng.uniform(*life, n), mat=mat)


BURSTS = [burst(T1, P1, 160, 0.6, 2.2, 1.2, 3.4, 0), burst(T2, P2, 160, 0.6, 2.4, 1.2, 3.6, 1),
          burst(TE + 0.05, P1, 260, 0.9, 2.6, 1.8, 4.2, 0, life=(0.7, 1.4), z0=1.15)]
spark_obj = bpy.data.objects.new("Sparks", bpy.data.meshes.new("Sparks")); scene.collection.objects.link(spark_obj)


def update_sparks(t):
    vs, fs, ms = [], [], []
    G = np.array([0, 0, -6.5])
    for B in BURSTS:
        u = t - B["T"]
        if u < 0 or u > 1.7:
            continue
        for i in range(len(B["life"])):
            if u > B["life"][i]:
                continue
            p = B["pos"][i] + B["vel"][i] * u + 0.5 * G * u * u
            v = B["vel"][i] + G * u
            tail = p - v * 0.018
            wid = 0.006 * (1 - u / B["life"][i]) + 0.0015
            side = np.cross(v, [0, 0, 1.0]); n_ = np.linalg.norm(side)
            side = side / n_ * wid if n_ > 1e-6 else np.array([wid, 0, 0])
            up = np.cross(side, v); up = up / (np.linalg.norm(up) + 1e-9) * wid
            b0 = len(vs)
            vs += [tuple(p + side), tuple(p - side), tuple(tail - side), tuple(tail + side), tuple(p + up), tuple(tail + up)]
            fs += [(b0, b0 + 1, b0 + 2, b0 + 3), (b0 + 4, b0, b0 + 3, b0 + 5)]; ms += [B["mat"], B["mat"]]
    m = bpy.data.meshes.new("Sparks"); m.from_pydata(vs, [], fs)
    for mt in SPARK_MATS:
        m.materials.append(mt)
    if ms:
        m.polygons.foreach_set("material_index", np.array(ms, dtype=np.int32))
    old = spark_obj.data; spark_obj.data = m; bpy.data.meshes.remove(old)


DUSTM = bpy.data.materials.new("Mote"); DUSTM.use_nodes = True
dmb = DUSTM.node_tree.nodes["Principled BSDF"]; dmb.inputs["Base Color"].default_value = (0.9, 0.85, 1.0, 1)
dmb.inputs["Emission Color"].default_value = (0.8, 0.6, 1.0, 1); dmb.inputs["Emission Strength"].default_value = 0.9
drng = np.random.default_rng(29); ND = 420
d_p0 = np.column_stack([drng.uniform(-2.2, 2.2, ND), drng.uniform(-1.6, 2.6, ND), drng.uniform(0.35, 1.9, ND)])
d_ph = drng.uniform(0, 2 * math.pi, (ND, 3)); d_w = drng.uniform(0.2, 0.6, (ND, 3))
dme = bpy.data.meshes.new("Motes"); dme.from_pydata(d_p0.tolist(), [], [])
dust_obj = bpy.data.objects.new("Motes", dme); scene.collection.objects.link(dust_obj)
dg_ = dust_obj.modifiers.new("M", "NODES"); dgt = bpy.data.node_groups.new("Motes", "GeometryNodeTree")
dgt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
dgt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
di = dgt.nodes.new("NodeGroupInput"); do_ = dgt.nodes.new("NodeGroupOutput"); dip = dgt.nodes.new("GeometryNodeInstanceOnPoints")
dico = dgt.nodes.new("GeometryNodeMeshIcoSphere"); find(dico.inputs, "Radius").default_value = 0.004
dsm = dgt.nodes.new("GeometryNodeSetMaterial"); find(dsm.inputs, "Material").default_value = DUSTM
dgt.links.new(di.outputs[0], dip.inputs["Points"]); dgt.links.new(dico.outputs["Mesh"], dip.inputs["Instance"])
dgt.links.new(dip.outputs["Instances"], dsm.inputs["Geometry"]); dgt.links.new(dsm.outputs["Geometry"], do_.inputs[0])
dg_.node_group = dgt


def update_dust(t):
    P = d_p0 + 0.12 * np.sin(d_w * t + d_ph)
    for Tk, c_ in ((T1, P1), (T2, P2), (TE, P1)):
        u = t - Tk
        if u > 0:
            dx, dy = P[:, 0] - c_[0], P[:, 1] - c_[1]; rr_ = np.hypot(dx, dy) + 1e-6
            push = 0.22 * (1 - math.exp(-u * 3)) * np.exp(-rr_ / 1.5)
            P[:, 0] += push * dx / rr_; P[:, 1] += push * dy / rr_; P[:, 2] += 0.5 * push
    dme.vertices.foreach_set("co", P.astype(np.float32).ravel()); dme.update()


for _f in range(-1, int(SECS * FPS) + 2):
    sph.location = sphere_at(_f / FPS); sph.keyframe_insert("location", frame=_f)
events = []
prev = field(-1.0)
hprev = field(-1.0 / FPS)
heat_s = np.zeros(NC)
for f in range(int(SECS * FPS)):
    t = f / FPS
    h = field(t)
    crossed = (prev < BASE + 0.13) & (h >= BASE + 0.13)
    events.append({"t": t, "n": int(crossed.sum()), "x": float(cx[crossed].mean()) if crossed.any() else 0.0})
    prev = h
    vel = (h - hprev) * FPS; hprev = h.copy()
    heat_raw = np.clip((h - 0.1) / 0.75 + np.clip((vel - 0.35) * 0.4, 0, 0.35) + shock(t), 0, 1)
    heat_s = np.minimum(np.maximum(heat_raw, heat_s * 0.95), heat_s + 0.035)  # big areas brighten over ~0.8 s and fade softly: no flash
    if f < F0 or f > F1:
        continue
    co[:, 6:12, 2] = h[:, None] - CH; co[:, 12:18, 2] = h[:, None]; co[:, 18:24, 2] = h[:, None] + 0.002
    me.vertices.foreach_set("co", co.ravel()); me.update()
    heat = heat_s.astype(np.float32)                           # calm = near-black indigo
    me.attributes["hn"].data.foreach_set("value", np.repeat(heat, 19))
    update_sparks(t); update_dust(t)
    sph.rotation_euler = (0.25 * math.sin(0.7 * t), 0.0, 1.6 * t)
    scene.frame_set(f)
    loc, tgt = cam_at(t)
    cam_o.location = loc; cam_o.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam_o.data.dof.focus_distance = (sph.matrix_world.translation - loc).length
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("frame", f, flush=True)
beats = [{"t": T1, "kind": "impact", "x": 0.0, "amp": 1.0}, {"t": TB0, "kind": "bounce", "x": 0.0, "amp": 0.8},
         {"t": T2, "kind": "impact", "x": float(P2[0]), "amp": 0.85}, {"t": TS0, "kind": "spiral", "x": 0.0, "amp": 0.6},
         {"t": TE, "kind": "erupt", "x": 0.0, "amp": 1.0}]
json.dump({"fps": FPS, "secs": SECS, "t_hit": T1, "beats": beats, "frames": events}, open(os.path.join(OUTDIR, "events.json"), "w"))
print("done")
