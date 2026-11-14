# 0017 Black Sphere (remake of 0014): one polished black sphere in a deep blue nebula, six transformations, a real ending.
# usage: blender -b -P bs.py -- OUT W H SPP T0 T1 [STEP] [stills:t1,t2,...|none]
import math, os, sys, random
import bpy
import numpy as np
from mathutils import Vector, Euler, Matrix

a = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SPP, T0, T1 = a[0], int(a[1]), int(a[2]), int(a[3]), float(a[4]), float(a[5])
STEP = int(a[6]) if len(a) > 6 else 1
STILLS = [float(x) for x in a[7].split(',')] if len(a) > 7 and a[7] != 'none' else None
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(14); random.seed(14)
FPS = 60; END = 17.0
HERE = os.path.dirname(os.path.abspath(__file__))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
pr = bpy.context.preferences.addons['cycles'].preferences
pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices:
    d.use = d.type in ('OPTIX', 'CUDA', 'CPU')
sc.cycles.device = 'GPU'; sc.cycles.samples = SPP
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 8; sc.cycles.glossy_bounces = 6; sc.cycles.transparent_max_bounces = 8
sc.cycles.blur_glossy = 0.6
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = FPS
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = 0.2
sc.render.use_motion_blur = STILLS is None; sc.render.motion_blur_shutter = 0.5


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


def lerp(p, q, k): return p * (1 - k) + q * k


def env(x, a_, d_):
    return 0.0 if x < 0 else (1 - math.exp(-x / a_)) * math.exp(-x / d_)


ENERGY = (0.32, 0.62, 1.0)

# ================================================================ materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree.nodes, m.node_tree.links


M_OBS, N, L = node_mat('obsidian')                         # polished black, micro roughness variation, clear coat
bs = N['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.005, 0.0055, 0.008, 1)
bs.inputs['Coat Weight'].default_value = 1.0; bs.inputs['Coat Roughness'].default_value = 0.012
tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 10
L.new(tc.outputs['Object'], nz.inputs['Vector'])
rr = N.new('ShaderNodeMapRange'); L.new(nz.outputs['Fac'], rr.inputs['Value']); rr.inputs['From Min'].default_value = 0.35; rr.inputs['From Max'].default_value = 0.7
rr.inputs['To Min'].default_value = 0.03; rr.inputs['To Max'].default_value = 0.11; L.new(rr.outputs[0], bs.inputs['Roughness'])
nb = N.new('ShaderNodeTexNoise'); nb.inputs['Scale'].default_value = 70.0; nb.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], nb.inputs['Vector'])
bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.02; L.new(nb.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], bs.inputs['Normal'])

M_IN, N, L = node_mat('lining')
bi = N['Principled BSDF']; bi.inputs['Base Color'].default_value = (0.01, 0.015, 0.03, 1); bi.inputs['Roughness'].default_value = 0.4

M_WALL, N, L = node_mat('wall')                            # fracture faces: energy light leaking (per object 'glow')
N.remove(N['Principled BSDF'])
og = N.new('ShaderNodeAttribute'); og.attribute_type = 'OBJECT'; og.attribute_name = 'glow'
lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.45
cr = N.new('ShaderNodeValToRGB'); L.new(lw.outputs['Facing'], cr.inputs['Fac'])
cr.color_ramp.elements[0].color = (0.45, 0.72, 1.0, 1); cr.color_ramp.elements[1].color = (0.04, 0.18, 1.0, 1)
em = N.new('ShaderNodeEmission'); L.new(cr.outputs['Color'], em.inputs['Color']); L.new(og.outputs['Fac'], em.inputs['Strength'])
dk = N.new('ShaderNodeBsdfPrincipled'); dk.inputs['Base Color'].default_value = (0.01, 0.012, 0.02, 1); dk.inputs['Roughness'].default_value = 0.4
ad = N.new('ShaderNodeAddShader'); L.new(dk.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N['Material Output'].inputs['Surface'])

