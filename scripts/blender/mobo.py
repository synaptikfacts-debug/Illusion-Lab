# 0026 v4 - a photoreal MOTHERBOARD (owner, Nov 17 2026: "too colourful, not ultra realistic" + a real motherboard photo).
# Real-board language: green solder mask with the copper traces showing through, white silkscreen outlines and pin-1 marks
# (NO text - garbled text reads as AI), a CPU in a socket frame (dark green substrate, fine gold pattern), a VRM row of grey
# metal chokes with silver polymer capacitors in front, DDR slots, small black ICs, dense 0603 SMD parts, mounting holes.
# Soft daylight. 1 unit = 10 mm. Usage: blender -b -P mobo.py -- out.png [samples] [WxH]
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

ANIM_ = globals().get("ANIM")
argv = (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) if not ANIM_ else []
OUT = os.path.abspath(argv[0]) if argv else os.path.abspath("mobo.png")
SAMPLES = int(argv[1]) if len(argv) > 1 else 128
W, H = (int(v) for v in (argv[2] if len(argv) > 2 else "1080x1920").split("x"))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.01
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
rng = random.Random(4626)


def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def bsdf(n):
    return next(x for x in n if x.type == "BSDF_PRINCIPLED")


def pm(name, col, rough, metal=0.0, coat=0.0, coat_r=0.1):
    m, n, _ = mat(name)
    b = bsdf(n)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_r
    return m


MASK = pm("SolderMask", (0.006, 0.016, 0.022), 0.42, coat=0.5, coat_r=0.2)   # v5: dark teal-black (owner: green is boring)
COPPER = pm("TraceGold", (0.55, 0.42, 0.18), 0.35, metal=0.85, coat=0.4, coat_r=0.15)
SILK = pm("Silkscreen", (0.5, 0.52, 0.5), 0.6)
GOLD = pm("Gold", (1.0, 0.76, 0.36), 0.25, metal=1.0)
PADHOT = pm("PadHot", (1.0, 0.74, 0.32), 0.3, metal=1.0)
bsdf(PADHOT.node_tree.nodes).inputs["Emission Color"].default_value = (1.0, 0.36, 0.05, 1)
PAD_HEAT = bsdf(PADHOT.node_tree.nodes).inputs["Emission Strength"]
TIN = pm("Tin", (0.82, 0.82, 0.8), 0.3, metal=1.0)
ALU = pm("CapAluminium", (0.78, 0.79, 0.8), 0.32, metal=1.0)
CAPTOP = pm("CapTop", (0.6, 0.61, 0.63), 0.42, metal=1.0)
CAPBASE = pm("CapBase", (0.02, 0.02, 0.022), 0.5)
CHOKE = pm("Choke", (0.3, 0.31, 0.33), 0.48, metal=0.8)
CHOKETOP = pm("ChokeTop", (0.12, 0.12, 0.13), 0.6, metal=0.4)
BLACKIC = pm("ICBody", (0.012, 0.012, 0.014), 0.5, coat=0.15)
PLASTIC = pm("SlotPlastic", (0.008, 0.008, 0.009), 0.45)
SOCKETM = pm("Socket", (0.03, 0.03, 0.033), 0.5, metal=0.3)
RES = pm("ResistorTop", (0.01, 0.01, 0.012), 0.4)
CERCAP = pm("CeramicCap", (0.45, 0.34, 0.22), 0.5)
HOLE = pm("Hole", (0.0, 0.0, 0.0), 0.9)

# CPU substrate with a fine gold pattern: concentric square rings + fan-out lines + a pad grid near the edges
CPUM, cn, cL = mat("CPUTop")
cb = bsdf(cn)
tc = cn.new("ShaderNodeTexCoord")
sep = cn.new("ShaderNodeSeparateXYZ"); cL.new(tc.outputs["Generated"], sep.inputs["Vector"])
def node_math(op, a, b=None, v=None):
    m_ = cn.new("ShaderNodeMath"); m_.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            m_.inputs[i].default_value = x
        else:
            cL.new(x, m_.inputs[i])
    return m_.outputs[0]
