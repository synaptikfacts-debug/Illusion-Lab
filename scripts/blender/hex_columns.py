# 0031 "3000 Hexagon Columns Shape Four Waves" - still for approval (owner, Nov 20 2026, picked idea 2 built on our
# 0011 "4096 pins draw four pictures": thousands of identical elements, each with its own rhythm, waves that freeze into
# abstract shapes, soft taps, a real ending). Ours: a honeycomb of ~3000 hexagonal columns of dark polished titanium with
# thin glowing top rims (deep blue when low, ice white when high). The hook moment: a heavy chrome sphere has just dropped
# into the field - the columns under it sank into a crater, a crest ring rises around it, ripples run outward.
# Usage: blender -b --factory-startup -P hex_columns.py -- <out.png>   env HX_RES (1080x1920), HX_SAMPLES (128)
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a_ = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a_[0])
rng = np.random.default_rng(31)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("HX_SAMPLES", "128"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 8; scene.cycles.blur_glossy = 0.5
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("HX_RES", "1080x1920").split("x")]
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT

RH = 0.065                 # hexagon circumradius
GAP = 0.008                # gap between columns
NQ, NR = 96, 86            # axial grid size (the field runs past the frame)
HIT = np.array([0.0, 0.0]) # where the sphere fell


def find(sockets, name, typ=None):
    return [s for s in sockets if s.name == name and (typ is None or s.type == typ)][0]


def link(o):
    scene.collection.objects.link(o)
    return o


def height(x, y):
    r = np.hypot(x - HIT[0], y - HIT[1])
    crater = -0.34 * np.exp(-(r / 0.42) ** 2)
    crest = 0.3 * np.exp(-((r - 0.9) / 0.17) ** 2)
    ripple = 0.13 * np.sin(r * 8.0 - 2.4) * np.exp(-r / 1.6) * (r > 1.08)
    return 0.18 + crater + crest + ripple


# ---- materials ----
TI = bpy.data.materials.new("Titanium"); TI.use_nodes = True
tb = TI.node_tree.nodes["Principled BSDF"]
tb.inputs["Base Color"].default_value = (0.13, 0.14, 0.16, 1); tb.inputs["Metallic"].default_value = 1.0
tb.inputs["Roughness"].default_value = 0.18; tb.inputs["Anisotropic"].default_value = 0.3
tn_, tl_ = TI.node_tree.nodes, TI.node_tree.links
ra = tn_.new("ShaderNodeAttribute"); ra.attribute_name = "rnd"
rgh = tn_.new("ShaderNodeMapRange"); rgh.inputs["To Min"].default_value = 0.12; rgh.inputs["To Max"].default_value = 0.3
tc_ = tn_.new("ShaderNodeTexCoord"); mp_ = tn_.new("ShaderNodeMapping"); mp_.inputs["Scale"].default_value = (1.0, 90.0, 1.0)
tl_.new(tc_.outputs["Object"], mp_.inputs["Vector"])
br = tn_.new("ShaderNodeTexNoise"); br.inputs["Scale"].default_value = 30.0; br.inputs["Detail"].default_value = 6
tl_.new(mp_.outputs["Vector"], br.inputs["Vector"])
rmix = tn_.new("ShaderNodeMath"); rmix.operation = "MULTIPLY_ADD"; tl_.new(br.outputs["Fac"], rmix.inputs[0]); rmix.inputs[1].default_value = 0.12
tl_.new(ra.outputs["Fac"], rgh.inputs["Value"]); tl_.new(rgh.outputs["Result"], rmix.inputs[2]); tl_.new(rmix.outputs[0], tb.inputs["Roughness"])
tint = tn_.new("ShaderNodeMapRange"); tint.inputs["To Min"].default_value = 0.09; tint.inputs["To Max"].default_value = 0.19
tl_.new(ra.outputs["Fac"], tint.inputs["Value"])
tcol = tn_.new("ShaderNodeCombineColor"); tl_.new(tint.outputs["Result"], tcol.inputs[0]); tl_.new(tint.outputs["Result"], tcol.inputs[1])
tb2 = tn_.new("ShaderNodeMath"); tb2.operation = "ADD"; tl_.new(tint.outputs["Result"], tb2.inputs[0]); tb2.inputs[1].default_value = 0.025
tl_.new(tb2.outputs[0], tcol.inputs[2]); tl_.new(tcol.outputs[0], tb.inputs["Base Color"])
bpb = tn_.new("ShaderNodeBump"); bpb.inputs["Strength"].default_value = 0.06; tl_.new(br.outputs["Fac"], bpb.inputs["Height"]); tl_.new(bpb.outputs["Normal"], tb.inputs["Normal"])
GLOW = bpy.data.materials.new("Rim"); GLOW.use_nodes = True
gn = GLOW.node_tree.nodes; gl = GLOW.node_tree.links
gb = gn["Principled BSDF"]; gb.inputs["Base Color"].default_value = (0.03, 0.03, 0.04, 1); gb.inputs["Roughness"].default_value = 0.15
att = gn.new("ShaderNodeAttribute"); att.attribute_name = "hn"
cr = gn.new("ShaderNodeValToRGB")                                               # the palette: low -> high
els = cr.color_ramp.elements
els[0].position = 0.0; els[0].color = (0.01, 0.03, 0.35, 1)                     # deep indigo
els[1].position = 1.0; els[1].color = (1.0, 0.95, 0.85, 1)                      # white-hot
for pos, col in ((0.22, (0.0, 0.45, 0.85)), (0.42, (0.45, 0.1, 1.0)), (0.6, (1.0, 0.06, 0.55)), (0.8, (1.0, 0.6, 0.08))):
    e_ = els.new(pos); e_.color = (*col, 1)                                     # cyan, violet, magenta, gold
