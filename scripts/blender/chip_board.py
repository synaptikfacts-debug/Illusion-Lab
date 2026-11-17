# 0026 "This chip is waking up" - v2 concept still (owner, Nov 17 2026: the open wire-bonded die "doesn't look like a chip at
# all" + a stock image of a processor on a circuit board). Reference does: an illustrated blue PCB, a glowing green chip,
# traces with via rings radiating out, bokeh. Ours does: a PHOTOREAL board - matte black solder mask, gold ENIG via rings and
# pads, a real flip-chip processor (dark substrate, mirror silicon die with thin-film rainbow, a ring of tiny SMD capacitors),
# 45-degree routed traces in buses, scattered SMD parts, and electric-blue signal pulses running along the traces.
# Materials for the die/gold/ceramic come from chip_wake.py (exec'd). Usage: blender -b -P chip_board.py -- out.png [samples] [WxH]
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) if not globals().get("ANIM") else []
OUT = os.path.abspath(argv[0]) if argv else os.path.abspath("board_still.png")
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
scene.view_settings.look = "AgX - Medium High Contrast"

# shared materials (mat, bsdf, metal, GOLD, GOLD_SAT, ALU, CER, DIE) from the v1 scene
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "chip_wake.py"), encoding="utf-8").read()
exec(_src[_src.index("def mat(name):"):_src.index("# ---- geometry")])

rng = random.Random(2626)

# ---- board: matte black solder mask with a faint weave ----
PCB, pn, pL = mat("SolderMask")
pb = bsdf(pn)
pb.inputs["Base Color"].default_value = (0.008, 0.02, 0.026, 1)   # dark teal-navy solder mask
pb.inputs["Roughness"].default_value = 0.48
pb.inputs["Coat Weight"].default_value = 0.35
pb.inputs["Coat Roughness"].default_value = 0.25
pwz = pn.new("ShaderNodeTexWave"); pwz.inputs["Scale"].default_value = 260.0
pbm = pn.new("ShaderNodeBump"); pbm.inputs["Strength"].default_value = 0.04
pL.new(pwz.outputs["Fac"], pbm.inputs["Height"]); pL.new(pbm.outputs["Normal"], pb.inputs["Normal"])
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
board = bpy.context.active_object
board.data.materials.append(PCB)

# copper under the mask: a slightly raised, glossier dark line
TRACE, tn, tL = mat("Trace")
tb = bsdf(tn)
tb.inputs["Base Color"].default_value = (0.62, 0.46, 0.2, 1)    # gold traces like the reference
tb.inputs["Metallic"].default_value = 0.9
tb.inputs["Roughness"].default_value = 0.32
tb.inputs["Coat Weight"].default_value = 0.6
# signal pulses: emission along the trace (UV.x = distance along the trace, UV.y = per-trace phase)
GLOW, gn, gL = mat("Signal")
gn.clear()
gtc = gn.new("ShaderNodeUVMap")
gsep = gn.new("ShaderNodeSeparateXYZ"); gL.new(gtc.outputs["UV"], gsep.inputs["Vector"])
HEAD = gn.new("ShaderNodeValue"); HEAD.name = "Head"; HEAD.outputs[0].default_value = 0.0   # animated later
gph = gn.new("ShaderNodeMath"); gph.operation = "ADD"; gL.new(gsep.outputs["Y"], gph.inputs[0]); gL.new(HEAD.outputs[0], gph.inputs[1])
gd = gn.new("ShaderNodeMath"); gd.operation = "SUBTRACT"; gL.new(gph.outputs[0], gd.inputs[0]); gL.new(gsep.outputs["X"], gd.inputs[1])
gfr = gn.new("ShaderNodeMath"); gfr.operation = "FRACT"; gL.new(gd.outputs[0], gfr.inputs[0])       # 0 at the head, grows behind it
gtail = gn.new("ShaderNodeMath"); gtail.operation = "POWER"; gtail.inputs[1].default_value = 10.0
ginv = gn.new("ShaderNodeMath"); ginv.operation = "SUBTRACT"; ginv.inputs[0].default_value = 1.0; gL.new(gfr.outputs[0], ginv.inputs[1])
gL.new(ginv.outputs[0], gtail.inputs[0])
gstr = gn.new("ShaderNodeMath"); gstr.operation = "MULTIPLY_ADD"; gstr.inputs[1].default_value = 40.0; gstr.inputs[2].default_value = 0.6
gL.new(gtail.outputs[0], gstr.inputs[0])
gem = gn.new("ShaderNodeEmission"); gem.inputs["Color"].default_value = (0.12, 0.42, 1.0, 1)
gL.new(gstr.outputs[0], gem.inputs["Strength"])
gout = gn.new("ShaderNodeOutputMaterial"); gL.new(gem.outputs[0], gout.inputs["Surface"])


