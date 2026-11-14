"""0015 Liquid Glass v3 - five different effects, 22 s seamless loop. Blender Cycles GPU/OptiX.
blender -b -P erupt3.py -- OUTDIR W H SAMPLES FPS T0 T1 [STEP]
1 eruption+freeze+shatter  2 shards stop mid-air and rewind into the slab  3 gel sinks through the glass, splits into
5 drops that bounce back up through it and merge  4 vortex swallows the gel and freezes into a twisted spike
5 crystal tower lifts the gel, light pours down the tower, everything bursts, gel shoots up and falls back = frame 1"""
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


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


# ---------------- crowns ----------------
CA = dict(hit=0.32, rise=1.25, freeze=1.55, s=1.0, nf=12, jet=1.25, tip=0.35)          # beat 1
CT = dict(hit=16.5, rise=17.4, freeze=17.75, s=1.75, nf=12, jet=2.0, tip=0.7)          # beat 5 tower
SA, REW0, REW1, MELT1 = 3.0, 4.6, 6.4, 7.6          # beat 1 shatter, rewind window, melt back flat
ST = 19.8                                           # beat 5 burst


def crown_params(c, tc):
    tc = min(tc, c['freeze'])
    u = sm(c['hit'], c['rise'], tc)
    s = c['s']
    r0 = (0.28 + 0.5 * u) * s ** 0.7
    h = 0.7 * s * math.sin(math.pi * min(u * 0.85, 1.0)) if u > 0 else 0.0
    hj = c['jet'] * s ** 0.5 * sm(c['hit'] + 0.43, c['freeze'], tc)
    return r0, h, hj, u


def crown(c, r, th, tc):
    r = np.asarray(r, float); th = np.asarray(th, float)
    if tc < c['hit']:
        return np.zeros_like(r)
    r0, h, hj, u = crown_params(c, tc)
    s = c['s']; nf = c['nf']
    wall = h * np.exp(-((r - r0) / (0.17 * s ** 0.5)) ** 2)
    fingers = 1 + 0.3 * np.sin(nf * th + 0.6)
    tips = c['tip'] * h * np.maximum(np.sin(nf * th + 0.6), 0) ** 4 * np.exp(-((r - r0) / (0.1 * s ** 0.5)) ** 2)
    cav = -0.32 * h * np.exp(-(r / max(r0 * 0.7, 0.1)) ** 2)
    jet = hj * np.exp(-(r / (0.2 * s ** 0.4)) ** 2)
    return wall * fingers + tips + cav + jet


def jet_top(c, tc):
    return max(float(crown(c, [0.0], [0.0], tc)[0]), 0.0)


def tcA(t):
    """crown time for beat 1/2 (None = crown not shown)"""
    if t < SA:
        return t
    if t < REW1:
        return None
    return CA['freeze'] - (CA['freeze'] - CA['hit']) * sm(REW1 + 0.2, MELT1, t)


# beat 4: vortex -> twisted spike
def vortexD(t):
    return 0.8 * sm(12.2, 13.2, t) * (1 - sm(13.8, 14.3, t))


def spikeH(t):
    return 1.35 * sm(13.9, 14.6, t) * (1 - sm(15.6, 16.3, t))


def vortex(r, th, t):
    D = vortexD(t); Hs = spikeH(t)
    out = -D * np.exp(-(r / 0.55) ** 2)
    out = out + 0.07 * (D / 0.8) * np.sin(3 * th - 10 * r + 9 * t) * np.exp(-((r - 0.5) / 0.4) ** 2)
    out = out + Hs * np.exp(-(np.maximum(r, 1e-4) / 0.2) ** 1.4) * (1 + 0.25 * np.sin(5 * th - 30 * r + 2.0)) + 0.15 * Hs * np.exp(-(r / 0.5) ** 2)
    return out


def surf_center(t):
    return float(vortex(np.array([0.0]), np.array([0.0]), t)[0])


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
gvol.inputs['Emission Color'].default_value = (0.6, 0.22, 1.0, 1)
gn.links.new(gvol.outputs[0], gn.nodes['Material Output'].inputs['Volume'])
_geo = gn.nodes.new('ShaderNodeNewGeometry')
_sep = gn.nodes.new('ShaderNodeSeparateXYZ'); gn.links.new(_geo.outputs['Position'], _sep.inputs[0])
_mr = gn.nodes.new('ShaderNodeMapRange')
_mr.inputs['From Min'].default_value = PT + 0.02; _mr.inputs['From Max'].default_value = PT + 0.35
gn.links.new(_sep.outputs['Z'], _mr.inputs['Value'])
FZ = gn.nodes.new('ShaderNodeValue'); GLOW = gn.nodes.new('ShaderNodeValue')
_mr2 = gn.nodes.new('ShaderNodeMapRange')            # light front pouring down the tower
gn.links.new(_sep.outputs['Z'], _mr2.inputs['Value'])


