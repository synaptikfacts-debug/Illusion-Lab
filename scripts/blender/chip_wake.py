# 0026 "This chip is waking up" - concept still (owner pick Nov 17 2026, after 0024 was liked).
# A REAL wire-bonded chip in an open ceramic package, macro: a silicon die with thin-film rainbow interference and a real
# floor plan (cache arrays, logic, buses, a power ring, aluminium bond pads), gold ball-bond wires arcing up to gold lead
# fingers on a stepped shelf, a gold seal ring, black ceramic body with gold leads. Dark studio, raking key, macro DOF.
# Usage: blender -b --factory-startup -P scripts/blender/chip_wake.py -- <out.png> [samples] [WxH]
import math
import os
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.abspath(argv[0]) if argv else os.path.abspath("chip_still.png")
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


def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def bsdf(n):
    return next(x for x in n if x.type == "BSDF_PRINCIPLED")


def metal(name, col, rough, film=0.0):
    m, n, L = mat(name)
    b = bsdf(n)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    if film:
        b.inputs["Thin Film Thickness"].default_value = film
    return m


GOLD = metal("Gold", (1.0, 0.76, 0.33), 0.16)
GOLD_SAT = metal("GoldSatin", (1.0, 0.74, 0.32), 0.32)
ALU = metal("Aluminium", (0.91, 0.92, 0.93), 0.28)

# black ceramic: almost black, a soft satin sheen, faint grain
CER, cn, cL = mat("Ceramic")
cb = bsdf(cn)
cb.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
cb.inputs["Roughness"].default_value = 0.42
cb.inputs["Coat Weight"].default_value = 0.25
cb.inputs["Coat Roughness"].default_value = 0.2
cnz = cn.new("ShaderNodeTexNoise"); cnz.inputs["Scale"].default_value = 900.0
cbm = cn.new("ShaderNodeBump"); cbm.inputs["Strength"].default_value = 0.08
cL.new(cnz.outputs["Fac"], cbm.inputs["Height"]); cL.new(cbm.outputs["Normal"], cb.inputs["Normal"])

# ---- the die surface: a floor plan of rectangular blocks, each its own pattern + thin-film thickness (rainbow) ----
DIE, dn, dL = mat("Die")
db = bsdf(dn)
# silicon under SiO2/SiN passivation: a near-mirror dark dielectric (IOR ~3.9) - interference gives SATURATED colours
db.inputs["Base Color"].default_value = (0.02, 0.022, 0.026, 1)
db.inputs["Metallic"].default_value = 0.0
db.inputs["IOR"].default_value = 3.9
db.inputs["Thin Film IOR"].default_value = 1.6
tc = dn.new("ShaderNodeTexCoord")


def brick_rand(scale, w, h, off):
    """rectangular floor-plan blocks: a brick texture whose per-brick random colour is used as a random number"""
    br = dn.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = scale
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h
    br.inputs["Mortar Size"].default_value = 0.012
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Color1"].default_value = (0, 0, 0, 1)
    br.inputs["Color2"].default_value = (1, 1, 1, 1)
    br.inputs["Mortar"].default_value = (0.5, 0.5, 0.5, 1)
    br.offset = off
    br.offset_frequency = 2
    dL.new(tc.outputs["Generated"], br.inputs["Vector"])
    bw = dn.new("ShaderNodeRGBToBW"); dL.new(br.outputs["Color"], bw.inputs["Color"])
    return bw.outputs["Val"], br.outputs["Fac"]


