# 0017 Black Sphere (remake) - obsidian sphere cracks, bursts into a slow-motion shell cloud around an amethyst geode,
# then every shard slams back and it seals with glowing purple seams.
# usage: blender -b -P sphere.py -- OUT W H SPP T0 T1 [STEP] [stills:t1,t2,...]
import math, os, sys, random
import bpy
import numpy as np
from mathutils import Vector, Euler, Matrix

a = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SPP, T0, T1 = a[0], int(a[1]), int(a[2]), int(a[3]), float(a[4]), float(a[5])
STEP = int(a[6]) if len(a) > 6 else 1
STILLS = [float(x) for x in a[7].split(',')] if len(a) > 7 and a[7] != 'none' else None
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(17); random.seed(17)
FPS = 60; END = 16.0

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
pr = bpy.context.preferences.addons['cycles'].preferences
pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices:
    d.use = d.type in ('OPTIX', 'CUDA', 'CPU')
sc.cycles.device = 'GPU'; sc.cycles.samples = SPP
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 10; sc.cycles.glossy_bounces = 6; sc.cycles.transmission_bounces = 10; sc.cycles.transparent_max_bounces = 8
sc.cycles.caustics_reflective = True; sc.cycles.caustics_refractive = True; sc.cycles.blur_glossy = 0.5
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = FPS
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Punchy'; sc.view_settings.exposure = 0.3
sc.render.use_motion_blur = STILLS is None; sc.render.motion_blur_shutter = 0.45


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


def lerp(p, q, k): return p * (1 - k) + q * k


# ================================================================ materials
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree.nodes, m.node_tree.links


# obsidian: polished black with micro roughness variation and a clear coat
M_OUT, N, L = node_mat('obsidian')
bs = N['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.006, 0.006, 0.008, 1)
bs.inputs['Coat Weight'].default_value = 1.0; bs.inputs['Coat Roughness'].default_value = 0.015; bs.inputs['IOR'].default_value = 1.5
tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 10
L.new(tc.outputs['Object'], nz.inputs['Vector'])
rr = N.new('ShaderNodeMapRange'); L.new(nz.outputs['Fac'], rr.inputs['Value']); rr.inputs['From Min'].default_value = 0.35; rr.inputs['From Max'].default_value = 0.7
rr.inputs['To Min'].default_value = 0.035; rr.inputs['To Max'].default_value = 0.14; L.new(rr.outputs[0], bs.inputs['Roughness'])
nb = N.new('ShaderNodeTexNoise'); nb.inputs['Scale'].default_value = 60.0; nb.inputs['Detail'].default_value = 6; L.new(tc.outputs['Object'], nb.inputs['Vector'])
bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.025; L.new(nb.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs['Normal'], bs.inputs['Normal'])

# inner lining: dark amethyst, glows a little with the core
M_IN, N, L = node_mat('lining')
bi = N['Principled BSDF']; bi.inputs['Base Color'].default_value = (0.03, 0.006, 0.07, 1); bi.inputs['Roughness'].default_value = 0.35
bi.inputs['Emission Color'].default_value = (0.5, 0.12, 1.0, 1); bi.inputs['Emission Strength'].default_value = 0.03

# fracture walls: the glow you see through the cracks (per-shard strength via object attribute 'glow')
M_WALL, N, L = node_mat('wall')
N.remove(N['Principled BSDF'])
og = N.new('ShaderNodeAttribute'); og.attribute_type = 'OBJECT'; og.attribute_name = 'glow'
gk = N.new('ShaderNodeMath'); gk.operation = 'MULTIPLY'; gk.inputs[1].default_value = 0.4; L.new(og.outputs['Fac'], gk.inputs[0]); WALL_K = gk.inputs[1]
lw = N.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.4
cr = N.new('ShaderNodeValToRGB'); L.new(lw.outputs['Facing'], cr.inputs['Fac'])
cr.color_ramp.elements[0].color = (0.85, 0.45, 1.0, 1); cr.color_ramp.elements[1].color = (0.35, 0.05, 1.0, 1)
em = N.new('ShaderNodeEmission'); L.new(cr.outputs['Color'], em.inputs['Color']); L.new(gk.outputs[0], em.inputs['Strength'])
dk = N.new('ShaderNodeBsdfPrincipled'); dk.inputs['Base Color'].default_value = (0.02, 0.01, 0.03, 1); dk.inputs['Roughness'].default_value = 0.5
ad = N.new('ShaderNodeAddShader'); L.new(dk.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1]); L.new(ad.outputs[0], N['Material Output'].inputs['Surface'])