def mathn(op, a_, b_):
    m = gn.nodes.new('ShaderNodeMath'); m.operation = op
    for i, v in enumerate((a_, b_)):
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            gn.links.new(v, m.inputs[i])
    return m.outputs[0]


fzm = mathn('MULTIPLY', _mr.outputs['Result'], FZ.outputs[0])
gn.links.new(mathn('MULTIPLY', fzm, 0.05), g.inputs['Roughness'])
gn.links.new(mathn('MULTIPLY', fzm, 0.35), gvol.inputs['Density'])
glowm = mathn('MULTIPLY', mathn('MULTIPLY', _mr.outputs['Result'], _mr2.outputs['Result']), GLOW.outputs[0])
gn.links.new(mathn('ADD', mathn('MULTIPLY', fzm, 0.5), mathn('MULTIPLY', glowm, 6.0)), gvol.inputs['Emission Strength'])

# ---------------- slab ----------------
bpy.ops.mesh.primitive_grid_add(x_subdivisions=420, y_subdivisions=420, size=5.0)
slab = bpy.context.object; slab.data.materials.append(glass)
for p in slab.data.polygons:
    p.use_smooth = True
slab.location.z = PT
sol = slab.modifiers.new('sol', 'SOLIDIFY'); sol.thickness = 2 * PT; sol.offset = -1.0; sol.use_even_offset = True
rest = np.zeros(len(slab.data.vertices) * 3); slab.data.vertices.foreach_get('co', rest); rest = rest.reshape(-1, 3)
RR = np.sqrt(rest[:, 0] ** 2 + rest[:, 1] ** 2); TH = np.arctan2(rest[:, 1], rest[:, 0])

# ---------------- gel + drops ----------------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=6, radius=1.0)
gs = bpy.context.object; gs.data.materials.append(gel); bpy.ops.object.shade_smooth()
grest = np.zeros(len(gs.data.vertices) * 3); gs.data.vertices.foreach_get('co', grest); grest = grest.reshape(-1, 3)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
dmesh = bpy.context.object.data; dmesh.materials.append(gel)
for p in dmesh.polygons:
    p.use_smooth = True
bpy.data.objects.remove(bpy.context.object)
DROPS = []
for i in range(5):
    o = bpy.data.objects.new(f'drop{i}', dmesh); sc.collection.objects.link(o)
    a_ = i / 5 * 2 * math.pi + 0.3
    DROPS.append(dict(o=o, d=Vector((math.cos(a_), math.sin(a_), 0)), ph=random.uniform(0, 6)))
gl = bpy.data.lights.new('glow', 'POINT'); gl.color = (0.6, 0.2, 1.0); gl.shadow_soft_size = 0.2
glo = bpy.data.objects.new('glow', gl); sc.collection.objects.link(glo)

# ---------------- shards ----------------
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0)
proto = bpy.context.object
for v in proto.data.vertices:
    v.co *= random.uniform(0.6, 1.3)
shardm = bpy.data.materials.new('shard'); shardm.use_nodes = True
_sb = shardm.node_tree.nodes['Principled BSDF']
_sb.inputs['Base Color'].default_value = (0.86, 0.76, 1.0, 1); _sb.inputs['IOR'].default_value = 1.5
_sb.inputs['Transmission Weight'].default_value = 1.0; _sb.inputs['Roughness'].default_value = 0.03
proto.data.materials.append(shardm)
smesh = proto.data; bpy.data.objects.remove(proto)


