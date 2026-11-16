# 0024 "This core is unlocking" renderer (Blender Cycles, OptiX). A machined cryptex sphere: 7 black anodised outer
# bands + 5 chrome inner bands around a faceted crystal core. Each band has a notch with a light strip; per-frame band
# transforms come from scripts/gen-core-frames.ts (timeline src/scenes/core/core.ts).
# Usage: blender -b --factory-startup -P scripts/blender/core_unlock.py -- <dataDir> <outDir> [samples] [k] [n] [only]
import json
import math
import os
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
DATA, OUT = os.path.abspath(argv[0]), os.path.abspath(argv[1])
SAMPLES = int(argv[2]) if len(argv) > 2 else 32
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)
spec = json.load(open(os.path.join(DATA, "frames.json")))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.render.engine = "CYCLES"
scene.cycles.device = "GPU"
if os.environ.get("CORE_CPU"):  # an extra CPU-only worker that eats frames from the end while the GPU workers run
    scene.cycles.device = "CPU"
    scene.render.threads_mode = "AUTO"
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE" if os.environ.get("CORE_CPU") else "OPTIX"
scene.cycles.max_bounces = 12
scene.cycles.glossy_bounces = 6
scene.cycles.transmission_bounces = 10
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.cycles.blur_glossy = 1.0
scene.render.use_persistent_data = True
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
if os.environ.get("CORE_RES"):
    scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ["CORE_RES"].split("x")]
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
try:
    scene.view_settings.view_transform = os.environ.get("CORE_VT", "Khronos PBR Neutral")
    scene.view_settings.look = "None"
except Exception:
    scene.view_settings.view_transform = "Filmic"

CEN = Vector((0, 0, 0.36))  # sphere centre (hovering over the base)
CYAN = (0.38, 0.86, 1.0)


# ---------- materials ----------
def mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def bsdf_of(nodes):
    return next(n for n in nodes if n.type == "BSDF_PRINCIPLED")


def engraved(name, base, rough, metal=1.0, groove_rough=0.12, groove_col=None, ticks=144):
    """Machined metal: dial ticks around the band (object space azimuth) + fine lathe lines; grooves catch the light."""
    m, n, L = mat(name)
    b = bsdf_of(n)
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    tc = n.new("ShaderNodeTexCoord")
    grad = n.new("ShaderNodeTexGradient")
    grad.gradient_type = "RADIAL"  # azimuth / 2pi around local Z
    sep = n.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], grad.inputs["Vector"])
    L.new(tc.outputs["Object"], sep.inputs["Vector"])
    # small ticks every 1/ticks turn, big ones every 6th
    def frac_mask(scale, width):
        mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = scale
        L.new(grad.outputs["Fac"], mul.inputs[0])
        fr = n.new("ShaderNodeMath"); fr.operation = "FRACT"
        L.new(mul.outputs[0], fr.inputs[0])
        lt = n.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = width
        L.new(fr.outputs[0], lt.inputs[0])
        return lt
    small = frac_mask(ticks, 0.1)
    big = frac_mask(ticks / 6, 0.035)
    # lathe rings along z (latitude lines)
    zm = n.new("ShaderNodeMath"); zm.operation = "MULTIPLY"; zm.inputs[1].default_value = 900.0
    L.new(sep.outputs["Z"], zm.inputs[0])
    zs = n.new("ShaderNodeMath"); zs.operation = "SINE"
    L.new(zm.outputs[0], zs.inputs[0])
    # tick marks only on a band of latitude (near each band's middle) - mask with noise-free sine of z
    mx = n.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    L.new(small.outputs[0], mx.inputs[0]); L.new(big.outputs[0], mx.inputs[1])
    gate = n.new("ShaderNodeMath"); gate.operation = "MULTIPLY"
    zz = n.new("ShaderNodeMath"); zz.operation = "MULTIPLY"; zz.inputs[1].default_value = 140.0
    L.new(sep.outputs["Z"], zz.inputs[0])
    zsin = n.new("ShaderNodeMath"); zsin.operation = "SINE"
    L.new(zz.outputs[0], zsin.inputs[0])
    zg = n.new("ShaderNodeMath"); zg.operation = "GREATER_THAN"; zg.inputs[1].default_value = 0.55
    L.new(zsin.outputs[0], zg.inputs[0])
    L.new(mx.outputs[0], gate.inputs[0]); L.new(zg.outputs[0], gate.inputs[1])
    # roughness: base +- lathe lines, polished in the grooves
    rmix = n.new("ShaderNodeMix"); rmix.data_type = "FLOAT"
    lathe = n.new("ShaderNodeMath"); lathe.operation = "MULTIPLY_ADD"
    L.new(zs.outputs[0], lathe.inputs[0]); lathe.inputs[1].default_value = rough * 0.08; lathe.inputs[2].default_value = rough
    L.new(gate.outputs[0], rmix.inputs["Factor"])
    L.new(lathe.outputs[0], rmix.inputs["A"])
    rmix.inputs["B"].default_value = groove_rough
    L.new(rmix.outputs["Result"], b.inputs["Roughness"])
    if groove_col is not None:
        cmix = n.new("ShaderNodeMix"); cmix.data_type = "RGBA"
        L.new(gate.outputs[0], cmix.inputs["Factor"])
        cmix.inputs["A"].default_value = (*base, 1)
        cmix.inputs["B"].default_value = (*groove_col, 1)
        L.new(cmix.outputs["Result"], b.inputs["Base Color"])
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; bump.inputs["Distance"].default_value = 0.0002
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    L.new(gate.outputs[0], inv.inputs[1])
    L.new(inv.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def plain(name, base, metal, rough, coat=0.0):
    m, n, L = mat(name)
    b = bsdf_of(n)
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    return m


def emissive(name, col, strength):
    m, n, L = mat(name)
    n.clear()
    e = n.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*col, 1)
    e.inputs["Strength"].default_value = strength
    o = n.new("ShaderNodeOutputMaterial")
    L.new(e.outputs[0], o.inputs["Surface"])
    return m, e