# amethyst crystal
M_CRY, N, L = node_mat('amethyst')
bc = N['Principled BSDF']; bc.inputs['Base Color'].default_value = (0.3, 0.04, 0.85, 1); bc.inputs['Roughness'].default_value = 0.03
bc.inputs['Transmission Weight'].default_value = 1.0; bc.inputs['IOR'].default_value = 1.55
bc.inputs['Emission Color'].default_value = (0.5, 0.1, 1.0, 1); CRY_E = bc.inputs['Emission Strength']; CRY_E.default_value = 0.2
_va = N.new('ShaderNodeVolumeAbsorption'); _va.inputs['Color'].default_value = (0.55, 0.12, 1.0, 1); _va.inputs['Density'].default_value = 9.0
L.new(_va.outputs[0], N['Material Output'].inputs['Volume'])

# ================================================================ the fractured obsidian shell
O_DIR = Vector((-0.35, -0.85, 0.4)).normalized()          # where the first crack starts (faces the camera)
_vz = np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voronoi.npz'))   # spherical Voronoi cells (precomputed)
SEEDS = _vz['seeds']; _off = np.r_[0, np.cumsum(_vz['lens'])]
REGIONS = [_vz['idx'][_off[i]:_off[i + 1]] for i in range(len(_vz['lens']))]; SVV = _vz['verts']


def disp(p):                                               # deterministic tangential wobble -> organic crack lines that still match
    q = np.array(p, dtype=np.float64)
    for k, (f, amp) in enumerate(((5.0, 0.018), (13.0, 0.007), (31.0, 0.0025))):
        ph = np.array([1.3, 2.1, 0.7]) * (k + 1)
        q = q + amp * np.stack([np.sin(f * q[..., 1] + ph[0]), np.sin(f * q[..., 2] + ph[1]), np.sin(f * q[..., 0] + ph[2])], -1)
    return q / np.linalg.norm(q, axis=-1, keepdims=True)


def slerp_pts(p, q, m):
    out = []
    for i in range(m):
        u = i / m; v = p * (1 - u) + q * u; out.append(v / np.linalg.norm(v))
    return out


R_IN = 0.925; RINGS = 7; SEG = 10
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
    P = disp(np.vstack(rows))                              # (RINGS+1)*B points on the unit sphere
    cen = P.mean(0) * 0.96
    nP = len(P)
    outer = P - cen; inner = P * R_IN - cen
    verts = np.vstack([outer, inner])
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
    me = bpy.data.meshes.new(f'sh{k}'); me.from_pydata(verts.tolist(), [], faces)
    me.validate()
    for m in (M_OUT, M_IN, M_WALL):
        me.materials.append(m)
    me.polygons.foreach_set('material_index', mats[:len(me.polygons)])
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    ob = bpy.data.objects.new(f'shard{k}', me); sc.collection.objects.link(ob)
    c = Vector(cen); dvec = c.normalized()
    ob.location = c; ob.rotation_mode = 'XYZ'; ob['glow'] = 0.0
    ang = math.acos(max(-1, min(1, dvec.dot(O_DIR))))
    area_ = float(np.linalg.norm(poly - ctr, axis=1).mean())
    SHARDS.append(dict(ob=ob, c=c, d=dvec, ang=ang, size=area_,
                       dist=random.uniform(0.9, 1.9) * (1.0 + 0.5 * (1 - min(area_ / 0.25, 1))),
                       w=Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * random.uniform(1.0, 3.0),
                       drift=Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * 0.03,
                       ph=random.uniform(0, 6.28), arr=0.0))
print('shards', len(SHARDS), flush=True)

# ================================================================ the amethyst geode inside
def crystal_mesh(seed):
    cr_ = random.Random(seed); V = []; F = []
    r = 0.025 + 0.01 * cr_.random(); h = 1.0; tip = 0.28
    for j in range(6):
        ph = 2 * math.pi * j / 6
        V.append((r * math.cos(ph), r * math.sin(ph), 0.0)); V.append((r * math.cos(ph) * 0.92, r * math.sin(ph) * 0.92, h))
    V.append((0, 0, h + tip))
    for j in range(6):
        a0, b0 = 2 * j, 2 * ((j + 1) % 6)
        F.append((a0, b0, b0 + 1, a0 + 1)); F.append((a0 + 1, b0 + 1, 12))
    me = bpy.data.meshes.new(f'cry{seed}'); me.from_pydata(V, [], F); me.materials.append(M_CRY); return me


