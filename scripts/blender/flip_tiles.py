# 0031 "A Ball Hit the Wall and 10,000 Tiles Answered" - still for approval (owner, Nov 20 2026, picked A after we studied
# 0011 "4096 pins draw four pictures"). Formula kept from 0011 (thousands of identical elements, each with its own
# timing -> emergent patterns, a reveal every few seconds, sound from the motion) + the 0030 impact hook. Ours: a wall of
# 100 x 100 flip tiles (mirror gold front, matte black back) in a dark studio; a chrome ball has just struck it and a ring
# wave of flipping tiles races outward from the hit - gold inside, tiles mid-flip on the wave front, black outside.
# New look vs the last reels (black ink + violet, dark geode, pastel sand): gold and black, warm key, cool rim.
# Usage: blender -b --factory-startup -P flip_tiles.py -- <out.png>   env FT_RES (1080x1920), FT_SAMPLES (128)
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
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("FT_SAMPLES", "128"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 8; scene.cycles.blur_glossy = 0.5
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("FT_RES", "1080x1920").split("x")]
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Punchy"; scene.view_settings.exposure = -0.15
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = OUT

N = 100                    # 100 x 100 = 10,000 tiles
PITCH = 0.11               # tile spacing (wall ~11 units)
TS = 0.096                 # tile size
TT = 0.01                  # tile thickness
HIT = np.array([0.6, 1.6]) # impact point on the wall (x, z)
R_FRONT, W_FRONT = 2.6, 1.15   # the wave front radius and width (tiles flipping)


def find(sockets, name, typ=None):
    return [s for s in sockets if s.name == name and (typ is None or s.type == typ)][0]


def link(o):
    scene.collection.objects.link(o)
    return o


# ---- materials ----
def metal(name, col, rough, aniso=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = rough
    if aniso:
        b.inputs["Anisotropic"].default_value = aniso
    return m


GOLD = metal("Gold", (1.0, 0.79, 0.4), 0.28, 0.5)
BLACK = bpy.data.materials.new("Black"); BLACK.use_nodes = True
bb = BLACK.node_tree.nodes["Principled BSDF"]; bb.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1); bb.inputs["Roughness"].default_value = 0.42
EDGE = metal("Edge", (0.25, 0.22, 0.18), 0.35)
CHROME = metal("Chrome", (0.95, 0.95, 0.97), 0.03)
BACKING = bpy.data.materials.new("Backing"); BACKING.use_nodes = True
kb = BACKING.node_tree.nodes["Principled BSDF"]; kb.inputs["Base Color"].default_value = (0.005, 0.005, 0.006, 1); kb.inputs["Roughness"].default_value = 0.8

# ---- the tiles: one mesh, each tile rotated about its own horizontal axis by its flip angle ----
xs = (np.arange(N) - (N - 1) / 2) * PITCH + 0.6
zs = (np.arange(N) - (N - 1) / 2) * PITCH + 1.6
gx, gz = np.meshgrid(xs, zs)
cx, cz = gx.ravel(), gz.ravel()
r = np.hypot(cx - HIT[0], cz - HIT[1])
# a slightly uneven front (each tile has its own timing), and a faint second ripple close to the hit
jit = rng.uniform(-0.08, 0.08, r.shape)
u = np.clip((R_FRONT - (r + jit)) / W_FRONT, 0, 1)          # 0 = not reached yet (black), 1 = done (gold)
u = u * u * (3 - 2 * u)
ang = math.pi * (1 - u)                                     # pi = black faces the camera, 0 = gold faces the camera
lift = 0.06 * np.sin(math.pi * u)                           # tiles pop off the wall while they turn
h = TS / 2; t = TT / 2
# local tile corners (x across, z up, y thickness; the GOLD face is at -y = towards the camera)
loc = np.array([[-h, -t, -h], [h, -t, -h], [h, -t, h], [-h, -t, h],      # front (gold)
                [-h, t, -h], [h, t, -h], [h, t, h], [-h, t, h]])         # back (black)
ca, sa = np.cos(ang), np.sin(ang)
verts, faces, mats = [], [], []
for i in range(len(cx)):
    c, s = ca[i], sa[i]
    # rotate about the tile's x axis: (y, z) -> (y c - z s, y s + z c)
    ly = loc[:, 1] * c - loc[:, 2] * s
    lz = loc[:, 1] * s + loc[:, 2] * c
    P = np.column_stack([loc[:, 0] + cx[i], ly - lift[i] - 0.02, lz + cz[i]])
    b0 = len(verts); verts.extend(P.tolist())
    for f, m in (((0, 1, 2, 3), 0), ((7, 6, 5, 4), 1), ((0, 4, 5, 1), 2), ((1, 5, 6, 2), 2), ((2, 6, 7, 3), 2), ((3, 7, 4, 0), 2)):
        faces.append(tuple(b0 + k for k in f)); mats.append(m)
me = bpy.data.meshes.new("Tiles"); me.from_pydata(verts, [], faces)
for m in (GOLD, BLACK, EDGE):
    me.materials.append(m)