ANOD = engraved("BlackAnodised", (0.02, 0.022, 0.028), 0.28, groove_rough=0.1, groove_col=(0.3, 0.32, 0.36))
EDGE = plain("PolishedEdge", (0.92, 0.93, 0.95), 1.0, 0.07)
def add_circuit(m):
    """Light channels etched into the INSIDE of the bands, like a circuit: grid traces broken by noise + vias.
    Lit per band through the object property "glow" (dark until the band unlocks)."""
    n, L = m.node_tree.nodes, m.node_tree.links
    b = bsdf_of(n)
    tc = n.new("ShaderNodeTexCoord")
    dp = n.new("ShaderNodeVectorMath"); dp.operation = "DOT_PRODUCT"
    L.new(tc.outputs["Normal"], dp.inputs[0]); L.new(tc.outputs["Object"], dp.inputs[1])
    inner = n.new("ShaderNodeMath"); inner.operation = "LESS_THAN"; inner.inputs[1].default_value = 0.0
    L.new(dp.outputs["Value"], inner.inputs[0])
    br = n.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 70.0; br.inputs["Mortar Size"].default_value = 0.018
    br.inputs["Mortar Smooth"].default_value = 0.0
    br.inputs["Color1"].default_value = (0, 0, 0, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1); br.inputs["Mortar"].default_value = (1, 1, 1, 1)
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 110.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    keep = n.new("ShaderNodeMath"); keep.operation = "GREATER_THAN"; keep.inputs[1].default_value = 0.6
    L.new(nz.outputs["Fac"], keep.inputs[0])
    tr = n.new("ShaderNodeMath"); tr.operation = "MULTIPLY"
    L.new(br.outputs["Fac"], tr.inputs[0]); L.new(keep.outputs[0], tr.inputs[1])
    vo = n.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 160.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    via = n.new("ShaderNodeMath"); via.operation = "LESS_THAN"; via.inputs[1].default_value = 0.07
    L.new(vo.outputs["Distance"], via.inputs[0])
    pat = n.new("ShaderNodeMath"); pat.operation = "MAXIMUM"
    L.new(tr.outputs[0], pat.inputs[0]); L.new(via.outputs[0], pat.inputs[1])
    at = n.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "glow"
    m1 = n.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    L.new(pat.outputs[0], m1.inputs[0]); L.new(inner.outputs[0], m1.inputs[1])
    m2 = n.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    L.new(m1.outputs[0], m2.inputs[0]); L.new(at.outputs["Fac"], m2.inputs[1])
    m3 = n.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.inputs[1].default_value = 7.0
    L.new(m2.outputs[0], m3.inputs[0])
    L.new(m3.outputs[0], b.inputs["Emission Strength"])
    sep = n.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs["Vector"])
    zr = n.new("ShaderNodeMapRange"); zr.inputs["From Min"].default_value = -0.1; zr.inputs["From Max"].default_value = 0.1
    L.new(sep.outputs["Z"], zr.inputs["Value"])
    cr = n.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (0.45, 0.25, 1.0, 1)
    cr.color_ramp.elements[1].color = (0.2, 0.8, 1.0, 1)
    L.new(zr.outputs["Result"], cr.inputs["Fac"])
    L.new(cr.outputs["Color"], b.inputs["Emission Color"])


