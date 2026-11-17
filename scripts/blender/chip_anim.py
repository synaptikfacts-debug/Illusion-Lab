# 0026 "This chip is waking up" - animation driver. Builds the board scene from chip_board.py (exec, no render), then for
# every frame: places the camera, builds the signal pulses as one emissive ribbon mesh (a bright head with a fading tail,
# and the part of the trace a pulse has already crossed keeps a soft glow - the board wakes up trace by trace), renders.
# Every pulse arrival/departure is written to events.json so the sound comes from the same events.
# Usage: blender -b --factory-startup -P chip_anim.py -- <outdir> <t0> <t1> <fps> <k> <workers> [fast]
#   env CHIP_FAST=1 -> EEVEE 540x960 preview; otherwise Cycles 1080x1920
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
FAST = bool(os.environ.get("CHIP_FAST"))

ANIM = True
_here = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(_here, "chip_board.py"), encoding="utf-8").read())

scene = bpy.context.scene
bpy.data.objects["Signals"].hide_render = True          # the still's static glow is replaced by real pulses
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

# ---- pulse material: emission from a vertex colour (rgb * strength baked in) ----
FXM = bpy.data.materials.new("Pulse")
FXM.use_nodes = True
fn = FXM.node_tree.nodes
fn.clear()
fa = fn.new("ShaderNodeAttribute"); fa.attribute_type = "GEOMETRY"; fa.attribute_name = "pc"
fe = fn.new("ShaderNodeEmission"); fe.inputs["Strength"].default_value = 1.0
fo = fn.new("ShaderNodeOutputMaterial")
FXM.node_tree.links.new(fa.outputs["Color"], fe.inputs["Color"]); FXM.node_tree.links.new(fe.outputs[0], fo.inputs["Surface"])
fx_me = bpy.data.meshes.new("Pulses")
fx_ob = bpy.data.objects.new("Pulses", fx_me)
scene.collection.objects.link(fx_ob)
fx_ob.visible_shadow = False

# ---- path data ----
P = [list(p) for p in paths]
CUM = []
for pts in P:
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + (pts[i] - pts[i - 1]).length)
    CUM.append(c)
LEN = [c[-1] for c in CUM]
SIDE = []
for j, pts in enumerate(P):
    if j < chip_paths:
        a = math.atan2(pts[0].y, pts[0].x)
        SIDE.append(int(round(a / (math.pi / 2))) % 4)       # 0:+x 1:+y 2:-x 3:-y
    else:
        SIDE.append(-1)
CHIP = [j for j in range(chip_paths)]
FILL = [j for j in range(chip_paths, len(P))]


def at(j, s):
    """point on path j at arc length s (clamped)"""
    s = max(0.0, min(LEN[j], s))
    c = CUM[j]
    i = 1
    while i < len(c) - 1 and c[i] < s:
        i += 1
    u = (s - c[i - 1]) / ((c[i] - c[i - 1]) or 1)
    return P[j][i - 1].lerp(P[j][i], u)


def seg(j, s0, s1, n=None):
    s0, s1 = max(0.0, s0), min(LEN[j], s1)
    if s1 <= s0:
        return []
    pts = [at(j, s0)]
    for i, c in enumerate(CUM[j]):
        if s0 < c < s1:
            pts.append(P[j][i])
    pts.append(at(j, s1))
    return pts


