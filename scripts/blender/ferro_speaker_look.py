# "Ferrofluid vs Music" - LOOK TEST stills (Blender Cycles, OptiX). A pool of ferrofluid sits in a black speaker dish;
# the music's magnetic field pulls it into a hexagonal field of spikes (Rosensweig instability).
# Three states: calm (rest), pulse (a ring of spikes on a beat), crown (last chord: full spike crown).
# Usage: blender -b --factory-startup -P scripts/blender/ferro_speaker_look.py -- <outDir> [samples]
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 128
os.makedirs(OUT, exist_ok=True)

R_POOL = 0.05  # metres
SPACING = 0.0058
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 10
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.image_settings.file_format = "PNG"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.003, 0.018, 1)


def principled(name, color, metal=0.0, rough=0.1, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = 0.02
    return m


ferro = principled("Ferrofluid", (0.006, 0.006, 0.008), metal=0.2, rough=0.05, coat=1.0)
chrome = principled("Chrome", (0.9, 0.9, 0.92), metal=1.0, rough=0.08)
rubber = principled("Surround", (0.003, 0.003, 0.004), rough=0.28)
floor_m = principled("Floor", (0.0015, 0.0015, 0.0025), rough=0.2, coat=0.4)

# --- ferrofluid surface: a fine grid, heights computed in numpy ---
N = 900
bpy.ops.mesh.primitive_grid_add(x_subdivisions=N, y_subdivisions=N, size=2 * R_POOL * 1.02)
fluid = bpy.context.active_object
fluid.data.materials.append(ferro)
bpy.ops.object.shade_smooth()
nv = len(fluid.data.vertices)
co = np.empty(nv * 3, dtype=np.float32)
fluid.data.vertices.foreach_get("co", co)
co = co.reshape(-1, 3)
X, Y = co[:, 0].astype(np.float64), co[:, 1].astype(np.float64)
r = np.hypot(X, Y)

# hex lattice of spike sites
sites = []
rows = int(R_POOL / (SPACING * 0.866)) + 2
for j in range(-rows, rows + 1):
    for i in range(-rows - 1, rows + 2):
        x = (i + 0.5 * (j % 2)) * SPACING
        y = j * SPACING * 0.866
        if math.hypot(x, y) < R_POOL * 0.9:
            sites.append((x, y))
sites = np.array(sites)


def heights(amp_fn, base=0.0025):
    """amp_fn(site_radius) -> spike height (m). Pool: a domed meniscus that falls off at the dish edge."""
    edge = np.clip((R_POOL - r) / 0.006, 0, 1)
    h = base * (1 - (r / R_POOL) ** 2 * 0.35) * np.sqrt(edge)
    # nearest-spike field: spikes are sharp cones with a soft rounded base (real Rosensweig profile)
    from_site = np.full(r.shape, 1e9)
    amp_near = np.zeros(r.shape)
    for sx, sy in sites:
        d = np.hypot(X - sx, Y - sy)
        closer = d < from_site
        from_site = np.where(closer, d, from_site)
        amp_near = np.where(closer, amp_fn(math.hypot(sx, sy)), amp_near)
    w = SPACING * 0.62
    prof = np.clip(1 - from_site / w, 0, 1)
    spike = amp_near * (prof ** 2.2) * (3 - 2 * prof) * 0.5 + amp_near * prof ** 6 * 0.5
    return (h + spike * edge) - 0.0004 * (1 - edge)


STATES = {
    "1_calm": lambda sr: 0.00008,
    "2_pulse": lambda sr: 0.012 * math.exp(-(((sr - 0.024) / 0.007) ** 2)) + 0.0012,
    "3_crown": lambda sr: 0.0012 + 0.026 * math.exp(-((sr / 0.017) ** 2)),
}

# --- speaker dish: rubber surround ring + chrome rim, glossy floor ---
bpy.ops.mesh.primitive_torus_add(major_radius=R_POOL + 0.006, minor_radius=0.0065, major_segments=160, minor_segments=32)
sur = bpy.context.active_object
sur.location.z = 0.001
sur.data.materials.append(rubber)
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_torus_add(major_radius=R_POOL + 0.0145, minor_radius=0.0022, major_segments=200, minor_segments=24)
rim = bpy.context.active_object
rim.location.z = 0.002
rim.data.materials.append(chrome)
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(radius=R_POOL + 0.03, depth=0.03, vertices=160)
body = bpy.context.active_object
body.location.z = -0.0155
body.data.materials.append(rubber)
bpy.ops.mesh.primitive_plane_add(size=2.0)
fl = bpy.context.active_object
fl.location.z = -0.0305
fl.data.materials.append(floor_m)
fl.hide_render = globals().get("NO_FLOOR", False)  # v5: a dark glossy floor reflects the dish (product shot)


def area(name, loc, size, power, color, target=(0, 0, 0.004)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size
    ld.energy = power
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    import mathutils
    lo.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    lo.visible_camera = False
    return lo


area("Cyan", (-0.16, 0.06, 0.09), (0.03, 0.25), 9, (0.1, 0.75, 1.0))
area("Magenta", (0.16, 0.08, 0.08), (0.03, 0.25), 9, (1.0, 0.1, 0.6))
area("Top", (0.0, 0.12, 0.25), (0.25, 0.04), 7, (1.0, 0.97, 0.92))
area("Back", (0.0, 0.35, 0.05), (0.3, 0.02), 3, (0.55, 0.3, 1.0))

# soft violet glow far behind the dish (out of focus), so the top of the frame is not flat black
bpy.ops.mesh.primitive_plane_add(size=1.2, location=(0, 0.7, 0.05), rotation=(math.radians(90), 0, 0))
bk = bpy.context.active_object
bm = bpy.data.materials.new("Backdrop")
bm.use_nodes = True
bn = bm.node_tree.nodes
bn.clear()
bo = bn.new("ShaderNodeOutputMaterial")
be = bn.new("ShaderNodeEmission")
bg = bn.new("ShaderNodeTexGradient")
bg.gradient_type = "SPHERICAL"
bmap = bn.new("ShaderNodeMapping")
bmap.inputs["Scale"].default_value = (2.2, 2.2, 2.2)
btc = bn.new("ShaderNodeTexCoord")
bcr = bn.new("ShaderNodeValToRGB")
bcr.color_ramp.elements[0].color = (0, 0, 0, 1)
bcr.color_ramp.elements[1].color = (0.32, 0.12, 0.7, 1)
bl = bm.node_tree.links
bl.new(btc.outputs["Object"], bmap.inputs["Vector"])
bl.new(bmap.outputs["Vector"], bg.inputs["Vector"])
bl.new(bg.outputs["Fac"], bcr.inputs["Fac"])
bl.new(bcr.outputs["Color"], be.inputs["Color"])
be.inputs["Strength"].default_value = 0.8
bl.new(be.outputs["Emission"], bo.inputs["Surface"])
bk.data.materials.append(bm)

cd = bpy.data.cameras.new("Cam")
cd.lens = 85
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new("Cam", cd)
tilt = math.radians(68)
dist = 0.3
cam.location = (0, -dist * math.sin(tilt), dist * math.cos(tilt) + 0.004)
cam.rotation_euler = (tilt, 0, 0)
cd.dof.focus_distance = dist
scene.collection.objects.link(cam)
scene.camera = cam

for name, fn in (STATES.items() if not globals().get("NO_RENDER") else []):  # ferro_music.py reuses this scene
    z = heights(fn)
    co[:, 2] = z.astype(np.float32)
    fluid.data.vertices.foreach_set("co", co.ravel())
    fluid.data.update()
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", name, flush=True)