add_circuit(ANOD)
CHROME = engraved("Chrome", (0.86, 0.88, 0.92), 0.05, groove_rough=0.35, groove_col=(0.25, 0.26, 0.28), ticks=96)
CHEDGE = plain("ChromeEdge", (0.95, 0.96, 0.98), 1.0, 0.03)


# ---------- geometry ----------
def band_mesh(name, R, T, lat0, lat1, gap_deg, ang0=0.0, ang1=2 * math.pi, steps=256, nprof=14):
    a0, a1 = math.radians(lat0 + (gap_deg if lat0 > -89.9 else 0)), math.radians(lat1 - (gap_deg if lat1 < 89.9 else 0))
    bm = bmesh.new()
    prof = []
    for k in range(nprof + 1):
        a = a0 + (a1 - a0) * k / nprof
        prof.append((R * math.cos(a), R * math.sin(a)))
    for k in range(nprof, -1, -1):
        a = a0 + (a1 - a0) * k / nprof
        prof.append(((R - T) * math.cos(a), (R - T) * math.sin(a)))
    vs = [bm.verts.new((max(1e-6, x) * math.cos(ang0), max(1e-6, x) * math.sin(ang0), z)) for x, z in prof]
    es = [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    full = abs(ang1 - ang0 - 2 * math.pi) < 1e-6
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=ang1 - ang0, steps=steps, use_merge=full)
    if not full:
        # close the two ends of a partial spin
        pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def cutter(R, T, width, zr):
    bpy.ops.mesh.primitive_cube_add(size=1)
    c = bpy.context.active_object
    depth = T * 0.55 + 0.02
    c.scale = (depth, width, zr)
    c.location = (R - T * 0.55 + depth / 2, 0, 0)
    c.hide_render = True
    c.hide_viewport = True
    return c


def build_shell(tag, sp, mats, edge_mat, notch_w):
    R, T, lats = sp["r"], sp["t"], sp["lats"]
    out = []
    cut = cutter(R, T, notch_w, R * 2.5)
    for i in range(len(lats) - 1):
        ob = band_mesh(f"{tag}{i}", R, T, lats[i], lats[i + 1], 0.45)
        ob.data.materials.append(mats)
        ob.data.materials.append(edge_mat)
        bo = ob.modifiers.new("notch", "BOOLEAN")
        bo.operation = "DIFFERENCE"
        bo.object = cut
        bo.solver = "EXACT"
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier="notch")
        bv = ob.modifiers.new("bevel", "BEVEL")
        bv.width = T * 0.09
        bv.segments = 3
        bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(40)
        bv.material = 1
        bv.harden_normals = True
        wn = ob.modifiers.new("wn", "WEIGHTED_NORMAL")
        wn.keep_sharp = True
        # the light strip in the notch floor, following the band's arc
        half = (notch_w * 0.55) / R
        st = band_mesh(f"{tag}{i}_strip", R - T * 0.5, 0.0012, lats[i], lats[i + 1], 1.4, -half, half, steps=4, nprof=10)
        sm_, se = emissive(f"{tag}{i}_light", CYAN, 0.0)
        st.data.materials.append(sm_)
        st.visible_shadow = False
        out.append((ob, st, se))
    return out


OUTB = build_shell("O", spec["outer"], ANOD, EDGE, 0.009)
INB = build_shell("I", spec["inner"], CHROME, CHEDGE, 0.005)

LEAK = []
for sp_ in (spec["outer"], spec["inner"]):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=sp_["r"] - sp_["t"] - 0.0012, location=CEN)
    lk = bpy.context.active_object
    lkm, lke = emissive("Leak", CYAN, 0.0)
    lk.data.materials.append(lkm)
    lk.visible_shadow = False
    LEAK.append((lk, lke))