M_PLASMA, N, L = node_mat('plasma')                        # churning energy core
N.remove(N['Principled BSDF'])
ptc = N.new('ShaderNodeTexCoord'); pn = N.new('ShaderNodeTexNoise'); pn.noise_dimensions = '4D'; pn.inputs['Scale'].default_value = 3.5
pn.inputs['Detail'].default_value = 12; pn.inputs['Roughness'].default_value = 0.6; L.new(ptc.outputs['Object'], pn.inputs['Vector']); PL_W = pn.inputs['W']
pcr = N.new('ShaderNodeValToRGB'); L.new(pn.outputs['Fac'], pcr.inputs['Fac'])
pcr.color_ramp.elements[0].position = 0.35; pcr.color_ramp.elements[0].color = (0.02, 0.08, 0.5, 1)
pcr.color_ramp.elements[1].position = 0.8; pcr.color_ramp.elements[1].color = (0.55, 0.8, 1.0, 1)
_e = pcr.color_ramp.elements.new(0.58); _e.color = (0.06, 0.3, 1.0, 1)
pem = N.new('ShaderNodeEmission'); L.new(pcr.outputs['Color'], pem.inputs['Color']); PL_E = pem.inputs['Strength']; PL_E.default_value = 6.0
L.new(pem.outputs[0], N['Material Output'].inputs['Surface'])


def emat(name, col, k):
    m_, N_, L_ = node_mat(name); N_.remove(N_['Principled BSDF'])
    e_ = N_.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = k
    L_.new(e_.outputs[0], N_['Material Output'].inputs['Surface']); return m_, e_.inputs['Strength']


# ================================================================ the smooth / spiky / rippling ball (one deforming mesh)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1.0)
ball = bpy.context.object; ball.name = 'ball'; ball.data.materials.append(M_OBS); bpy.ops.object.shade_smooth()
nv = len(ball.data.vertices); U = np.zeros(nv * 3, np.float32); ball.data.vertices.foreach_get('co', U); U = U.reshape(-1, 3)
U /= np.linalg.norm(U, axis=1)[:, None]
NSP = 62
SDIR = []
for i in range(NSP):
    y = 1 - (i + 0.5) / NSP * 2; r_ = math.sqrt(max(0.0, 1 - y * y)); th = math.pi * (3 - math.sqrt(5)) * i
    SDIR.append((math.cos(th) * r_, math.sin(th) * r_, y))
SDIR = np.array(SDIR, np.float32)
COSS = U @ SDIR.T
W_SP = 0.21
cc = np.clip(1 - np.arccos(np.clip(COSS, -1, 1)) / W_SP, 0, 1)
PROF = (cc ** 2.6 * (3 - 2 * cc) * 0.55 + cc ** 9 * 0.45).astype(np.float32)          # sharp cone, soft base
del cc
SGAIN = rng.uniform(0.7, 1.15, NSP).astype(np.float32); SPH = rng.uniform(0, 0.35, NSP)
RIP_O = np.array([-0.4, -0.8, 0.45], np.float32); RIP_O /= np.linalg.norm(RIP_O)
RIP_ANG = np.arccos(np.clip(U @ RIP_O, -1, 1))


def ball_shape(t):
    amp = np.zeros(NSP, np.float32)
    # 1: spikes already erupting at frame 0, springy retract
    k1 = (0.55 + 0.45 * sm(0.0, 0.3, t)) * (1 - sm(1.2, 1.9, t))
    if t < 2.2:
        for k in range(NSP):
            s_ = k1 * (1 + 0.15 * math.sin(2 * math.pi * 3.0 * (t - SPH[k])) * math.exp(-t * 2))
            amp[k] = 0.42 * SGAIN[k] * max(s_, 0)
    # 6: giant urchin, spikes grow in a spiral wave, pulse, then retract for the ending
    if 12.2 < t < 15.6:
        for k in range(NSP):
            tk = 12.35 + 0.35 * (k / NSP)
            g = sm(tk, tk + 0.35, t) * (1 - sm(14.7 + 0.25 * (k / NSP), 15.3 + 0.25 * (k / NSP), t))
            amp[k] = (0.85 + 0.12 * math.sin(2 * math.pi * 2.2 * t + k)) * SGAIN[k] * g
    r = 1.0 + PROF @ amp
    # 5: liquid ripples racing over the surface from the impact point
    if 10.5 < t < 13.0:
        u = t - 10.55
        wv = np.sin(16.0 * RIP_ANG - 9.0 * u) * np.exp(-((RIP_ANG - 1.6 * u) / 0.5) ** 2) * np.exp(-u * 1.1)
        r += 0.03 * wv * (1 - sm(12.4, 12.8, t))
    # breathing on the ending
    r *= 1 + 0.004 * math.sin(2 * math.pi * 0.8 * t) * sm(15.4, 16, t)
    return r


