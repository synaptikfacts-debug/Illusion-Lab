# 0027 v3 hybrid, part 2: render a milk-drop impact = the REAL simulated liquid (crater, spray, droplets, waves; meshes
# from milk_sim_bake.py) + a hand-built CROWN on top (Mantaflow cannot hold the thin sheet): a translucent flaring sheet
# with a scalloped rim that thickens into a bead, ~22 irregular curved fingers whose tip drops pinch off and fly
# ballistically, small satellite drops; the crown sinks back as the crater closes.
# Usage: blender -b --factory-startup -P milk_hybrid.py -- <meshdir> <outdir> <f0> <f1> <k> <workers>   env MH_RES, MH_SAMPLES
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a_ = sys.argv[sys.argv.index("--") + 1:]
MESHDIR, OUT = os.path.abspath(a_[0]), os.path.abspath(a_[1])
F0, F1, K, NW = int(a_[2]), int(a_[3]), int(a_[4]), int(a_[5])
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi
IMPACT = 4            # sim frame of the impact
LIFE = 40             # crown life in sim frames
FILM = 0.025          # film surface height
rng = np.random.default_rng(27)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("MH_SAMPLES", "64"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("MH_RES", "540x960").split("x")]
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.image_settings.file_format = "PNG"

MILK = bpy.data.materials.new("Milk"); MILK.use_nodes = True
b = MILK.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.93, 0.93, 0.91, 1); b.inputs["Roughness"].default_value = 0.16
b.inputs["Subsurface Weight"].default_value = 1.0; b.inputs["Subsurface Radius"].default_value = (1.0, 0.8, 0.6)
b.inputs["Subsurface Scale"].default_value = 0.012; b.inputs["Coat Weight"].default_value = 0.4; b.inputs["Coat Roughness"].default_value = 0.05


INK = MILK.copy(); INK.name = "MilkInk"
_n, _l = INK.node_tree.nodes, INK.node_tree.links
_milk = _n["Principled BSDF"]
_ink = _n.new("ShaderNodeBsdfPrincipled")
_ink.inputs["Base Color"].default_value = (0.001, 0.001, 0.0012, 1); _ink.inputs["Roughness"].default_value = 0.45
_ink.inputs["Specular IOR Level"].default_value = 0.08; _ink.inputs["Coat Weight"].default_value = 0.12; _ink.inputs["Coat Roughness"].default_value = 0.08
_mix = _n.new("ShaderNodeMixShader"); _out = _n["Material Output"]
_l.new(_milk.outputs[0], _mix.inputs[1]); _l.new(_ink.outputs[0], _mix.inputs[2]); _l.new(_mix.outputs[0], _out.inputs["Surface"])


def _attr(name):
    a = _n.new("ShaderNodeAttribute"); a.attribute_type = "OBJECT"; a.attribute_name = name
    return a.outputs["Fac"]


def _m(op, a, b=None):
    m = _n.new("ShaderNodeMath"); m.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            m.inputs[i].default_value = x
        else:
            _l.new(x, m.inputs[i])
    return m.outputs[0]


