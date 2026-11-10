# Ferrofluid Labyrinth - one ray-traced test still (Blender Cycles, GPU/OptiX). Everything is built in code (no .blend
# files in git). Real macro scale: a 5.4 x 9.6 cm cell, fluid ~0.6 mm tall between two glass plates.
#   - fluid: a finely subdivided sheet displaced by the labyrinth height map; near-black, glossy, clear-coated
#            ferrofluid where the mask says fluid, fully transparent elsewhere
#   - glass: two real glass plates (IOR 1.5) above and below
#   - light: an LED panel behind the cell (amber core -> magenta -> violet), a softbox and a thin strip light above
#            so the curved fluid surface shows real reflections
#   - camera: 90 mm macro lens at f/4, tilted 20 degrees -> real depth of field
# Usage: blender -b --factory-startup -P scripts/blender/labyrinth_still.py -- <mapsDir> <out.png> [samples]
import math
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
MAPS, OUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 384

W_CELL, H_CELL = 0.054, 0.096  # metres
FLUID_H = 0.0006

scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# --- render settings ---
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 16
scene.cycles.transparent_max_bounces = 32
scene.cycles.transmission_bounces = 16
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_depth = "8"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)


def image(name, path):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = "Non-Color"
    return img


height_img = image("height", f"{MAPS}/height.png")
mask_img = image("mask", f"{MAPS}/mask.png")

# --- fluid sheet ---
bpy.ops.mesh.primitive_grid_add(x_subdivisions=1080, y_subdivisions=1920, size=1.0)  # one vertex per output pixel
fluid = bpy.context.active_object
fluid.name = "Ferrofluid"
fluid.scale = (W_CELL, H_CELL, 1.0)
fluid.location = (0, 0, 0.00002)
tex = bpy.data.textures.new("height", type="IMAGE")
tex.image = height_img
tex.extension = "EXTEND"
disp = fluid.modifiers.new("Displace", "DISPLACE")
disp.texture = tex
disp.texture_coords = "UV"
disp.direction = "Z"
disp.mid_level = 0.0
disp.strength = FLUID_H
bpy.ops.object.shade_smooth()