cmeshes = [crystal_mesh(s) for s in range(4)]
CRY = []
NC = 520
cd_ = rng.normal(0, 1, (NC, 3)); cd_ /= np.linalg.norm(cd_, axis=1)[:, None]
for i in range(NC):
    d = Vector(cd_[i]); ob = bpy.data.objects.new(f'cry{i}', cmeshes[i % 4]); sc.collection.objects.link(ob)
    tilt = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * 0.25
    dd = (d + tilt).normalized()
    ob.location = d * 0.42; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = dd.to_track_quat('Z', 'Y')
    L_ = random.uniform(0.18, 0.42); ob.scale = (random.uniform(0.9, 1.6), random.uniform(0.9, 1.6), L_)
    CRY.append(dict(ob=ob, L=L_, sc=tuple(ob.scale)))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.45, segments=48, ring_count=24); geo = bpy.context.object
M_GEO, N, L = node_mat('geodebase')
bg_ = N['Principled BSDF']; bg_.inputs['Base Color'].default_value = (0.15, 0.04, 0.3, 1); bg_.inputs['Roughness'].default_value = 0.6
bg_.inputs['Emission Color'].default_value = (0.55, 0.12, 1.0, 1); GEO_E = bg_.inputs['Emission Strength']; GEO_E.default_value = 1.0
geo.data.materials.append(M_GEO)
core = bpy.data.lights.new('core', 'POINT'); core.color = (0.75, 0.45, 1.0); core.shadow_soft_size = 0.3
coreo = bpy.data.objects.new('core', core); sc.collection.objects.link(coreo); coreo.location = (0, 0, 0)

# ================================================================ debris: dark chips and glowing embers released at the burst
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0); chipme = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
chipme.materials.append(M_OUT)
M_EMB, N, L = node_mat('ember'); N.remove(N['Principled BSDF'])
ee = N.new('ShaderNodeEmission'); ee.inputs['Color'].default_value = (0.75, 0.35, 1.0, 1); ee.inputs['Strength'].default_value = 40
L.new(ee.outputs[0], N['Material Output'].inputs['Surface'])
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0); embme = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
embme.materials.append(M_EMB)
DEB = []
for i in range(420):
    emb = i % 3 == 0
    d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
    ob = bpy.data.objects.new(f'deb{i}', embme if emb else chipme); sc.collection.objects.link(ob); ob.rotation_mode = 'XYZ'
    s_ = random.uniform(0.004, 0.012) if emb else random.uniform(0.006, 0.03)
    DEB.append(dict(ob=ob, d=d, v=random.uniform(0.6, 3.2), s=(s_ * random.uniform(0.6, 1.4), s_, s_ * random.uniform(0.5, 1.2)),
                    w=Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * 6, emb=emb, t0=0.0))
# early chips popping off the first crack
for i in range(40):
    DEB[i]['t0'] = random.uniform(0.05, 2.8); DEB[i]['d'] = (O_DIR + Vector((random.gauss(0, .5), random.gauss(0, .5), random.gauss(0, .5)))).normalized()
    DEB[i]['v'] = random.uniform(0.15, 0.5)

# ================================================================ studio lights for reflections + deep space
def area(name, loc, size, energy, col, refl=True, cam=False):
    l = bpy.data.lights.new(name, 'AREA'); l.shape = 'RECTANGLE'; l.size = size[0]; l.size_y = size[1]; l.energy = energy; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc; sc.collection.objects.link(o)
    o.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); o.visible_camera = cam; o.visible_glossy = refl
    return l


area('key', (-3.2, -3.0, 3.4), (3.0, 1.2), 900, (1.0, 0.98, 1.0))
area('strip', (3.6, -1.2, 0.6), (0.25, 3.5), 520, (0.85, 0.75, 1.0))
area('rimP', (2.2, 3.2, 2.0), (1.5, 1.5), 700, (0.6, 0.2, 1.0))
area('rimC', (-3.0, 2.6, -1.6), (1.2, 0.3), 320, (0.2, 0.8, 1.0))
area('bounce', (0.0, -2.0, -3.4), (3.0, 3.0), 60, (0.5, 0.45, 0.7))