def set_ball(t):
    r = ball_shape(t)
    ball.data.vertices.foreach_set('co', (U * r[:, None]).astype(np.float32).ravel()); ball.data.update()


# ================================================================ the shell, fractured into tiles / shards (precomputed spherical Voronoi)
_vz = np.load(os.path.join(HERE, 'voronoi.npz'))
_off = np.r_[0, np.cumsum(_vz['lens'])]
REGIONS = [_vz['idx'][_off[i]:_off[i + 1]] for i in range(len(_vz['lens']))]; SVV = _vz['verts']


def disp(p):
    q = np.array(p, dtype=np.float64)
    for k, (f, amp_) in enumerate(((5.0, 0.016), (13.0, 0.006), (31.0, 0.002))):
        ph = np.array([1.3, 2.1, 0.7]) * (k + 1)
        q = q + amp_ * np.stack([np.sin(f * q[..., 1] + ph[0]), np.sin(f * q[..., 2] + ph[1]), np.sin(f * q[..., 0] + ph[2])], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def slerp_pts(p, q, m):
    out = []
    for i in range(m):
        u = i / m; v = p * (1 - u) + q * u; out.append(v / np.linalg.norm(v))
    return out


R_IN = 0.955; RINGS = 7; SEG = 10
SHARDS = []
for k, reg in enumerate(REGIONS):
    poly = SVV[reg]
    bnd = []
    for i in range(len(poly)):
        bnd += slerp_pts(poly[i], poly[(i + 1) % len(poly)], SEG)
    bnd = np.array(bnd); B = len(bnd)
    ctr = poly.mean(0); ctr /= np.linalg.norm(ctr)
    rows = [np.repeat(ctr[None], B, 0)]
    for l in range(1, RINGS + 1):
        u = l / RINGS; v = ctr[None] * (1 - u) + bnd * u; rows.append(v / np.linalg.norm(v, axis=1)[:, None])
    P = disp(np.vstack(rows)); nP = len(P)
    cen = P.mean(0) * 0.95
    verts = np.vstack([P - cen, P * R_IN - cen])
    faces = []; mats = []
    for l in range(RINGS):
        for j in range(B):
            j2 = (j + 1) % B
            a0, b0, c0, d0 = l * B + j, l * B + j2, (l + 1) * B + j2, (l + 1) * B + j
            if l == 0:
                faces.append((a0, d0, c0)); mats.append(0); faces.append((c0 + nP, d0 + nP, a0 + nP)); mats.append(1)
            else:
                faces.append((a0, d0, c0, b0)); mats.append(0); faces.append((b0 + nP, c0 + nP, d0 + nP, a0 + nP)); mats.append(1)
    lb = RINGS * B
    for j in range(B):
        j2 = (j + 1) % B
        faces.append((lb + j, lb + j + nP, lb + j2 + nP, lb + j2)); mats.append(2)
    me = bpy.data.meshes.new(f'sh{k}'); me.from_pydata(verts.tolist(), [], faces); me.validate()
    for m in (M_OBS, M_IN, M_WALL):
        me.materials.append(m)
    me.polygons.foreach_set('material_index', mats[:len(me.polygons)])
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    ob = bpy.data.objects.new(f'shard{k}', me); sc.collection.objects.link(ob)
    c = Vector(cen); dv = c.normalized(); ob.location = c; ob.rotation_mode = 'XYZ'; ob['glow'] = 0.0
    area_ = float(np.linalg.norm(poly - ctr, axis=1).mean())
    SHARDS.append(dict(ob=ob, c=c, d=dv, lift=random.uniform(0.04, 0.32), z=dv.z,
                       dist=random.uniform(0.7, 1.5) * (1.0 + 0.5 * (1 - min(area_ / 0.25, 1))),
                       w=Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * random.uniform(0.8, 2.5),
                       ph=random.uniform(0, 6.28)))
print('shards', len(SHARDS), flush=True)

# ================================================================ plasma core, orbiters with light trails, shockwave rings, sparks
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, segments=64, ring_count=32); core = bpy.context.object; core.data.materials.append(M_PLASMA)
bpy.ops.object.shade_smooth()
cl = bpy.data.lights.new('coreL', 'POINT'); cl.color = ENERGY; cl.shadow_soft_size = 0.5
clo = bpy.data.objects.new('coreL', cl); sc.collection.objects.link(clo)

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24); orbme = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
orbme.materials.append(M_OBS)
for p_ in orbme.polygons:
    p_.use_smooth = True