ax = node_math("ABSOLUTE", node_math("SUBTRACT", sep.outputs["X"], 0.5))
ay = node_math("ABSOLUTE", node_math("SUBTRACT", sep.outputs["Y"], 0.5))
dch = node_math("MAXIMUM", ax, ay)                                   # square "radius" 0..0.5
rings = node_math("LESS_THAN", node_math("FRACT", node_math("MULTIPLY", dch, 30.0)), 0.36)
fanx = node_math("LESS_THAN", node_math("FRACT", node_math("MULTIPLY", sep.outputs["X"], 64.0)), 0.36)
fany = node_math("LESS_THAN", node_math("FRACT", node_math("MULTIPLY", sep.outputs["Y"], 64.0)), 0.36)
fan = node_math("MAXIMUM", node_math("MULTIPLY", fanx, node_math("GREATER_THAN", ay, ax)), node_math("MULTIPLY", fany, node_math("GREATER_THAN", ax, ay)))
zone1 = node_math("MULTIPLY", node_math("GREATER_THAN", dch, 0.07), node_math("LESS_THAN", dch, 0.17))   # ring band
zone2 = node_math("MULTIPLY", node_math("GREATER_THAN", dch, 0.17), node_math("LESS_THAN", dch, 0.4))    # fan-out band
gold_mask = node_math("MAXIMUM", node_math("MULTIPLY", rings, zone1), node_math("MULTIPLY", fan, zone2))
grid = cn.new("ShaderNodeTexBrick"); grid.inputs["Scale"].default_value = 60.0; grid.inputs["Mortar Size"].default_value = 0.35
grid.inputs["Brick Width"].default_value = 1.0; grid.inputs["Row Height"].default_value = 1.0; grid.offset = 0.0
cL.new(tc.outputs["Generated"], grid.inputs["Vector"])
padz = node_math("MULTIPLY", node_math("SUBTRACT", 1.0, grid.outputs["Fac"]), node_math("MULTIPLY", node_math("GREATER_THAN", dch, 0.41), node_math("LESS_THAN", dch, 0.47)))
core = node_math("LESS_THAN", dch, 0.07)
gm = node_math("MINIMUM", node_math("MAXIMUM", node_math("MAXIMUM", gold_mask, padz), core), 1.0)
mixc = cn.new("ShaderNodeMix"); mixc.data_type = "RGBA"
mixc.inputs["A"].default_value = (0.015, 0.06, 0.04, 1); mixc.inputs["B"].default_value = (1.0, 0.75, 0.35, 1)
cL.new(gm, mixc.inputs["Factor"]); cL.new(mixc.outputs["Result"], cb.inputs["Base Color"])
cL.new(gm, cb.inputs["Metallic"])
rgh = cn.new("ShaderNodeMapRange"); rgh.inputs["To Min"].default_value = 0.22; rgh.inputs["To Max"].default_value = 0.2
cL.new(gm, rgh.inputs["Value"]); cL.new(rgh.outputs["Result"], cb.inputs["Roughness"])
cb.inputs["Coat Weight"].default_value = 0.6
bmp = cn.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.25; bmp.inputs["Distance"].default_value = 0.002
cL.new(gm, bmp.inputs["Height"]); cL.new(bmp.outputs["Normal"], cb.inputs["Normal"])


GROUPS = []
_CUR = None
_NOGRP = False


def grp(kind, c):
    global _CUR
    _CUR = []
    GROUPS.append({"kind": kind, "c": Vector((c[0], c[1], 0)), "objs": _CUR})


def endgrp():
    global _CUR
    _CUR = None


def _reg(o):
    if _CUR is not None and not _NOGRP:
        _CUR.append(o)
    return o


def box(size, loc, m, rz=0.0, bevel=0.0, name=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    if name:
        o.name = name
    o.scale = size
    o.rotation_euler.z = rz
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("b", "BEVEL"); b.width = bevel; b.segments = 3
    return _reg(o)


def cyl(r, h, loc, m, v=32):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=v)
    o = bpy.context.active_object
    o.data.materials.append(m)
    return _reg(o)


