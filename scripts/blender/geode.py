# 0031 "What's Inside This Rock?" - still for approval (owner, Nov 20 2026: "let's see how no. 1 would look").
# The reveal moment: a plain grey egg-shaped rock has just split open (the hit came on frame 0 in the reel); its back
# half faces the camera - a rim of white / pale-blue agate bands around a hollow lined with hundreds of ice-blue
# hexagonal crystals that point to the centre and glow from a light inside; stone chips and dust are still flying.
# New look vs the last reels (0030 aurora net green/violet, 0028 black ink + violet): cool basalt grey, ice blue, silver.
# Usage: blender -b --factory-startup -P geode.py -- <out.png>   env GE_RES (1080x1920), GE_SAMPLES (256)
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

a_ = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a_[0])
rng = np.random.default_rng(31)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("GE_SAMPLES", "256"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 12; scene.cycles.transmission_bounces = 12; scene.cycles.glossy_bounces = 6
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False; scene.cycles.blur_glossy = 1.0
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("GE_RES", "1080x1920").split("x")]
scene.view_settings.view_transform = "Khronos PBR Neutral"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0.35
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT

EGG = 1.3          # the rock is an upright egg: fills the 9:16 frame
RC = 0.64          # radius of the hollow inside


def link(o):
    scene.collection.objects.link(o)
    return o


def principled(name, base, rough, **kw):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1); b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m, b


def bump_noise(m, b, scale, strength, detail=8):
    nt = m.node_tree
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return nz


# ---- materials ----
ROCK, rb = principled("Rock", (0.16, 0.165, 0.18), 0.86)          # cool basalt grey, rough
nzr = bump_noise(ROCK, rb, 22.0, 0.8)
cr = ROCK.node_tree.nodes.new("ShaderNodeValToRGB")                # mottled: darker and lighter grey patches
cr.color_ramp.elements[0].color = (0.07, 0.072, 0.08, 1); cr.color_ramp.elements[1].color = (0.27, 0.275, 0.29, 1)
nz2 = ROCK.node_tree.nodes.new("ShaderNodeTexNoise"); nz2.inputs["Scale"].default_value = 3.5; nz2.inputs["Detail"].default_value = 6
ROCK.node_tree.links.new(nz2.outputs["Fac"], cr.inputs["Fac"]); ROCK.node_tree.links.new(cr.outputs["Color"], rb.inputs["Base Color"])