R1, M1 = brick_rand(0.62, 0.62, 0.34, 0.37)      # big macro blocks (CPU cores, cache, IO)
R2, M2 = brick_rand(2.2, 0.5, 0.21, 0.29)      # sub-blocks
R3, M3 = brick_rand(7.5, 0.45, 0.18, 0.41)      # small blocks inside the sub-blocks
_, M4 = brick_rand(46.0, 0.9, 0.12, 0.0)        # the metal routing grid (mortar = thin bus lines)
# fine textures inside blocks
brA = dn.new("ShaderNodeTexBrick"); brA.inputs["Scale"].default_value = 260.0; brA.inputs["Mortar Size"].default_value = 0.12
brA.inputs["Brick Width"].default_value = 0.5; brA.inputs["Row Height"].default_value = 0.25; brA.offset = 0.0
dL.new(tc.outputs["Generated"], brA.inputs["Vector"])                       # cache arrays: very fine regular grid
mpB = dn.new("ShaderNodeMapping"); mpB.inputs["Scale"].default_value = (1.0, 9.0, 1.0)
dL.new(tc.outputs["Generated"], mpB.inputs["Vector"])
nzB = dn.new("ShaderNodeTexNoise"); nzB.inputs["Scale"].default_value = 420.0; nzB.inputs["Detail"].default_value = 0.0
dL.new(mpB.outputs["Vector"], nzB.inputs["Vector"])
thB = dn.new("ShaderNodeMath"); thB.operation = "GREATER_THAN"; thB.inputs[1].default_value = 0.5; dL.new(nzB.outputs["Fac"], thB.inputs[0])
wvC = dn.new("ShaderNodeTexWave"); wvC.wave_type = "BANDS"; wvC.wave_profile = "SAW"; wvC.inputs["Scale"].default_value = 70.0
dL.new(tc.outputs["Generated"], wvC.inputs["Vector"])
thC = dn.new("ShaderNodeMath"); thC.operation = "GREATER_THAN"; thC.inputs[1].default_value = 0.55; dL.new(wvC.outputs["Fac"], thC.inputs[0])


def mixf(a, b, fac):
    m_ = dn.new("ShaderNodeMix"); m_.data_type = "FLOAT"
    dL.new(fac, m_.inputs["Factor"]); dL.new(a, m_.inputs["A"]); dL.new(b, m_.inputs["B"])
    return m_.outputs["Result"]


def gt(v, t):
    g = dn.new("ShaderNodeMath"); g.operation = "GREATER_THAN"; g.inputs[1].default_value = t; dL.new(v, g.inputs[0]); return g.outputs[0]


pat = mixf(mixf(brA.outputs["Fac"], thB.outputs[0], gt(R2, 0.4)), thC.outputs[0], gt(R2, 0.82))
# film thickness: the big block sets the colour family, the sub-block shifts it, metal lines add a little
t1 = dn.new("ShaderNodeMath"); t1.operation = "MULTIPLY_ADD"; t1.inputs[1].default_value = 300.0; t1.inputs[2].default_value = 260.0  # 1st-2nd order = saturated
dL.new(R1, t1.inputs[0])
t2 = dn.new("ShaderNodeMath"); t2.operation = "MULTIPLY_ADD"; t2.inputs[1].default_value = 14.0
dL.new(R2, t2.inputs[0]); dL.new(t1.outputs[0], t2.inputs[2])
t3 = dn.new("ShaderNodeMath"); t3.operation = "MULTIPLY_ADD"; t3.inputs[1].default_value = 45.0
dL.new(pat, t3.inputs[0]); dL.new(t2.outputs[0], t3.inputs[2])
t4 = dn.new("ShaderNodeMath"); t4.operation = "MULTIPLY_ADD"; t4.inputs[1].default_value = 22.0
dL.new(R3, t4.inputs[0]); dL.new(t3.outputs[0], t4.inputs[2])
bus = dn.new("ShaderNodeMath"); bus.operation = "SUBTRACT"; bus.inputs[0].default_value = 1.0; dL.new(M4, bus.inputs[1])
t5 = dn.new("ShaderNodeMath"); t5.operation = "MULTIPLY_ADD"; t5.inputs[1].default_value = 0.0
dL.new(bus.outputs[0], t5.inputs[0]); dL.new(t4.outputs[0], t5.inputs[2])
dL.new(t5.outputs[0], db.inputs["Thin Film Thickness"])
rr = dn.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.2; rr.inputs["To Max"].default_value = 0.08
dL.new(pat, rr.inputs["Value"]); dL.new(rr.outputs["Result"], db.inputs["Roughness"])
# channels between blocks (mortar of both brick layers) are recessed
ch0 = dn.new("ShaderNodeMath"); ch0.operation = "MINIMUM"; dL.new(M1, ch0.inputs[0]); dL.new(M2, ch0.inputs[1])
ch = dn.new("ShaderNodeMath"); ch.operation = "MINIMUM"; dL.new(ch0.outputs[0], ch.inputs[0]); dL.new(M3, ch.inputs[1])
hh = dn.new("ShaderNodeMath"); hh.operation = "MULTIPLY_ADD"; hh.inputs[1].default_value = 0.25
dL.new(pat, hh.inputs[0]); dL.new(ch.outputs[0], hh.inputs[2])
dbm = dn.new("ShaderNodeBump"); dbm.inputs["Strength"].default_value = 0.3; dbm.inputs["Distance"].default_value = 0.002
dL.new(hh.outputs[0], dbm.inputs["Height"]); dL.new(dbm.outputs["Normal"], db.inputs["Normal"])