ORB = []
ORB_P = [(Vector((0.3, 0.2, 1.0)).normalized(), 1.75, 0.0), (Vector((-0.6, 0.3, 0.6)).normalized(), 2.05, 2.1), (Vector((0.5, -0.4, 0.75)).normalized(), 1.55, 4.2)]
M_TRAIL, N, L = node_mat('trail'); N.remove(N['Principled BSDF'])
ta = N.new('ShaderNodeAttribute'); ta.attribute_name = 'age'
tp_ = N.new('ShaderNodeMath'); tp_.operation = 'SUBTRACT'; tp_.inputs[0].default_value = 1.0; L.new(ta.outputs['Fac'], tp_.inputs[1])
tq_ = N.new('ShaderNodeMath'); tq_.operation = 'POWER'; L.new(tp_.outputs[0], tq_.inputs[0]); tq_.inputs[1].default_value = 2.0
tk_ = N.new('ShaderNodeMath'); tk_.operation = 'MULTIPLY'; L.new(tq_.outputs[0], tk_.inputs[0]); TR_K = tk_.inputs[1]; TR_K.default_value = 14.0
tcr = N.new('ShaderNodeValToRGB'); L.new(ta.outputs['Fac'], tcr.inputs['Fac'])
tcr.color_ramp.elements[0].color = (0.9, 0.97, 1.0, 1); tcr.color_ramp.elements[1].color = (0.1, 0.3, 1.0, 1)
te = N.new('ShaderNodeEmission'); L.new(tcr.outputs['Color'], te.inputs['Color']); L.new(tk_.outputs[0], te.inputs['Strength'])
ttr = N.new('ShaderNodeBsdfTransparent'); tad = N.new('ShaderNodeAddShader'); L.new(te.outputs[0], tad.inputs[0]); L.new(ttr.outputs[0], tad.inputs[1])
L.new(tad.outputs[0], N['Material Output'].inputs['Surface'])
TRAILS = []
NTR = 70
for i in range(3):
    o = bpy.data.objects.new(f'orb{i}', orbme); sc.collection.objects.link(o); o.scale = (0.14,) * 3; ORB.append(o)
    me = bpy.data.meshes.new(f'trail{i}'); me.vertices.add(NTR * 2); me.loops.add((NTR - 1) * 4); me.polygons.add(NTR - 1)
    lo = []
    for j in range(NTR - 1):
        lo += [2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2]
    me.loops.foreach_set('vertex_index', lo); me.polygons.foreach_set('loop_start', list(range(0, (NTR - 1) * 4, 4))); me.update(calc_edges=True)
    me.attributes.new('age', 'FLOAT', 'POINT').data.foreach_set('value', np.repeat(np.linspace(0, 1, NTR), 2).astype(np.float32))
    me.materials.append(M_TRAIL)
    tob = bpy.data.objects.new(f'trailo{i}', me); sc.collection.objects.link(tob); tob.visible_shadow = False; TRAILS.append(tob)
TO0, TO1 = 4.5, 6.6


def orb_pos(i, t):
    nrm, R_, ph = ORB_P[i]
    a_ = Vector((1, 0, 0)) if abs(nrm.x) < 0.9 else Vector((0, 1, 0))
    u_ = nrm.cross(a_).normalized(); w_ = nrm.cross(u_).normalized()
    s = (t - TO0); ang = ph + 4.2 * s + 1.2 * s * s
    out = sm(TO0, TO0 + 0.35, t) * (1 - sm(TO1 - 0.3, TO1, t))
    rr_ = 0.9 + (R_ - 0.9) * out
    return (u_ * math.cos(ang) + w_ * math.sin(ang)) * rr_


