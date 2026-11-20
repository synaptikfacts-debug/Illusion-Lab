# 0031 "Kinetic sand cutting" - still for approval (owner, Nov 20 2026, picked option 1: "beautiful visual effects that
# make everyone watch to the end - ASMR effects"). The most satisfying moment: a big cube of pastel layered kinetic sand,
# a steel knife mid-cut, the slice peeling away and crumbling, the fresh cut showing a swirl pattern inside.
# The colours live in 3D (object space), so every cut face shows the real inside of the cube - the slice carries its own.
# New look vs the last reels (dark ink / dark geode): bright soft studio, pastel pink, lilac, sky blue, mint, lemon.
# Usage: blender -b --factory-startup -P sand_cut.py -- <out.png>   env SC_RES (1080x1920), SC_SAMPLES (128)
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

a_ = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a_[0])
rng = np.random.default_rng(31)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("SC_SAMPLES", "128"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("SC_RES", "1080x1920").split("x")]
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"; scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT

PALETTE = [(0.92, 0.12, 0.42), (0.42, 0.14, 0.82), (0.08, 0.42, 0.95), (0.06, 0.74, 0.56), (1.0, 0.8, 0.08)]   # vivid
CUT_X = 0.36           # where the knife is: the slice is x in [CUT_X, 0.5]


def link(o):
    scene.collection.objects.link(o)
    return o


def find(sockets, name, typ=None):
    return [s for s in sockets if s.name == name and (typ is None or s.type == typ)][0]


# ---- kinetic sand: matte, fine-grained, colour = a 3D swirl of pastel bands (consistent through the whole volume) ----
def sand_material(name, per_object_colour=False, grain_coords=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.12
    tc = N.new("ShaderNodeTexCoord")
    CO = tc.outputs["Object"]
    if grain_coords:
        ga = N.new("ShaderNodeAttribute"); ga.attribute_type = "INSTANCER"; ga.attribute_name = "gpos"; CO = ga.outputs["Vector"]
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position = 0.0; els[0].color = (*PALETTE[0], 1); els[1].position = 0.2; els[1].color = (*PALETTE[1], 1)
    for k, c in enumerate(PALETTE[2:]):
        e = els.new(0.4 + 0.2 * k); e.color = (*c, 1)
    if per_object_colour:                                  # crumbs: one palette colour each
        oi = N.new("ShaderNodeObjectInfo"); L.new(oi.outputs["Random"], ramp.inputs["Fac"])
    else:
        # stacked wavy layers: band = fract(1.8 z + A(x) sin(6 y + 3 x) + wobble); the wave grows deeper inside the
        # cube (A(x)), so every new slice shows a different, wilder pattern
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(CO, sep.inputs[0])
        sy6 = N.new("ShaderNodeMath"); sy6.operation = "MULTIPLY_ADD"; L.new(sep.outputs["Y"], sy6.inputs[0]); sy6.inputs[1].default_value = 6.0
        sx3 = N.new("ShaderNodeMath"); sx3.operation = "MULTIPLY"; L.new(sep.outputs["X"], sx3.inputs[0]); sx3.inputs[1].default_value = 3.0
        L.new(sx3.outputs[0], sy6.inputs[2])
        sn_ = N.new("ShaderNodeMath"); sn_.operation = "SINE"; L.new(sy6.outputs[0], sn_.inputs[0])
        amp = N.new("ShaderNodeMath"); amp.operation = "MULTIPLY_ADD"; L.new(sep.outputs["X"], amp.inputs[0]); amp.inputs[1].default_value = -0.28
        amp.inputs[2].default_value = 0.2                                    # 0.06 at the right face .. 0.34 at the far left
        wv = N.new("ShaderNodeMath"); wv.operation = "MULTIPLY"; L.new(sn_.outputs[0], wv.inputs[0]); L.new(amp.outputs[0], wv.inputs[1])
        z2 = N.new("ShaderNodeMath"); z2.operation = "MULTIPLY_ADD"; L.new(sep.outputs["Z"], z2.inputs[0]); z2.inputs[1].default_value = 1.8
        L.new(wv.outputs[0], z2.inputs[2])
        wn = N.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 6.0; wn.inputs["Detail"].default_value = 5
        L.new(CO, wn.inputs["Vector"])
        w2 = N.new("ShaderNodeMath"); w2.operation = "MULTIPLY_ADD"; L.new(wn.outputs["Fac"], w2.inputs[0]); w2.inputs[1].default_value = 0.09
        L.new(z2.outputs[0], w2.inputs[2])
        fr = N.new("ShaderNodeMath"); fr.operation = "FRACT"; L.new(w2.outputs[0], fr.inputs[0])
        L.new(fr.outputs[0], ramp.inputs["Fac"])
    # grain: tiny bright and dark specks in the colour + a fine granular bump
    gn = N.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 900.0; gn.inputs["Detail"].default_value = 2
    L.new(tc.outputs["Object"], gn.inputs["Vector"])
    gm = N.new("ShaderNodeMapRange"); gm.inputs["From Min"].default_value = 0.3; gm.inputs["From Max"].default_value = 0.7
    gm.inputs["To Min"].default_value = 0.72; gm.inputs["To Max"].default_value = 1.15; L.new(gn.outputs["Fac"], gm.inputs["Value"])
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"
    find(mul.inputs, "Factor", "VALUE").default_value = 1.0
    ci = [s for s in mul.inputs if s.type == "RGBA"]
    L.new(ramp.outputs["Color"], ci[0]); L.new(gm.outputs["Result"], ci[1])
    L.new([s for s in mul.outputs if s.type == "RGBA"][0], b.inputs["Base Color"])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 340.0
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.9; bp.inputs["Distance"].default_value = 0.004
    L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


SAND = sand_material("Sand")
GRAIN = sand_material("Grain", grain_coords=True)
CRUMB = sand_material("Crumb", per_object_colour=True)


# ---- the block and the slice: built in cube space, with slightly crumbly, soft edges ----
def box_mesh(name, x0, x1, crumble_face_x=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.007, segments=2, affect="EDGES")
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    for v in bm.verts:                                     # crumbly edges + a hand-pressed, slightly uneven surface
        p = v.co
        n = noise.fractal(p * 9.0, 0.5, 2.0, 3)
        edge = sum(1 for c, lo, hi in ((p.x, x0, x1), (p.y, -0.5, 0.5), (p.z, -0.5, 0.5)) if min(abs(c - lo), abs(c - hi)) < 0.03)
        if edge >= 2:
            v.co = p * (1 - 0.006 * (1 + n))
        elif crumble_face_x is None or abs(p.x - crumble_face_x) > 1e-4:
            v.co = p + p.normalized() * 0.003 * n
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(SAND)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return link(bpy.data.objects.new(name, me))


block = box_mesh("Block", -0.5, CUT_X, crumble_face_x=CUT_X)
slice_ = box_mesh("Slice", CUT_X + 0.004, 0.5)
# the slice peels away: it tips over its bottom outer edge, out from the block
pivot = Vector((0.5, 0, -0.5))
ang = math.radians(25)        # tips OUT, away from the block (its cut face turns up to us)
slice_.matrix_world = Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, "Y") @ Matrix.Translation(-pivot)
slice_.location.x += 0.07