def outline(cx, cy, w, h, rz=0.0, t=0.012):
    """white silkscreen rectangle around a part + a pin-1 dot (printed on the board: never part of a dropping group)"""
    global _NOGRP
    _NOGRP = True
    c, s = math.cos(rz), math.sin(rz)
    R = lambda x, y: Vector((cx + x * c - y * s, cy + x * s + y * c, 0.0012))
    for (x, y, sw, sh) in ((0, h / 2, w, t), (0, -h / 2, w, t), (w / 2, 0, t, h), (-w / 2, 0, t, h)):
        box((sw, sh, 0.002), R(x, y), SILK, rz)
    d = cyl(t * 1.6, 0.002, R(-w / 2 - 0.05, h / 2 + 0.05), SILK, 12)
    _NOGRP = False


# ---- board ----
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(MASK)

occupied = []


def free(c, r):
    return all((c - q).length > r + rq for q, rq in occupied)


def take(c, r):
    occupied.append((c, r))


# v6 (owner: "I want the chip black, like before"): a black matte QFP with gold gull-wing leads soldered straight onto
# gold pads (no socket), pin-1 dimple, bevelled moulded body
SOCK = 4.0
take(Vector((0, 0, 0)), 2.3)
EPOXY = pm("Epoxy", (0.0018, 0.0019, 0.0022), 0.62, coat=0.08, coat_r=0.3)
bsdf(EPOXY.node_tree.nodes).inputs["Specular IOR Level"].default_value = 0.12   # matte black, not a grey sheen
LEADG = pm("LeadGold", (1.0, 0.78, 0.38), 0.22, metal=1.0)
BODY, BH, NL, PITCH = 3.0, 0.2, 30, 0.09
CPU_OBJS = []
PADS_XY = []
CPU_OBJS.append(box((BODY, BODY, BH), (0, 0, 0.045 + BH / 2), EPOXY, bevel=0.05, name="CPU"))
CPU_OBJS.append(cyl(0.1, 0.012, (-BODY / 2 + 0.3, -BODY / 2 + 0.3, 0.045 + BH), EPOXY, 32))
for side in range(4):
    a_ = side * math.pi / 2
    ca, sa = math.cos(a_), math.sin(a_)
    R = lambda x, y, z=0.0: Vector((x * ca - y * sa, x * sa + y * ca, z))
    for i in range(NL):
        y = (i - (NL - 1) / 2) * PITCH
        CPU_OBJS.append(box((0.09, 0.04, 0.015), R(BODY / 2 + 0.045, y, 0.13), LEADG, a_))
        sl = box((0.12, 0.04, 0.015), R(BODY / 2 + 0.12, y, 0.075), LEADG, a_)
        sl.rotation_euler.rotate_axis("Y", math.radians(58)); CPU_OBJS.append(sl)
        CPU_OBJS.append(box((0.11, 0.04, 0.015), R(BODY / 2 + 0.205, y, 0.015), LEADG, a_))
        PADS_XY.append(R(BODY / 2 + 0.3, y)); box((0.18, 0.05, 0.004), R(BODY / 2 + 0.215, y, 0.002), PADHOT, a_)   # board pad
outline(0, 0, BODY + 0.75, BODY + 0.75)
GROUPS.append({"kind": "chip", "c": Vector((0, 0, 0)), "objs": CPU_OBJS})

# VRM: a row of chokes with silver solid capacitors in front, above and left of the socket
for i in range(7):
    x = -3.9 + i * 1.3
    c = Vector((x, 3.6, 0))
    grp("choke", c)
    box((1.05, 1.05, 0.62), (x, 3.6, 0.31), CHOKE, bevel=0.06); take(c, 0.75)
    box((0.86, 0.86, 0.01), (x, 3.6, 0.623), CHOKETOP)
    endgrp()
    outline(x, 3.6, 1.15, 1.15)
    cp = Vector((x + 0.1, 2.55, 0))
    grp("cap", cp)
    cyl(0.36, 0.08, (cp.x, cp.y, 0.04), CAPBASE, 40)
    cyl(0.34, 0.82, (cp.x, cp.y, 0.49), ALU, 48)
    cyl(0.31, 0.02, (cp.x, cp.y, 0.91), CAPTOP, 48)
    endgrp()
    take(cp, 0.45)