# crystal core: faceted glass with a living light inside
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.045, location=CEN)
crystal = bpy.context.active_object
for p in crystal.data.polygons:
    p.use_smooth = False
gm, gn, gl = mat("CrystalGlass")
gb = bsdf_of(gn)
gb.inputs["Base Color"].default_value = (0.55, 0.88, 1.0, 1)
gb.inputs["Transmission Weight"].default_value = 1.0
gb.inputs["Roughness"].default_value = 0.02
gb.inputs["IOR"].default_value = 1.6
crystal.data.materials.append(gm)
crystal.visible_shadow = False
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.025, location=CEN)
heart = bpy.context.active_object
# the heart: a ball of light with living energy veins (4D voronoi cell edges drifting in time), not a flat disc
hm, hn, hL = mat("CoreHeart")
hn.clear()
he = hn.new("ShaderNodeEmission")
hout = hn.new("ShaderNodeOutputMaterial")
htc = hn.new("ShaderNodeTexCoord")
hvo = hn.new("ShaderNodeTexVoronoi")
hvo.voronoi_dimensions = "4D"
hvo.feature = "DISTANCE_TO_EDGE"
hvo.inputs["Scale"].default_value = 150.0
HW = hvo.inputs["W"]
hnz = hn.new("ShaderNodeTexNoise"); hnz.inputs["Scale"].default_value = 70.0; hnz.inputs["Detail"].default_value = 4.0
hdm = hn.new("ShaderNodeVectorMath"); hdm.operation = "MULTIPLY_ADD"
hdm.inputs[1].default_value = (0.012, 0.012, 0.012)
hL.new(hnz.outputs["Color"], hdm.inputs[0]); hL.new(htc.outputs["Object"], hdm.inputs[2]); hL.new(htc.outputs["Object"], hnz.inputs["Vector"])
hL.new(hdm.outputs["Vector"], hvo.inputs["Vector"])
hmr = hn.new("ShaderNodeMapRange")
hmr.inputs["From Min"].default_value = 0.0
hmr.inputs["From Max"].default_value = 0.07
hmr.inputs["To Min"].default_value = 1.0
hmr.inputs["To Max"].default_value = 0.12
hL.new(hvo.outputs["Distance"], hmr.inputs["Value"])
hcol = hn.new("ShaderNodeValToRGB")
hcol.color_ramp.elements[0].color = (0.12, 0.03, 0.55, 1)
hcol.color_ramp.elements[1].color = (0.7, 0.97, 1.0, 1)
hL.new(hmr.outputs["Result"], hcol.inputs["Fac"])
hL.new(hcol.outputs["Color"], he.inputs["Color"])
hmul = hn.new("ShaderNodeMath"); hmul.operation = "MULTIPLY"
hL.new(hmr.outputs["Result"], hmul.inputs[0])
HSTR = hmul.inputs[1]
hL.new(hmul.outputs[0], he.inputs["Strength"])
hL.new(he.outputs[0], hout.inputs["Surface"])
heart.data.materials.append(hm)
heart.visible_shadow = False
core_light = bpy.data.lights.new("CoreLight", "POINT")
core_light.color = (0.15, 0.62, 1.0)
core_light.shadow_soft_size = 0.03
cl = bpy.data.objects.new("CoreLight", core_light)
cl.location = CEN
scene.collection.objects.link(cl)