# the cut face: grey crystalline rock outside, then white / pale-blue agate bands around the hollow
CUT, cb = principled("Cut", (0.3, 0.31, 0.33), 0.55)
nt = CUT.node_tree
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
rx = nt.nodes.new("ShaderNodeMath"); rx.operation = "MULTIPLY"; nt.links.new(sep.outputs["X"], rx.inputs[0]); rx.inputs[1].default_value = 1.0
rz = nt.nodes.new("ShaderNodeMath"); rz.operation = "DIVIDE"; nt.links.new(sep.outputs["Z"], rz.inputs[0]); rz.inputs[1].default_value = EGG
cmb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(rx.outputs[0], cmb.inputs["X"]); nt.links.new(rz.outputs[0], cmb.inputs["Y"])
ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; nt.links.new(cmb.outputs[0], ln.inputs[0])
nd = nt.nodes.new("ShaderNodeTexNoise"); nd.inputs["Scale"].default_value = 4.0; nd.inputs["Detail"].default_value = 4
nt.links.new(tc.outputs["Object"], nd.inputs["Vector"])
dist = nt.nodes.new("ShaderNodeMath"); dist.operation = "MULTIPLY_ADD"; nt.links.new(nd.outputs["Fac"], dist.inputs[0])
dist.inputs[1].default_value = 0.09; nt.links.new(ln.outputs["Value"], dist.inputs[2])         # wobbly radius
rr = nt.nodes.new("ShaderNodeMath"); rr.operation = "DIVIDE"; nt.links.new(dist.outputs[0], rr.inputs[0]); rr.inputs[1].default_value = RC
band = nt.nodes.new("ShaderNodeMath"); band.operation = "SINE"
bm_ = nt.nodes.new("ShaderNodeMath"); bm_.operation = "MULTIPLY"; nt.links.new(rr.outputs[0], bm_.inputs[0]); bm_.inputs[1].default_value = 110.0
nB = nt.nodes.new("ShaderNodeTexNoise"); nB.inputs["Scale"].default_value = 5.0; nB.inputs["Detail"].default_value = 3
nt.links.new(tc.outputs["Object"], nB.inputs["Vector"])
ph_ = nt.nodes.new("ShaderNodeMath"); ph_.operation = "MULTIPLY_ADD"; nt.links.new(nB.outputs["Fac"], ph_.inputs[0]); ph_.inputs[1].default_value = 9.0
nt.links.new(bm_.outputs[0], ph_.inputs[2]); nt.links.new(ph_.outputs[0], band.inputs[0])
ag = nt.nodes.new("ShaderNodeValToRGB")                                                         # agate stripes
ag.color_ramp.elements[0].color = (0.24, 0.3, 0.38, 1); ag.color_ramp.elements[1].color = (0.82, 0.86, 0.9, 1)
e_ = ag.color_ramp.elements.new(0.55); e_.color = (0.34, 0.44, 0.55, 1)
e2_ = ag.color_ramp.elements.new(0.8); e2_.color = (0.6, 0.66, 0.72, 1)
nt.links.new(band.outputs[0], ag.inputs["Fac"])
zone = nt.nodes.new("ShaderNodeMapRange"); zone.inputs["From Min"].default_value = 1.27; zone.inputs["From Max"].default_value = 1.31
nt.links.new(rr.outputs[0], zone.inputs["Value"])                                                # 0 = agate rim, 1 = grey rock
sp = nt.nodes.new("ShaderNodeTexNoise"); sp.inputs["Scale"].default_value = 60.0; sp.inputs["Detail"].default_value = 6; sp.inputs["Roughness"].default_value = 0.75
nt.links.new(tc.outputs["Object"], sp.inputs["Vector"])
gr = nt.nodes.new("ShaderNodeValToRGB"); gr.color_ramp.elements[0].color = (0.035, 0.037, 0.042, 1); gr.color_ramp.elements[1].color = (0.24, 0.245, 0.26, 1)
nt.links.new(sp.outputs["Fac"], gr.inputs["Fac"])
mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"          # sockets by type: their indices moved in Blender 5
_mi = [x for x in mixc.inputs if x.type == "RGBA"]; _mf = [x for x in mixc.inputs if x.name == "Factor" and x.type == "VALUE"][0]
nt.links.new(zone.outputs["Result"], _mf); nt.links.new(ag.outputs["Color"], _mi[0]); nt.links.new(gr.outputs["Color"], _mi[1])
nt.links.new([x for x in mixc.outputs if x.type == "RGBA"][0], cb.inputs["Base Color"])

DRUSE, db = principled("Druse", (0.72, 0.8, 0.88), 0.3)          # the sparkly quartz crust under the crystals
bump_noise(DRUSE, db, 60.0, 0.6, 2)

# ice-blue crystals: clear glass-like quartz, tinted per crystal (pale at the rim, deeper aquamarine in the depth)
CRY = bpy.data.materials.new("Crystal"); CRY.use_nodes = True
cn = CRY.node_tree.nodes; cl = CRY.node_tree.links
cbsdf = cn["Principled BSDF"]
cbsdf.inputs["Roughness"].default_value = 0.11; cbsdf.inputs["IOR"].default_value = 1.54
cbsdf.inputs["Transmission Weight"].default_value = 1.0
attr = cn.new("ShaderNodeAttribute"); attr.attribute_name = "tint"
cramp = cn.new("ShaderNodeValToRGB")
cramp.color_ramp.elements[0].color = (0.94, 0.98, 1.0, 1); cramp.color_ramp.elements[1].color = (0.5, 0.78, 1.0, 1)
cl.new(attr.outputs["Fac"], cramp.inputs["Fac"]); cl.new(cramp.outputs["Color"], cbsdf.inputs["Base Color"])
cbsdf.inputs["Emission Color"].default_value = (0.35, 0.7, 1.0, 1)
em = cn.new("ShaderNodeMath"); em.operation = "MULTIPLY"; cl.new(attr.outputs["Fac"], em.inputs[0]); em.inputs[1].default_value = 0.0
cl.new(em.outputs[0], cbsdf.inputs["Emission Strength"])                                          # a faint inner glow in the depth

# ---- the rock: a lumpy egg, split by a vertical plane; the back half faces the camera ----
def lumpy(v, amp1=0.09, amp2=0.035, amp3=0.012):
    n1 = noise.fractal(v * 1.6, 0.6, 2.0, 4); n2 = noise.fractal(v * 7.0 + Vector((5, 1, 2)), 0.5, 2.0, 3)
    n3 = noise.fractal(v * 22.0 + Vector((2, 7, 1)), 0.5, 2.0, 2)
    return 1.0 + amp1 * n1 + amp2 * n2 + amp3 * n3


