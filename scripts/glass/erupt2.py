"""0015 Liquid Glass Explosion - full reel (28 s seamless loop, 4 escalating eruptions). Blender Cycles GPU/OptiX.
blender -b -P erupt2.py -- OUTDIR W H SAMPLES FPS T0 T1 [STEP]
Each cycle: a purple gel drop falls (already moving at frame 1), the solid glass slab erupts like liquid into a
crown + jet that lifts the gel, freezes into violet-tinted crystal (gel keeps wobbling), shatters into shards that
rain down and melt back into the slab, the gel lands and sinks THROUGH the glass, next drop falls in."""
import math, os, sys, random
import bpy
import numpy as np
from mathutils import Vector, Euler

a = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SAMPLES, FPS, T0, T1 = a[0], int(a[1]), int(a[2]), int(a[3]), int(a[4]), float(a[5]), float(a[6])
STEP = int(a[7]) if len(a) > 7 else 1
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

PT = 0.12; R = 0.3; G = 6.0; LOOP = 22.0
CYC = [dict(hit=0.32, rise=1.25, freeze=1.55, shatter=3.0, s=1.0, nf=12, jet=1.25, tip=0.35),
       dict(hit=5.0, rise=5.85, freeze=6.15, shatter=7.7, s=1.2, nf=9, jet=1.05, tip=0.45),
       dict(hit=9.8, rise=10.7, freeze=11.0, shatter=12.7, s=1.4, nf=16, jet=1.45, tip=0.6),
       dict(hit=15.0, rise=16.0, freeze=16.35, shatter=19.0, s=1.75, nf=12, jet=1.7, tip=0.7),
       dict(hit=22.32, rise=23.25, freeze=23.55, shatter=25.0, s=1.0, nf=12, jet=1.25, tip=0.35)]   # loop: = cycle 0


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


def crown_params(c, t):
    tc = min(t, c['freeze'])
    u = sm(c['hit'], c['rise'], tc)
    s = c['s']
    r0 = (0.28 + 0.5 * u) * s ** 0.7
    h = 0.7 * s * math.sin(math.pi * min(u * 0.85, 1.0)) if u > 0 else 0.0
    hj = c['jet'] * s ** 0.5 * sm(c['hit'] + 0.43, c['freeze'], tc)
    return r0, h, hj, u


def crown_height(c, r, th, t):
    r = np.asarray(r, float); th = np.asarray(th, float)
    if t >= c['shatter'] or t < c['hit']:
        return np.zeros_like(r)
    r0, h, hj, u = crown_params(c, t)
    s = c['s']; nf = c['nf']
    wall = h * np.exp(-((r - r0) / (0.17 * s ** 0.5)) ** 2)
    fingers = 1 + 0.3 * np.sin(nf * th + 0.6)
    tips = c['tip'] * h * np.maximum(np.sin(nf * th + 0.6), 0) ** 4 * np.exp(-((r - r0) / (0.1 * s ** 0.5)) ** 2)
    cav = -0.32 * h * np.exp(-(r / max(r0 * 0.7, 0.1)) ** 2)
    jet = hj * np.exp(-(r / (0.2 * s ** 0.4)) ** 2)
    return wall * fingers + tips + cav + jet


def jet_top(c, t):
    return max(float(crown_height(c, [0.0], [0.0], t)[0]), 0.0)


# per-cycle derived times: landing and sinking of the gel
for c in CYC:
    z0 = PT + jet_top(c, c['shatter'] - 1e-3) - 0.08 + R
    c['z0'] = z0
    c['land'] = c['shatter'] + math.sqrt(2 * max(z0 - (PT + R * 0.7), 0.0) / G)
    c['sink'] = c['land'] + 0.5
    c['gone'] = c['sink'] + 0.9

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
gvol.inputs['Absorption Color'].default_value = (0.92, 0.82, 1.0, 1)
gvol.inputs['Color'].default_value = (0.85, 0.7, 1.0, 1)
gvol.inputs['Emission Color'].default_value = (0.55, 0.2, 1.0, 1)
gn.links.new(gvol.outputs[0], gn.nodes['Material Output'].inputs['Volume'])
# frozen look only on the risen sculpture (z above the slab top), driven by FZ
_geo = gn.nodes.new('ShaderNodeNewGeometry')
_sep = gn.nodes.new('ShaderNodeSeparateXYZ'); gn.links.new(_geo.outputs['Position'], _sep.inputs[0])
_mr = gn.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = PT + 0.02; _mr.inputs['From Max'].default_value = PT + 0.35
gn.links.new(_sep.outputs['Z'], _mr.inputs['Value'])
FZ = gn.nodes.new('ShaderNodeValue'); FZ.outputs[0].default_value = 0.0