me.polygons.foreach_set("material_index", np.array(mats, dtype=np.int32))
link(bpy.data.objects.new("Tiles", me))

# the backing panel behind the tiles (shows in the gaps)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0.6, 0.03, 1.6), rotation=(math.radians(90), 0, 0))
bk = bpy.context.active_object; bk.scale = (N * PITCH + 0.4, N * PITCH + 0.4, 1); bk.data.materials.append(BACKING)

# ---- the chrome ball, just bounced back off the hit ----
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.34, location=(HIT[0] - 0.15, -0.75, HIT[1] - 0.12), segments=96, ring_count=48)
ball = bpy.context.active_object; ball.data.materials.append(CHROME)
for p in ball.data.polygons:
    p.use_smooth = True

# ---- world: a dark stage for the camera; reflections see warm/cool softboxes (the gold and chrome glint) ----
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
bgw = wn["Background"]; bgw.inputs["Color"].default_value = (0.002, 0.002, 0.003, 1)
stu = wn.new("ShaderNodeBackground"); tcw = wn.new("ShaderNodeTexCoord"); sxw = wn.new("ShaderNodeSeparateXYZ")
wl.new(tcw.outputs["Generated"], sxw.inputs[0])
gz_ = wn.new("ShaderNodeValToRGB"); gz_.color_ramp.elements[0].position = 0.3; gz_.color_ramp.elements[0].color = (0.01, 0.01, 0.012, 1)
gz_.color_ramp.elements[1].position = 0.62; gz_.color_ramp.elements[1].color = (1.6, 1.5, 1.4, 1)
wl.new(sxw.outputs["Z"], gz_.inputs["Fac"])
wv_ = wn.new("ShaderNodeTexWave"); wv_.wave_type = "BANDS"; wv_.bands_direction = "X"; wv_.inputs["Scale"].default_value = 1.6
wl.new(tcw.outputs["Generated"], wv_.inputs["Vector"])
mw = wn.new("ShaderNodeMix"); mw.data_type = "RGBA"; mw.blend_type = "MULTIPLY"; find(mw.inputs, "Factor", "VALUE").default_value = 0.8
mwi = [x for x in mw.inputs if x.type == "RGBA"]; wl.new(gz_.outputs["Color"], mwi[0]); wl.new(wv_.outputs["Color"], mwi[1])
wl.new([x for x in mw.outputs if x.type == "RGBA"][0], stu.inputs["Color"])
lpw = wn.new("ShaderNodeLightPath"); msw = wn.new("ShaderNodeMixShader")
wl.new(lpw.outputs["Is Camera Ray"], msw.inputs["Fac"]); wl.new(stu.outputs[0], msw.inputs[1]); wl.new(bgw.outputs[0], msw.inputs[2])
wl.new(msw.outputs[0], wn["World Output"].inputs["Surface"])


# ---- light: a warm raking key (the flipping tiles catch it one by one), a cool rim from the other side ----
def area(name, loc, size, pw, col, target=(0.6, 0, 1.6)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = pw; l.color = col
    o = link(bpy.data.objects.new(name, l)); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


area("Key", (-5.0, -3.5, 5.0), 3.0, 900, (1.0, 0.9, 0.78))
area("Rim", (6.0, -2.0, -1.0), 2.5, 500, (0.7, 0.82, 1.0))
area("Top", (1.0, -4.0, 7.0), 4.0, 250, (1.0, 0.97, 0.94))
# a big softbox behind the camera: the gold faces mirror it (bright gold), tiles mid-turn sweep from bright to dark
area("Softbox", (5.0, -12.5, 2.4), 13.0, 5200, (1.0, 0.96, 0.9))

# ---- camera: 3/4 across the wall, the ring of the wave and the ball in focus ----
cam = bpy.data.cameras.new("Cam"); cam.lens = 32; cam.dof.use_dof = True; cam.dof.aperture_fstop = 2.8
co = link(bpy.data.objects.new("Cam", cam)); co.location = (3.6, -5.2, 2.6)
tgt = Vector((0.2, 0.0, 1.2))
co.rotation_euler = (tgt - co.location).to_track_quat("-Z", "Y").to_euler()
cam.dof.focus_distance = (Vector((HIT[0], -0.4, HIT[1])) - co.location).length
scene.camera = co

# soft bloom on the brightest glints
ctr = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
ctr.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
rl = ctr.nodes.new("CompositorNodeRLayers"); gl = ctr.nodes.new("CompositorNodeGlare")
gl.inputs["Type"].default_value = "Bloom"; gl.inputs["Threshold"].default_value = 1.4; gl.inputs["Strength"].default_value = 0.3; gl.inputs["Size"].default_value = 0.6
cout = ctr.nodes.new("NodeGroupOutput"); ctr.links.new(rl.outputs["Image"], gl.inputs["Image"]); ctr.links.new(gl.outputs["Image"], cout.inputs[0])
scene.compositing_node_group = ctr; scene.render.use_compositing = True

bpy.ops.render.render(write_still=True)
print("wrote", OUT)