m = bpy.data.materials.new("Ferrofluid")
m.use_nodes = True
nt = m.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
mix = nt.nodes.new("ShaderNodeMixShader")
transp = nt.nodes.new("ShaderNodeBsdfTransparent")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Base Color"].default_value = (0.004, 0.0035, 0.004, 1)
bsdf.inputs["Roughness"].default_value = 0.06
bsdf.inputs["Coat Weight"].default_value = 1.0
bsdf.inputs["Coat Roughness"].default_value = 0.02
mtex = nt.nodes.new("ShaderNodeTexImage")
mtex.image = mask_img
mtex.interpolation = "Cubic"
uv = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(uv.outputs["UV"], mtex.inputs["Vector"])
nt.links.new(mtex.outputs["Color"], mix.inputs["Fac"])
# thin ferrofluid at the edge of each channel is translucent amber-brown (real thin-film look)
htex = nt.nodes.new("ShaderNodeTexImage")
htex.image = height_img
htex.interpolation = "Cubic"
nt.links.new(uv.outputs["UV"], htex.inputs["Vector"])
tint = nt.nodes.new("ShaderNodeValToRGB")
tint.color_ramp.elements[0].position = 0.0
tint.color_ramp.elements[0].color = (1, 1, 1, 1)
tint.color_ramp.elements[1].position = 0.45
tint.color_ramp.elements[1].color = (0.12, 0.05, 0.015, 1)
nt.links.new(htex.outputs["Color"], tint.inputs["Fac"])
nt.links.new(tint.outputs["Color"], transp.inputs["Color"])
nt.links.new(transp.outputs["BSDF"], mix.inputs[1])
nt.links.new(bsdf.outputs["BSDF"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
fluid.data.materials.append(m)

# --- glass plates ---
glass = bpy.data.materials.new("Glass")
glass.use_nodes = True
g = glass.node_tree.nodes
g.clear()
gout = g.new("ShaderNodeOutputMaterial")
gb = g.new("ShaderNodeBsdfGlass")
gb.inputs["IOR"].default_value = 1.5
gb.inputs["Roughness"].default_value = 0.0
glass.node_tree.links.new(gb.outputs["BSDF"], gout.inputs["Surface"])


# the top plate is a real-world piece of glass: fine dust specks catching the side lights, faint smudges
glass_top = bpy.data.materials.new("GlassTop")
glass_top.use_nodes = True
gt = glass_top.node_tree
gt.nodes.clear()
t_out = gt.nodes.new("ShaderNodeOutputMaterial")
t_glass = gt.nodes.new("ShaderNodeBsdfGlass")
t_glass.inputs["IOR"].default_value = 1.5
t_dust = gt.nodes.new("ShaderNodeBsdfDiffuse")
t_dust.inputs["Color"].default_value = (0.85, 0.82, 0.78, 1)
t_mix = gt.nodes.new("ShaderNodeMixShader")
t_co = gt.nodes.new("ShaderNodeTexCoord")
specks = gt.nodes.new("ShaderNodeTexNoise")
specks.inputs["Scale"].default_value = 900.0
specks.inputs["Detail"].default_value = 1.0
sramp = gt.nodes.new("ShaderNodeValToRGB")
sramp.color_ramp.elements[0].position = 0.74
sramp.color_ramp.elements[0].color = (0, 0, 0, 1)
sramp.color_ramp.elements[1].position = 0.78
sramp.color_ramp.elements[1].color = (0.7, 0.7, 0.7, 1)
smudge = gt.nodes.new("ShaderNodeTexNoise")
smudge.inputs["Scale"].default_value = 18.0
smudge.inputs["Detail"].default_value = 4.0
mramp = gt.nodes.new("ShaderNodeMapRange")
mramp.inputs["From Min"].default_value = 0.45
mramp.inputs["From Max"].default_value = 0.8
mramp.inputs["To Min"].default_value = 0.0
mramp.inputs["To Max"].default_value = 0.05
gt.links.new(t_co.outputs["Object"], specks.inputs["Vector"])
gt.links.new(t_co.outputs["Object"], smudge.inputs["Vector"])
gt.links.new(specks.outputs["Fac"], sramp.inputs["Fac"])
gt.links.new(smudge.outputs["Fac"], mramp.inputs["Value"])
gt.links.new(mramp.outputs["Result"], t_glass.inputs["Roughness"])
gt.links.new(sramp.outputs["Color"], t_mix.inputs["Fac"])
gt.links.new(t_glass.outputs["BSDF"], t_mix.inputs[1])
gt.links.new(t_dust.outputs["BSDF"], t_mix.inputs[2])
gt.links.new(t_mix.outputs["Shader"], t_out.inputs["Surface"])


def plate(name, z_bottom, thick, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    p = bpy.context.active_object
    p.name = name
    p.scale = (W_CELL * 1.6, H_CELL * 1.4, thick)
    p.location = (0, 0, z_bottom + thick / 2)
    p.data.materials.append(mat or glass)
    return p


plate("GlassBottom", -0.0015, 0.0015)
plate("GlassTop", FLUID_H + 0.0001, 0.0015, glass_top)

# --- LED panel behind the cell ---
bpy.ops.mesh.primitive_plane_add(size=1.0)
panel = bpy.context.active_object
panel.name = "LEDPanel"
panel.scale = (W_CELL * 2.2, H_CELL * 1.8, 1)
panel.location = (0, 0, -0.012)
pm = bpy.data.materials.new("LED")
pm.use_nodes = True
pn = pm.node_tree.nodes
pn.clear()
pout = pn.new("ShaderNodeOutputMaterial")
em = pn.new("ShaderNodeEmission")
em.inputs["Strength"].default_value = 1.5
tc = pn.new("ShaderNodeTexCoord")
dist = pn.new("ShaderNodeVectorMath")
dist.operation = "DISTANCE"
dist.inputs[1].default_value = (0.5, 0.5, 0.5)
ramp = pn.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (1.0, 0.42, 0.06, 1)
cr.elements[1].position = 0.3
cr.elements[1].color = (0.25, 0.02, 0.5, 1)
mid = cr.elements.new(0.13)
mid.color = (0.95, 0.04, 0.32, 1)
pm.node_tree.links.new(tc.outputs["Generated"], dist.inputs[0])
pm.node_tree.links.new(dist.outputs["Value"], ramp.inputs["Fac"])
pm.node_tree.links.new(ramp.outputs["Color"], em.inputs["Color"])
pm.node_tree.links.new(em.outputs["Emission"], pout.inputs["Surface"])
panel.data.materials.append(pm)

# --- lights above (reflections on the curved fluid) ---
def area(name, loc, rot, size, power, color=(1, 0.97, 0.92)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size
    ld.energy = power
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    lo.rotation_euler = rot
    scene.collection.objects.link(lo)
    return lo


# lights at the sides: the flat glass cannot mirror them into the lens, the curved fluid edges still catch them
area("Softbox", (0.2, 0.02, 0.13), (0, math.radians(57), 0), (0.08, 0.14), 1.6)
area("Strip", (-0.2, 0.04, 0.12), (0, math.radians(-59), 0), (0.006, 0.14), 0.9, (0.9, 0.95, 1.0))
# soft fill from behind the camera: a faint sheen on the black fluid (the flat glass mirrors it away from the lens)
area("Fill", (0.0, -0.22, 0.24), (math.radians(42), 0, 0), (0.3, 0.2), 0.8)

# --- macro camera ---
cd = bpy.data.cameras.new("Macro")
cd.lens = 90
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 4.5
cam = bpy.data.objects.new("Macro", cd)
tilt = math.radians(20)
dcam = 0.27
cam.location = (0, -dcam * math.sin(tilt), dcam * math.cos(tilt))
cam.rotation_euler = (tilt, 0, 0)
cd.dof.focus_distance = dcam
scene.collection.objects.link(cam)
scene.camera = cam

if not globals().get("NO_RENDER"):  # labyrinth_anim.py builds the same scene and renders frames itself
    scene.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("RENDERED", OUT)
