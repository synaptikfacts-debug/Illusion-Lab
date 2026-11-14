"""0015 Through the Glass - Blender Cycles (GPU/OptiX).
blender -b -P glass.py -- OUTDIR W H SAMPLES FPS T0 T1
A purple gel sphere falls onto a thick glass pane, squashes, and sinks THROUGH the solid glass;
the pane ripples like water while staying sharp glass. Black bg, purple main, cyan accent."""
import math, os, sys
import bpy
import numpy as np
from mathutils import Vector

a = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SAMPLES, FPS, T0, T1 = a[0], int(a[1]), int(a[2]), int(a[3]), int(a[4]), float(a[5]), float(a[6])
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
pr = bpy.context.preferences.addons['cycles'].preferences
pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices:
    d.use = d.type in ('OPTIX', 'CUDA')
sc.cycles.device = 'GPU'; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 16; sc.cycles.transmission_bounces = 16; sc.cycles.transparent_max_bounces = 16
sc.cycles.caustics_refractive = True
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'
wd = bpy.data.worlds.new('w'); sc.world = wd; wd.use_nodes = True
wd.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)

PT = 0.125   # pane half thickness (pane centred at z=0)
R = 0.5      # gel radius


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


gel = bpy.data.materials.new('gel'); gel.use_nodes = True
nt = gel.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.55, 0.12, 1.0, 1)
b.inputs['Roughness'].default_value = 0.04
b.inputs['IOR'].default_value = 1.38
b.inputs['Transmission Weight'].default_value = 1.0
pv_ = nt.nodes.new('ShaderNodeVolumePrincipled')
pv_.inputs['Color'].default_value = (0.75, 0.3, 1.0, 1); pv_.inputs['Density'].default_value = 0.9
pv_.inputs['Absorption Color'].default_value = (0.7, 0.2, 1.0, 1)
pv_.inputs['Emission Color'].default_value = (0.55, 0.12, 1.0, 1); pv_.inputs['Emission Strength'].default_value = 0.55
nt.links.new(pv_.outputs[0], nt.nodes['Material Output'].inputs['Volume'])
glass = bpy.data.materials.new('glass'); glass.use_nodes = True
g = glass.node_tree.nodes['Principled BSDF']
g.inputs['Base Color'].default_value = (0.92, 0.97, 1.0, 1)
g.inputs['Roughness'].default_value = 0.0
g.inputs['IOR'].default_value = 1.5
g.inputs['Transmission Weight'].default_value = 1.0
gv = glass.node_tree.nodes.new('ShaderNodeVolumeAbsorption'); gv.inputs['Color'].default_value = (0.75, 0.95, 1.0, 1); gv.inputs['Density'].default_value = 0.25
glass.node_tree.links.new(gv.outputs[0], glass.node_tree.nodes['Material Output'].inputs['Volume'])


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
    e = t.nodes.new('ShaderNodeEmission'); e.inputs[0].default_value = (*col, 1); e.inputs[1].default_value = s
    o = t.nodes.new('ShaderNodeOutputMaterial'); t.links.new(e.outputs[0], o.inputs[0]); return m


bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=260, size=3.2)
pane = bpy.context.object; pane.data.materials.append(glass)
for p in pane.data.polygons:
    p.use_smooth = True
pane.location.z = PT
sol = pane.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 2 * PT; sol.offset = -1.0; sol.use_even_offset = True
bev = pane.modifiers.new('bev', 'BEVEL'); bev.width = 0.03; bev.segments = 4; bev.limit_method = 'ANGLE'
pane_rest = np.zeros(len(pane.data.vertices) * 3); pane.data.vertices.foreach_get('co', pane_rest); pane_rest = pane_rest.reshape(-1, 3)

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
gs = bpy.context.object; gs.data.materials.append(gel); bpy.ops.object.shade_smooth()
gel_rest = np.zeros(len(gs.data.vertices) * 3); gs.data.vertices.foreach_get('co', gel_rest); gel_rest = gel_rest.reshape(-1, 3)

bpy.ops.mesh.primitive_torus_add(major_radius=0.5, minor_radius=0.012, major_segments=128, minor_segments=12)
ring = bpy.context.object
rmat = emit('ring', (0.2, 0.9, 1.0), 0.0); ring.data.materials.append(rmat)


def area(name, loc, size, energy, col):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size[0]; l.size_y = size[1]
    l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


