# 0027 v3 hybrid, part 1: bake ONE real milk-drop impact (Mantaflow FLIP, slow motion) and dump the liquid surface of every
# frame to <out>/m_####.npz (verts float32, faces int32) so the render script can load it instantly.
# Usage: blender -b --factory-startup -P milk_sim_bake.py -- <cachedir> <outdir> <res> <frames> <timescale>
import os
import sys
import time

import bpy
import numpy as np

a_ = sys.argv[sys.argv.index("--") + 1:]
CACHE, OUT, RES, NF, TS = os.path.abspath(a_[0]), os.path.abspath(a_[1]), int(a_[2]), int(a_[3]), float(a_[4])
os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, NF
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.25)); dom = bpy.context.active_object; dom.scale = (0.8, 0.8, 0.5)
bpy.ops.object.transform_apply(scale=True)
m = dom.modifiers.new("Fluid", "FLUID"); m.fluid_type = "DOMAIN"
ds = m.domain_settings
ds.domain_type = "LIQUID"; ds.resolution_max = RES; ds.use_mesh = True; ds.cache_directory = CACHE
ds.cache_type = "ALL"; ds.cache_frame_start = 1; ds.cache_frame_end = NF
ds.mesh_scale = 2; ds.mesh_particle_radius = 1.5
ds.time_scale = TS; ds.surface_tension = 0.02
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.0125)); layer = bpy.context.active_object; layer.scale = (0.79, 0.79, 0.025)
bpy.ops.object.transform_apply(scale=True)
fm = layer.modifiers.new("Fluid", "FLUID"); fm.fluid_type = "FLOW"
fs = fm.flow_settings; fs.flow_type = "LIQUID"; fs.flow_behavior = "GEOMETRY"
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(0, 0, 0.1), segments=32, ring_count=16); drop = bpy.context.active_object
dm = drop.modifiers.new("Fluid", "FLUID"); dm.fluid_type = "FLOW"
dfs = dm.flow_settings; dfs.flow_type = "LIQUID"; dfs.flow_behavior = "GEOMETRY"; dfs.use_initial_velocity = True
dfs.velocity_coord = (0.0, 0.0, -2.6)
t0 = time.time()
if not os.environ.get("DUMP_ONLY"):
    with bpy.context.temp_override(object=dom, active_object=dom, selected_objects=[dom]):
        bpy.ops.fluid.bake_all()
print("BAKE seconds", round(time.time() - t0, 1))
dg = bpy.context.evaluated_depsgraph_get()
for f in range(1, NF + 1):
    scene.frame_set(f)
    ev = dom.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    n = len(me.vertices)
    V = np.zeros(n * 3, np.float32); me.vertices.foreach_get("co", V)
    me.calc_loop_triangles()
    T = np.zeros(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", T)
    M = np.array(dom.matrix_world)
    V = V.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
    np.savez_compressed(os.path.join(OUT, "m_%04d.npz" % f), v=V.astype(np.float32), f=T.reshape(-1, 3))
    ev.to_mesh_clear()
print("dumped", NF)