# ---------- stage ----------
bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, 0))
floor = bpy.context.active_object
fm, fn, fL = mat("Floor")
fb = bsdf_of(fn)
fb.inputs["Base Color"].default_value = (0.006, 0.007, 0.009, 1)
fb.inputs["Coat Weight"].default_value = 1.0
fb.inputs["Coat Roughness"].default_value = 0.03
fnz = fn.new("ShaderNodeTexNoise"); fnz.inputs["Scale"].default_value = 30.0
fmr = fn.new("ShaderNodeMapRange"); fmr.inputs["To Min"].default_value = 0.25; fmr.inputs["To Max"].default_value = 0.55
fL.new(fnz.outputs["Fac"], fmr.inputs["Value"])
ftc = fn.new("ShaderNodeTexCoord")
fgr = fn.new("ShaderNodeTexGradient"); fgr.gradient_type = "SPHERICAL"
fmap = fn.new("ShaderNodeMapping"); fmap.inputs["Scale"].default_value = (0.25, 0.25, 0.25)
fL.new(ftc.outputs["Object"], fmap.inputs["Vector"]); fL.new(fmap.outputs["Vector"], fgr.inputs["Vector"])
fwav = fn.new("ShaderNodeMath"); fwav.operation = "MULTIPLY"; fwav.inputs[1].default_value = 900.0
fL.new(fgr.outputs["Fac"], fwav.inputs[0])
fsin = fn.new("ShaderNodeMath"); fsin.operation = "SINE"
fL.new(fwav.outputs[0], fsin.inputs[0])
fring = fn.new("ShaderNodeMath"); fring.operation = "MULTIPLY_ADD"; fring.inputs[1].default_value = 0.18; fring.inputs[2].default_value = 0.0
fL.new(fsin.outputs[0], fring.inputs[0])
fadd = fn.new("ShaderNodeMath"); fadd.operation = "ADD"
fL.new(fmr.outputs["Result"], fadd.inputs[0]); fL.new(fring.outputs[0], fadd.inputs[1])
fL.new(fadd.outputs[0], fb.inputs["Roughness"])
fbr = fn.new("ShaderNodeTexBrick"); fbr.inputs["Scale"].default_value = 2.2; fbr.inputs["Mortar Size"].default_value = 0.006
fbr.inputs["Color1"].default_value = (0.012, 0.014, 0.018, 1); fbr.inputs["Color2"].default_value = (0.008, 0.009, 0.012, 1)
fbr.inputs["Mortar"].default_value = (0.0, 0.0, 0.0, 1)
fL.new(ftc.outputs["Object"], fbr.inputs["Vector"]); fL.new(fbr.outputs["Color"], fb.inputs["Base Color"])
fbump = fn.new("ShaderNodeBump"); fbump.inputs["Strength"].default_value = 0.25
fbsum = fn.new("ShaderNodeMath"); fbsum.operation = "ADD"
fL.new(fbr.outputs["Fac"], fbsum.inputs[0]); fL.new(fring.outputs[0], fbsum.inputs[1])
fL.new(fbsum.outputs[0], fbump.inputs["Height"]); fL.new(fbump.outputs["Normal"], fb.inputs["Normal"])
fb.inputs["Metallic"].default_value = 0.7
floor.data.materials.append(fm)

# the base: a machined ring with a light emitter under the hovering sphere
bpy.ops.mesh.primitive_cylinder_add(vertices=192, radius=0.085, depth=0.03, location=(0, 0, 0.015))
base = bpy.context.active_object
bpy.ops.mesh.primitive_cylinder_add(vertices=192, radius=0.055, depth=0.05, location=(0, 0, 0.02))
hole = bpy.context.active_object
hole.hide_render = True
bo = base.modifiers.new("hole", "BOOLEAN"); bo.object = hole; bo.operation = "DIFFERENCE"
bpy.context.view_layer.objects.active = base
bpy.ops.object.modifier_apply(modifier="hole")
bb = base.modifiers.new("bevel", "BEVEL"); bb.width = 0.002; bb.segments = 3; bb.limit_method = "ANGLE"; bb.angle_limit = math.radians(40)
base.data.materials.clear()
base.data.materials.append(plain("BaseMat", (0.012, 0.013, 0.016), 0.6, 0.38))
for p in base.data.polygons:
    p.use_smooth = True
bpy.ops.mesh.primitive_torus_add(major_radius=0.058, minor_radius=0.0018, location=(0, 0, 0.03))
emit_ring = bpy.context.active_object
erm, ere = emissive("Emitter", CYAN, 0.0)
emit_ring.data.materials.append(erm)
emit_ring.visible_shadow = False

