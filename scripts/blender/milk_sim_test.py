# 0027 v3 - feasibility test: a REAL liquid splash (Mantaflow FLIP). A nickel plunger punches into a thin layer of milk;
# bake the sim, then render a few frames with the milk shader to judge the look and the time it takes.
# Usage: blender -b --factory-startup -P milk_sim_test.py -- <cachedir> <outdir> <res> <frames>
import math
import os
import sys
import time

import bpy
from mathutils import Vector

a_ = sys.argv[sys.argv.index("--") + 1:]
CACHE, OUT, RES, NF = os.path.abspath(a_[0]), os.path.abspath(a_[1]), int(a_[2]), int(a_[3])
os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, NF
scene.render.fps = 24

# domain 1.6 x 1.6 x 1.0 (units ~ 10 cm), thin milk layer 0.12, plunger from above
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.25)); dom = bpy.context.active_object; dom.scale = (0.7, 0.7, 0.5)
bpy.ops.object.transform_apply(scale=True)
m = dom.modifiers.new("Fluid", "FLUID"); m.fluid_type = "DOMAIN"
ds = m.domain_settings
ds.domain_type = "LIQUID"; ds.resolution_max = RES; ds.use_mesh = True; ds.cache_directory = CACHE
ds.cache_type = "ALL"; ds.cache_frame_start = 1; ds.cache_frame_end = NF
ds.use_spray_particles = False
ds.mesh_scale = 2; ds.mesh_particle_radius = 1.6; ds.use_speed_vectors = False
ds.time_scale = 0.25                                  # slow motion in the sim itself (high-speed-camera look)
ds.surface_tension = 0.02
ds.use_collision_border_bottom = True
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.0125)); layer = bpy.context.active_object; layer.scale = (0.69, 0.69, 0.025)   # THIN film: the crown needs it
bpy.ops.object.transform_apply(scale=True)
fm = layer.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "FLOW"
fs = fm.flow_settings; fs.flow_type = "LIQUID"; fs.flow_behavior = "GEOMETRY"; fs.use_initial_velocity = False
layer.hide_render = True
# a falling DROP of milk (the classic coronet): a liquid sphere with a fast downward initial velocity
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, 0.12), segments=32, ring_count=16); drop = bpy.context.active_object
dm = drop.modifiers.new("Fluid", "FLUID"); dm.fluid_type = "FLOW"
dfs = dm.flow_settings; dfs.flow_type = "LIQUID"; dfs.flow_behavior = "GEOMETRY"; dfs.use_initial_velocity = True
dfs.velocity_coord = (0.0, 0.0, -2.6)
drop.hide_render = True
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.3, location=(0, 0, 0.9), vertices=32); pl = bpy.context.active_object   # the nozzle

t0 = time.time()
with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom]):
    bpy.ops.fluid.bake_all()
print("BAKE seconds", round(time.time() - t0, 1))

# quick look render
MILK = bpy.data.materials.new("Milk"); MILK.use_nodes = True
b = MILK.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.92, 0.92, 0.9, 1); b.inputs["Roughness"].default_value = 0.18
b.inputs["Subsurface Weight"].default_value = 1.0; b.inputs["Subsurface Scale"].default_value = 0.05
b.inputs["Coat Weight"].default_value = 0.35
dom.data.materials.append(MILK)
NICK = bpy.data.materials.new("Nickel"); NICK.use_nodes = True
nb = NICK.node_tree.nodes["Principled BSDF"]; nb.inputs["Metallic"].default_value = 1.0; nb.inputs["Roughness"].default_value = 0.15
pl.data.materials.append(NICK)
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences; prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = 32; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.005, 1)
for name, loc, size, pw in (("Back", (0.3, 4.0, 1.4), 3.0, 900), ("Key", (-3, -2.5, 3.2), 2.0, 400), ("Rim", (3, 0.5, 0.9), 0.5, 300)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = pw
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector((0, 0, 0.2)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); scene.collection.objects.link(o)
camd = bpy.data.cameras.new("C"); camd.lens = 50; cam = bpy.data.objects.new("C", camd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = Vector((0.0, -0.95, 0.22)); cam.rotation_euler = (Vector((0, 0, 0.06)) - cam.location).to_track_quat("-Z", "Y").to_euler()
for f in (3, 5, 7, 9, 12, 16, 20, 26):
    if f > NF:
        continue
    scene.frame_set(f)
    scene.render.filepath = os.path.join(OUT, "sim_%03d.png" % f)
    bpy.ops.render.render(write_still=True)
print("done")