def cav_r(d):
    return RC * (1.0 + 0.05 * noise.fractal(d * 2.2 + Vector((3, 3, 3)), 0.5, 2.0, 3))


# the back half as one clean shell (no booleans): outer rock surface + the hollow's wall + the flat ring of the cut
NT, NP = 288, 72                                   # around x from the cut ring to the back pole
verts, faces, mats = [], [], []


def dir_of(th, ph):
    return Vector((math.cos(ph) * math.cos(th), math.sin(ph), math.cos(ph) * math.sin(th)))


def surf(fn):
    i0 = len(verts)
    for j in range(NP):                            # ph = 0 (the cut plane) .. just short of the pole
        ph = (math.pi / 2) * j / NP
        for i in range(NT):
            d = dir_of(2 * math.pi * i / NT, ph)
            verts.append(Vector((d.x, d.y, d.z * EGG)) * fn(d))
    d = Vector((0, 1, 0)); verts.append(Vector((0, 1, 0)) * fn(d))
    return i0


o0 = surf(lumpy)
i0 = surf(cav_r)
pole_o, pole_i = o0 + NP * NT, i0 + NP * NT
for j in range(NP - 1):
    for i in range(NT):
        a, b = j * NT + i, j * NT + (i + 1) % NT
        c, d_ = (j + 1) * NT + (i + 1) % NT, (j + 1) * NT + i
        faces.append((o0 + a, o0 + d_, o0 + c, o0 + b)); mats.append(0)          # rock, facing out
        faces.append((i0 + a, i0 + b, i0 + c, i0 + d_)); mats.append(2)          # the hollow's wall, facing in
for i in range(NT):
    a, b = (NP - 1) * NT + i, (NP - 1) * NT + (i + 1) % NT
    faces.append((o0 + a, pole_o, o0 + b)); mats.append(0)
    faces.append((i0 + a, i0 + b, pole_i)); mats.append(2)
    faces.append((o0 + i, o0 + (i + 1) % NT, i0 + (i + 1) % NT, i0 + i)); mats.append(1)   # the cut ring, facing the camera
me = bpy.data.meshes.new("Half"); me.from_pydata([tuple(v) for v in verts], [], faces)
me.materials.append(ROCK); me.materials.append(CUT); me.materials.append(DRUSE)
me.polygons.foreach_set("material_index", np.array(mats, dtype=np.int32))
me.validate(); me.update()
for p_ in me.polygons:
    p_.use_smooth = p_.material_index != 1
half = link(bpy.data.objects.new("Half", me))

# ---- crystals: hexagonal prisms with pointed tips, rooted on the hollow's wall, all pointing to the centre ----
def crystal_mesh(n_cry):
    verts, faces, tint = [], [], []
    k = 0
    while k < n_cry:
        d = Vector(rng.normal(0, 1, 3)); d.normalize()
        if d.y < 0.05:
            continue                                        # only the back half's bowl (y > 0)
        base = Vector((d.x, d.y, d.z * EGG)) * cav_r(d) * 0.985
        depth = d.y                                         # 0 at the rim, 1 at the bottom of the bowl
        L = rng.uniform(0.12, 0.22) + 0.2 * depth * rng.uniform(0.5, 1.0)
        r = L * rng.uniform(0.22, 0.3)
        ax = (Vector((0, 0, 0)) - base).normalized()
        ax = (ax + Vector(rng.normal(0, 0.18, 3))).normalized()
        q = ax.to_track_quat("Z", "Y")
        rot0 = rng.uniform(0, math.pi / 3)
        i0 = len(verts)
        ring = [(math.cos(rot0 + j * math.pi / 3), math.sin(rot0 + j * math.pi / 3)) for j in range(6)]
        for (cx, cy) in ring:
            verts.append(base + q @ Vector((cx * r, cy * r, -0.02)))
        for (cx, cy) in ring:
            verts.append(base + q @ Vector((cx * r, cy * r, 0.72 * L)))
        verts.append(base + q @ Vector((0, 0, L)))
        t = min(1.0, 0.25 + 0.75 * depth + rng.uniform(-0.15, 0.15))
        tint += [t] * 13
        for j in range(6):
            a, b2 = j, (j + 1) % 6
            faces.append((i0 + a, i0 + b2, i0 + 6 + b2, i0 + 6 + a))
            faces.append((i0 + 6 + a, i0 + 6 + b2, i0 + 12))
        faces.append(tuple(i0 + j for j in range(5, -1, -1)))
        k += 1
    return verts, faces, tint