def _mul(k):
    m = gn.nodes.new('ShaderNodeMath'); m.operation = 'MULTIPLY'
    gn.links.new(_mr.outputs['Result'], m.inputs[0]); gn.links.new(FZ.outputs[0], m.inputs[1])
    m2 = gn.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = k
    gn.links.new(m.outputs[0], m2.inputs[0]); return m2


gn.links.new(_mul(0.05).outputs[0], g.inputs['Roughness'])
gn.links.new(_mul(0.35).outputs[0], gvol.inputs['Density'])
gn.links.new(_mul(0.5).outputs[0], gvol.inputs['Emission Strength'])

# ---------------- slab ----------------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=420, y_subdivisions=420, size=5.0)
slab = bpy.context.object; slab.data.materials.append(glass)
for p in slab.data.polygons:
    p.use_smooth = True
slab.location.z = PT
sol = slab.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 2 * PT; sol.offset = -1.0; sol.use_even_offset = True
rest = np.zeros(len(slab.data.vertices) * 3); slab.data.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
RR = np.sqrt(rest[:, 0] ** 2 + rest[:, 1] ** 2); TH = np.arctan2(rest[:, 1], rest[:, 0])

# ---------------- gels (one per cycle) ----------------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
g0 = bpy.context.object; g0.data.materials.append(gel); bpy.ops.object.shade_smooth()
grest = np.zeros(len(g0.data.vertices) * 3); g0.data.vertices.foreach_get('co', grest); grest = grest.reshape(-1, 3)
GELS = [g0]
for i in range(1, len(CYC)):
    o = g0.copy(); o.data = g0.data.copy(); sc.collection.objects.link(o); GELS.append(o)

# ---------------- shards (per cycle, spawned on the frozen crown) ----------------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0)
proto = bpy.context.object
for v in proto.data.vertices:
    v.co *= random.uniform(0.6, 1.3)