for i in range(4):
    y = 2.3 - i * 1.3
    grp("choke", (-3.7, y))
    box((1.05, 1.05, 0.62), (-3.7, y, 0.31), CHOKE, bevel=0.06); box((0.86, 0.86, 0.01), (-3.7, y, 0.623), CHOKETOP); take(Vector((-3.7, y, 0)), 0.75)
    endgrp(); outline(-3.7, y, 1.15, 1.15)
    grp("cap", (-2.65, y - 0.4))
    cyl(0.34, 0.82, (-2.65, y - 0.4, 0.49), ALU, 48); cyl(0.31, 0.02, (-2.65, y - 0.4, 0.91), CAPTOP, 48)
    cyl(0.36, 0.08, (-2.65, y - 0.4, 0.04), CAPBASE, 40); take(Vector((-2.65, y - 0.4, 0)), 0.45)
    endgrp()

# DDR slots to the right
for k in range(4):
    x = 4.0 + k * 0.62
    grp("slot", (x, 1.0))
    box((0.42, 13.0, 0.5), (x, 1.0, 0.25), PLASTIC)
    box((0.12, 12.4, 0.04), (x, 1.0, 0.5), BLACKIC)
    endgrp()
    take(Vector((x, 1.0, 0)), 0.3)
for k in range(4):
    for yy in range(-5, 8):
        take(Vector((4.0 + k * 0.62, yy, 0)), 0.32)
# a chipset under a small black IC, a few QFP/QFN ICs, a crystal, scattered
ICS = []


def ic(c, w, h, rz, leads=True):
    ICS.append((c.copy(), w, h, rz))
    grp("ic", c)
    box((w, h, 0.09), (c.x, c.y, 0.045), BLACKIC, rz, bevel=0.01)
    if leads:
        n = max(3, int(w / 0.1))
        for sd in (-1, 1):
            for i in range(n):
                u = (i - (n - 1) / 2) * 0.1
                q = Vector((u, sd * (h / 2 + 0.04), 0.012)); q.rotate(Matrix.Rotation(rz, 3, "Z"))
                box((0.035, 0.09, 0.015), c + q, TIN, rz)
    endgrp()
    outline(c.x, c.y, w + 0.18, h + 0.25, rz)
for _ in range(400):
    c = Vector((rng.uniform(-6.5, 3.3), rng.uniform(-7.5, 10.0), 0))
    w = rng.uniform(0.45, 1.0); h = w * rng.choice([1.0, 0.55])
    if free(c, w * 0.8 + 0.25):
        ic(c, w, h, rng.choice([0, math.pi / 2]), leads=h < w)
        take(c, w * 0.8)
    if len([1 for q in occupied]) > 90:
        break
for _ in range(60):
    c = Vector((rng.uniform(-5.5, 3.3), rng.uniform(-7.5, 1.8), 0))
    if free(c, 0.45):
        grp("cap", c)
        cyl(0.3, 0.7, (c.x, c.y, 0.43), ALU, 40); cyl(0.27, 0.02, (c.x, c.y, 0.79), CAPTOP, 40)
        cyl(0.32, 0.08, (c.x, c.y, 0.04), CAPBASE, 32); take(c, 0.4)
        endgrp()
        if rng.random() < 0.4:
            break
c = Vector((-1.6, -3.4, 0))
if free(c, 0.4):
    grp("ic", c); box((0.5, 0.22, 0.12), (c.x, c.y, 0.06), TIN, bevel=0.05); endgrp(); take(c, 0.35); outline(c.x, c.y, 0.65, 0.35)