_geo = _n.new("ShaderNodeNewGeometry"); _sep = _n.new("ShaderNodeSeparateXYZ"); _l.new(_geo.outputs["Position"], _sep.inputs[0])
_xy = _n.new("ShaderNodeCombineXYZ"); _l.new(_sep.outputs["X"], _xy.inputs["X"]); _l.new(_sep.outputs["Y"], _xy.inputs["Y"])
_len = _n.new("ShaderNodeVectorMath"); _len.operation = "LENGTH"; _l.new(_xy.outputs[0], _len.inputs[0])
R = _len.outputs["Value"]
# swirl: rotate the noise lookup by an angle that grows with radius and time -> spiral tendrils
_rot = _n.new("ShaderNodeVectorRotate"); _rot.rotation_type = "Z_AXIS"
_l.new(_geo.outputs["Position"], _rot.inputs["Vector"])
_l.new(_m("ADD", _m("MULTIPLY", R, 22.0), _attr("tw")), _rot.inputs["Angle"])
_mp = _n.new("ShaderNodeMapping"); _l.new(_rot.outputs[0], _mp.inputs["Vector"])
_mp.inputs["Scale"].default_value = (7.0, 7.0, 22.0)                      # streaks stretched up the crown wall
_nz = _n.new("ShaderNodeTexNoise"); _nz.inputs["Scale"].default_value = 2.2; _nz.inputs["Detail"].default_value = 6.0
_nz.inputs["Distortion"].default_value = 1.4
_l.new(_mp.outputs[0], _nz.inputs["Vector"])
streak = _m("MULTIPLY", _m("SUBTRACT", _nz.outputs["Fac"], 0.47), 40.0)      # sharp marbling edges
streak = _m("MINIMUM", _m("MAXIMUM", streak, 0.0), 1.0)
# bloom: dye inside a radius that grows after the impact, soft edge
bloom = _m("MINIMUM", _m("MAXIMUM", _m("DIVIDE", _m("SUBTRACT", _attr("dye_r"), R), _m("MAXIMUM", _attr("dye_r"), 0.001)), 0.0), 1.0)
bloom = _m("MULTIPLY", _m("POWER", bloom, 0.5), streak)
# the drop itself (anything above the film before the impact) and the finger tips (above tipz) are pure ink
drop = _m("MULTIPLY", _m("GREATER_THAN", _sep.outputs["Z"], 0.04), _attr("drop"))
tips = _m("MULTIPLY", _m("GREATER_THAN", _sep.outputs["Z"], _attr("tipz")), _attr("tipon"))
dye = _m("MAXIMUM", _m("MAXIMUM", drop, tips), _m("MULTIPLY", bloom, _attr("amt")))
_l.new(_m("MINIMUM", dye, 1.0), _mix.inputs["Fac"])


def new_obj(name):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); o.data.materials.append(INK)
    for k_, v_ in (("dye_r", 0.0), ("drop", 0.0), ("tipz", 9.0), ("tipon", 0.0), ("amt", 1.0), ("tw", 0.0)):
        o[k_] = v_
    return o


sim = new_obj("Sim")
crown = new_obj("Crown")
sol = crown.modifiers.new("t", "SOLIDIFY"); sol.thickness = 0.0028; sol.offset = 0.0
bits = new_obj("Bits")


def set_mesh(o, V, F):
    me = o.data; me.clear_geometry(); me.from_pydata(V, [], F)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))


def tube(V, F, pts, radii, n=10):
    """tube through a polyline with per-point radius, capped at the end"""
    base = len(V)
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        x = t.orthogonal().normalized(); y = t.cross(x)
        for j in range(n):
            a = j / n * TAU
            V.append(tuple(p + (x * math.cos(a) + y * math.sin(a)) * r))
    for i in range(len(pts) - 1):
        for j in range(n):
            a = base + i * n + j; c = base + i * n + (j + 1) % n
            F.append((a, c, c + n, a + n))
    tip = len(V); V.append(tuple(pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1]))
    last = base + (len(pts) - 1) * n
    for j in range(n):
        F.append((last + j, last + (j + 1) % n, tip))


def sphere(V, F, c, r, n=8):
    base = len(V); m = 2 * n
    for i in range(1, n):
        th = math.pi * i / n
        for j in range(m):
            ph = TAU * j / m
            V.append((c[0] + r * math.sin(th) * math.cos(ph), c[1] + r * math.sin(th) * math.sin(ph), c[2] + r * math.cos(th)))
    top = len(V); V.append((c[0], c[1], c[2] + r)); bot = len(V); V.append((c[0], c[1], c[2] - r))
    for i in range(n - 2):
        for j in range(m):
            a = base + i * m + j; c2 = base + i * m + (j + 1) % m
            F.append((a, c2, c2 + m, a + m))
    lb = base + (n - 2) * m
    for j in range(m):
        F.append((top, base + (j + 1) % m, base + j)); F.append((bot, lb + j, lb + (j + 1) % m))