def add_grains(obj, density):
    g = obj.modifiers.new("Grains", "NODES"); t = bpy.data.node_groups.new("Grains_" + obj.name, "GeometryNodeTree")
    t.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    t.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = t.nodes.new("NodeGroupInput"); go = t.nodes.new("NodeGroupOutput")
    dp = t.nodes.new("GeometryNodeDistributePointsOnFaces"); find(dp.inputs, "Density").default_value = density
    find(dp.inputs, "Seed").default_value = len(obj.name)
    ico = t.nodes.new("GeometryNodeMeshIcoSphere"); find(ico.inputs, "Radius").default_value = 0.0032; find(ico.inputs, "Subdivisions").default_value = 1
    ip = t.nodes.new("GeometryNodeInstanceOnPoints")
    rv = t.nodes.new("FunctionNodeRandomValue"); rv.data_type = "FLOAT"
    fl = [x for x in rv.inputs if x.type == "VALUE" and x.name in ("Min", "Max")]; fl[0].default_value = 0.55; fl[1].default_value = 1.35
    rr = t.nodes.new("FunctionNodeRandomValue"); rr.data_type = "FLOAT_VECTOR"
    vv = [x for x in rr.inputs if x.type == "VECTOR" and x.name in ("Min", "Max")]; vv[1].default_value = (6.3, 6.3, 6.3)
    pos = t.nodes.new("GeometryNodeInputPosition")
    st = t.nodes.new("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT_VECTOR"; st.domain = "INSTANCE"
    find(st.inputs, "Name").default_value = "gpos"
    sm = t.nodes.new("GeometryNodeSetMaterial"); find(sm.inputs, "Material").default_value = GRAIN
    jn = t.nodes.new("GeometryNodeJoinGeometry")
    L = t.links.new
    L(gi.outputs[0], dp.inputs["Mesh"]); L(dp.outputs["Points"], ip.inputs["Points"]); L(ico.outputs["Mesh"], ip.inputs["Instance"])
    L([x for x in rv.outputs if x.type == "VALUE"][0], ip.inputs["Scale"]); L([x for x in rr.outputs if x.type == "VECTOR"][0], ip.inputs["Rotation"])
    L(ip.outputs["Instances"], st.inputs["Geometry"]); L(pos.outputs[0], find(st.inputs, "Value", "VECTOR"))
    L(st.outputs[0], sm.inputs["Geometry"]); L(gi.outputs[0], jn.inputs[0]); L(sm.outputs[0], jn.inputs[0]); L(jn.outputs[0], go.inputs[0])
    g.node_group = t


GD = float(os.environ.get("SC_GRAINS", "140000"))
add_grains(block, GD)
if not os.environ.get("SC_DBG_NOSLICE"):
    add_grains(slice_, GD)
else:
    slice_.hide_render = True

# ---- the knife: a polished steel blade standing in the cut, handle above the frame ----
STEEL = bpy.data.materials.new("Steel"); STEEL.use_nodes = True
sb = STEEL.node_tree.nodes["Principled BSDF"]; sb.inputs["Base Color"].default_value = (0.86, 0.87, 0.9, 1)
sb.inputs["Metallic"].default_value = 1.0; sb.inputs["Roughness"].default_value = 0.05
bm = bmesh.new()
W_, H_, T_ = 0.42, 1.4, 0.012                               # blade width (y), height (z), thickness (x)
verts = [(-T_ / 2, -W_ / 2, 0.0), (T_ / 2, -W_ / 2, 0.0), (T_ / 2, W_ / 2, 0.0), (-T_ / 2, W_ / 2, 0.0),
         (-T_ / 2, -W_ / 2, H_), (T_ / 2, -W_ / 2, H_), (T_ / 2, W_ / 2, H_), (-T_ / 2, W_ / 2, H_)]
vv = [bm.verts.new(v) for v in verts]
for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)):
    bm.faces.new([vv[i] for i in f])