# ---- traces under the mask: buses with 45-degree jogs, everywhere between the parts ----
def ribbon(paths, width, z, m, name):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for pts in paths:
        vs = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            nrm = Vector((-t.y, t.x, 0)) * width / 2
            vs.append((bm.verts.new((p.x + nrm.x, p.y + nrm.y, z)), bm.verts.new((p.x - nrm.x, p.y - nrm.y, z))))
        for i in range(len(vs) - 1):
            bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); scene.collection.objects.link(ob)
    return ob


paths = []
_bus_c = []
for _ in range(900):
    if len(_bus_c) >= 85:
        break
    c = Vector((rng.uniform(-8, 8), rng.uniform(-9, 9), 0))
    if c.length < 2.6 or any((c - q).length < 1.7 for q in _bus_c):
        continue                                           # real traces on one layer never cross: keep buses apart
    _bus_c.append(c)
    a = rng.choice([0, 0.5, 1, 1.5]) * math.pi
    ca, sa = math.cos(a), math.sin(a)
    R = lambda x, y: c + Vector((x * ca - y * sa, x * sa + y * ca, 0))
    n = rng.randint(4, 10); jog = rng.choice([-1, 1]) * rng.uniform(0.15, 0.45)
    L1, L2 = rng.uniform(0.3, 0.9), rng.uniform(0.4, 1.2)
    for k in range(n):
        y = k * 0.05; kk = k if jog > 0 else n - 1 - k
        paths.append([R(0, y), R(L1 + kk * 0.04, y), R(L1 + kk * 0.04 + abs(jog), y + jog), R(L1 + kk * 0.04 + abs(jog) + L2, y + jog)])
CHIP_PATHS = []
for side in range(4):
    a_ = side * math.pi / 2
    ca, sa = math.cos(a_), math.sin(a_)
    R = lambda x, y: Vector((x * ca - y * sa, x * sa + y * ca, 0))
    i = 0
    while i < NL:
        n = rng.randint(4, 7); jog = rng.choice([-1, 1]) * rng.uniform(0.2, 0.7)
        x1 = BODY / 2 + 0.75 + rng.uniform(0, 0.5); L = rng.uniform(3.0, 7.0)
        for k in range(n):
            if i + k >= NL:
                break
            y = (i + k - (NL - 1) / 2) * PITCH
            kk = k if jog > 0 else n - 1 - k
            xk = x1 + kk * 0.05
            CHIP_PATHS.append([R(BODY / 2 + 0.3, y), R(xk, y), R(xk + abs(jog), y + jog), R(xk + L, y + jog)])
        i += n
ribbon(paths, 0.009, 0.0006, COPPER, "Traces")
ribbon(CHIP_PATHS, 0.011, 0.0006, COPPER, "ChipTraces")
for _ in range(220):                                      # vias
    c = Vector((rng.uniform(-8, 8), rng.uniform(-9, 9), 0))
    if free(c, 0.06):
        cyl(0.03, 0.002, (c.x, c.y, 0.0012), TIN, 12)
# 0603 parts in ORGANISED rows (v5, owner: "fix the scattered details")
def part(c, rz):
    if not free(c, 0.065):
        return
    take(c, 0.06)
    grp("smd", c)
    body = RES if rng.random() < 0.55 else CERCAP
    box((0.1, 0.05, 0.035), (c.x, c.y, 0.018), body, rz)
    for e in (-1, 1):
        d = Vector((math.cos(rz), math.sin(rz), 0)) * 0.05 * e
        box((0.018, 0.051, 0.036), c + d + Vector((0, 0, 0.018)), TIN, rz)
    endgrp()


def row(start, direction, n, step, rz):
    for i in range(n):
        part(start + direction * (i * step), rz)


for (c, w, h, rz) in ICS:                                   # a row of decoupling parts along each side of every IC
    ca, sa = math.cos(rz), math.sin(rz)
    ux, uy = Vector((ca, sa, 0)), Vector((-sa, ca, 0))
    for sd in (-1, 1):
        n = max(3, int(w / 0.14))
        start = c + uy * sd * (h / 2 + 0.32) - ux * (n - 1) * 0.07
        row(start, ux, n, 0.14, rz + math.pi / 2)
    n2 = max(2, int(h / 0.14))
    start = c + ux * (w / 2 + 0.3) - uy * (n2 - 1) * 0.07
    row(start, uy, n2, 0.14, rz)