cv, cf, ct = crystal_mesh(int(os.environ.get("GE_CRYSTALS", "270")))
cme2 = bpy.data.meshes.new("Crystals"); cme2.from_pydata([tuple(v) for v in cv], [], cf)
at = cme2.attributes.new("tint", "FLOAT", "POINT"); at.data.foreach_set("value", np.array(ct, dtype=np.float32))
cme2.materials.append(CRY)
link(bpy.data.objects.new("Crystals", cme2))

# ---- flying stone chips (a few with crystal crust) and fine dust: the split just happened ----
def chip(name, loc, size, mat):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    sc = rng.uniform(0.5, 1.3, 3) * size; off = Vector(rng.uniform(0, 50, 3))
    for v in bm.verts:
        k_ = 1 + 0.35 * noise.fractal(v.co * 1.8 + off, 0.5, 2.0, 3)
        v.co = Vector((v.co.x * sc[0] * k_, v.co.y * sc[1] * k_, v.co.z * sc[2] * k_))
    me_ = bpy.data.meshes.new(name); bm.to_mesh(me_); bm.free(); me_.materials.append(mat)
    me_.polygons.foreach_set("use_smooth", [True] * len(me_.polygons))
    o = link(bpy.data.objects.new(name, me_)); o.location = loc
    o.rotation_euler = tuple(rng.uniform(0, math.tau, 3))
    return o


for k in range(18):
    side = rng.choice([-1, 1])
    ang = rng.uniform(-1.2, 1.2)
    rad = rng.uniform(1.05, 1.7)
    loc = (side * rad * math.cos(ang) * 0.9, rng.uniform(-0.9, -0.1), rad * math.sin(ang) * EGG)
    chip(f"Chip{k}", loc, rng.uniform(0.025, 0.07), ROCK if rng.uniform() < 0.8 else DRUSE)
DUST, _ = principled("Dust", (0.35, 0.37, 0.4), 0.7)
dp = np.column_stack([rng.normal(0, 1.0, 260), rng.uniform(-2.6, -0.2, 260), rng.normal(0, 1.3, 260)])
dme = bpy.data.meshes.new("Dust"); dme.from_pydata(dp.tolist(), [], [])
dust = link(bpy.data.objects.new("Dust", dme))
g = dust.modifiers.new("D", "NODES"); gt = bpy.data.node_groups.new("D", "GeometryNodeTree")
gt.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gt.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi = gt.nodes.new("NodeGroupInput"); go = gt.nodes.new("NodeGroupOutput"); ip = gt.nodes.new("GeometryNodeInstanceOnPoints")
ico = gt.nodes.new("GeometryNodeMeshIcoSphere"); ico.inputs["Radius"].default_value = 0.0035
rv = gt.nodes.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT"
_fl = [s for s in rv.inputs if s.type == "VALUE" and s.name in ("Min", "Max")]
_fl[0].default_value = 0.5; _fl[1].default_value = 2.2
_rv_out = [s for s in rv.outputs if s.type == "VALUE"][0]
smt = gt.nodes.new("GeometryNodeSetMaterial"); smt.inputs["Material"].default_value = DUST
gt.links.new(gi.outputs[0], ip.inputs["Points"]); gt.links.new(ico.outputs["Mesh"], ip.inputs["Instance"])
gt.links.new(_rv_out, ip.inputs["Scale"])
gt.links.new(ip.outputs["Instances"], smt.inputs["Geometry"]); gt.links.new(smt.outputs["Geometry"], go.inputs[0])
g.node_group = gt