RINGS_FX = []
M_RING, RING_E = emat('ring', (0.55, 0.8, 1.0), 0.0)
for i in range(4):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.005, major_segments=200, minor_segments=10)
    o = bpy.context.object; o.data.materials.append(M_RING if i == 0 else emat(f'ring{i}', (0.55, 0.8, 1.0), 0.0)[0]); o.visible_shadow = False
    RINGS_FX.append(o)
RING_T = [(0.12, Vector((0.25, 0.1, 1))), (7.4, Vector((-0.2, 0.3, 1))), (12.4, Vector((0.1, -0.25, 1))), (15.4, Vector((0, 0.15, 1)))]
M_SPK, _ = emat('spark', (0.6, 0.85, 1.0), 60.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0); spkme = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
spkme.materials.append(M_SPK)
SPK = []
for i in range(260):
    o = bpy.data.objects.new(f'spk{i}', spkme); sc.collection.objects.link(o); o.visible_shadow = False
    d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
    SPK.append(dict(ob=o, d=d, v=random.uniform(0.8, 3.0), s=random.uniform(0.003, 0.009), t0=random.choice((0.1, 7.4, 7.4, 12.4, 15.4)) + random.uniform(0, 0.15)))

# ================================================================ lights (reflections) + deep blue nebula
def area(name, loc, size, energy, col, refl=True):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size[0]; l.size_y = size[1]; l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); o.visible_camera = False; o.visible_glossy = refl
    return l


area('key', (-3.4, -3.2, 3.6), (2.6, 1.4), 700, (0.92, 0.95, 1.0))
area('strip', (3.8, -1.6, 0.8), (0.22, 4.0), 420, (0.75, 0.85, 1.0))
area('rim', (1.8, 3.6, 2.2), (1.4, 1.4), 650, (0.35, 0.55, 1.0))
area('under', (-1.0, -1.5, -3.6), (3.0, 3.0), 50, (0.4, 0.5, 0.8))

wd = bpy.data.worlds.new('nebula'); sc.world = wd; wd.use_nodes = True
N = wd.node_tree.nodes; L = wd.node_tree.links; bgw = N['Background']
tw_ = N.new('ShaderNodeTexCoord'); mpw = N.new('ShaderNodeMapping'); mpw.vector_type = 'VECTOR'; L.new(tw_.outputs['Generated'], mpw.inputs['Vector']); WROT = mpw.inputs['Rotation']
V_ = mpw.outputs[0]


def mth(op, x, y):
    n_ = N.new('ShaderNodeMath'); n_.operation = op
    for i_, z in enumerate((x, y)):
        if isinstance(z, (int, float)): n_.inputs[i_].default_value = z
        else: L.new(z, n_.inputs[i_])
    return n_.outputs[0]


def mr(x, a0, a1, b0, b1):
    n_ = N.new('ShaderNodeMapRange'); L.new(x, n_.inputs['Value']); n_.inputs['From Min'].default_value = a0; n_.inputs['From Max'].default_value = a1
    n_.inputs['To Min'].default_value = b0; n_.inputs['To Max'].default_value = b1; return n_.outputs[0]


def stars(scale, wdt, pw, gain):
    vo = N.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = scale; L.new(V_, vo.inputs['Vector'])
    sp = N.new('ShaderNodeSeparateColor'); L.new(vo.outputs['Color'], sp.inputs[0])
    return mth('MULTIPLY', mth('POWER', mr(vo.outputs['Distance'], 0, wdt, 1, 0), pw), mth('MULTIPLY', mth('POWER', sp.outputs[0], 4), gain))


