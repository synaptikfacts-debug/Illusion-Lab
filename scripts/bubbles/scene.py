"""0015 Bubble cluster - Blender Cycles (GPU/OptiX).
blender -b -P scene.py -- OUT.png W H SAMPLES T STYLE      STYLE = violet | studio
Hundreds of glossy spheres packed into a ball with small thorns.
violet: violet lacquer in black space with a purple/magenta ring glow behind.
studio: glossy black on a seamless white studio backdrop with soft shadows."""
import math, sys, random
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SAMPLES, T, STYLE = argv[0], int(argv[1]), int(argv[2]), int(argv[3]), float(argv[4]), argv[5]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'OPTIX'
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type in ('OPTIX', 'CUDA')
sc.cycles.device = 'GPU'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 10; sc.cycles.glossy_bounces = 8
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Punchy' if STYLE == 'violet' else 'AgX - Medium High Contrast'
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1) if STYLE == 'violet' else (0.85, 0.85, 0.87, 1)
bg.inputs[1].default_value = 1.0 if STYLE == 'violet' else 0.0


def mat_emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s
    o = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(e.outputs[0], o.inputs[0])
    return m


vm = bpy.data.materials.new('body'); vm.use_nodes = True
b = vm.node_tree.nodes['Principled BSDF']
if STYLE == 'violet':
    b.inputs['Base Color'].default_value = (0.20, 0.015, 0.42, 1)
    b.inputs['Metallic'].default_value = 0.25
    b.inputs['Roughness'].default_value = 0.18
    b.inputs['Subsurface Weight'].default_value = 0.08
    b.inputs['Subsurface Radius'].default_value = (0.6, 0.1, 1.0)
else:
    b.inputs['Base Color'].default_value = (0.008, 0.008, 0.009, 1)
    b.inputs['Metallic'].default_value = 0.0
    b.inputs['Roughness'].default_value = 0.3
b.inputs['Coat Weight'].default_value = 1.0
b.inputs['Coat Roughness'].default_value = 0.03
b.inputs['Coat IOR'].default_value = 1.6

# ---- bubble cluster ----
random.seed(4)
N = 170
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.0)
proto = bpy.context.object; proto.data.materials.append(vm)
for p in proto.data.polygons:
    p.use_smooth = True
mesh = proto.data
bpy.data.objects.remove(proto)
golden = math.pi * (3 - math.sqrt(5))
for i in range(N):
    z = 1 - 2 * (i + 0.5) / N
    r = math.sqrt(1 - z * z); a = i * golden
    d = Vector((r * math.cos(a), r * math.sin(a), z))
    d += Vector((random.uniform(-.04, .04), random.uniform(-.04, .04), random.uniform(-.04, .04)))
    d.normalize()
    rad = random.uniform(0.15, 0.31)
    o = bpy.data.objects.new(f'b{i}', mesh); sc.collection.objects.link(o)
    o.location = d * (1.0 - rad * 0.45); o.scale = (rad, rad, rad)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.93)
core = bpy.context.object; core.data.materials.append(vm); bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.035, radius2=0.0, depth=0.32)
cone = bpy.context.object; cone.data.materials.append(vm); bpy.ops.object.shade_smooth()
cmesh = cone.data; bpy.data.objects.remove(cone)
for i in range(34):
    d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
    o = bpy.data.objects.new(f't{i}', cmesh); sc.collection.objects.link(o)
    o.location = d * 1.08
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    s = random.uniform(0.7, 1.3); o.scale = (s, s, s)


def area(name, loc, size, energy, col):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size[0]; l.size_y = size[1]
    l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


if STYLE == 'violet':
    bpy.ops.mesh.primitive_torus_add(major_radius=6.0, minor_radius=0.22, location=(0, 14, 0.4), rotation=(math.radians(78), 0, math.radians(-8)))
    bpy.context.object.data.materials.append(mat_emit('ring', (0.55, 0.05, 1.0), 2.2))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=2.6, location=(0, 14, 0.4))
    hm = bpy.data.materials.new('hole'); hm.use_nodes = True
    hm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1)
    bpy.context.object.data.materials.append(hm)
    for i in range(120):
        loc = (random.uniform(-14, 14), random.uniform(18, 30), random.uniform(-22, 22))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.02, 0.06), location=loc)
        bpy.context.object.data.materials.append(mat_emit(f's{i}', random.choice([(1, .8, 1), (.8, .7, 1), (1, .5, .9)]), random.uniform(4, 14)))
    area('key', (-3.0, -4.0, 3.5), (2.0, 2.0), 700, (1.0, 0.95, 1.0))
    area('rimR', (4.0, 3.0, 0.8), (0.6, 4.0), 2200, (1.0, 0.25, 0.85))
    area('rimL', (-4.0, 3.0, -0.5), (0.6, 4.0), 1800, (0.55, 0.2, 1.0))
    area('fill', (0.0, -3.0, -3.0), (3.0, 1.0), 150, (0.6, 0.3, 1.0))
else:
    # seamless white cyclorama: floor curving up into a back wall
    bpy.ops.mesh.primitive_plane_add(size=1)
    cyc = bpy.context.object
    import bmesh
    bm = bmesh.new()
    prof = []
    for k in range(40):
        a = k / 39 * math.pi / 2
        prof.append((0, 6 + 3 * math.sin(a) - 3, -1.6 + 3 - 3 * math.cos(a)))
    prof = [(0, -3, -1.6)] + prof + [(0, 6, 9)]
    cols = []
    for x in (-6, 6):
        cols.append([bm.verts.new((x, y, z)) for _, y, z in prof])
    for k in range(len(prof) - 1):
        bm.faces.new((cols[0][k], cols[1][k], cols[1][k + 1], cols[0][k + 1]))
    bm.to_mesh(cyc.data); bm.free()
    for p in cyc.data.polygons:
        p.use_smooth = True
    wm = bpy.data.materials.new('white'); wm.use_nodes = True
    wb = wm.node_tree.nodes['Principled BSDF']
    wb.inputs['Base Color'].default_value = (0.82, 0.82, 0.83, 1); wb.inputs['Roughness'].default_value = 0.6
    cyc.data.materials.append(wm)
    cyc.visible_glossy = False   # studio trick: backdrop not seen in reflections -> deep black lacquer
    area('top', (0.0, -0.5, 5.0), (4.0, 4.0), 1400, (1, 1, 1))
    area('key', (-3.5, -3.5, 2.5), (2.5, 2.5), 700, (1, 0.98, 0.96))
    area('stripR', (3.5, -1.0, 0.5), (0.5, 4.0), 900, (1, 1, 1))
    area('stripL', (-3.5, 1.5, 0.3), (0.5, 4.0), 500, (1, 1, 1))

cd = bpy.data.cameras.new('cam'); cd.lens = 50; cd.sensor_width = 36; cd.sensor_fit = 'HORIZONTAL'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 0.9 if STYLE == 'violet' else 4.0
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
a = math.radians(-90 + 8 * T)
cam.location = (4.1 * math.cos(a), 4.1 * math.sin(a), 0.5)
cam.rotation_euler = (-Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
cd.dof.focus_distance = 4.1 - 1.0
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print('saved', OUT)
