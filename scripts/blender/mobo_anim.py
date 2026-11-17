# 0026 "This motherboard builds itself" - animation driver for scripts/blender/mobo.py (exec'd, no render).
# Beat sheet (seconds):
#  0-0.45   HOOK: low and close, the black chip drops onto glowing reflow-orange pads; 0.45 it SEATS (big thock, pads flash)
#  0.6-2.9  the tiny parts snap in, row by row, racing round the chip like dominoes (soft ticks)
#  3.0-6.2  the chokes land one by one along the VRM row (heavy thuds), each silver capacitor drops in front of its choke
#  6.3-8.0  the rest of the board fills in a wave outwards (ICs, their rows, caps, slots); the camera pulls up to the hero
#  8.3      POWER: blue pulses race out of the chip along every trace, the status LEDs light
#  9-12     the board talks: waves in from one side, answers out of the other; the camera dives low along a bus
#  12.8-14.6 CLIMAX: the whole board pulses twice
#  15.5-18.4 it settles; one last pulse runs back into the chip; the LEDs go out except the power LED
#  18.4-21  the camera eases away, fade
# Usage: blender -b --factory-startup -P mobo_anim.py -- <outdir> <t0> <t1> <fps> <k> <workers>   (env MOBO_FAST=1: EEVEE preview)
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

_args = sys.argv[sys.argv.index("--") + 1:]
OUTDIR = os.path.abspath(_args[0])
T0, T1, FPS = float(_args[1]), float(_args[2]), int(_args[3])
K, NW = int(_args[4]), int(_args[5])
FAST = bool(os.environ.get("MOBO_FAST"))
DUR = 21.0

ANIM = True
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mobo.py"), encoding="utf-8").read())
scene = bpy.context.scene
if FAST:
    for _eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = _eng
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x, scene.render.resolution_y = 540, 960
else:
    scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
    scene.cycles.samples = 64
scene.render.image_settings.file_format = "PNG"
# bloom only on the true emitters (pulses, LEDs, hot pads)
ct = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
_rl = ct.nodes.new("CompositorNodeRLayers"); _gl = ct.nodes.new("CompositorNodeGlare")
_gl.inputs["Type"].default_value = "Bloom"; _gl.inputs["Threshold"].default_value = 2.0
_gl.inputs["Strength"].default_value = 0.35; _gl.inputs["Size"].default_value = 0.6
_co = ct.nodes.new("NodeGroupOutput")
ct.links.new(_rl.outputs["Image"], _gl.inputs["Image"]); ct.links.new(_gl.outputs["Image"], _co.inputs[0])
scene.compositing_node_group = ct; scene.render.use_compositing = True

rr = random.Random(2626)