# vault wall: a big cylinder of machined panels around the set, softly lit; thin light lines run around it
bpy.ops.mesh.primitive_cylinder_add(vertices=256, radius=2.2, depth=4.0, location=(0, 0, 1.6), end_fill_type="NOTHING")
wall = bpy.context.active_object
wm, wn_, wL = mat("VaultWall")
wb = bsdf_of(wn_)
wb.inputs["Metallic"].default_value = 0.85
wtc = wn_.new("ShaderNodeTexCoord")
brick = wn_.new("ShaderNodeTexBrick")
brick.inputs["Scale"].default_value = 3.0
brick.inputs["Mortar Size"].default_value = 0.012
brick.inputs["Color1"].default_value = (0.04, 0.05, 0.07, 1)
brick.inputs["Color2"].default_value = (0.03, 0.034, 0.042, 1)
brick.inputs["Mortar"].default_value = (0.004, 0.004, 0.005, 1)
brick.offset = 0.0
wmap = wn_.new("ShaderNodeMapping"); wmap.inputs["Scale"].default_value = (1.0, 1.0, 2.2)
wL.new(wtc.outputs["Object"], wmap.inputs["Vector"]); wL.new(wmap.outputs["Vector"], brick.inputs["Vector"])
wL.new(brick.outputs["Color"], wb.inputs["Base Color"])
wr = wn_.new("ShaderNodeMapRange"); wr.inputs["To Min"].default_value = 0.22; wr.inputs["To Max"].default_value = 0.42
wL.new(brick.outputs["Fac"], wr.inputs["Value"]); wL.new(wr.outputs["Result"], wb.inputs["Roughness"])
wbump = wn_.new("ShaderNodeBump"); wbump.inputs["Strength"].default_value = 0.6
wL.new(brick.outputs["Fac"], wbump.inputs["Height"]); wL.new(wbump.outputs["Normal"], wb.inputs["Normal"])
wall.data.materials.append(wm)
for p in wall.data.polygons:
    p.use_smooth = True
LINES = []
for z, s in [(0.06, 1.0), (0.62, 0.6), (1.05, 0.45), (1.6, 0.3)]:
    bpy.ops.mesh.primitive_torus_add(major_radius=2.17, minor_radius=0.004, major_segments=256, location=(0, 0, z))
    ln = bpy.context.active_object
    lm, le = emissive(f"Line{z}", (0.25, 0.75, 1.0), 6.0 * s)
    ln.data.materials.append(lm)
    ln.visible_shadow = False
    LINES.append((le, 6.0 * s))

# lights: a raking key softbox (top-left), a cool rim strip (behind right), a faint fill
def area(name, loc, size, power, col, shape="RECTANGLE", size_y=None):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = shape
    l.size = size
    if size_y:
        l.size_y = size_y
    l.energy = power
    l.color = col
    o = bpy.data.objects.new(name, l)
    o.location = loc
    scene.collection.objects.link(o)
    d = CEN - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o, l


key, keyL = area("Key", (-0.55, -0.45, 0.95), 0.7, 65.0, (1.0, 0.97, 0.93))
rim, rimL = area("Rim", (0.5, 0.55, 0.45), 0.06, 30.0, (0.35, 0.78, 1.0), size_y=0.7)
rim2, rim2L = area("Rim2", (-0.55, 0.5, 0.3), 0.05, 22.0, (0.6, 0.3, 1.0), size_y=0.5)
fill, fillL = area("Fill", (0.6, -0.7, 0.35), 0.9, 6.0, (0.85, 0.92, 1.0))
for o in (key, rim, rim2, fill):
    o.data.cycles.is_caustics_light = False
fill.visible_glossy = False
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.002, 0.003, 1)

# camera
camd = bpy.data.cameras.new("Cam")
camd.lens = 70
camd.sensor_fit = "AUTO"
camd.sensor_width = 36
camd.dof.use_dof = True
camd.dof.aperture_fstop = 4.0
camd.clip_start = 0.01
cam = bpy.data.objects.new("Cam", camd)
scene.collection.objects.link(cam)
scene.camera = cam