def make_shards(c, n, tag):
    out = []
    r0, h, hj, _ = crown_params(c, c['freeze'])
    for i in range(n):
        if i < n // 6:
            r = abs(random.gauss(0, 0.06 * c['s'])); th = random.uniform(0, 2 * math.pi)
        else:
            r = r0 + random.gauss(0, 0.06 * c['s']); th = random.uniform(0, 2 * math.pi)
        z = PT + float(crown(c, [r], [th], c['freeze'])[0]) * random.uniform(0.15, 1.0)
        if z < PT + 0.05:
            continue
        o = bpy.data.objects.new(f'{tag}{i}', smesh); sc.collection.objects.link(o); o.hide_render = True
        s = random.uniform(0.02, 0.07) * c['s'] ** 0.5
        outv = Vector((math.cos(th), math.sin(th), 0))
        out.append(dict(o=o, p0=Vector((r * math.cos(th), r * math.sin(th), z)),
                        v=outv * random.uniform(0.6, 2.2) * c['s'] ** 0.5 + Vector((0, 0, random.uniform(0.5, 2.6) * c['s'] ** 0.5)),
                        s=Vector((s * random.uniform(0.4, 1.0), s, s * random.uniform(0.2, 0.6))),
                        rot=Euler((random.uniform(0, 6), random.uniform(0, 6), random.uniform(0, 6))),
                        w=Vector((random.uniform(-9, 9), random.uniform(-9, 9), random.uniform(-9, 9)))))
    return out


SHA = make_shards(CA, 320, 'a')
SHT = make_shards(CT, 520, 't')

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
area('under', (1.0, -1.6, -1.8), (1.4, 1.4), 380, (0.7, 0.4, 1.0))
area('under2', (0.3, 0.2, -1.6), (1.2, 1.2), 450, (0.6, 0.25, 1.0))
glo.visible_camera = False
bpy.data.objects['under2'].visible_transmission = False

cd = bpy.data.cameras.new('cam'); cd.lens = 50; cd.sensor_width = 36; cd.sensor_fit = 'HORIZONTAL'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 2.0
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam


# ---------------- choreography ----------------
def shard_age(t):
    """beat 2: shards slow to a stop mid-air, hang, then fly backwards"""
    x = min(max((t - SA) / 0.6, 0.0), 1.0)
    U = 0.32
    return U * (1 - (1 - x) ** 2) * (1 - sm(REW0, REW1, t))


def wob(w, k=0.3):
    return 1 - k * math.exp(-w * 5) * math.cos(w * 15) if w >= 0 else 1.0


def gel(t):
    """returns (pos, squash, scale) of the main gel; scale 0 = hidden"""
    if t < CA['hit']:                                          # falling at frame 1
        u = CA['hit'] - t; k = max(0.0, 1 - u / 0.32)
        return Vector((0, 0, PT + R + 15.6 * u * u)), 1.0 + 0.15 * k * k, 1.0
    if t < SA:                                                 # beat 1: pressed in, lifted by the jet
        hit = CA['hit']
        base = PT - 0.12 * math.sin(math.pi * sm(hit, hit + 0.43, t)) * (1 - sm(hit + 0.43, hit + 0.68, t)) + jet_top(CA, t) - 0.08
        sq = 1 - 0.3 * math.exp(-(t - hit) * 6) * math.cos((t - hit) * 16)
        if t > CA['freeze']:
            sq = 1 + 0.08 * math.sin((t - CA['freeze']) * 11) * math.exp(-(t - CA['freeze']) * 1.2)
        return Vector((0, 0, base + R * sq)), sq, 1.0
    z0 = PT + jet_top(CA, CA['freeze']) - 0.08 + R
    if t < REW1:                                               # beat 2: falls, hangs, rewinds
        u = shard_age(t)
        return Vector((0, 0, z0 - 0.5 * G * u * u)), 1 + 0.06 * math.sin(t * 9) * (1 - sm(REW0, REW1, t)), 1.0
    if t < 8.0:                                                # rides the melting jet down, settles
        tc = tcA(t)
        z = PT + R + max(jet_top(CA, tc) - 0.08, 0.0)
        return Vector((0, 0, z)), wob(t - MELT1), 1.0
    if t < 11.6:                                               # beat 3: sinks through, splits, drops come back, merge
        k = sm(8.0, 9.0, t)
        sq = wob(t - 8.0, 0.15)
        z = PT + R * sq - k * (2 * PT + 2.4 * R)
        scl = (1 - sm(9.0, 9.3, t)) + sm(11.15, 11.5, t)
        if t >= 11.0:
            z = PT + R
            sq = wob(t - 11.45, 0.3)
        return Vector((0, 0, z)), sq, min(scl, 1.0)
    if t < 16.5:                                               # beat 4: thrown out, spirals into the vortex, rides the spike
        rr = 0.5 * sm(12.2, 12.6, t) * (1 - sm(12.6, 13.6, t))
        ang = 7.0 * max(t - 12.2, 0.0)
        surf = -vortexD(t) * math.exp(-(rr / 0.55) ** 2)
        if t >= 13.6:
            surf = surf_center(t)
        sq = wob(t - 13.9, 0.12) if t > 13.9 else 1.0
        if t > 16.3:
            sq = wob(t - 16.3, 0.25)
        return Vector((rr * math.cos(ang), rr * math.sin(ang), PT + max(surf, -0.6) + R * sq)), sq, 1.0
    if t < ST:                                                 # beat 5: tower lifts the gel
        hit = CT['hit']
        base = PT - 0.1 * math.sin(math.pi * sm(hit, hit + 0.43, t)) * (1 - sm(hit + 0.43, hit + 0.68, t)) + jet_top(CT, t) - 0.08
        sq = 1 - 0.25 * math.exp(-(t - hit) * 6) * math.cos((t - hit) * 16)
        if t > CT['freeze']:
            sq = 1 + 0.06 * math.sin((t - CT['freeze']) * 11) * math.exp(-(t - CT['freeze']) * 1.0)
        return Vector((0, 0, base + R * sq)), sq, 1.0
    if t < 21.0:                                               # burst: gel shoots up out of frame
        u = t - ST
        z0 = PT + jet_top(CT, CT['freeze']) - 0.08 + R
        return Vector((0, 0, z0 + 9.0 * u - 0.5 * G * u * u)), 1.0 + 0.2 * math.exp(-u * 3), 1.0
    if t >= LOOP - 0.7:                                        # ...and falls back in = frame 1
        u = LOOP + CA['hit'] - t
        return Vector((0, 0, PT + R + 15.6 * u * u)), 1.0, 1.0
    return Vector((0, 0, 50)), 1.0, 0.0