def sm(a, b, x):
    u = max(0.0, min(1.0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)


# ---------------- assembly schedule ----------------
SEAT = 0.45
FALL = {"chip": 0.42, "smd": 0.32, "ic": 0.7, "cap": 1.3, "choke": 1.5, "slot": 1.0}
icgroups = [g for g in GROUPS if g["kind"] == "ic"]
smd = [g for g in GROUPS if g["kind"] == "smd"]
for g in GROUPS:
    g["t"] = None
for g in GROUPS:
    if g["kind"] == "chip":
        g["t"] = SEAT
ring_smd = sorted([g for g in smd if g["c"].length < 3.1], key=lambda g: (math.atan2(g["c"].y, g["c"].x) + 2 * math.pi) % (2 * math.pi))
for i, g in enumerate(ring_smd):
    g["t"] = 0.65 + 2.2 * i / max(1, len(ring_smd))
chokes = [g for g in GROUPS if g["kind"] == "choke"]
row_chokes = sorted([g for g in chokes if g["c"].y > 3.0], key=lambda g: g["c"].x)
col_chokes = sorted([g for g in chokes if g["c"].y <= 3.0], key=lambda g: -g["c"].y)
for i, g in enumerate(row_chokes + col_chokes):
    g["t"] = 3.0 + 0.3 * i
for g in GROUPS:
    if g["kind"] == "cap" and g["c"].y > -1.5 and g["c"].length < 5.2:
        near = min(chokes, key=lambda h: (h["c"] - g["c"]).length)
        if (near["c"] - g["c"]).length < 1.4:
            g["t"] = near["t"] + 0.16
for g in GROUPS:
    if g["t"] is None and g["kind"] in ("ic", "cap", "slot"):
        g["t"] = min(8.0, 6.3 + 0.2 * max(0.0, g["c"].length - 2.5)) + rr.uniform(0, 0.08)
for g in smd:                                         # decoupling rows land right after their IC
    if g["t"] is None:
        near = min(icgroups, key=lambda h: (h["c"] - g["c"]).length) if icgroups else None
        if near is not None and (near["c"] - g["c"]).length < 1.2:
            g["t"] = near["t"] + 0.12 + 0.25 * rr.random()
        else:
            g["t"] = min(8.1, 6.4 + 0.2 * max(0.0, g["c"].length - 2.5)) + rr.uniform(0, 0.1)
for g in GROUPS:
    g["base"] = [o.location.copy() for o in g["objs"]]
    g["h0"] = FALL.get(g["kind"], 0.6)


def assemble(t):
    for g in GROUPS:
        h0 = g["h0"]
        T = SEAT if g["kind"] == "chip" else 0.16 + 0.14 * h0   # fall time (the chip falls from frame 0)
        t0 = g["t"] - T
        if t < t0:
            hidden, dz = True, 0.0
        elif t < g["t"]:
            u = (t - t0) / T
            hidden, dz = False, h0 * (1 - u * u)
        else:
            a = t - g["t"]
            hidden, dz = False, 0.04 * h0 * math.exp(-a * 14) * abs(math.sin(a * 34))
        for o, b in zip(g["objs"], g["base"]):
            o.hide_render = hidden
            o.location = b + Vector((0, 0, dz))
    PAD_HEAT.default_value = (2.4 + 1.2 * math.sin(t * 9)) if t < SEAT else 10.0 * math.exp(-(t - SEAT) * 2.2)


# ---------------- signals (one colour: blue) ----------------
P = [list(p) for p in CHIP_PATHS] + [list(p) for p in paths]
NCHIP = len(CHIP_PATHS)
CUM = []
for pts in P:
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + (pts[i] - pts[i - 1]).length)
    CUM.append(c)
LEN = [c[-1] for c in CUM]
SIDE = [int(round(math.atan2(P[j][0].y, P[j][0].x) / (math.pi / 2))) % 4 if j < NCHIP else -1 for j in range(len(P))]


def at(j, s):
    s = max(0.0, min(LEN[j], s)); c = CUM[j]; i = 1
    while i < len(c) - 1 and c[i] < s:
        i += 1
    u = (s - c[i - 1]) / ((c[i] - c[i - 1]) or 1)
    return P[j][i - 1].lerp(P[j][i], u)


def seg(j, s0, s1):
    s0, s1 = max(0.0, s0), min(LEN[j], s1)
    if s1 <= s0:
        return []
    out = [at(j, s0)]
    for i, c in enumerate(CUM[j]):
        if s0 < c < s1:
            out.append(P[j][i])
    out.append(at(j, s1))
    return out


SPEED = 2.6
POWER = 8.3
EV = []
order = sorted(range(NCHIP), key=lambda j: (math.atan2(P[j][0].y, P[j][0].x) + 2 * math.pi) % (2 * math.pi))
for n_, j in enumerate(order):
    EV.append({"path": j, "t": POWER + 0.35 * n_ / max(1, NCHIP), "inward": False, "gain": 1.3, "kind": "power"})
for j in range(NCHIP, len(P)):
    d = P[j][0].length
    EV.append({"path": j, "t": POWER + 0.6 + 0.18 * d + rr.uniform(0, 0.2), "inward": rr.random() < 0.5, "gain": 0.8, "kind": "ring"})
for w, (tw, side) in enumerate([(9.6, 0), (10.15, 1), (10.7, 2), (11.25, 3), (11.8, 0), (12.3, 2)]):
    for j in rr.sample([j for j in range(NCHIP) if SIDE[j] == side], min(9, sum(1 for j in range(NCHIP) if SIDE[j] == side))):
        EV.append({"path": j, "t": tw + rr.uniform(-0.03, 0.03), "inward": True, "gain": 1.0, "kind": "wave%d" % w})
    for j in rr.sample([j for j in range(NCHIP) if SIDE[j] == (side + 2) % 4], min(9, sum(1 for j in range(NCHIP) if SIDE[j] == (side + 2) % 4))):
        EV.append({"path": j, "t": tw + 0.2 + rr.uniform(0, 0.05), "inward": False, "gain": 1.0, "kind": "reply%d" % w})