# ---- geometry (1 unit = 10 mm) ----
def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    return o


def bevel(o, w, seg=3):
    b = o.modifiers.new("bev", "BEVEL"); b.width = w; b.segments = seg; b.limit_method = "ANGLE"


PK, CAV = 3.2, 1.7            # package width, cavity width
pkg = box("Package", (PK, PK, 0.34), (0, 0, -0.17), CER); bevel(pkg, 0.03)
cut = box("Cut", (CAV + 0.5, CAV + 0.5, 0.2), (0, 0, 0.0), CER)      # the stepped shelf (upper tier)
cut2 = box("Cut2", (CAV, CAV, 0.4), (0, 0, -0.1), CER)               # the die cavity (lower tier)
for c in (cut, cut2):
    m_ = pkg.modifiers.new("b" + c.name, "BOOLEAN"); m_.object = c; m_.operation = "DIFFERENCE"
    c.hide_render = True
box("CavityFloor", (CAV, CAV, 0.01), (0, 0, -0.205), GOLD_SAT)
seal = box("SealRing", (CAV + 0.86, CAV + 0.86, 0.012), (0, 0, 0.006), GOLD)
sh = box("SealHole", (CAV + 0.62, CAV + 0.62, 0.05), (0, 0, 0.006), GOLD)
m_ = seal.modifiers.new("hole", "BOOLEAN"); m_.object = sh; m_.operation = "DIFFERENCE"; sh.hide_render = True
DIE_W, DIE_T = 1.15, 0.07
DZ = -0.2 + DIE_T                                                    # die top height
die = box("Die", (DIE_W, DIE_W, DIE_T), (0, 0, -0.2 + DIE_T / 2), DIE)
die.data.materials.clear(); die.data.materials.append(DIE)
# bond pads round the die edge + lead fingers on the shelf, wires between them
NP = 22                                                              # pads per side
SHELF_Z = -0.1
pads, fingers = [], []
for side in range(4):
    ang = side * math.pi / 2
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(NP):
        u = (i - (NP - 1) / 2) / (NP - 1)
        pl = Vector((DIE_W / 2 - 0.035, u * (DIE_W - 0.14), DZ + 0.002))
        fl = Vector((CAV / 2 + 0.11, u * (CAV + 0.22), SHELF_Z + 0.004))
        rot = lambda v: Vector((v.x * ca - v.y * sa, v.x * sa + v.y * ca, v.z))
        p, f = rot(pl), rot(fl)
        pd = box("Pad", (0.038, 0.032, 0.004), p, ALU); pd.rotation_euler.z = ang
        fg = box("Finger", (0.16, 0.042, 0.008), f, GOLD); fg.rotation_euler.z = ang
        pads.append(p); fingers.append(f)