NFG = 22
FG_PH = np.sort(rng.uniform(0, TAU, NFG) * 0.15 + np.linspace(0, TAU, NFG, endpoint=False))
FG_L = rng.uniform(0.35, 1.0, NFG)                   # irregular finger lengths
FG_DET = rng.uniform(0.38, 0.62, NFG)                # when each tip drop pinches off (fraction of life)
FG_CURL = rng.uniform(0.6, 1.2, NFG)


def build_crown(f):
    u = (f - IMPACT) / LIFE
    CV, CF, BV, BF = [], [], [], []
    if u <= 0 or u > 1.4:
        return CV, CF, BV, BF
    grow = min(1.0, u / 0.35)
    sink = max(0.0, (u - 0.62) / 0.38)
    rb = 0.045 + 0.075 * math.sqrt(min(u, 1.0))              # base radius spreads
    H = 0.11 * math.sin(math.pi * 0.5 * grow) * (1.0 - min(1.0, sink) ** 1.4)
    flare = 0.05 * grow + 0.02 * u
    if H > 0.004 and u <= 1.0:
        ns, nphi = 22, 220
        scal = 0.18 * grow
        top = []
        for i in range(ns):
            s = i / (ns - 1)
            for j in range(nphi):
                ph = j / nphi * TAU
                sc = math.cos(NFG * ph) * scal * s ** 4
                r = rb + flare * s ** 1.7 + 0.004 * sc
                z = FILM - 0.004 + H * s * (1.0 + 0.08 * sc)
                CV.append((r * math.cos(ph), r * math.sin(ph), z))
                if i == ns - 1:
                    top.append(Vector((r * math.cos(ph), r * math.sin(ph), z)))
        for i in range(ns - 1):
            for j in range(nphi):
                a = i * nphi + j; c = i * nphi + (j + 1) % nphi
                CF.append((a, c, c + nphi, a + nphi))
        # the rim bead (a closed tube along the top edge, varicose)
        n = 8; base = len(BV)
        for j, p in enumerate(top):
            t = (top[(j + 1) % nphi] - top[j - 1]).normalized()
            x = Vector((0, 0, 1)).cross(t).normalized(); y = t.cross(x)
            rr = 0.0042 * (1 + 0.35 * math.cos(NFG * j / nphi * TAU)) * grow
            for k in range(n):
                a = k / n * TAU
                BV.append(tuple(p + (x * math.cos(a) + y * math.sin(a)) * rr))
        for j in range(nphi):
            for k in range(n):
                a = base + j * n + k; c = base + j * n + (k + 1) % n
                a2 = base + ((j + 1) % nphi) * n + k; c2 = base + ((j + 1) % nphi) * n + (k + 1) % n
                BF.append((a, c, c2, a2))
        # fingers from the scallop peaks
        for i in range(NFG):
            ph = FG_PH[i]
            rr0 = rb + flare
            p0 = Vector((rr0 * math.cos(ph), rr0 * math.sin(ph), FILM + H * 1.04))
            out = Vector((math.cos(ph), math.sin(ph), 0))
            L = 0.07 * FG_L[i] * min(1.0, u / 0.4) * (1.0 - max(0.0, (u - FG_DET[i]) / 0.25)) * (1 - sink)
            if L < 0.003:
                continue
            pts, rad = [], []
            for k in range(7):
                v = k / 6
                pts.append(p0 + out * (L * v * 0.55 * FG_CURL[i]) + Vector((0, 0, L * v)) - Vector((0, 0, 0.25 * L * v * v * FG_CURL[i])))
                rad.append(0.0042 - 0.002 * v)
            tube(BV, BF, pts, rad, 8)
            if u < FG_DET[i]:
                sphere(BV, BF, tuple(pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.004), 0.0062 * (0.8 + 0.4 * FG_L[i]), 7)
    # detached tip drops + satellites: ballistic
    for i in range(NFG):
        ta = (u - FG_DET[i]) * LIFE / 24 * 3.0       # seconds of flight (slow motion)
        if ta <= 0:
            continue
        ph = FG_PH[i]
        rr0 = rb + flare + 0.03 * FG_L[i]
        v_out, v_up = 0.11 * FG_CURL[i], 0.2 * FG_L[i]
        z = FILM + 0.11 * 1.1 + v_up * ta - 0.6 * ta * ta
        if z < FILM:
            continue
        r = rr0 + v_out * ta
        sphere(BV, BF, (r * math.cos(ph), r * math.sin(ph), z), 0.0062 * (0.8 + 0.4 * FG_L[i]), 7)
        if FG_L[i] > 0.7:
            sphere(BV, BF, (r * math.cos(ph + 0.02), r * math.sin(ph + 0.02), z - 0.012), 0.0025, 5)
    return CV, CF, BV, BF