wd = bpy.data.worlds.new('space'); sc.world = wd; wd.use_nodes = True
N = wd.node_tree.nodes; L = wd.node_tree.links; bgw = N['Background']
tcw = N.new('ShaderNodeTexCoord')
v1 = N.new('ShaderNodeTexVoronoi'); v1.inputs['Scale'].default_value = 420; L.new(tcw.outputs['Generated'], v1.inputs['Vector'])
s1 = N.new('ShaderNodeMapRange'); L.new(v1.outputs['Distance'], s1.inputs['Value']); s1.inputs['From Max'].default_value = 0.09; s1.inputs['To Min'].default_value = 1.0; s1.inputs['To Max'].default_value = 0.0
p1 = N.new('ShaderNodeMath'); p1.operation = 'POWER'; L.new(s1.outputs[0], p1.inputs[0]); p1.inputs[1].default_value = 12
sp = N.new('ShaderNodeSeparateColor'); L.new(v1.outputs['Color'], sp.inputs[0])
p2 = N.new('ShaderNodeMath'); p2.operation = 'POWER'; L.new(sp.outputs[0], p2.inputs[0]); p2.inputs[1].default_value = 5
st = N.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; L.new(p1.outputs[0], st.inputs[0]); L.new(p2.outputs[0], st.inputs[1])
st2 = N.new('ShaderNodeMath'); st2.operation = 'MULTIPLY'; L.new(st.outputs[0], st2.inputs[0]); st2.inputs[1].default_value = 10.0
nn1 = N.new('ShaderNodeTexNoise'); nn1.inputs['Scale'].default_value = 1.6; nn1.inputs['Detail'].default_value = 12; nn1.inputs['Roughness'].default_value = 0.65
L.new(tcw.outputs['Generated'], nn1.inputs['Vector'])
neb = N.new('ShaderNodeMapRange'); L.new(nn1.outputs['Fac'], neb.inputs['Value']); neb.inputs['From Min'].default_value = 0.48; neb.inputs['From Max'].default_value = 0.8
nebp = N.new('ShaderNodeMath'); nebp.operation = 'POWER'; L.new(neb.outputs[0], nebp.inputs[0]); nebp.inputs[1].default_value = 2.2
ncr = N.new('ShaderNodeValToRGB'); L.new(nn1.outputs['Color'], ncr.inputs['Fac']) if False else L.new(nn1.outputs['Fac'], ncr.inputs['Fac'])
ncr.color_ramp.elements[0].position = 0.45; ncr.color_ramp.elements[0].color = (0.05, 0.02, 0.18, 1); ncr.color_ramp.elements[1].color = (0.35, 0.08, 0.5, 1)
_e = ncr.color_ramp.elements.new(0.62); _e.color = (0.08, 0.12, 0.45, 1)
nsc = N.new('ShaderNodeVectorMath'); nsc.operation = 'SCALE'; L.new(ncr.outputs['Color'], nsc.inputs[0])
nk = N.new('ShaderNodeMath'); nk.operation = 'MULTIPLY'; L.new(nebp.outputs[0], nk.inputs[0]); nk.inputs[1].default_value = 0.22; L.new(nk.outputs[0], nsc.inputs['Scale'])
sv = N.new('ShaderNodeVectorMath'); sv.operation = 'SCALE'; sv.inputs[0].default_value = (1.0, 0.96, 1.0); L.new(st2.outputs[0], sv.inputs['Scale'])
add1 = N.new('ShaderNodeVectorMath'); add1.operation = 'ADD'; L.new(nsc.outputs[0], add1.inputs[0]); L.new(sv.outputs[0], add1.inputs[1])
L.new(add1.outputs[0], bgw.inputs['Color']); bgw.inputs['Strength'].default_value = 1.0

# ================================================================ camera
cdat = bpy.data.cameras.new('cam'); cdat.sensor_width = 36; cdat.sensor_fit = 'HORIZONTAL'; cdat.clip_start = 0.01
cdat.dof.use_dof = True
cam = bpy.data.objects.new('cam', cdat); sc.collection.objects.link(cam); sc.camera = cam

# bloom
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
    for k_, v_ in (('Threshold', 1.0), ('Strength', 0.4), ('Size', 0.6)):
        if k_ in g.inputs:
            g.inputs[k_].default_value = v_
    ng.links.new(rl.outputs['Image'], g.inputs[0]); ng.links.new(g.outputs[0], out_in)
except Exception as e:
    print('bloom failed', e)

# ================================================================ timeline
TB, TR0, TS = 3.2, 9.6, 12.4          # burst, start of the pull back, seal
PULSES = (1.4, 2.2, 2.85)