for side in range(4):                                       # two neat rows around the CPU socket
    a_ = side * math.pi / 2
    ux, uy = Vector((math.cos(a_), math.sin(a_), 0)), Vector((-math.sin(a_), math.cos(a_), 0))
    for r_ in (2.45, 2.62):
        row(ux * r_ - uy * 1.75, uy, 26, 0.14, a_)
for pts in rng.sample(paths, 60):                           # short rows where buses end
    e_ = pts[-1]; d_ = (pts[-1] - pts[-2]).normalized()
    row(e_ + d_ * 0.2 + Vector((-d_.y, d_.x, 0)) * -0.2, Vector((-d_.y, d_.x, 0)), 4, 0.13, math.atan2(d_.y, d_.x))
for p in ((-6.2, 4.6), (2.6, -6.8), (-6.4, -7.2)):         # mounting holes
    cyl(0.3, 0.003, (p[0], p[1], 0.0014), TIN, 48); cyl(0.2, 0.004, (p[0], p[1], 0.0016), HOLE, 48)

# ---- daylight: a big soft window from the front-left, a cool fill, a bright grey world for metal reflections ----
def area(name, loc, size, power, col, size_y=None, target=(0, 0, 0)):
    l = bpy.data.lights.new(name, "AREA"); l.shape = "RECTANGLE"; l.size = size; l.size_y = size_y or size
    l.energy = power; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return o


area("Key", (-6.0, -4.0, 7.0), 4.5, 2200.0, (1.0, 0.96, 0.9))
area("Rim", (6.0, 7.0, 3.0), 1.2, 900.0, (0.6, 0.78, 1.0), size_y=7.0)
area("Top", (0.0, 4.0, 12.0), 10.0, 160.0, (1.0, 1.0, 1.0))
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.035, 0.04, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.4

camd = bpy.data.cameras.new("Cam"); camd.lens = 50; camd.sensor_width = 36
cam = bpy.data.objects.new("Cam", camd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = Vector((3.2, -8.6, 9.2))
tgt = Vector((-0.3, 0.6, 0.1))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
camd.dof.use_dof = True
camd.dof.focus_distance = (tgt - cam.location).length
camd.dof.aperture_fstop = 5.6

LEDM = bpy.data.materials.new("LED"); LEDM.use_nodes = True
_ln = LEDM.node_tree.nodes; _ln.clear()
_oi = _ln.new("ShaderNodeObjectInfo"); _em = _ln.new("ShaderNodeEmission")
_mu = _ln.new("ShaderNodeMath"); _mu.operation = "MULTIPLY"; _mu.inputs[1].default_value = 60.0
_pb = _ln.new("ShaderNodeBsdfPrincipled"); _pb.inputs["Base Color"].default_value = (0.85, 0.88, 0.9, 1); _pb.inputs["Roughness"].default_value = 0.25
_ad = _ln.new("ShaderNodeAddShader"); _out = _ln.new("ShaderNodeOutputMaterial")
_L = LEDM.node_tree.links
_L.new(_oi.outputs["Color"], _em.inputs["Color"]); _L.new(_oi.outputs["Alpha"], _mu.inputs[0]); _L.new(_mu.outputs[0], _em.inputs["Strength"])
_L.new(_pb.outputs[0], _ad.inputs[0]); _L.new(_em.outputs[0], _ad.inputs[1]); _L.new(_ad.outputs[0], _out.inputs["Surface"])
LEDS = []
for (x, y) in ((2.2, -2.05), (2.35, -2.05), (2.5, -2.05), (2.65, -2.05), (-2.3, 2.15), (2.2, 2.2)):
    o = box((0.09, 0.05, 0.03), (x, y, 0.016), LEDM); o.color = (0.1, 0.45, 1.0, 0.0); LEDS.append(o)

if not ANIM_:
    scene.render.filepath = OUT
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("wrote", OUT)