# ---- stage + light: black glossy floor, dark studio, strong back light so the sheet glows ----
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0)); fl = bpy.context.active_object
FM = bpy.data.materials.new("Black"); FM.use_nodes = True
fb = FM.node_tree.nodes["Principled BSDF"]; fb.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1); fb.inputs["Roughness"].default_value = 0.08
fl.data.materials.append(FM)


def area(name, loc, size, power, sy=None, target=(0, 0, 0.06)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.size_y = sy or size; l.shape = "RECTANGLE"; l.energy = power
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); scene.collection.objects.link(o)


area("Back", (0.0, 1.6, 0.45), 1.4, 110)
area("Key", (-1.1, -0.9, 1.1), 0.9, 30)
area("RimL", (1.0, 0.2, 0.25), 0.2, 35, sy=1.2)
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.003, 0.003, 0.004, 1)
camd = bpy.data.cameras.new("C"); camd.lens = 70; camd.sensor_width = 36
cam = bpy.data.objects.new("C", camd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = Vector((0.06, -1.05, 0.2)); look = Vector((0, 0, 0.06))
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
camd.dof.use_dof = True; camd.dof.focus_distance = (look - cam.location).length; camd.dof.aperture_fstop = 4.0

for f in list(range(F0, F1 + 1))[K::NW]:
    path = os.path.join(MESHDIR, "m_%04d.npz" % f)
    if not os.path.exists(path):
        continue
    d = np.load(path)
    set_mesh(sim, d["v"].tolist(), d["f"].tolist())
    CV, CF, BV, BF = build_crown(f)
    uu = max(0.0, (f - IMPACT) / 60.0)
    for o in (sim, crown, bits):
        o["dye_r"] = 0.06 + 0.42 * math.sqrt(uu)          # the black bloom spreads through the milk
        o["tw"] = 1.4 * uu                                  # and keeps swirling
    sim["drop"] = 1.0 if f <= IMPACT + 1 else 0.0           # the falling drop is ink
    crown["amt"] = 1.0; sim["amt"] = 0.9; bits["amt"] = 1.0
    uc = (f - IMPACT) / LIFE
    bits["tipon"] = 1.0; bits["tipz"] = FILM + 0.11 * math.sin(math.pi * 0.5 * min(1.0, max(0.0, uc) / 0.35)) * 0.96 + 0.012
    if CV:
        set_mesh(crown, CV, CF)
    else:
        crown.data.clear_geometry()
    if BV:
        set_mesh(bits, BV, BF)
    else:
        bits.data.clear_geometry()
    scene.render.filepath = os.path.join(OUT, "h_%04d.png" % f)
    bpy.ops.render.render(write_still=True)
print("done")