kme = bpy.data.meshes.new("Knife"); bm.to_mesh(kme); bm.free(); kme.materials.append(STEEL)
knife = link(bpy.data.objects.new("Knife", kme))
kbv = knife.modifiers.new("B", "BEVEL"); kbv.width = 0.004; kbv.segments = 3
knife.location = (CUT_X + 0.02, 0.04, 0.56); knife.rotation_euler = (0, math.radians(-8), math.radians(4))
HANDLE = bpy.data.materials.new("Handle"); HANDLE.use_nodes = True
hb = HANDLE.node_tree.nodes["Principled BSDF"]; hb.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1); hb.inputs["Roughness"].default_value = 0.35
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, H_ + 0.22)); hd = bpy.context.active_object
hd.scale = (0.05, 0.13, 0.44); hd.parent = knife; hd.data.materials.append(HANDLE)
bv = hd.modifiers.new("B", "BEVEL"); bv.width = 0.3; bv.segments = 4

# ---- crumbs: falling from the slice's broken bottom edge, and scattered on the tray ----
def crumb(loc, size):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = Vector(rng.uniform(0, 40, 3)); sc = rng.uniform(0.6, 1.3, 3) * size
    for v in bm.verts:
        k = 1 + 0.4 * noise.fractal(v.co * 1.5 + off, 0.5, 2.0, 2)
        v.co = Vector((v.co.x * sc[0] * k, v.co.y * sc[1] * k, v.co.z * sc[2] * k))
    me = bpy.data.meshes.new("C"); bm.to_mesh(me); bm.free(); me.materials.append(CRUMB)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = link(bpy.data.objects.new("C", me)); o.location = loc; o.rotation_euler = tuple(rng.uniform(0, 6.28, 3))


for k in range(30):                                       # breaking off the slice's top edge, mid-air
    crumb((rng.uniform(0.62, 0.95), rng.uniform(-0.45, 0.45), rng.uniform(-0.35, 0.2)), rng.uniform(0.008, 0.024))
for k in range(46):                                       # in the air under the slice
    crumb((rng.uniform(0.6, 1.2), rng.uniform(-0.45, 0.45), rng.uniform(-0.48, -0.15)), rng.uniform(0.008, 0.028))
for k in range(220):                                      # already on the tray, thickest near the cube
    r = abs(rng.normal(0, 0.55)) + 0.55; a = rng.uniform(0, 2 * math.pi)
    crumb((r * math.cos(a) + 0.1, r * math.sin(a), -0.5 + 0.004), rng.uniform(0.006, 0.022))