proto.data.materials.append(glass)
smesh = proto.data; bpy.data.objects.remove(proto)
for ci, c in enumerate(CYC[:4]):
    c['shards'] = []
    r0, h, hj, _ = crown_params(c, c['freeze'])
    for i in range(int(300 * c['s'])):
        if i < 50:
            r = abs(random.gauss(0, 0.06 * c['s'])); th = random.uniform(0, 2 * math.pi)
        else:
            r = r0 + random.gauss(0, 0.06 * c['s']); th = random.uniform(0, 2 * math.pi)
        z = PT + float(crown_height(c, [r], [th], c['freeze'])[0]) * random.uniform(0.15, 1.0)
        if z < PT + 0.05:
            continue
        o = bpy.data.objects.new(f'sh{ci}_{i}', smesh); sc.collection.objects.link(o); o.hide_render = True
        s = random.uniform(0.02, 0.07) * c['s'] ** 0.5
        out = Vector((math.cos(th), math.sin(th), 0))
        c['shards'].append(dict(o=o, p0=Vector((r * math.cos(th), r * math.sin(th), z)),
                                v=out * random.uniform(0.6, 2.2) * c['s'] ** 0.5 + Vector((0, 0, random.uniform(0.5, 2.6) * c['s'] ** 0.5)),
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
sc.render.motion_blur_shutter = 0.5


# ---------------- choreography ----------------
def gel_state(c, t):
    hit, F, S = c['hit'], c['freeze'], c['shatter']
    if t < hit - 0.7 or t >= c['gone']:
        return None
    if t < hit:                                              # falling, already moving fast
        u = hit - t
        k = max(0.0, 1 - u / 0.32)
        return PT + R + 15.6 * u * u, 1.0 + 0.15 * k * k
    if t < S:                                                # pressed in, lifted by the jet, wobbling on the frozen jet
        base = PT - 0.12 * math.sin(math.pi * sm(hit, hit + 0.43, t)) * (1 - sm(hit + 0.43, hit + 0.68, t)) + jet_top(c, t) - 0.08
        sq = 1 - 0.3 * math.exp(-(t - hit) * 6) * math.cos((t - hit) * 16)
        if t > F:
            sq = 1 + 0.08 * math.sin((t - F) * 11) * math.exp(-(t - F) * 1.2)
        return base + R * sq, sq
    if t < c['land']:                                        # falls as the crystal shatters
        return c['z0'] - 0.5 * G * (t - S) ** 2, 1.0
    w = t - c['land']                                        # lands, wobbles, then sinks through the glass
    sq = 1 - 0.35 * math.exp(-w * 5) * math.cos(w * 15)
    k = sm(c['sink'], c['gone'], t)
    return PT + R * sq - k * (2 * PT + 2.4 * R), sq


RIPS = []
for c in CYC:
    RIPS += [(c['hit'], 0.02 * c['s']), (c['shatter'], 0.03 * c['s']), (c['land'], 0.015), (c['sink'], 0.02)]
RIPS += [(t0 - LOOP, a_) for t0, a_ in RIPS if t0 > LOOP - 3.0 and t0 < LOOP]


def update(t):
    dz = np.zeros_like(RR)
    for c in CYC:
        dz += crown_height(c, RR, TH, t)
    for t0, amp in RIPS:
        age = t - t0
        if 0 <= age < 3.0:
            front = RR - age * 1.0
            dz += amp * np.sin(front * 16) * np.exp(-front * front * 5) * np.exp(-age * 1.0)
    v = rest.copy(); v[:, 2] += dz
    slab.data.vertices.foreach_set('co', v.ravel()); slab.data.update()
    FZ.outputs[0].default_value = max(sm(c['freeze'], c['freeze'] + 0.12, t) * (1 - sm(c['shatter'], c['shatter'] + 0.05, t)) for c in CYC)
    for c, o in zip(CYC, GELS):
        st = gel_state(c, t)
        if st is None:
            o.hide_render = True; continue
        o.hide_render = False
        zc, sq = st
        gv = grest.copy(); gv[:, 2] *= sq; gv[:, 0] /= math.sqrt(sq); gv[:, 1] /= math.sqrt(sq); gv *= R
        o.data.vertices.foreach_set('co', gv.ravel()); o.data.update(); o.location = (0, 0, zc)
    for c in CYC[:4]:
        S = c['shatter']
        for s in c['shards']:
            o = s['o']
            if t < S or t > S + 2.7:
                o.hide_render = True; continue
            o.hide_render = False
            u = t - S
            zl = PT + s['s'].z * 0.6
            vz = s['v'].z
            ul = (vz + math.sqrt(vz * vz + 2 * G * max(s['p0'].z - zl, 0.0))) / G
            px = s['p0'].x + s['v'].x * ul; py = s['p0'].y + s['v'].y * ul
            if math.hypot(px, py) > 2.5:
                zl = -2.0 + s['s'].z * 0.6
                ul = (vz + math.sqrt(vz * vz + 2 * G * max(s['p0'].z - zl, 0.0))) / G
            uu = min(u, ul)
            o.location = s['p0'] + s['v'] * uu + Vector((0, 0, -0.5 * G * uu * uu))
            o.rotation_euler = Euler((s['rot'].x + s['w'].x * uu * 0.3, s['rot'].y + s['w'].y * uu * 0.3, s['rot'].z + s['w'].z * uu * 0.3))
            m = 1 - sm(S + 1.6, S + 2.6, t)                   # shards melt back into the slab
            o.scale = s['s'] * max(m, 0.001)
    # camera: periodic sway (loops), scales with the crown, pushes in during each freeze
    size = CYC[0]['s']
    for c in CYC[1:]:
        size = size + (c['s'] - size) * sm(c['hit'] - 1.6, c['hit'] - 0.6, t)
    push = sum((-0.5 if i < 3 else -0.8) * sm(c['freeze'], c['shatter'], t) * (1 - sm(c['shatter'], c['shatter'] + 1.0, t)) for i, c in enumerate(CYC))
    lift = sum(0.45 * c['s'] ** 0.5 * sm(c['hit'] + 0.28, c['freeze'], t) * (1 - sm(c['shatter'], c['shatter'] + 1.2, t)) for c in CYC)
    ang = math.radians(-90 + 22 * math.sin(2 * math.pi * t / LOOP) + 6 * math.sin(4 * math.pi * t / LOOP))
    d = 3.8 * size ** 0.75 + push
    tz = 0.35 + lift
    cam.location = (d * math.cos(ang), d * math.sin(ang), tz + 0.55 * size ** 0.5)
    tgt = Vector((0, 0, tz))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (tgt - cam.location).length


for f in range(int(round(T0 * FPS)), int(round(T1 * FPS)), STEP):
    p = f'{OUT}/f{f:05d}.png'
    if os.path.exists(p):
        continue
    update(f / FPS)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