def ribbon(paths, width, z, m, name, per_trace_phase=True):
    """flat strips along polylines; UV.x = metres along the path / 2.5, UV.y = a random phase per path"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    for pts in paths:
        ph = rng.random() if per_trace_phase else 0.0
        acc = [0.0]
        for i in range(1, len(pts)):
            acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
        vs = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            nrm = Vector((-t.y, t.x, 0)) * width / 2
            vs.append((bm.verts.new((p.x + nrm.x, p.y + nrm.y, z)), bm.verts.new((p.x - nrm.x, p.y - nrm.y, z)), acc[i]))
        for i in range(len(vs) - 1):
            f = bm.faces.new((vs[i][0], vs[i][1], vs[i + 1][1], vs[i + 1][0]))
            for lp, (u, side) in zip(f.loops, ((vs[i][2], 0), (vs[i][2], 1), (vs[i + 1][2], 1), (vs[i + 1][2], 0))):
                lp[uv].uv = (u / 2.5, ph)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(m)
    scene.collection.objects.link(ob)
    return ob


def cyl(r, h, loc, m, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    o = bpy.context.active_object
    o.data.materials.append(m)
    return o


def box(size, loc, m, rz=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.scale = size
    o.rotation_euler.z = rz
    o.data.materials.append(m)
    return o


# ---- the chip (v3, owner: the rainbow die "looks like a carpet"; Google's chip = a black QFP with gold gull-wing leads) ----
EPOXY, en_, eL_ = mat("Epoxy")
eb_ = bsdf(en_)
eb_.inputs["Base Color"].default_value = (0.006, 0.0065, 0.008, 1)
eb_.inputs["Roughness"].default_value = 0.55
eb_.inputs["Coat Weight"].default_value = 0.15
enz = en_.new("ShaderNodeTexNoise"); enz.inputs["Scale"].default_value = 700.0
ebm = en_.new("ShaderNodeBump"); ebm.inputs["Strength"].default_value = 0.06
eL_.new(enz.outputs["Fac"], ebm.inputs["Height"]); eL_.new(ebm.outputs["Normal"], eb_.inputs["Normal"])
CAPB = metal("CapBody", (0.55, 0.42, 0.28), 0.5)
CAPB.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.0
BODY, BH, NL, PITCH = 2.0, 0.15, 24, 0.075
_before_chip = set(bpy.data.objects)
PADM, pdn, pdL = mat("PadHot")                       # gold pads that can glow reflow-orange (emission driven per frame)
pdb = bsdf(pdn)
pdb.inputs["Base Color"].default_value = (1.0, 0.74, 0.32, 1); pdb.inputs["Metallic"].default_value = 1.0
pdb.inputs["Roughness"].default_value = 0.3
pdb.inputs["Emission Color"].default_value = (1.0, 0.38, 0.06, 1)
PAD_HEAT = pdb.inputs["Emission Strength"]; PAD_HEAT.default_value = 0.0
PADS = []
body = box((BODY, BODY, BH), (0, 0, 0.035 + BH / 2), EPOXY)
bv = body.modifiers.new("b", "BEVEL"); bv.width = 0.035; bv.segments = 4
dimple = cyl(0.07, 0.01, (-BODY / 2 + 0.22, -BODY / 2 + 0.22, 0.035 + BH), EPOXY, 32)   # pin-1 mark
TIN = metal("LeadGold", (1.0, 0.78, 0.38), 0.22)
for side in range(4):
    a = side * math.pi / 2
    ca, sa = math.cos(a), math.sin(a)
    R = lambda x, y, z=0.0: Vector((x * ca - y * sa, x * sa + y * ca, z))
    for i in range(NL):
        y = (i - (NL - 1) / 2) * PITCH
        # gull-wing: out of the body mid-height, bend down, a flat foot on its pad
        box((0.07, 0.032, 0.012), R(BODY / 2 + 0.035, y, 0.105), TIN, a)
        sl = box((0.1, 0.032, 0.012), R(BODY / 2 + 0.095, y, 0.06), TIN, a)
        sl.rotation_euler.rotate_axis("Y", math.radians(58) * (1 if side in (0, 1) else 1))
        box((0.09, 0.032, 0.012), R(BODY / 2 + 0.165, y, 0.012), TIN, a)
        PADS.append(box((0.15, 0.042, 0.004), R(BODY / 2 + 0.175, y, 0.002), PADM, a))     # the board pad

CHIP_OBJS = [o for o in bpy.data.objects if o not in _before_chip and o not in PADS]

# ---- a populated board (owner: "more detail and colour"): electrolytic caps with coloured sleeves, smaller chips, RAM,
# ferrite inductors, a crystal can - placed apart from each other, kept out of the chip's area ----
def plain_m(name, col, rough, metal_=0.0, coat=0.0):
    m_, n_, _ = mat(name); b_ = bsdf(n_)
    b_.inputs["Base Color"].default_value = (*col, 1); b_.inputs["Roughness"].default_value = rough
    b_.inputs["Metallic"].default_value = metal_; b_.inputs["Coat Weight"].default_value = coat
    return m_
SLEEVES = [plain_m("SleeveBlue", (0.03, 0.14, 0.75), 0.28, coat=0.8), plain_m("SleevePurple", (0.42, 0.06, 0.7), 0.28, coat=0.8),
           plain_m("SleeveTeal", (0.0, 0.45, 0.5), 0.28, coat=0.8), plain_m("SleeveRed", (0.6, 0.03, 0.08), 0.28, coat=0.8)]
ALTOP = metal("AlTop", (0.85, 0.86, 0.88), 0.25)
FERRITE = plain_m("Ferrite", (0.06, 0.06, 0.065), 0.6)
CHIPBLK = plain_m("SmallChip", (0.008, 0.008, 0.01), 0.45, coat=0.2)
placed = []
def free_spot(r, tries=200, rmin=2.0, rmax=10.0):
    for _ in range(tries):
        ang = rng.uniform(0, 2 * math.pi); d = rng.uniform(rmin, rmax)
        c = Vector((d * math.cos(ang) * 1.1, d * math.sin(ang) + 2.0, 0))
        if max(abs(c.x), abs(c.y)) < 2.0:
            continue
        if all((c - q).length > r + rq + 0.15 for q, rq in placed):
            placed.append((c, r)); return c
    return None
for _ in range(26):                                          # electrolytic capacitors
    r = rng.uniform(0.16, 0.3); h = rng.uniform(0.45, 0.85); c = free_spot(r, rmin=2.4)
    if c is None: continue
    o = cyl(r, h, (c.x, c.y, h / 2), rng.choice(SLEEVES), 40)
    top = cyl(r * 0.94, 0.02, (c.x, c.y, h + 0.005), ALTOP, 40)
    box((r * 1.5, 0.012, 0.012), (c.x, c.y, h + 0.016), PCB)                    # the vent cross
    box((0.012, r * 1.5, 0.012), (c.x, c.y, h + 0.016), PCB)
for _ in range(8):                                           # smaller QFN/SOIC chips with leads
    w = rng.uniform(0.5, 0.9); c = free_spot(w * 0.75, rmin=2.5)
    if c is None: continue
    rz = rng.choice([0, math.pi / 2])
    box((w, w * rng.choice([1.0, 0.6]), 0.09), (c.x, c.y, 0.045), CHIPBLK, rz)
    nl = int(w / 0.09)
    for sd in (-1, 1):
        for i in range(nl):
            u = (i - (nl - 1) / 2) * 0.09
            q = Vector((u, sd * (w * 0.3 + 0.05), 0.012))
            q.rotate(Matrix.Rotation(rz, 3, "Z"))
            box((0.03, 0.1, 0.012), c + q, TIN, rz)
for _ in range(5):                                           # RAM chips (BGA, flat black rectangles)
    c = free_spot(0.75, rmin=3.0)
    if c is None: continue
    box((1.3, 0.75, 0.1), (c.x, c.y, 0.06), CHIPBLK, rng.choice([0, math.pi / 2]))
for _ in range(12):                                          # ferrite inductors
    s_ = rng.uniform(0.22, 0.36); c = free_spot(s_ * 0.75, rmin=2.2)
    if c is None: continue
    o = box((s_, s_, s_ * 0.6), (c.x, c.y, s_ * 0.3), FERRITE); bv_ = o.modifiers.new("b", "BEVEL"); bv_.width = 0.03; bv_.segments = 3
c = free_spot(0.3, rmin=2.3)                                 # a crystal oscillator can
if c is not None:
    o = box((0.5, 0.22, 0.14), (c.x, c.y, 0.07), ALTOP); bv_ = o.modifiers.new("b", "BEVEL"); bv_.width = 0.05; bv_.segments = 4

# ---- traces: buses of neighbouring leads run straight out, fan with one 45-degree jog, continue to the edge ----
paths = []
for side in range(4):
    a = side * math.pi / 2
    ca, sa = math.cos(a), math.sin(a)
    R = lambda x, y: Vector((x * ca - y * sa, x * sa + y * ca, 0))
    i = 0
    while i < NL:
        n = rng.randint(3, 6)
        jog = rng.choice([-1, 1]) * rng.uniform(0.15, 0.7)
        x1 = BODY / 2 + 0.45 + rng.uniform(0, 0.6)
        L = rng.uniform(5.0, 11.0)
        for k in range(n):
            if i + k >= NL:
                break
            y = (i + k - (NL - 1) / 2) * PITCH
            if rng.random() < 0.15:
                continue                               # a few leads route underneath (no visible trace)
            kk = k if jog > 0 else (n - 1 - k)
            xk = x1 + kk * 0.05
            y2 = y + jog
            pts = [R(BODY / 2 + 0.25, y), R(xk, y), R(xk + abs(jog), y2), R(xk + L, y2)]
            paths.append(pts)
        i += n
# the rest of the motherboard: many more routed buses all over the board (not tied to the chip)
chip_paths = len(paths)
centres = []
for _ in range(400):
    c = Vector((rng.uniform(-9, 9), rng.uniform(-6, 12), 0))
    if c.length < 3.4 or any((c - q).length < 1.9 for q in centres):
        continue                                       # keep buses apart - real traces on one layer never cross
    if len(centres) >= 70:
        break
    centres.append(c)
    a = rng.choice([0, 0.5, 1, 1.5]) * math.pi
    ca, sa = math.cos(a), math.sin(a)
    R2 = lambda x, y: c + Vector((x * ca - y * sa, x * sa + y * ca, 0))
    n = rng.randint(3, 9); jog = rng.choice([-1, 1]) * rng.uniform(0.2, 0.8); L1 = rng.uniform(0.4, 2.0); L2 = rng.uniform(0.8, 3.5)
    for k in range(n):
        y = k * 0.06; kk = k if jog > 0 else n - 1 - k
        paths.append([R2(0, y), R2(L1 + kk * 0.05, y), R2(L1 + kk * 0.05 + abs(jog), y + jog), R2(L1 + kk * 0.05 + abs(jog) + L2, y + jog)])
ribbon(paths, 0.018, 0.0015, TRACE, "Traces", False)
lit = [p for j, p in enumerate(paths) if rng.random() < (0.32 if j < chip_paths else 0.07)]
ribbon(lit, 0.008, 0.0025, GLOW, "Signals")
for pts in paths:                                         # via ring where a trace ends or turns
    for p in (pts[-1],) + ((pts[2],) if rng.random() < 0.25 else ()):
        o = cyl(0.04, 0.006, (p.x, p.y, 0.003), GOLD, 20)
        cyl(0.017, 0.008, (p.x, p.y, 0.003), PCB, 16)
# scattered SMD parts between the buses
RES, rn_, rL_ = mat("ResistorBody")
rb_ = bsdf(rn_); rb_.inputs["Base Color"].default_value = (0.01, 0.01, 0.012, 1); rb_.inputs["Roughness"].default_value = 0.35
for pts in rng.sample(paths, 260):
    i = rng.randint(1, len(pts) - 2)
    p0, p1 = pts[i], pts[i + 1]
    d = (p1 - p0)
    if d.length < 0.4:
        continue
    t = d.normalized()
    p = p0 + d * rng.uniform(0.2, 0.8) + Vector((-t.y, t.x, 0)) * 0.09 + Vector((0, 0, 0.02))
    rz = math.atan2(t.y, t.x)
    big = rng.random() < 0.3
    box((0.16 if big else 0.1, 0.08 if big else 0.05, 0.04), p, CAPB if rng.random() < 0.5 else RES, rz)
    for e in (-1, 1):
        dd = Vector((math.cos(rz), math.sin(rz), 0)) * (0.075 if big else 0.045) * e
        box((0.02, 0.081 if big else 0.051, 0.041), p + dd, ALU, rz)

# ---- light ----
def area(name, loc, size, power, col, size_y=None, target=(0, 0, 0.1)):
    l = bpy.data.lights.new(name, "AREA"); l.shape = "RECTANGLE"; l.size = size; l.size_y = size_y or size
    l.energy = power; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return o


area("Key", (-5.0, -3.0, 5.0), 4.0, 420.0, (1.0, 0.97, 0.93))
area("Rim", (4.0, 4.5, 2.0), 0.8, 260.0, (0.6, 0.78, 1.0), size_y=5.0)
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.002, 0.004, 1)
# bloom on the signals only
ct = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ct.nodes.new("CompositorNodeRLayers"); gl_ = ct.nodes.new("CompositorNodeGlare")
gl_.inputs["Type"].default_value = "Bloom"; gl_.inputs["Threshold"].default_value = 1.5
gl_.inputs["Strength"].default_value = 0.5; gl_.inputs["Size"].default_value = 0.7
co = ct.nodes.new("NodeGroupOutput")
ct.links.new(rl.outputs["Image"], gl_.inputs["Image"]); ct.links.new(gl_.outputs["Image"], co.inputs[0])
scene.compositing_node_group = ct; scene.render.use_compositing = True

# ---- camera: low 3/4 like a product macro, shallow focus on the chip, the far board melts into bokeh ----
camd = bpy.data.cameras.new("Cam"); camd.lens = 42; camd.sensor_width = 36
cam = bpy.data.objects.new("Cam", camd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = Vector((2.9, -5.6, 5.6))
tgt = Vector((0.0, 0.6, 0.0))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
camd.dof.use_dof = True
camd.dof.focus_distance = (tgt - cam.location).length - 0.4
camd.dof.aperture_fstop = 2.8

if not globals().get("ANIM"):                              # chip_anim.py exec's this file to build the scene only
    scene.render.filepath = OUT
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("wrote", OUT)
