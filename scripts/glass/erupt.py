"""0015 Liquid Glass Explosion - Blender Cycles (GPU/OptiX).
blender -b -P erupt.py -- OUTDIR W H SAMPLES FPS T0 T1
A purple gel sphere hits a thick glass slab; the solid glass erupts like liquid into a crown splash
with a central jet that lifts the gel. Everything freezes into frosted crystal while the camera keeps moving,
then the crystal shatters into hundreds of glass shards that rain onto the slab and a black mirror floor."""
import math, os, sys, random
import bpy
import numpy as np
from mathutils import Vector, Euler

a = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SAMPLES, FPS, T0, T1 = a[0], int(a[1]), int(a[2]), int(a[3]), int(a[4]), float(a[5]), float(a[6])
os.makedirs(OUT, exist_ok=True)
random.seed(11)

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

PT = 0.12; R = 0.3
HIT, RISE, FREEZE, SHATTER = 0.32, 1.25, 1.55, 3.7
G = 6.0


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


# ---------------- materials ----------------
gel = bpy.data.materials.new('gel'); gel.use_nodes = True
nt = gel.node_tree; b = nt.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.55, 0.12, 1.0, 1); b.inputs['Roughness'].default_value = 0.03
b.inputs['IOR'].default_value = 1.38; b.inputs['Transmission Weight'].default_value = 1.0
pv = nt.nodes.new('ShaderNodeVolumePrincipled')
pv.inputs['Color'].default_value = (0.75, 0.3, 1.0, 1); pv.inputs['Density'].default_value = 1.4
pv.inputs['Absorption Color'].default_value = (0.7, 0.2, 1.0, 1)
pv.inputs['Emission Color'].default_value = (0.55, 0.12, 1.0, 1); pv.inputs['Emission Strength'].default_value = 0.9
nt.links.new(pv.outputs[0], nt.nodes['Material Output'].inputs['Volume'])

glass = bpy.data.materials.new('glass'); glass.use_nodes = True
gn = glass.node_tree; g = gn.nodes['Principled BSDF']
g.inputs['Base Color'].default_value = (0.94, 0.97, 1.0, 1); g.inputs['IOR'].default_value = 1.5
g.inputs['Transmission Weight'].default_value = 1.0; g.inputs['Roughness'].default_value = 0.0
gvol = gn.nodes.new('ShaderNodeVolumePrincipled')
gvol.inputs['Color'].default_value = (0.8, 0.95, 1.0, 1); gvol.inputs['Density'].default_value = 0.0
gvol.inputs['Absorption Color'].default_value = (0.85, 0.97, 1.0, 1)
gvol.inputs['Emission Color'].default_value = (0.25, 0.85, 1.0, 1); gvol.inputs['Emission Strength'].default_value = 0.0
gn.links.new(gvol.outputs[0], gn.nodes['Material Output'].inputs['Volume'])

shard_m = glass   # shards share the glass look (frosted while frozen)

# ---------------- slab ----------------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=300, y_subdivisions=300, size=3.4)
slab = bpy.context.object; slab.data.materials.append(glass)
for p in slab.data.polygons:
    p.use_smooth = True
slab.location.z = PT
sol = slab.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 2 * PT; sol.offset = -1.0; sol.use_even_offset = True
rest = np.zeros(len(slab.data.vertices) * 3); slab.data.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
RR = np.sqrt(rest[:, 0] ** 2 + rest[:, 1] ** 2); TH = np.arctan2(rest[:, 1], rest[:, 0])


def crown_params(t):
    tc = min(t, FREEZE)
    u = sm(HIT, RISE, tc)
    r0 = 0.28 + 0.5 * u
    h = 0.7 * math.sin(math.pi * min(u * 0.85, 1.0)) if u > 0 else 0.0
    hj = 1.25 * sm(0.75, FREEZE, tc)
    return r0, h, hj, u


def crown_height(r, th, t):
    r0, h, hj, u = crown_params(t)
    if t >= SHATTER:
        return np.zeros_like(r)
    wall = h * np.exp(-((r - r0) / 0.17) ** 2)
    fingers = 1 + 0.3 * np.sin(12 * th + 0.6)
    tips = 0.35 * h * np.maximum(np.sin(12 * th + 0.6), 0) ** 4 * np.exp(-((r - r0) / 0.1) ** 2)
    cav = -0.32 * h * np.exp(-(r / max(r0 * 0.7, 0.1)) ** 2)
    jet = hj * np.exp(-(r / 0.2) ** 2)
    return wall * fingers + tips + cav + jet