st = mth('ADD', mth('ADD', stars(140, 0.1, 9, 26.0), stars(420, 0.13, 10, 6.0)), stars(1000, 0.16, 10, 1.5))
n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 1.4; n1.inputs['Detail'].default_value = 14; n1.inputs['Roughness'].default_value = 0.62
L.new(V_, n1.inputs['Vector'])
n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 4.5; n2.inputs['Detail'].default_value = 10; n2.inputs['Roughness'].default_value = 0.6
L.new(V_, n2.inputs['Vector'])
cloud = mth('POWER', mr(n1.outputs['Fac'], 0.38, 0.78, 0, 1), 1.5)
dust = mr(n2.outputs['Fac'], 0.45, 0.65, 1.0, 0.25)
neb = mth('MULTIPLY', cloud, dust)
ncr = N.new('ShaderNodeValToRGB'); L.new(n2.outputs['Fac'], ncr.inputs['Fac'])
ncr.color_ramp.elements[0].position = 0.3; ncr.color_ramp.elements[0].color = (0.04, 0.09, 0.32, 1)
ncr.color_ramp.elements[1].position = 0.75; ncr.color_ramp.elements[1].color = (0.18, 0.32, 0.7, 1)
_e = ncr.color_ramp.elements.new(0.55); _e.color = (0.03, 0.18, 0.3, 1)
nsc = N.new('ShaderNodeVectorMath'); nsc.operation = 'SCALE'; L.new(ncr.outputs['Color'], nsc.inputs[0]); L.new(mth('MULTIPLY', neb, 0.5), nsc.inputs['Scale'])
svv = N.new('ShaderNodeVectorMath'); svv.operation = 'SCALE'; svv.inputs[0].default_value = (0.9, 0.95, 1.0); L.new(mth('MULTIPLY', st, mth('ADD', 0.5, cloud)), svv.inputs['Scale'])
add1 = N.new('ShaderNodeVectorMath'); add1.operation = 'ADD'; L.new(nsc.outputs[0], add1.inputs[0]); L.new(svv.outputs[0], add1.inputs[1])
base = N.new('ShaderNodeVectorMath'); base.operation = 'ADD'; L.new(add1.outputs[0], base.inputs[0]); base.inputs[1].default_value = (0.004, 0.007, 0.018)
L.new(base.outputs[0], bgw.inputs['Color'])

# ================================================================ camera + bloom
cdat = bpy.data.cameras.new('cam'); cdat.sensor_width = 36; cdat.sensor_fit = 'HORIZONTAL'; cdat.clip_start = 0.01; cdat.dof.use_dof = True
cam = bpy.data.objects.new('cam', cdat); sc.collection.objects.link(cam); sc.camera = cam
try:
    sc.render.use_compositing = True
    if hasattr(sc, 'compositing_node_group'):
        ng = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); sc.compositing_node_group = ng
        ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new('CompositorNodeRLayers'); out_in = ng.nodes.new('NodeGroupOutput').inputs[0]
    else:
        sc.use_nodes = True; ng = sc.node_tree; rl = ng.nodes['Render Layers']; out_in = ng.nodes['Composite'].inputs[0]
    g = ng.nodes.new('CompositorNodeGlare')
    try:
        g.glare_type = 'BLOOM'
    except Exception:
        g.inputs['Type'].default_value = 'Bloom'
    for k_, v_ in (('Threshold', 1.0), ('Strength', 0.45), ('Size', 0.6)):
        if k_ in g.inputs:
            g.inputs[k_].default_value = v_
    ng.links.new(rl.outputs['Image'], g.inputs[0]); ng.links.new(g.outputs[0], out_in)
except Exception as e:
    print('bloom failed', e)

# ================================================================ timeline
# 0-2.0 spikes  | 2.0-4.4 mosaic tiles lift in a wave | 4.4-6.8 three orbiters with light trails
# 6.8-10.5 cracks, slow-motion shatter around a plasma core, slam back | 10.5-12.4 liquid ripples
# 12.4-15.3 giant urchin, spins | 15.3-17 everything settles into one perfect sphere, last ring, fade
TM0, TM1 = 2.0, 4.4
TC0, TBU, TRB, TSL = 6.8, 7.4, 9.7, 10.5
SHARD_ON = [(TM0, TM1), (TC0, TSL)]


def shards_visible(t): return any(a_ <= t < b_ for a_, b_ in SHARD_ON)