# ---- stage: a soft lilac-grey tray, a pastel backdrop, out-of-focus sand cubes behind (detail to every edge) ----
TRAY = bpy.data.materials.new("Tray"); TRAY.use_nodes = True
tb = TRAY.node_tree.nodes["Principled BSDF"]; tb.inputs["Base Color"].default_value = (0.42, 0.4, 0.48, 1); tb.inputs["Roughness"].default_value = 0.6
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.5)); bpy.context.active_object.data.materials.append(TRAY)
BACK = bpy.data.materials.new("Back"); BACK.use_nodes = True
bkn = BACK.node_tree.nodes; bkb = bkn["Principled BSDF"]; bkb.inputs["Roughness"].default_value = 0.9
gtc = bkn.new("ShaderNodeTexCoord"); gsep = bkn.new("ShaderNodeSeparateXYZ"); BACK.node_tree.links.new(gtc.outputs["Generated"], gsep.inputs[0])
gr = bkn.new("ShaderNodeValToRGB"); gr.color_ramp.elements[0].color = (0.36, 0.3, 0.46, 1); gr.color_ramp.elements[1].color = (0.18, 0.24, 0.36, 1)
BACK.node_tree.links.new(gsep.outputs["Z"], gr.inputs["Fac"]); BACK.node_tree.links.new(gr.outputs["Color"], bkb.inputs["Base Color"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 6, 3), rotation=(math.radians(90), 0, 0))
bk = bpy.context.active_object; bk.scale = (18, 10, 1); bk.data.materials.append(BACK)
for k, (x, y, s) in enumerate(((-1.9, 3.2, 0.8), (1.7, 4.2, 1.0), (-0.4, 5.0, 0.9), (2.6, 2.6, 0.6))):
    bpy.ops.mesh.primitive_cube_add(size=s, location=(x, y, -0.5 + s / 2)); o = bpy.context.active_object
    o.rotation_euler.z = rng.uniform(-0.6, 0.6); o.data.materials.append(SAND)
    bvm = o.modifiers.new("B", "BEVEL"); bvm.width = 0.03; bvm.segments = 3
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bgw = wn["Background"]; bgw.inputs["Color"].default_value = (0.75, 0.75, 0.8, 1); bgw.inputs["Strength"].default_value = 0.25
stu = wn.new("ShaderNodeBackground"); tcw = wn.new("ShaderNodeTexCoord"); sxw = wn.new("ShaderNodeSeparateXYZ")
wl.new(tcw.outputs["Generated"], sxw.inputs[0])
gz = wn.new("ShaderNodeValToRGB"); gz.color_ramp.elements[0].position = 0.2; gz.color_ramp.elements[0].color = (0.04, 0.04, 0.05, 1)
gz.color_ramp.elements[1].position = 0.45; gz.color_ramp.elements[1].color = (2.4, 2.4, 2.5, 1)
wl.new(sxw.outputs["Z"], gz.inputs["Fac"])
wv_ = wn.new("ShaderNodeTexWave"); wv_.wave_type = "BANDS"; wv_.bands_direction = "X"; wv_.inputs["Scale"].default_value = 2.2
wl.new(tcw.outputs["Generated"], wv_.inputs["Vector"])
mw = wn.new("ShaderNodeMix"); mw.data_type = "RGBA"; mw.blend_type = "MULTIPLY"; find(mw.inputs, "Factor", "VALUE").default_value = 0.85
mwi = [x for x in mw.inputs if x.type == "RGBA"]; wl.new(gz.outputs["Color"], mwi[0]); wl.new(wv_.outputs["Color"], mwi[1])
wl.new([x for x in mw.outputs if x.type == "RGBA"][0], stu.inputs["Color"])
lpw = wn.new("ShaderNodeLightPath"); msw = wn.new("ShaderNodeMixShader")
mxg = wn.new("ShaderNodeMath"); mxg.operation = "SUBTRACT"; mxg.inputs[0].default_value = 1.0; wl.new(lpw.outputs["Is Glossy Ray"], mxg.inputs[1])
wl.new(mxg.outputs[0], msw.inputs["Fac"]); wl.new(stu.outputs[0], msw.inputs[1]); wl.new(bgw.outputs[0], msw.inputs[2])
wl.new(msw.outputs[0], wn["World Output"].inputs["Surface"])

# ---- light: a big soft key from upper left (the grain shows), a fill, a rim that outlines the crumbs ----
def area(name, loc, size, pw, col, target=(0, 0, -0.1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = pw; l.color = col
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("Key", (-1.2, -2.6, 3.4), 2.4, 360, (1.0, 0.97, 0.94))
area("Fill", (3.0, -2.6, 1.2), 3.0, 120, (0.92, 0.95, 1.0))
area("Rim", (1.2, 3.0, 2.4), 1.6, 260, (1.0, 0.96, 0.98))

# ---- camera: 3/4, a little above, 70 mm, shallow depth of field on the cut ----
cam = bpy.data.cameras.new("Cam"); cam.lens = 62; cam.dof.use_dof = True; cam.dof.aperture_fstop = 4.5
co = link(bpy.data.objects.new("Cam", cam)); co.location = (1.75, -3.7, 1.45)
tgt = Vector((0.45, 0.0, -0.02))
co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (Vector((CUT_X, 0, 0)) - co.location).length
scene.camera = co

bpy.ops.render.render(write_still=True)
print("wrote", OUT)