def apply(fr, t):
    tau = fr["tau"]
    for bands, data, shell in ((OUTB, fr["outer"], 0), (INB, fr["inner"], 1)):
        n = len(bands)
        for i, ((ob, st, se), b) in enumerate(zip(bands, data)):
            M = Matrix.Translation(CEN) @ Matrix.Rotation(b["angle"], 4, Vector(b["axis"])) @ Matrix.Scale(b["scale"], 4) @ Matrix.Translation((0, 0, b["lift"] / b["scale"])) @ Matrix.Rotation(b["spin"] - math.pi / 2, 4, "Z")
            ob.matrix_world = M
            st.matrix_world = M
            # the seam pulse runs bottom -> top across the outer bands
            pulse = math.exp(-(((tau - (6.75 + 0.06 * (i - (n - 1) / 2))) / 0.14) ** 2)) if shell == 0 else 0.0
            se.inputs["Strength"].default_value = 10.0 * b["lock"] + 16.0 * pulse
            ob["glow"] = (0.25 * b["lock"] + 1.3 * fr["opened"][shell] + 0.5 * fr["core"]) if shell == 0 else 0.0
    for k, (lk, lke) in enumerate(LEAK):
        data = fr["outer"] if k == 0 else fr["inner"]
        opened = max(max(b["scale"] - 1, abs(b["lift"]) * 10, abs(b["angle"])) for b in data)
        lk.hide_render = opened > 0.002
        lke.inputs["Strength"].default_value = 4.0 * fr["leak"][k] + 40.0 * fr["seam"]
    c = fr["core"]
    HSTR.default_value = 30.0 * c
    HW.default_value = 0.35 * tau
    core_light.energy = 220.0 * c
    crystal.rotation_euler = (0.3 * tau, 0.2 * tau, 0.45 * tau)
    heart.rotation_euler = crystal.rotation_euler
    ere.inputs["Strength"].default_value = 3.0 + 6.0 * c
    fade = 1.0
    f0, f1 = spec["fade"]
    if t > f0:
        fade = max(0.0, 1 - (t - f0) / (f1 - f0)) ** 1.5
    for le, s in LINES:
        le.inputs["Strength"].default_value = s * fade
    keyL.energy = 65.0 * fade
    rimL.energy = 26.0 * fade
    rim2L.energy = 22.0 * fade
    fillL.energy = 6.0 * fade
    for l in WASH:
        l.energy = 520.0 * fade
    # camera orbit around the sphere centre
    yaw, pitch, dist = fr["yaw"], fr["pitch"], fr["dist"]
    tgt = CEN + Vector(fr.get("look", (0, 0, 0)))
    loc = tgt + Vector((math.sin(yaw) * math.cos(pitch) * dist, -math.cos(yaw) * math.cos(pitch) * dist, math.sin(pitch) * dist))
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    build_fx(fr.get("fx", []), loc)
    camd.dof.focus_distance = (tgt - loc).length - (0.02 if fr.get("look", [0, 0, 0])[1] == 0 else 0.004)


# light linking: the core lights the machine, the base and the floor - not the vault wall (it washed it flat blue)
lit = bpy.data.collections.new("CoreLit")
for ob, st, se in OUTB + INB:
    lit.objects.link(ob)
for o in (crystal, heart, base, emit_ring) + tuple(l for l, _ in LEAK):
    lit.objects.link(o)
cl.light_linking.receiver_collection = lit
# the rims only sculpt the machine (their glare on the glossy floor made a flat pale patch at the frame edge)
for o in (rim, rim2):
    o.light_linking.receiver_collection = lit

# wall uplights: soft pools of light rising up the vault panels behind the sphere (lit wall only), so the top of the
# frame has depth and texture instead of flat dark blue
wl = bpy.data.collections.new("WallLit")
wl.objects.link(wall)
WASH = []
for k in range(7):
    a = math.radians(-60 + 20 * k)
    l = bpy.data.lights.new(f"Wash{k}", "SPOT")
    l.energy = 520.0
    l.spot_size = math.radians(38)
    l.spot_blend = 0.9
    l.shadow_soft_size = 0.05
    l.color = (0.3, 0.7, 1.0) if k % 2 else (0.58, 0.32, 1.0)
    o = bpy.data.objects.new(f"Wash{k}", l)
    o.location = (2.0 * math.sin(a), 2.0 * math.cos(a), 0.02)
    tgt = Vector((2.18 * math.sin(a), 2.18 * math.cos(a), 1.6))
    o.rotation_euler = (tgt - o.location).to_track_quat("-Z", "Y").to_euler()
    o.light_linking.receiver_collection = wl
    scene.collection.objects.link(o)
    WASH.append(l)

# atmosphere: a thin haze so the core's light leaves the slits as beams
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.2))
haze = bpy.context.active_object
haze.scale = (4.2, 4.2, 2.4)
vm, vn, vL = mat("Haze")
vn.remove(bsdf_of(vn))
pv = vn.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = float(os.environ.get("CORE_HAZE", "0.012"))
pv.inputs["Anisotropy"].default_value = 0.55
pv.inputs["Color"].default_value = (0.7, 0.8, 1.0, 1)
vL.new(pv.outputs[0], next(x for x in vn if x.type == "OUTPUT_MATERIAL").inputs["Volume"])
haze.data.materials.append(vm)
haze.visible_shadow = False
lit.objects.link(haze)
scene.cycles.volume_step_rate = 4.0
scene.cycles.volume_max_steps = 96