def crack_arrival(sh):                 # cracks race outward from O_DIR across the sphere before the burst
    return -0.12 + (sh['ang'] / math.pi) ** 0.85 * 3.1


def pulse(t):
    return sum(math.exp(-((t - p) / 0.09) ** 2) for p in PULSES)


def shard_state(sh, t):
    """returns (location, rotation euler, glow)"""
    c, d = sh['c'], sh['d']
    cr_ = sm(crack_arrival(sh), crack_arrival(sh) + 0.25, t)
    if t < TB:
        gap = cr_ * (0.006 + 0.004 * pulse(t)) + 0.012 * sm(TB - 0.35, TB, t) * cr_
        glow = cr_ * (5.0 + 8.0 * pulse(t)) + 8.0 * sm(TB - 0.4, TB, t)
        return c + d * gap, Vector((0, 0, 0)), glow
    u = t - TB
    def hang(tt):
        uu = tt - TB
        out = sh['dist'] * (1 - math.exp(-uu * 3.2)) + 0.08 * uu
        p = c + d * out + sh['drift'] * uu + Vector((0, 0, 0.01 * math.sin(uu * 0.9 + sh['ph'])))
        sw = 0.42 * (1 - math.exp(-uu * 0.8)) * uu / max(p.length, 0.6)
        p = Matrix.Rotation(sw, 3, 'Z') @ p
        rot = sh['w'] * (0.35 * (1 - math.exp(-uu * 3.2)) + 0.05 * uu)
        return p, rot
    if t < TR0:
        p, rot = hang(t)
        return p, rot, 5.0 * math.exp(-u * 1.2) + 1.2
    ph0, rot0 = hang(TR0)
    if t < TS:
        k = ((t - TR0) / (TS - TR0)) ** 3.2
        p, rot = hang(t)
        p = lerp(p, c, k) if k < 1 else c
        return p, lerp(rot, Vector((0, 0, 0)), k), 1.2 + 6.0 * k
    # sealed: hairline gap keeps the glowing seams visible, one last pulse, then calm
    w_ = t - TS
    gap = 0.0035 + 0.006 * math.exp(-w_ * 6)
    glow = 5.0 + 16.0 * math.exp(-w_ * 2.5) + 7.0 * math.exp(-((t - 14.2) / 0.3) ** 2)
    return c + d * gap, Vector((0, 0, 0)), glow * (1 - 0.4 * sm(15.0, 16.0, t))


def cam_state(t):
    # 0-3: very close on the first crack, pulling back; 3.2 burst; 3.5-8 drift in to the geode; 9.6-12.4 back out; seal; slow pull back
    az0 = math.atan2(O_DIR.x, -O_DIR.y)
    az = az0 + math.radians(18) * sm(0.0, 3.0, t) + math.radians(55) * sm(3.4, 9.6, t) - math.radians(30) * sm(9.6, 12.4, t) + math.radians(10) * sm(12.4, 16, t)
    el = math.radians(22) * (1 - sm(0.0, 3.0, t)) + math.radians(10) + math.radians(8) * sm(3.4, 8.0, t) * (1 - sm(9.6, 12.0, t))
    dist = (2.0 + 1.3 * sm(0.0, 3.0, t)) * (1 - sm(3.3, 4.6, t)) + 4.6 * sm(3.3, 4.6, t) * (1 - sm(5.0, 8.4, t)) \
        + 2.9 * sm(5.0, 8.4, t) * (1 - sm(9.4, 11.6, t)) + 2.9 * sm(9.4, 11.6, t) + 0.3 * sm(12.6, 16.0, t)
    pos = Vector((dist * math.cos(el) * math.sin(az), -dist * math.cos(el) * math.cos(az), dist * math.sin(el)))
    tgt = O_DIR * 0.55 * (1 - sm(0.3, 2.8, t))
    # shake at burst and seal
    sh_ = 0.02 * math.exp(-max(t - TB, 0) * 4) * (t > TB) + 0.015 * math.exp(-max(t - TS, 0) * 5) * (t > TS)
    pos += Vector((math.sin(t * 61), math.sin(t * 47 + 1), math.sin(t * 53 + 2))) * sh_
    lens = 58 - 8 * sm(0.0, 3.0, t) + 8 * sm(5.0, 8.4, t) * (1 - sm(9.4, 11.6, t))
    focus = (tgt - pos).length if t < 4 else (pos.length - 0.9 * sm(5.0, 8.4, t) * (1 - sm(9.4, 11.6, t)) - (1 - sm(5, 8.4, t)) * 0.9)
    fstop = 2.8 if t < 3.2 else 4.0
    return pos, tgt, lens, max(focus, 0.2), fstop