# ---------------- gel ----------------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
gs = bpy.context.object; gs.data.materials.append(gel); bpy.ops.object.shade_smooth()
grest = np.zeros(len(gs.data.vertices) * 3); gs.data.vertices.foreach_get('co', grest); grest = grest.reshape(-1, 3)

# ---------------- shards (spawned at the frozen crown surface) ----------------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0)
proto = bpy.context.object
for v in proto.data.vertices:
    v.co *= random.uniform(0.6, 1.3)
proto.data.materials.append(shard_m)
smesh = proto.data; bpy.data.objects.remove(proto)
SH = []
_r0, _h, _hj, _ = crown_params(FREEZE)
for i in range(380):
    if i < 60:      # from the jet
        r = abs(random.gauss(0, 0.06)); th = random.uniform(0, 2 * math.pi)
    else:
        r = _r0 + random.gauss(0, 0.06); th = random.uniform(0, 2 * math.pi)
    z = PT + float(crown_height(np.array([r]), np.array([th]), FREEZE)[0]) * random.uniform(0.15, 1.0)
    if z < PT + 0.05:
        continue
    o = bpy.data.objects.new(f'sh{i}', smesh); sc.collection.objects.link(o)
    s = random.uniform(0.02, 0.07)
    out = Vector((math.cos(th), math.sin(th), 0))
    SH.append(dict(o=o, p0=Vector((r * math.cos(th), r * math.sin(th), z)),
                   v=out * random.uniform(0.6, 2.2) + Vector((0, 0, random.uniform(0.5, 2.6))),
                   s=Vector((s * random.uniform(0.4, 1.0), s, s * random.uniform(0.2, 0.6))),
                   rot=Euler((random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6))),
                   w=Vector((random.uniform(-9, 9), random.uniform(-9, 9), random.uniform(-9, 9)))))

# ---------------- environment ----------------
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -2.0))
fl = bpy.context.object
fm = bpy.data.materials.new('floor'); fm.use_nodes = True
fb = fm.node_tree.nodes['Principled BSDF']
fb.inputs['Base Color'].default_value = (0.006, 0.004, 0.01, 1); fb.inputs['Roughness'].default_value = 0.1
fb.inputs['Coat Weight'].default_value = 1.0; fb.inputs['Coat Roughness'].default_value = 0.02
fl.data.materials.append(fm)
bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 8, 0.6), rotation=(math.radians(90), 0, 0))
card = bpy.context.object
cm = bpy.data.materials.new('card'); cm.use_nodes = True; ct = cm.node_tree; ct.nodes.clear()
tc_ = ct.nodes.new('ShaderNodeTexCoord'); gr = ct.nodes.new('ShaderNodeTexGradient'); gr.gradient_type = 'SPHERICAL'
mp = ct.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.22, 0.22, 0.22)
ct.links.new(tc_.outputs['Object'], mp.inputs[0]); ct.links.new(mp.outputs[0], gr.inputs[0])
cr = ct.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (0, 0, 0, 1); cr.color_ramp.elements[1].color = (0.28, 0.04, 0.55, 1)
ct.links.new(gr.outputs[1], cr.inputs[0])
ce = ct.nodes.new('ShaderNodeEmission'); ct.links.new(cr.outputs[0], ce.inputs[0])
co = ct.nodes.new('ShaderNodeOutputMaterial'); ct.links.new(ce.outputs[0], co.inputs[0])
card.data.materials.append(cm)


def area(name, loc, size, energy, col, refl=False):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size[0]; l.size_y = size[1]
    l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = False; o.visible_glossy = refl


area('key', (-2.2, -2.2, 3.2), (1.4, 1.4), 520, (1.0, 0.97, 1.0), refl=True)
area('rimR', (2.8, 2.2, 1.4), (0.3, 1.4), 520, (0.75, 0.3, 1.0))
area('rimL', (-2.8, 2.2, 1.0), (0.3, 1.4), 420, (0.55, 0.25, 1.0))
area('cyan', (0.5, 2.8, -1.4), (2.0, 0.2), 220, (0.2, 0.85, 1.0))
area('under', (1.0, -1.6, -1.8), (1.4, 1.4), 300, (0.7, 0.4, 1.0))

cd = bpy.data.cameras.new('cam'); cd.lens = 50; cd.sensor_width = 36; cd.sensor_fit = 'HORIZONTAL'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.0
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam


def gel_center(t):
    r0, h, hj, u = crown_params(t)
    if t < HIT:                                   # falling fast from frame 1
        k = t / HIT
        return PT + R + 1.6 * (1 - k * k), 1.0 + 0.15 * k * k
    if t < SHATTER:                               # pushed down into the cavity, then lifted by the jet
        peak = float(crown_height(np.array([0.0]), np.array([0.0]), t)[0])
        base = PT - 0.12 * math.sin(math.pi * sm(HIT, 0.75, t)) * (1 - sm(0.75, 1.0, t)) + max(peak, 0.0) - 0.08
        sq = 1 - 0.3 * math.exp(-(t - HIT) * 6) * math.cos((t - HIT) * 16)
        if t > FREEZE:                            # gel keeps wobbling on the frozen jet (alive vs frozen)
            sq = 1 + 0.08 * math.sin((t - FREEZE) * 11) * math.exp(-(t - FREEZE) * 1.2)
        return base + R * sq, sq
    u = t - SHATTER                               # falls back down as the crystal shatters
    z0 = PT + max(float(crown_height(np.array([0.0]), np.array([0.0]), FREEZE)[0]), 0.0) - 0.08 + R
    z = max(z0 - 0.5 * G * u * u, PT + R * 0.7)
    sq = 1.0
    if z <= PT + R * 0.7 + 1e-3:
        land = SHATTER + math.sqrt(2 * (z0 - PT - R * 0.7) / G)
        w = t - land
        sq = 1 - 0.35 * math.exp(-w * 5) * math.cos(w * 15)
        z = PT + R * sq
    return z, sq


def update(t):
    # slab: liquid crown (until shatter), then flat with outgoing ripples
    dz = crown_height(RR, TH, t)
    if t >= SHATTER:
        age = t - SHATTER
        front = RR - age * 1.1
        dz = dz + 0.03 * np.sin(front * 16) * np.exp(-front * front * 5) * np.exp(-age * 1.0)
    elif t >= HIT:
        age = min(t, FREEZE) - HIT
        front = RR - age * 1.0 - 0.9
        dz = dz + 0.02 * np.sin(front * 18) * np.exp(-front * front * 5) * np.exp(-age * 1.0)
    v = rest.copy(); v[:, 2] += dz
    slab.data.vertices.foreach_set('co', v.ravel()); slab.data.update()
    # frozen look: frosted + faint cyan inner glow while frozen
    fz = sm(FREEZE, FREEZE + 0.12, t) * (1 - sm(SHATTER, SHATTER + 0.05, t))
    # gel
    zc, sq = gel_center(t)
    gv = grest.copy(); gv[:, 2] *= sq; gv[:, 0] /= math.sqrt(sq); gv[:, 1] /= math.sqrt(sq); gv *= R
    gs.data.vertices.foreach_set('co', gv.ravel()); gs.data.update(); gs.location = (0, 0, zc)
    # shards
    for s in SH:
        o = s['o']
        if t < SHATTER:
            o.hide_render = True; continue
        o.hide_render = False
        u = t - SHATTER
        p = s['p0'] + s['v'] * u + Vector((0, 0, -0.5 * G * u * u))
        rr = math.hypot(p.x, p.y)
        if p.z < PT + s['s'].z and rr < 1.7:      # landed on the slab: stop
            p.z = PT + s['s'].z * 0.6
            u = min(u, 0.6)
        o.location = p
        o.rotation_euler = Euler((s['rot'].x + s['w'].x * u * 0.3, s['rot'].y + s['w'].y * u * 0.3, s['rot'].z + s['w'].z * u * 0.3))
        o.scale = s['s']
    # camera: close, low, slow orbit; drifts up with the jet; pushes in during the freeze
    ang = math.radians(-90 + 9 * t)
    d = 3.8 - 0.5 * sm(FREEZE, SHATTER, t) + 0.6 * sm(SHATTER, SHATTER + 1.0, t)
    tz = 0.35 + 0.45 * sm(0.6, FREEZE, t) * (1 - sm(SHATTER, SHATTER + 1.2, t))
    cam.location = (d * math.cos(ang), d * math.sin(ang), tz + 0.55)
    tgt = Vector((0, 0, tz))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (tgt - cam.location).length


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icefix.py')).read())
for f in range(int(round(T0 * FPS)), int(round(T1 * FPS))):
    p = f'{OUT}/f{f:05d}.png'
    if os.path.exists(p):
        continue
    update(f / FPS)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