# leads out of the package sides
for side in range(4):
    ang = side * math.pi / 2
    for i in range(18):
        u = (i - 8.5) / 17 * (PK - 0.5)
        x = PK / 2 + 0.16
        o = box("Lead", (0.34, 0.07, 0.025), (x * math.cos(ang) - u * math.sin(ang), x * math.sin(ang) + u * math.cos(ang), -0.25), GOLD)
        o.rotation_euler.z = ang
# gold wires: ball on the pad, a loop rising ~0.18, landing flat on the finger (wedge)
wire_curve_data = []
for k, (p, f) in enumerate(zip(pads, fingers)):
    cu = bpy.data.curves.new(f"Wire{k}", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0021
    cu.bevel_resolution = 3
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(2)
    d = (f - p)
    top = p + d * 0.32 + Vector((0, 0, 0.17 + 0.02 * math.sin(k * 1.7)))
    pts = [p + Vector((0, 0, 0.006)), top, f + Vector((0, 0, 0.004))]
    for bp, co in zip(sp.bezier_points, pts):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    sp.bezier_points[0].handle_right = p + Vector((0, 0, 0.12))       # ball bond: the wire leaves straight up
    sp.bezier_points[0].handle_left = p - Vector((0, 0, 0.02))
    sp.bezier_points[0].handle_left_type = sp.bezier_points[0].handle_right_type = "FREE"
    ob = bpy.data.objects.new(f"Wire{k}", cu)
    ob.data.materials.append(GOLD)
    scene.collection.objects.link(ob)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0075, location=p + Vector((0, 0, 0.004)), segments=16, ring_count=8)
    bpy.context.active_object.data.materials.append(GOLD)

# ---- stage: dark glossy surface ----
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -0.264))
fl_ = bpy.context.active_object
FM, fn_, fL_ = mat("Floor")
fb_ = bsdf(fn_)
fb_.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
fb_.inputs["Roughness"].default_value = 0.18
fl_.data.materials.append(FM)


# ---- lights: a big raking softbox (key), a cool strip rim, a warm low kicker; colour comes from the film, not gels ----
def area(name, loc, size, power, col, size_y=None, target=(0, 0, -0.1)):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = "RECTANGLE"
    l.size = size
    l.size_y = size_y or size
    l.energy = power
    l.color = col
    o = bpy.data.objects.new(name, l)
    o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return o


area("Key", (-4.0, -2.5, 4.5), 4.0, 900.0, (1.0, 0.97, 0.92))
area("Rim", (3.5, 3.0, 1.8), 0.6, 420.0, (0.75, 0.88, 1.0), size_y=4.0)
area("Kick", (3.0, -3.5, 0.6), 1.5, 160.0, (1.0, 0.86, 0.7))
area("Top", (0.0, 0.0, 6.0), 3.0, 120.0, (0.92, 0.95, 1.0))
# the die is a mirror: a big soft panel in the mirror direction of the camera makes the interference colours glow
# (exactly how real die macro shots are lit); with a gradient across it the colours shift from block to block
mir = area("DieMirror", (-2.6, 4.1, 3.4), 3.2, 190.0, (0.95, 0.97, 1.0), size_y=2.2, target=(0, 0, -0.13))
mir.visible_camera = False
_dc = bpy.data.collections.new("DieOnly"); _dc.objects.link(die)
mir.light_linking.receiver_collection = _dc          # light the die only - the black ceramic stays black
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.0022, 0.0026, 1)

# ---- camera: macro 3/4, low, shallow focus on the near wires ----
camd = bpy.data.cameras.new("Cam")
camd.lens = 100
camd.sensor_width = 36
cam = bpy.data.objects.new("Cam", camd)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = Vector((2.2, -3.25, 1.75))
tgt = Vector((-0.05, 0.2, -0.16))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
camd.dof.use_dof = True
camd.dof.focus_distance = (tgt - cam.location).length - 0.55
camd.dof.aperture_fstop = 8.0

scene.render.filepath = OUT
scene.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("wrote", OUT)