for k, tc in enumerate((13.0, 14.0)):                 # climax: the whole board pulses twice
    for n_, j in enumerate(order):
        EV.append({"path": j, "t": tc + 0.25 * n_ / max(1, NCHIP), "inward": False, "gain": 1.6, "kind": "climax%d" % k})
    for j in range(NCHIP, len(P)):
        EV.append({"path": j, "t": tc + 0.35 + 0.12 * P[j][0].length, "inward": rr.random() < 0.5, "gain": 1.0, "kind": "climaxring%d" % k})
for tw in (15.6, 16.4):
    for j in rr.sample(range(NCHIP), 6):
        EV.append({"path": j, "t": tw + rr.uniform(0, 0.2), "inward": rr.random() < 0.5, "gain": 0.8, "kind": "settle"})
LAST = max(range(NCHIP), key=lambda j: LEN[j])
EV.append({"path": LAST, "t": 18.3, "inward": True, "gain": 1.8, "kind": "last"})
TAIL = 0.75
BLUE = (0.12, 0.45, 1.0)

FXM = bpy.data.materials.new("Pulse"); FXM.use_nodes = True
_fn = FXM.node_tree.nodes; _fn.clear()
_fa = _fn.new("ShaderNodeAttribute"); _fa.attribute_type = "GEOMETRY"; _fa.attribute_name = "pc"
_fe = _fn.new("ShaderNodeEmission"); _fo = _fn.new("ShaderNodeOutputMaterial")
FXM.node_tree.links.new(_fa.outputs["Color"], _fe.inputs["Color"]); FXM.node_tree.links.new(_fe.outputs[0], _fo.inputs["Surface"])
fx_me = bpy.data.meshes.new("Pulses"); fx_ob = bpy.data.objects.new("Pulses", fx_me)
scene.collection.objects.link(fx_ob); fx_ob.visible_shadow = False


def build(t):
    verts, faces, cols = [], [], []
    fade_all = 1.0 - sm(18.6, 20.4, t)

    def add(pts, w, fn):
        if len(pts) < 2:
            return
        b = len(verts)
        for k, q in enumerate(pts):
            tan = pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]
            sd = Vector((-tan.y, tan.x, 0))
            if sd.length < 1e-9:
                sd = Vector((1, 0, 0))
            sd.normalize()
            g = fn(k / (len(pts) - 1)) * fade_all
            verts.append(q + sd * w + Vector((0, 0, 0.003))); verts.append(q - sd * w + Vector((0, 0, 0.003)))
            cols.extend([(BLUE[0] * g, BLUE[1] * g, BLUE[2] * g, 1.0)] * 2)
        for k in range(len(pts) - 1):
            a = b + 2 * k
            faces.append((a, a + 1, a + 3, a + 2))

    for e in EV:
        j, L = e["path"], LEN[e["path"]]
        gain = e["gain"]
        if e["inward"]:
            head = (e["t"] - t) * SPEED
            if head > L + TAIL:
                continue
            if head > -0.05:
                add(seg(j, max(head, 0), head + TAIL), 0.007, lambda u: 50.0 * gain * (1 - u) ** 2.5 + 0.4)
            age = max(0.0, t - e["t"]); glow = (0.7 * math.exp(-age / 1.8) + 0.12) * gain
            if max(head, 0) < L:
                add(seg(j, max(head, 0), L), 0.005, lambda u: glow)
        else:
            head = (t - e["t"]) * SPEED
            if head < 0:
                continue
            if head < L + TAIL:
                add(seg(j, head - TAIL, head), 0.007, lambda u: 50.0 * gain * u ** 2.5 + 0.4)
            age = max(0.0, t - e["t"] - L / SPEED); glow = (0.7 * math.exp(-age / 1.8) + 0.12) * gain
            add(seg(j, 0, min(head - TAIL * 0.5, L)), 0.005, lambda u: glow)
    fx_me.clear_geometry()
    fx_me.from_pydata([tuple(v) for v in verts], [], faces)
    at_ = fx_me.color_attributes.new("pc", "FLOAT_COLOR", "POINT")
    for i, c in enumerate(cols):
        at_.data[i].color = c
    fx_me.materials.clear(); fx_me.materials.append(FXM)
    for i, o in enumerate(LEDS):                        # status LEDs: on at power, off at the end except the power LED (last)
        on = sm(POWER + 0.1 + 0.08 * i, POWER + 0.2 + 0.08 * i, t)
        off = 1.0 if i == len(LEDS) - 1 else 1.0 - sm(18.5, 18.8, t)
        flick = 1.0 if i == len(LEDS) - 1 else 0.75 + 0.25 * math.sin(t * 11 + i * 2.1)
        o.color = (BLUE[0], BLUE[1], BLUE[2], on * off * flick * (1.0 - sm(19.6, 20.8, t)))