def drops(t):
    """beat 3: five drops under the glass, bounce back up through it and merge"""
    res = []
    for i, dd in enumerate(DROPS):
        if t < 9.0 or t >= 11.5:
            res.append(None); continue
        s = sm(9.0, 9.3, t) * (1 - sm(11.2, 11.5, t))
        spread = 0.45 * sm(9.0, 9.6, t)
        spread = spread * (1 - sm(9.9, 10.9, t)) + 0.28 * sm(9.9, 10.9, t) * (1 - sm(10.9, 11.4, t))
        zc = PT + R - (2 * PT + 2.4 * R)
        z = zc - 0.3 * sm(9.0, 9.8, t) + (PT + 0.1 - zc + 0.3) * sm(9.85, 10.8, t)
        z += 0.04 * math.sin(t * 13 + dd['ph']) * (1 - sm(10.8, 11.3, t))
        res.append((dd['d'] * spread + Vector((0, 0, z)), 0.15 * s))
    return res


RIPS = [(0.32, 0.02), (SA, 0.03), (REW1, 0.02), (MELT1, 0.02), (8.4, 0.02), (9.05, 0.015), (10.3, 0.022), (11.4, 0.02),
        (16.3, 0.02), (16.5, 0.025), (ST, 0.04)]
RIPS += [(t0 - LOOP, a_) for t0, a_ in RIPS if t0 > LOOP - 3.0]