# ---- the story (seconds), v3 (owner: "boring, I wouldn't waste my time") ----
#  0-0.45 HOOK: low and close, the black chip drops onto glowing reflow-orange pads; 0.45 it SEATS (thock, flash)
#  0.47-1.2 a multicolour burst races out along every bus; 1.2-3 the far board lights up in a spreading ring, LEDs pop on
#  3-7 conversation: waves of colour race in from one side, the chip answers out of the other; the camera keeps moving
rr = random.Random(2600)
SPEED = 2.8
PAL = [(0.12, 0.42, 1.0), (0.08, 1.0, 0.45), (1.0, 0.12, 0.55), (1.0, 0.55, 0.08)]   # blue, emerald, magenta, amber
COL = [PAL[(j // 5) % 4] if j < chip_paths else PAL[rr.randrange(4)] for j in range(len(P))]
EV = []
SEAT = 0.45
order = sorted(CHIP, key=lambda j: (math.atan2(P[j][0].y, P[j][0].x) + 2 * math.pi) % (2 * math.pi))
for n_, j in enumerate(order):                                   # the burst: every bus fires as the chip seats
    EV.append({"path": j, "t": SEAT + 0.02 + 0.3 * n_ / len(order), "inward": False, "gain": 1.4, "kind": "burst"})
for j in FILL:                                                   # the far board answers in a spreading ring
    d = P[j][0].length
    EV.append({"path": j, "t": 1.0 + 0.22 * d + rr.uniform(0, 0.25), "inward": rr.random() < 0.4, "gain": 0.9, "kind": "ring"})
for w, (tw, side) in enumerate([(3.0, 0), (3.6, 1), (4.2, 2), (4.8, 3), (5.4, 0), (6.0, 2), (6.5, 1)]):
    for j in rr.sample([j for j in CHIP if SIDE[j] == side], 8):  # a wave lands...
        EV.append({"path": j, "t": tw + rr.uniform(-0.03, 0.03), "inward": True, "gain": 1.1, "kind": "wave%d" % w})
    for j in rr.sample([j for j in CHIP if SIDE[j] == (side + 2) % 4], 8):   # ...and the chip answers out the other side
        EV.append({"path": j, "t": tw + 0.18 + rr.uniform(0, 0.05), "inward": False, "gain": 1.1, "kind": "reply%d" % w})
os.makedirs(OUTDIR, exist_ok=True)
with open(os.path.join(OUTDIR, "events.json"), "w") as f:
    json.dump([{"t": e["t"], "kind": e["kind"], "inward": e["inward"], "len": LEN[e["path"]],
                "x": P[e["path"]][0].x, "y": P[e["path"]][0].y} for e in EV] + [{"t": SEAT, "kind": "seat", "inward": True, "len": 0, "x": 0, "y": 0}], f)

# ---- LEDs along the buses: they switch on in the colour of the first pulse that passes them ----
LEDM = bpy.data.materials.new("LED"); LEDM.use_nodes = True
ln_ = LEDM.node_tree.nodes; ln_.clear()
loi = ln_.new("ShaderNodeObjectInfo"); lem = ln_.new("ShaderNodeEmission")
lmul = ln_.new("ShaderNodeMath"); lmul.operation = "MULTIPLY"; lmul.inputs[1].default_value = 40.0
lpb = ln_.new("ShaderNodeBsdfPrincipled"); lpb.inputs["Base Color"].default_value = (0.9, 0.9, 0.88, 1); lpb.inputs["Roughness"].default_value = 0.3
lad = ln_.new("ShaderNodeAddShader"); lout = ln_.new("ShaderNodeOutputMaterial")
LL = LEDM.node_tree.links
LL.new(loi.outputs["Color"], lem.inputs["Color"]); LL.new(loi.outputs["Alpha"], lmul.inputs[0]); LL.new(lmul.outputs[0], lem.inputs["Strength"])
LL.new(lpb.outputs[0], lad.inputs[0]); LL.new(lem.outputs[0], lad.inputs[1]); LL.new(lad.outputs[0], lout.inputs["Surface"])
LEDS = []
for j in rr.sample(range(len(P)), 60):
    s_ = rr.uniform(0.3, LEN[j] * 0.8)
    q = at(j, s_); q2 = at(j, s_ + 0.05)
    tdir = (q2 - q).normalized() if (q2 - q).length > 1e-6 else Vector((1, 0, 0))
    pos = q + Vector((-tdir.y, tdir.x, 0)) * 0.08 + Vector((0, 0, 0.014))
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.active_object; o.scale = (0.07, 0.04, 0.028); o.rotation_euler.z = math.atan2(tdir.y, tdir.x)
    o.data.materials.append(LEDM); o.color = (0, 0, 0, 0)
    on = 1e9
    for e in EV:                                                 # when does a pulse head pass this point?
        if e["path"] != j:
            continue
        tp = e["t"] - s_ / SPEED if e["inward"] else e["t"] + s_ / SPEED
        on = min(on, tp)
    LEDS.append((o, on, COL[j], rr.uniform(0, 6.28)))

TAIL = 0.75
def build(t, campos):
    verts, faces, cols = [], [], []

    def ribbon_add(pts, w, inten_fn, col):
        if len(pts) < 2:
            return
        b = len(verts)
        for k, q in enumerate(pts):
            tan = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)])
            side = Vector((-tan.y, tan.x, 0))
            if side.length < 1e-9:
                side = Vector((1, 0, 0))
            side.normalize()
            u = k / (len(pts) - 1)
            g = inten_fn(u)
            verts.append(q + side * w + Vector((0, 0, 0.0035)))
            verts.append(q - side * w + Vector((0, 0, 0.0035)))
            cols.extend([(col[0] * g, col[1] * g, col[2] * g, 1.0)] * 2)
        for k in range(len(pts) - 1):
            a = b + 2 * k
            faces.append((a, a + 1, a + 3, a + 2))

    for e in EV:
        j, L = e["path"], LEN[e["path"]]
        if e["inward"]:
            head = (e["t"] - t) * SPEED                      # distance from the chip end; 0 at arrival
            if head > L + TAIL:
                continue
            if head > -0.05:                                 # the moving pulse
                ribbon_add(seg(j, max(head, 0), head + TAIL), 0.007, lambda u: 60.0 * e["gain"] * (1 - u) ** 2.5 + 0.5, COL[j])
            lit0 = max(head, 0.0)                            # the crossed part keeps glowing, fading slowly
            age = max(0.0, t - e["t"])
            glow = (0.8 * math.exp(-age / 2.0) + 0.18) * e["gain"]
            if lit0 < L:
                ribbon_add(seg(j, lit0, L), 0.005, lambda u: glow, COL[j])
        else:
            head = (t - e["t"]) * SPEED
            if head < 0:
                continue
            if head < L + TAIL:
                ribbon_add(seg(j, head - TAIL, head), 0.007, lambda u: 60.0 * e["gain"] * u ** 2.5 + 0.5, COL[j])
            age = max(0.0, t - e["t"] - L / SPEED)
            glow = (0.8 * math.exp(-age / 2.0) + 0.18) * e["gain"]
            ribbon_add(seg(j, 0, min(head - TAIL * 0.5, L)), 0.005, lambda u: glow, COL[j])
    fx_me.clear_geometry()
    fx_me.from_pydata([tuple(v) for v in verts], [], faces)
    at_ = fx_me.color_attributes.new("pc", "FLOAT_COLOR", "POINT")
    for i, c in enumerate(cols):
        at_.data[i].color = c
    fx_me.materials.clear()
    fx_me.materials.append(FXM)