# ---- stage: a dark slate floor below (soft focus), soft out-of-focus specks far behind: detail to every edge ----
SLATE, sb = principled("Slate", (0.025, 0.027, 0.032), 0.32)
bump_noise(SLATE, sb, 6.0, 0.25)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 4, -1.85)); bpy.context.active_object.data.materials.append(SLATE)
SPECK = bpy.data.materials.new("Speck"); SPECK.use_nodes = True
sn = SPECK.node_tree.nodes; sn.clear(); se = sn.new("ShaderNodeEmission"); se.inputs["Color"].default_value = (0.55, 0.78, 1.0, 1)
se.inputs["Strength"].default_value = 0.8; so = sn.new("ShaderNodeOutputMaterial"); SPECK.node_tree.links.new(se.outputs[0], so.inputs["Surface"])
for k in range(28):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=rng.uniform(0.015, 0.035), location=(rng.uniform(-3.5, 4.5), rng.uniform(5, 9), rng.uniform(-1.0, 5.0)))
    bpy.context.active_object.data.materials.append(SPECK)
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bgc = wn["Background"]; bgc.inputs["Color"].default_value = (0.004, 0.006, 0.01, 1)
# an invisible studio: the camera sees a dark stage, but reflections see soft bright boxes -> real sparkle on the
# crystals and a wet sheen on the rock
stu = wn.new("ShaderNodeBackground"); stu.inputs["Strength"].default_value = 1.0
tcw = wn.new("ShaderNodeTexCoord"); sxw = wn.new("ShaderNodeSeparateXYZ"); wl.new(tcw.outputs["Generated"], sxw.inputs[0])
gz = wn.new("ShaderNodeValToRGB"); gz.color_ramp.elements[0].position = 0.45; gz.color_ramp.elements[0].color = (0.01, 0.012, 0.016, 1)
gz.color_ramp.elements[1].position = 0.97; gz.color_ramp.elements[1].color = (0.5, 0.55, 0.62, 1)
wl.new(sxw.outputs["Z"], gz.inputs["Fac"])
wv_ = wn.new("ShaderNodeTexWave"); wv_.inputs["Scale"].default_value = 3.0; wv_.wave_type = "BANDS"; wv_.bands_direction = "X"
wl.new(tcw.outputs["Generated"], wv_.inputs["Vector"])
mulw = wn.new("ShaderNodeMix"); mulw.data_type = "RGBA"; mulw.blend_type = "MULTIPLY"
_wf = [x for x in mulw.inputs if x.name == "Factor" and x.type == "VALUE"][0]; _wf.default_value = 0.6
_wi = [x for x in mulw.inputs if x.type == "RGBA"]
wl.new(gz.outputs["Color"], _wi[0]); wl.new(wv_.outputs["Color"], _wi[1])
wl.new([x for x in mulw.outputs if x.type == "RGBA"][0], stu.inputs["Color"])
lp = wn.new("ShaderNodeLightPath"); msw = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], msw.inputs["Fac"]); wl.new(stu.outputs[0], msw.inputs[1]); wl.new(bgc.outputs[0], msw.inputs[2])
wl.new(msw.outputs[0], wn["World Output"].inputs["Surface"])

# ---- light: a raking key from upper left, a cool rim from behind, the glow inside the hollow ----
def area(name, loc, size, pw, col, target=(0, 0, 0)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = pw; l.color = col
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("Key", (-4.6, -2.6, 2.8), 2.0, 240, (1.0, 0.97, 0.93))
area("Rim", (3.0, 3.0, 2.6), 1.6, 420, (0.75, 0.88, 1.0))
area("Fill", (2.5, -4.5, -1.0), 3.0, 10, (0.7, 0.8, 1.0))
CRY_ONLY = bpy.data.collections.new("CrystalsOnly"); CRY_ONLY.objects.link(bpy.data.objects["Crystals"])
for name, loc, pw, sz in (("Glow", (0.05, -0.55, 0.1), 160, 0.35), ("Glow2", (-0.3, -0.35, 0.45), 60, 0.2), ("Glow3", (0.3, -0.3, -0.5), 50, 0.2)):
    l = bpy.data.lights.new(name, "POINT"); l.energy = pw; l.color = (0.62, 0.86, 1.0); l.shadow_soft_size = sz
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    o.light_linking.receiver_collection = CRY_ONLY        # light linking: these light ONLY the crystals (the cut stays dark)

# ---- camera: 50 mm, eye level with the hollow, shallow depth of field ----
cam = bpy.data.cameras.new("Cam"); cam.lens = 50; cam.dof.use_dof = True; cam.dof.aperture_fstop = 2.8
co = link(bpy.data.objects.new("Cam", cam)); co.location = (1.7, -5.3, 0.75)
co.rotation_euler = (Vector((0, 0.15, 0.0)) - co.location).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (Vector((0, 0.1, 0)) - co.location).length
scene.camera = co

# bloom on the brightest glints only
ctr = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ctr.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ctr.nodes.new("CompositorNodeRLayers"); gl = ctr.nodes.new("CompositorNodeGlare")
gl.inputs["Type"].default_value = "Bloom"; gl.inputs["Threshold"].default_value = 1.6; gl.inputs["Strength"].default_value = 0.25; gl.inputs["Size"].default_value = 0.6
cout = ctr.nodes.new("NodeGroupOutput"); ctr.links.new(rl.outputs["Image"], gl.inputs["Image"]); ctr.links.new(gl.outputs["Image"], cout.inputs[0])
scene.compositing_node_group = ctr; scene.render.use_compositing = True

bpy.ops.render.render(write_still=True)
print("wrote", OUT)