def shard_state(sh, t):
    c, d = sh['c'], sh['d']
    if TM0 <= t < TM1:                                     # tiles lift in a wave from the top down, then sink back
        tz = TM0 + 0.15 + (1 - sh['z']) / 2 * 0.9
        h = sh['lift'] * sm(tz, tz + 0.35, t) * (1 - sm(TM1 - 0.9 + 0.2 * (1 - sh['z']) / 2, TM1 - 0.15, t))
        glow = 1.6 * min(h / 0.1, 1.0)
        return c + d * h, Vector((0, 0, 0)), glow
    if TC0 <= t < TBU:                                     # cracks light up
        k = sm(TC0, TBU, t)
        return c + d * 0.006 * k, Vector((0, 0, 0)), 1.5 + 3.5 * k
    if TBU <= t < TSL:
        def hang(tt):
            uu = tt - TBU
            out = sh['dist'] * (1 - math.exp(-uu * 3.0)) + 0.05 * uu
            p = c + d * out
            p = Matrix.Rotation(0.35 * uu / max(p.length, 0.8), 3, 'Z') @ p
            return p, sh['w'] * (0.3 * (1 - math.exp(-uu * 3)) + 0.05 * uu)
        p, rot = hang(t)
        if t >= TRB:
            k = ((t - TRB) / (TSL - TRB)) ** 3
            p = lerp(p, c, k); rot = lerp(rot, Vector((0, 0, 0)), k)
        return p, rot, 0.7 + 1.6 * math.exp(-(t - TBU) * 1.5)
    return c, Vector((0, 0, 0)), 0.0


def cam_state(t):
    az = math.radians(-18) + math.radians(14) * math.sin(t * 0.33) + math.radians(28) * sm(4.4, 7.0, t) - math.radians(20) * sm(10.5, 13.0, t)
    el = math.radians(14 + 6 * math.sin(t * 0.27))
    dist = 3.35 - 0.35 * sm(2.0, 3.0, t) * (1 - sm(4.0, 4.6, t)) + 0.6 * sm(4.4, 5.0, t) * (1 - sm(6.4, 7.0, t)) \
        + 0.9 * sm(TBU, TBU + 0.6, t) * (1 - sm(TRB, TSL, t)) - 0.3 * sm(10.6, 11.6, t) * (1 - sm(12.2, 12.6, t)) \
        + 1.1 * sm(12.4, 13.2, t) * (1 - sm(15.0, 16.0, t)) - 0.25 * sm(15.4, 17.0, t)
    pos = Vector((dist * math.cos(el) * math.sin(az), -dist * math.cos(el) * math.cos(az), dist * math.sin(el)))
    shake = 0.0
    for t_ in (0.12, TBU, TSL, 12.4, 15.4):
        shake += 0.035 * math.exp(-max(t - t_, 0) * 6) * (t > t_)
    pos += Vector((math.sin(t * 71), math.sin(t * 53 + 1), math.sin(t * 61 + 2))) * shake
    tgt = Vector((0, 0, 0))
    return pos, tgt, 50.0, (tgt - pos).length - 0.75, 5.0