def update(t):
    dz = np.zeros_like(RR)
    tc = tcA(t)
    if tc is not None:
        dz += crown(CA, RR, TH, tc)
    if 12.0 < t < 16.5:
        dz += vortex(RR, TH, t)
    if CT['hit'] <= t < ST:
        dz += crown(CT, RR, TH, t)
    for t0, amp in RIPS:
        age = t - t0
        if 0 <= age < 3.0:
            front = RR - age * 1.0
            dz += amp * np.sin(front * 16) * np.exp(-front * front * 5) * np.exp(-age * 1.0)
    v = rest.copy(); v[:, 2] += dz
    slab.data.vertices.foreach_set('co', v.ravel()); slab.data.update()
    FZ.outputs[0].default_value = max(sm(1.55, 1.67, t) * (1 - sm(6.6, 6.8, t)),
                                      sm(14.6, 14.75, t) * (1 - sm(15.6, 15.8, t)),
                                      sm(17.75, 17.87, t) * (1 - sm(ST, ST + 0.05, t)))
    # beat 5: light pours from the gel down the tower
    gw = sm(18.3, 18.7, t) * (1 - sm(ST, ST + 0.25, t))
    GLOW.outputs[0].default_value = gw
    top = PT + jet_top(CT, CT['freeze'])
    zf = top - (top - PT) * sm(18.5, 19.5, t)
    _mr2.inputs['From Min'].default_value = zf - 0.35; _mr2.inputs['From Max'].default_value = zf
    pv.inputs['Emission Strength'].default_value = 0.9 + 1.6 * gw
    # gel
    pos, sq, scl = gel(t)
    if scl <= 0.001:
        gs.hide_render = True
    else:
        gs.hide_render = False
        gv = grest.copy(); gv[:, 2] *= sq; gv[:, 0] /= math.sqrt(sq); gv[:, 1] /= math.sqrt(sq); gv *= R * scl
        gs.data.vertices.foreach_set('co', gv.ravel()); gs.data.update(); gs.location = pos
    glo.location = pos; gl.energy = 500.0 * gw
    for dd, st in zip(DROPS, drops(t)):
        if st is None or st[1] < 0.002:
            dd['o'].hide_render = True; continue
        dd['o'].hide_render = False; dd['o'].location = st[0]; dd['o'].scale = (st[1],) * 3
    # beat 1/2 shards: fly, hang, rewind
    for s in SHA:
        o = s['o']
        if t < SA or t >= REW1:
            o.hide_render = True; continue
        o.hide_render = False
        u = shard_age(t)
        o.location = s['p0'] + s['v'] * u + Vector((0, 0, -0.5 * G * u * u))
        o.rotation_euler = Euler((s['rot'].x + s['w'].x * u * 0.6, s['rot'].y + s['w'].y * u * 0.6, s['rot'].z + s['w'].z * u * 0.6))
        o.scale = s['s']
    # beat 5 shards: real burst, land, melt back in
    for s in SHT:
        o = s['o']
        if t < ST or t > ST + 2.2:
            o.hide_render = True; continue
        o.hide_render = False
        u = t - ST
        zl = PT + s['s'].z * 0.6; vz = s['v'].z
        ul = (vz + math.sqrt(vz * vz + 2 * G * max(s['p0'].z - zl, 0.0))) / G
        px = s['p0'].x + s['v'].x * ul; py = s['p0'].y + s['v'].y * ul
        if math.hypot(px, py) > 2.5:
            zl = -2.0 + s['s'].z * 0.6
            ul = (vz + math.sqrt(vz * vz + 2 * G * max(s['p0'].z - zl, 0.0))) / G
        uu = min(u, ul)
        o.location = s['p0'] + s['v'] * uu + Vector((0, 0, -0.5 * G * uu * uu))
        o.rotation_euler = Euler((s['rot'].x + s['w'].x * uu * 0.3, s['rot'].y + s['w'].y * uu * 0.3, s['rot'].z + s['w'].z * uu * 0.3))
        o.scale = s['s'] * max(1 - sm(ST + 1.4, ST + 2.2, t), 0.001)
    # camera: periodic sway, framed per beat
    size = 1.0 + 0.6 * sm(15.9, 16.9, t) * (1 - sm(20.2, 21.2, t))
    push = -0.45 * sm(1.55, SA, t) * (1 - sm(REW1, MELT1, t)) + 0.5 * sm(14.6, 15.4, t) * (1 - sm(15.9, 16.6, t)) \
           - 0.7 * sm(CT['freeze'], 19.6, t) * (1 - sm(ST, ST + 0.8, t))
    lift = 0.45 * sm(0.6, CA['freeze'], t) * (1 - sm(MELT1 - 0.5, MELT1, t)) + 0.45 * sm(13.9, 14.6, t) * (1 - sm(15.6, 16.3, t)) \
           + 0.6 * sm(CT['hit'] + 0.28, CT['freeze'], t) * (1 - sm(ST, ST + 1.0, t))
    low = 0.6 * sm(8.3, 9.0, t) * (1 - sm(10.6, 11.3, t))       # dip to see under the glass during beat 3
    ang = math.radians(-90 + 22 * math.sin(2 * math.pi * t / LOOP) + 6 * math.sin(4 * math.pi * t / LOOP))
    d = 3.8 * size ** 0.75 + push
    tz = 0.35 + lift - low
    cam.location = (d * math.cos(ang), d * math.sin(ang), tz + 0.55 * size ** 0.5 + 0.55 * sm(12.0, 12.6, t) * (1 - sm(13.6, 14.2, t)) - 0.55 * low)
    tgt = Vector((0, 0, tz))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (tgt - cam.location).length


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ending.py')).read())

for f in range(int(round(T0 * FPS)), int(round(T1 * FPS)), STEP):
    p = f'{OUT}/f{f:05d}.png'
    if os.path.exists(p):
        continue
    update(f / FPS)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