def sm(a, b, x):
    u = max(0.0, min(1.0, (x - a) / (b - a)))
    return u * u * (3 - 2 * u)


from mathutils import Matrix  # noqa: E402

BASE = {o.name: o.location.copy() for o in CHIP_OBJS}
CHIPC = Vector((0, 0, 0.12))


def chip_drop(t):
    """the chip falls the last few millimetres onto the pads, seats at SEAT with a tiny bounce"""
    if t < SEAT:
        dz = 0.32 * (1 - t / SEAT) ** 2
    else:
        dz = 0.012 * math.exp(-(t - SEAT) * 18) * abs(math.sin((t - SEAT) * 40))
    for o in CHIP_OBJS:
        o.location = BASE[o.name] + Vector((0, 0, dz))
    # reflow: pads glow orange while waiting, flash at the seat, cool to gold over a second
    PAD_HEAT.default_value = (2.5 + 1.5 * math.sin(t * 9)) if t < SEAT else 9.0 * math.exp(-(t - SEAT) * 2.4)


def camera(t):
    """0-0.45 low and close as the chip drops; a jolt at the seat; 0.6-2.8 pull up and away on an arc; then keep orbiting,
    dipping low between the tall parts so the board slides past in depth"""
    if t < 0.6:
        pos = Vector((1.7, -2.9, 1.05 + 0.1 * t))
        look = Vector((0, 0, 0.18))
        lens = 30.0
        if t > SEAT:
            k = math.exp(-(t - SEAT) * 22) * 0.03
            pos += Vector((0, 0, k * math.sin((t - SEAT) * 90)))
        return pos, look, lens
    u = sm(0.6, 2.8, t)
    ang = math.radians(-62 + 30 * u + 70 * sm(2.8, 7.5, t))
    rad = 2.4 + 3.1 * u - 0.9 * sm(4.5, 7.0, t)
    hgt = 0.65 + 3.3 * u - 1.6 * sm(3.5, 6.5, t)
    pos = Vector((rad * math.sin(-ang), -rad * math.cos(ang), hgt))
    look = CHIPC.lerp(Vector((0, 0.8, 0)), 0.5 * u)
    lens = 30.0 + 8.0 * u
    return pos, look, lens


cam = scene.camera
camd = cam.data
frames = list(range(int(round(T0 * FPS)), int(round(T1 * FPS))))
for f in frames[K::NW]:
    t = f / FPS
    pos, look, lens = camera(t)
    cam.location = pos
    cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    camd.lens = lens
    camd.dof.focus_distance = (CHIPC - pos).length
    camd.dof.aperture_fstop = 2.8
    chip_drop(t)
    build(t, pos)
    for o, on, c, ph in LEDS:
        lit = 0.0 if t < on else (1.0 if t < on + 0.15 else 0.55 + 0.25 * math.sin(t * 7 + ph))
        o.color = (c[0], c[1], c[2], lit)
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % f)
    bpy.ops.render.render(write_still=True)
print("done", len(frames[K::NW]))