def apply(t):
    for sh in SHARDS:
        p, rot, glow = shard_state(sh, t)
        sh['ob'].location = p; sh['ob'].rotation_euler = Euler(tuple(rot)); sh['ob']['glow'] = glow
    reveal = sm(TB - 0.2, TB + 0.6, t)
    core.energy = 6 + 14 * pulse(t) + 55 * reveal * (1 - 0.7 * sm(TS - 0.3, TS, t)) * (1 + 0.6 * math.exp(-((t - 8.6) / 0.5) ** 2))
    if t > TS:
        core.energy = 10 + 60 * math.exp(-(t - TS) * 3)
    GEO_E.default_value = 0.08 + 0.3 * reveal * (1 + math.exp(-((t - 8.6) / 0.5) ** 2))
    CRY_E.default_value = 0.04 + 0.12 * reveal * (1 + 1.5 * math.exp(-((t - 8.6) / 0.5) ** 2))
    gr = 0.75 + 0.25 * sm(TB, TB + 2.0, t) + 0.25 * math.exp(-((t - 8.6) / 0.6) ** 2) - 0.2 * sm(TR0, TS, t)
    for c_ in CRY:
        s0 = c_['sc']; c_['ob'].scale = (s0[0], s0[1], s0[2] * gr)
    for db in DEB:
        ob = db['ob']
        t0 = db['t0'] if db['t0'] > 0 else TB
        u = t - t0
        if u < 0 or (t > TS + 0.2 and db['t0'] == 0):
            ob.hide_render = True; ob.location = (0, 0, 0); ob.scale = (1e-4,) * 3; continue
        ob.hide_render = False
        r0 = 1.0 if db['t0'] > 0 else 0.95
        out = db['v'] * (1 - math.exp(-u * 2.6)) / 2.6 * 2.6 * (0.45 if db['t0'] == 0 else 1.0) + 0.05 * u
        if db['t0'] == 0 and t > TR0:
            out *= 1 - ((t - TR0) / (TS - TR0)) ** 3
        ob.location = db['d'] * (r0 + out); ob.rotation_euler = Euler(tuple(db['w'] * u))
        fade = 1.0 if db['t0'] == 0 else (1 - sm(1.2, 2.0, u))
        ob.scale = tuple(x * max(fade, 1e-3) for x in db['s'])
    pos, tgt, lens, focus, fstop = cam_state(t)
    cam.location = pos; cam.rotation_euler = (tgt - pos).to_track_quat('-Z', 'Y').to_euler()
    cdat.lens = lens; cdat.dof.focus_distance = focus; cdat.dof.aperture_fstop = fstop


def key(f):
    for sh in SHARDS:
        o = sh['ob']; o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_euler', frame=f); o.keyframe_insert('["glow"]', frame=f)
    for db in DEB:
        o = db['ob']; o.keyframe_insert('location', frame=f); o.keyframe_insert('rotation_euler', frame=f); o.keyframe_insert('scale', frame=f)
        o.keyframe_insert('hide_render', frame=f)
    for c_ in CRY:
        c_['ob'].keyframe_insert('scale', frame=f)
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    cdat.keyframe_insert('lens', frame=f); cdat.dof.keyframe_insert('focus_distance', frame=f); cdat.dof.keyframe_insert('aperture_fstop', frame=f)
    core.keyframe_insert('energy', frame=f); GEO_E.keyframe_insert('default_value', frame=f); CRY_E.keyframe_insert('default_value', frame=f)


if STILLS:
    for tt in STILLS:
        apply(tt); sc.render.filepath = f'{OUT}/still_{tt:05.2f}.png'; bpy.ops.render.render(write_still=True); print('still', tt, flush=True)
else:
    f0, f1 = int(round(T0 * FPS)), int(round(T1 * FPS))
    todo = [f for f in range(f0, f1, STEP) if not os.path.exists(f'{OUT}/f{f:05d}.png')]
    if todo:
        for f in range(max(todo[0] - 1, 0), todo[-1] + 2):
            apply(f / FPS); key(f)
        print('keyed', todo[0], todo[-1], flush=True)
        for f in todo:
            sc.frame_set(f); sc.render.filepath = f'{OUT}/f{f:05d}.png'
            bpy.ops.render.render(write_still=True); print('frame', f, flush=True)