# FX: sparks, arcs, shockwaves, energy pulses, motes - one mesh of camera-facing emissive ribbons rebuilt every frame
fxm, fxn, fxL = mat("FX")
fxn.clear()
fxa = fxn.new("ShaderNodeAttribute"); fxa.attribute_type = "GEOMETRY"; fxa.attribute_name = "fxc"
fxe = fxn.new("ShaderNodeEmission"); fxe.inputs["Strength"].default_value = 1.0
fxo = fxn.new("ShaderNodeOutputMaterial")
fxL.new(fxa.outputs["Color"], fxe.inputs["Color"]); fxL.new(fxe.outputs[0], fxo.inputs["Surface"])
try:
    fxm.emission_sampling = "NONE"
except Exception:
    pass
fx_me = bpy.data.meshes.new("FX")
fx_ob = bpy.data.objects.new("FX", fx_me)
scene.collection.objects.link(fx_ob)
fx_me.materials.append(fxm)
fx_ob.visible_shadow = False


# a lens bloom on the emissive parts only (sparks, arcs, the core) - threshold well above any lit surface
ctree = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ctree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
crl = ctree.nodes.new("CompositorNodeRLayers")
cgl = ctree.nodes.new("CompositorNodeGlare")
cgl.inputs["Type"].default_value = "Bloom"
cgl.inputs["Threshold"].default_value = 2.5
cgl.inputs["Strength"].default_value = 0.55
cgl.inputs["Size"].default_value = 0.6
cout = ctree.nodes.new("NodeGroupOutput")
ctree.links.new(crl.outputs["Image"], cgl.inputs["Image"])
ctree.links.new(cgl.outputs["Image"], cout.inputs[0])
scene.compositing_node_group = ctree
scene.render.use_compositing = True


def build_fx(lines, campos):
    verts, faces, cols = [], [], []
    for ln in lines:
        p = ln["p"]
        pts = [Vector(p[k:k + 3]) for k in range(0, len(p), 3)]
        if len(pts) < 2:
            continue
        w = ln["w"] * 0.5
        c = ln["c"]
        s = ln["s"]
        base = len(verts)
        tp = ln.get("t", 0)
        for k, q in enumerate(pts):
            u = k / (len(pts) - 1)
            fk = (0.04 + 0.96 * u ** 2) if tp else 1.0  # sparks: a white-hot head, a fading tail
            wk = (0.3 + 0.7 * u) if tp else 1.0
            tan = (pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)])
            side = tan.cross(campos - q)
            if side.length < 1e-9:
                side = Vector((0, 0, 1))
            side.normalize()
            taper = 1.0 if 0 < k < len(pts) - 1 or len(pts) == 2 else 0.6
            verts.append(q + side * w * taper * wk)
            verts.append(q - side * w * taper * wk)
            cols += [(c[0] * s * fk, c[1] * s * fk, c[2] * s * fk, 1.0)] * 2
        for k in range(len(pts) - 1):
            a = base + 2 * k
            faces.append((a, a + 1, a + 3, a + 2))
    fx_me.clear_geometry()
    fx_me.from_pydata([tuple(v) for v in verts], [], faces)
    at = fx_me.color_attributes.new("fxc", "FLOAT_COLOR", "POINT")
    for i, cc in enumerate(cols):
        at.data[i].color = cc
    fx_me.materials.clear()
    fx_me.materials.append(fxm)


if os.environ.get("CORE_HIDE_BANDS"):
    for ob, st, se in (OUTB + INB if os.environ["CORE_HIDE_BANDS"] == "1" else OUTB):
        ob.hide_render = True

todo = ONLY if ONLY is not None else list(range(K, spec["n"], NN))
if os.environ.get("CORE_REVERSE"):
    todo = todo[::-1]
t0 = time.time()
for i, f in enumerate(todo):
    path = os.path.join(OUT, f"f_{f:04d}.png")
    if os.path.exists(path) and not os.environ.get("CORE_FORCE"):
        continue
    apply(spec["frames"][f], spec["times"][f])
    if os.environ.get("CORE_HIDE_BANDS"):
        print("HEART", f, HSTR.default_value, core_light.energy, [l.hide_render for l, _ in LEAK], flush=True)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t0) / (i + 1):.2f} s/frame", flush=True)
print(f"done {len(todo)} frames in {time.time() - t0:.0f} s", flush=True)