gl.new(att.outputs["Fac"], cr.inputs["Fac"]); gl.new(cr.outputs["Color"], gb.inputs["Emission Color"])
es = gn.new("ShaderNodeMath"); es.operation = "POWER"; es.inputs[1].default_value = 2.6
gl.new(att.outputs["Fac"], es.inputs[0])
es2 = gn.new("ShaderNodeMath"); es2.operation = "MULTIPLY_ADD"; es2.inputs[1].default_value = 24.0; es2.inputs[2].default_value = 0.02   # dark base, hot crests
gl.new(es.outputs[0], es2.inputs[0]); gl.new(es2.outputs[0], gb.inputs["Emission Strength"])
CHROME = bpy.data.materials.new("Chrome"); CHROME.use_nodes = True
cb = CHROME.node_tree.nodes["Principled BSDF"]; cb.inputs["Base Color"].default_value = (0.95, 0.95, 0.97, 1)
cb.inputs["Metallic"].default_value = 1.0; cb.inputs["Roughness"].default_value = 0.03

# ---- the columns: one mesh; each hexagon = 6 sides + a thin glowing rim ring + a polished top ----
verts, faces, mats, hn_face, rnd_face = [], [], [], [], []
ang = np.radians(np.arange(6) * 60 + 30)            # pointy-top hexagons
ro = RH - GAP / 2                                   # outer edge (top of the chamfer)
rm, ri = ro * 0.94, ro * 0.82                       # the machined chamfer ends at rm; the glowing rim runs rm -> ri
CH = 0.008                                          # chamfer depth: a real machined edge that catches the light
crng = np.random.default_rng(5)
for q in range(-NQ // 2, NQ // 2):
    for rr in range(-NR // 2, NR // 2):
        x = math.sqrt(3) * RH * (q + rr / 2); y = 1.5 * RH * rr
        h = float(height(x, y))
        hn = float(np.clip((h - 0.0) / 0.5, 0, 1)); rv = float(crng.uniform())
        b0 = len(verts)
        for z_, rad in ((-1.2, ro), (h - CH, ro), (h, rm), (h + 0.002, ri)):
            for a_ in ang:
                verts.append((x + rad * math.cos(a_), y + rad * math.sin(a_), z_))
        for ring, mat in ((0, 0), (1, 0), (2, 1)):      # sides, chamfer (titanium), glowing rim
            for k in range(6):
                k2 = (k + 1) % 6; o0, o1 = b0 + 6 * ring, b0 + 6 * (ring + 1)
                faces.append((o0 + k, o0 + k2, o1 + k2, o1 + k)); mats.append(mat); hn_face.append(hn); rnd_face.append(rv)
        faces.append(tuple(b0 + 18 + k for k in range(6))); mats.append(1); hn_face.append(hn); rnd_face.append(rv)
me = bpy.data.meshes.new("Columns"); me.from_pydata(verts, [], faces)
me.materials.append(TI); me.materials.append(GLOW)
me.polygons.foreach_set("material_index", np.array(mats, dtype=np.int32))
at = me.attributes.new("hn", "FLOAT", "FACE"); at.data.foreach_set("value", np.array(hn_face, dtype=np.float32))
at2 = me.attributes.new("rnd", "FLOAT", "FACE"); at2.data.foreach_set("value", np.array(rnd_face, dtype=np.float32))
link(bpy.data.objects.new("Columns", me))

# ---- the sphere, resting in the crater it just made ----
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(HIT[0], HIT[1], float(height(0.0, 0.0)) + 0.27), segments=96, ring_count=48)
sph = bpy.context.active_object; sph.name = "Sphere"; sph.data.materials.append(CHROME)
for p in sph.data.polygons:
    p.use_smooth = True

# ---- world: dark for the camera, soft cool fog far away; reflections see softboxes ----
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bgw = wn["Background"]
tcw = wn.new("ShaderNodeTexCoord"); sxw = wn.new("ShaderNodeSeparateXYZ"); wl.new(tcw.outputs["Generated"], sxw.inputs[0])
hz = wn.new("ShaderNodeValToRGB"); hz.color_ramp.elements[0].position = 0.45; hz.color_ramp.elements[0].color = (0.004, 0.008, 0.02, 1)
hz.color_ramp.elements[1].position = 0.56; hz.color_ramp.elements[1].color = (0.0005, 0.0008, 0.002, 1)
wl.new(sxw.outputs["Z"], hz.inputs["Fac"]); wl.new(hz.outputs["Color"], bgw.inputs["Color"])
stu = wn.new("ShaderNodeBackground")
gz_ = wn.new("ShaderNodeValToRGB"); gz_.color_ramp.elements[0].position = 0.45; gz_.color_ramp.elements[0].color = (0.005, 0.006, 0.01, 1)
gz_.color_ramp.elements[1].position = 0.8; gz_.color_ramp.elements[1].color = (0.7, 0.74, 0.8, 1)
wl.new(sxw.outputs["Z"], gz_.inputs["Fac"])
wv_ = wn.new("ShaderNodeTexWave"); wv_.wave_type = "BANDS"; wv_.bands_direction = "X"; wv_.inputs["Scale"].default_value = 1.8
wl.new(tcw.outputs["Generated"], wv_.inputs["Vector"])
mw = wn.new("ShaderNodeMix"); mw.data_type = "RGBA"; mw.blend_type = "MULTIPLY"; find(mw.inputs, "Factor", "VALUE").default_value = 0.8
mwi = [x for x in mw.inputs if x.type == "RGBA"]; wl.new(gz_.outputs["Color"], mwi[0]); wl.new(wv_.outputs["Color"], mwi[1])
wl.new([x for x in mw.outputs if x.type == "RGBA"][0], stu.inputs["Color"])
lpw = wn.new("ShaderNodeLightPath"); msw = wn.new("ShaderNodeMixShader")
wl.new(lpw.outputs["Is Camera Ray"], msw.inputs["Fac"]); wl.new(stu.outputs[0], msw.inputs[1]); wl.new(bgw.outputs[0], msw.inputs[2])
wl.new(msw.outputs[0], wn["World Output"].inputs["Surface"])


def area(name, loc, size, pw, col, target=(0, 0, 0)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = pw; l.color = col
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("Key", (-4.2, 4.8, 2.0), 0.35, 260, (1.0, 0.95, 0.9))      # raking from behind-left: the facets catch it
area("Rim", (3.5, 3.5, 1.2), 2.0, 260, (0.7, 0.82, 1.0))
area("Front", (1.0, -5.0, 3.5), 5.0, 25, (0.9, 0.94, 1.0))

# ---- camera: low 3/4 across the field, the crater, the crest ring and the sphere in focus ----
cam = bpy.data.cameras.new("Cam"); cam.lens = 27; cam.dof.use_dof = True; cam.dof.aperture_fstop = 2.8
co = link(bpy.data.objects.new("Cam", cam)); co.location = (1.1, -2.05, 3.35)
tgt = Vector((0.05, 0.45, -0.8))
co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (Vector((0, 0, 0.1)) - co.location).length
scene.camera = co

ctr = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ctr.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ctr.nodes.new("CompositorNodeRLayers"); glr = ctr.nodes.new("CompositorNodeGlare")
glr.inputs["Type"].default_value = "Bloom"; glr.inputs["Threshold"].default_value = 1.2; glr.inputs["Strength"].default_value = 0.35; glr.inputs["Size"].default_value = 0.65
cout = ctr.nodes.new("NodeGroupOutput"); ctr.links.new(rl.outputs["Image"], glr.inputs["Image"]); ctr.links.new(glr.outputs["Image"], cout.inputs[0])
scene.compositing_node_group = ctr; scene.render.use_compositing = True

bpy.ops.render.render(write_still=True)
print("wrote", OUT)