# ---------------- camera: Catmull-Rom through key poses ----------------
KEYS = [  # t, position, look-at, lens
    (0.0, (1.4, -2.3, 1.55), (0.0, 0.1, 0.1), 30),
    (0.7, (1.8, -2.8, 1.75), (0.0, -0.3, 0.05), 30),
    (2.0, (2.9, -3.3, 1.7), (0.4, -0.6, 0.05), 32),
    (3.2, (1.2, -0.8, 2.1), (-1.4, 3.4, 0.2), 30),
    (5.0, (-1.0, -0.6, 2.3), (-3.2, 2.6, 0.2), 30),
    (6.4, (-0.5, -3.5, 3.6), (-1.5, 1.5, 0.2), 34),
    (8.0, (3.2, -8.0, 8.4), (-0.3, 0.6, 0.1), 46),
    (9.4, (2.6, -6.4, 5.8), (0.0, 0.3, 0.1), 42),
    (11.2, (1.6, -4.2, 1.1), (0.4, 1.4, 0.1), 30),
    (13.0, (-3.0, -5.6, 4.0), (0.0, 0.2, 0.05), 36),
    (14.8, (0.4, -6.2, 7.2), (0.0, 0.6, 0.0), 40),
    (17.0, (2.6, -5.8, 4.6), (0.0, 0.2, 0.1), 40),
    (18.6, (2.2, -4.6, 3.4), (0.0, 0.0, 0.12), 42),
    (21.0, (3.8, -9.6, 9.6), (-0.2, 0.6, 0.05), 46),
]


def cr(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def camera(t):
    ks = KEYS
    i = max(0, min(len(ks) - 2, max(k for k in range(len(ks)) if ks[k][0] <= t)))
    t1, t2 = ks[i][0], ks[i + 1][0]
    u = (t - t1) / (t2 - t1)
    u = u * u * (3 - 2 * u) * 0.35 + u * 0.65             # a little ease at each key
    g = lambda k, idx: Vector(ks[max(0, min(len(ks) - 1, k))][idx])
    pos = cr(g(i - 1, 1), g(i, 1), g(i + 1, 1), g(i + 2, 1), u)
    look = cr(g(i - 1, 2), g(i, 2), g(i + 1, 2), g(i + 2, 2), u)
    lens = ks[i][3] + (ks[i + 1][3] - ks[i][3]) * u
    if SEAT < t < SEAT + 0.3:                               # a jolt when the chip seats
        k = math.exp(-(t - SEAT) * 20) * 0.035
        pos += Vector((0, 0, k * math.sin((t - SEAT) * 95)))
    return pos, look, lens


# ---------------- events for the sound ----------------
os.makedirs(OUTDIR, exist_ok=True)
with open(os.path.join(OUTDIR, "events.json"), "w") as f:
    json.dump({"drops": [{"t": g["t"], "kind": g["kind"], "x": g["c"].x, "y": g["c"].y} for g in GROUPS],
               "signals": [{"t": e["t"], "kind": e["kind"], "inward": e["inward"], "len": LEN[e["path"]], "x": P[e["path"]][0].x} for e in EV],
               "seat": SEAT, "power": POWER}, f)

cam = scene.camera
camd = cam.data
frames = list(range(int(round(T0 * FPS)), int(round(T1 * FPS))))
for fr in frames[K::NW]:
    t = fr / FPS
    pos, look, lens = camera(t)
    cam.location = pos
    cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    camd.lens = lens
    camd.dof.focus_distance = (look - pos).length
    camd.dof.aperture_fstop = 3.2
    assemble(t)
    build(t)
    fade = 1.0 - sm(19.3, 20.95, t)                        # fade to black with the last sound
    scene.view_settings.exposure = math.log2(max(1e-4, fade))
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % fr)
    bpy.ops.render.render(write_still=True)
print("done", len(frames[K::NW]))