def apply(t):
    vis = shards_visible(t)
    ball.hide_render = vis
    for sh in SHARDS:
        o = sh['ob']; o.hide_render = not vis
        p, rot, glow = shard_state(sh, t)
        o.location = p; o.rotation_euler = Euler(tuple(rot)); o['glow'] = glow
    # core: visible behind tiles and during the shatter
    coreon = (TM0 <= t < TM1) or (TC0 <= t < TSL)
    core.hide_render = not coreon
    burst = sm(TBU - 0.1, TBU + 0.3, t) * (1 - sm(TRB, TSL, t))
    core.scale = (1.0 + 0.25 * burst + 0.03 * math.sin(t * 9),) * 3
    PL_E.default_value = 1.0 + 1.8 * burst
    cl.energy = (12 + 45 * burst) if coreon else 0.0
    # orbiters
    on = TO0 <= t < TO1 + 0.05
    for i, o in enumerate(ORB):
        o.hide_render = not on
        if on:
            o.location = orb_pos(i, t)
    # rings
    for (t_, nrm), o in zip(RING_T, RINGS_FX):
        u = t - t_
        if u < 0 or u > 1.4:
            o.hide_render = True; o.scale = (1e-3,) * 3; continue
        o.hide_render = False; rr_ = 1.08 + 1.9 * (1 - math.exp(-u * 2.4))
        o.scale = (rr_, rr_, 1 + 1.5 * u); o.rotation_euler = cam_state(t)[0].normalized().to_track_quat('Z', 'Y').to_euler()
        o.data.materials[0].node_tree.nodes['Emission'].inputs['Strength'].default_value = 14.0 * math.exp(-u * 2.8)
    # sparks
    for s_ in SPK:
        u = t - s_['t0']; o = s_['ob']
        if u < 0 or u > 1.6:
            o.hide_render = True; o.scale = (1e-4,) * 3; o.location = (0, 0, 0); continue
        o.hide_render = False
        o.location = s_['d'] * (1.02 + s_['v'] * (1 - math.exp(-u * 2.2)) / 2.2 * 2)
        o.scale = (s_['s'] * (1 - sm(0.8, 1.6, u)) + 1e-4,) * 3
    # sky drifts, camera
    WROT.default_value = (0.0, 0.0, 0.01 * t)
    pos, tgt, lens, fd, fs = cam_state(t)
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cdat.lens = lens; cdat.dof.focus_distance = fd; cdat.dof.aperture_fstop = fs
    # ending fade of the energy
    if t > 16.0:
        cl.energy *= 0.0


def apply_mesh(t):                                         # per-frame mesh data (not keyframable)
    if not shards_visible(t):
        set_ball(t)
    PL_W.default_value = t * 0.6
    on = TO0 <= t < TO1 + 0.05
    for i, tob in enumerate(TRAILS):
        tob.hide_render = not on
        if not on:
            continue
        pts = [orb_pos(i, max(t - j * 0.012, TO0)) for j in range(NTR)]
        nrm = ORB_P[i][0]
        co = []
        for j, p in enumerate(pts):
            wdt = 0.018 * (1 - j / NTR) + 0.002
            co += list(p + nrm * wdt); co += list(p - nrm * wdt)
        tob.data.vertices.foreach_set('co', co); tob.data.update()


def key(f):
    for sh in SHARDS:
        o = sh['ob']
        for prop in ('location', 'rotation_euler', '["glow"]', 'hide_render'):
            o.keyframe_insert(prop, frame=f)
    ball.keyframe_insert('hide_render', frame=f); core.keyframe_insert('hide_render', frame=f); core.keyframe_insert('scale', frame=f)
    for o in ORB:
        o.keyframe_insert('location', frame=f); o.keyframe_insert('hide_render', frame=f)
    for o in RINGS_FX:
        o.keyframe_insert('scale', frame=f); o.keyframe_insert('rotation_euler', frame=f); o.keyframe_insert('hide_render', frame=f)
        o.data.materials[0].node_tree.nodes['Emission'].inputs['Strength'].keyframe_insert('default_value', frame=f)
    for s_ in SPK:
        o = s_['ob']; o.keyframe_insert('location', frame=f); o.keyframe_insert('scale', frame=f); o.keyframe_insert('hide_render', frame=f)
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    cdat.dof.keyframe_insert('focus_distance', frame=f)
    PL_E.keyframe_insert('default_value', frame=f); cl.keyframe_insert('energy', frame=f); WROT.keyframe_insert('default_value', frame=f)


if STILLS:
    for tt in STILLS:
        apply(tt); apply_mesh(tt); sc.render.filepath = f'{OUT}/still_{tt:05.2f}.png'; bpy.ops.render.render(write_still=True); print('still', tt, flush=True)
else:
    f0, f1 = int(round(T0 * FPS)), int(round(T1 * FPS))
    todo = [f for f in range(f0, f1, STEP) if not os.path.exists(f'{OUT}/f{f:05d}.png')]
    if todo:
        for f in range(max(todo[0] - 1, 0), todo[-1] + 2):
            apply(f / FPS); key(f)
        for f in todo:
            sc.frame_set(f); apply_mesh(f / FPS); sc.render.filepath = f'{OUT}/f{f:05d}.png'
            bpy.ops.render.render(write_still=True); print('frame', f, flush=True)