area('key', (-2.5, -2.0, 3.5), (1.6, 1.6), 500, (1.0, 0.96, 1.0))
area('rimR', (3.0, 2.5, 1.2), (0.25, 1.2), 380, (0.75, 0.3, 1.0))
area('rimL', (-3.0, 2.5, 1.0), (0.25, 1.2), 300, (0.5, 0.25, 1.0))
area('cyan', (0.0, 3.5, -2.0), (3.0, 0.15), 160, (0.2, 0.85, 1.0))
area('under', (1.2, -1.8, -2.6), (1.5, 1.5), 450, (0.7, 0.4, 1.0))
area('underR', (-2.6, 1.0, -1.4), (0.4, 2.0), 500, (0.85, 0.3, 1.0))
bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 9, -0.2), rotation=(math.radians(90), 0, 0))
card = bpy.context.object
cm = bpy.data.materials.new('card'); cm.use_nodes = True; ct = cm.node_tree; ct.nodes.clear()
tc = ct.nodes.new('ShaderNodeTexCoord'); gr = ct.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
mp = ct.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.2, 0.2, 0.2)
ct.links.new(tc.outputs['Object'], mp.inputs[0]); ct.links.new(mp.outputs[0], gr.inputs[0])
cr = ct.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0, 0, 0, 1); cr.color_ramp.elements[1].color = (0.22, 0.03, 0.45, 1)
ct.links.new(gr.outputs[1], cr.inputs[0])
ce = ct.nodes.new('ShaderNodeEmission'); ct.links.new(cr.outputs[0], ce.inputs[0]); ce.inputs[1].default_value = 1.0
co = ct.nodes.new('ShaderNodeOutputMaterial'); ct.links.new(ce.outputs[0], co.inputs[0])
card.data.materials.append(cm)

cd = bpy.data.cameras.new('cam'); cd.lens = 55; cd.sensor_width = 36; cd.sensor_fit = 'HORIZONTAL'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.2
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam

HIT = 0.42
RIPS = [(HIT, 0.016), (1.0, 0.009), (2.0, 0.013), (3.7, 0.009), (4.9, 0.011), (6.2, 0.018)]


def gel_state(t):
    if t < HIT:
        u = t / HIT
        return PT + R + 1.3 * (1 - u * u), 1.0 + 0.12 * u * u, 0.0
    u = t - HIT
    sq = 1 - 0.32 * math.exp(-u * 5.0) * math.cos(u * 15.0)
    s1 = sm(1.0, 1.9, t) * (1 - sm(2.0, 2.6, t)) * 0.55
    s2 = sm(3.6, 6.2, t)
    sink = max(s1, s2)
    z = PT + R * sq - sink * (2 * PT + 2 * R)
    if t > 6.2:
        z -= 0.9 * max(0.0, t - 7.5) ** 2
    return z, sq, sink


def update(t):
    zc, sq, sink = gel_state(t)
    v = gel_rest.copy()
    v[:, 2] *= sq; v[:, 0] /= math.sqrt(sq); v[:, 1] /= math.sqrt(sq)
    wob = 0.03 * math.sin(t * 9.0) * math.exp(-max(t - HIT, 0) * 0.8)
    v[:, 0] *= 1 + wob; v[:, 1] *= 1 - wob
    v *= R
    world_z = v[:, 2] + zc
    if sink < 0.05:
        below = world_z < PT
        v[below, 2] += (PT - world_z[below]) * 0.92
    gs.data.vertices.foreach_set('co', v.ravel()); gs.data.update()
    gs.location = (0, 0, zc)
    pv = pane_rest.copy()
    r = np.sqrt(pv[:, 0] ** 2 + pv[:, 1] ** 2)
    dz = np.zeros_like(r)
    for t0, amp in RIPS:
        age = t - t0
        if 0 <= age < 3.0:
            front = r - age * 0.9
            dz += amp * np.sin(front * 18) * np.exp(-front * front * 6) * np.exp(-age * 1.2)
    dz -= 0.05 * (1 - sq) * np.exp(-r * r * 6)
    pv[:, 2] += dz
    pane.data.vertices.foreach_set('co', pv.ravel()); pane.data.update()
    cross = 1.0 if (zc - R < PT and zc + R > -PT and sink > 0.05) else 0.0
    rad = math.sqrt(max(R * R - min(zc * zc, R * R), 0.0)) * 1.02
    ring.scale = (max(rad, 0.01) / 0.5,) * 3
    ring.location = (0, 0, PT)
    rmat.node_tree.nodes['Emission'].inputs[1].default_value = 18.0 * cross
    ang = math.radians(-90 + 6 * t)
    ce_z = -0.1
    cam.location = (4.4 * math.cos(ang), 4.4 * math.sin(ang), 0.95)
    tgt = Vector((0, 0, ce_z))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (tgt - cam.location).length


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fx.py')).read())
for f in range(int(round(T0 * FPS)), int(round(T1 * FPS))):
    p = f'{OUT}/f{f:05d}.png'
    if os.path.exists(p):
        continue
    tt = story_time(f / FPS)
    update(tt)
    update_fx(tt)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)