# 0016 Midnight Bloom - field of closed flowers under the Milky Way, a shooting star, a wave of blooming light.
# usage: blender -b -P bloom.py -- OUT W H SPP PALETTE SHOTS(A,B,C)
import math, os, sys, random
import bpy
import numpy as np
from mathutils import Vector, Euler

a = sys.argv[sys.argv.index('--') + 1:]
OUT, W, H, SPP, PAL, SHOTS = a[0], int(a[1]), int(a[2]), int(a[3]), a[4], a[5].split(',')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7); random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
pr = bpy.context.preferences.addons['cycles'].preferences
pr.compute_device_type = 'OPTIX'; pr.get_devices()
for d in pr.devices:
    d.use = d.type in ('OPTIX', 'CUDA', 'CPU')
sc.cycles.device = 'GPU'; sc.cycles.samples = SPP
sc.render.threads_mode = 'AUTO'
sc.cycles.use_denoising = True; sc.cycles.denoiser = 'OPTIX'
sc.cycles.max_bounces = 6; sc.cycles.transparent_max_bounces = 8; sc.cycles.volume_bounces = 1
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.view_settings.view_transform = 'AgX'; sc.view_settings.exposure = 0.9

PALS = {
    'natural': dict(petal=(0.9, 0.88, 0.8), petal2=(0.95, 0.9, 0.75), centre=(0.95, 0.55, 0.05), glow=(1.0, 0.8, 0.5), glow2=(1.0, 0.85, 0.6), gk=5.0, res=0.1,
                    grass=(0.06, 0.14, 0.035), stem=(0.07, 0.17, 0.04), soil=(0.01, 0.012, 0.007),
                    sky=(0.004, 0.008, 0.022), band=(0.75, 0.78, 1.0), core=(1.0, 0.82, 0.62),
                    hor=(0.05, 0.07, 0.14), moon=(0.62, 0.72, 1.0), moonE=1.4, fly=(0.85, 1.0, 0.3), fog=(0.6, 0.7, 1.0)),
    'blue': dict(ramp=[(0.0, (0.04, 0.16, 1.0)), (0.38, (0.22, 0.08, 1.0)), (0.66, (0.03, 0.55, 1.0)), (0.9, (0.85, 0.12, 0.85))],
                 petal=(0.06, 0.2, 1.0), petal2=(0.12, 0.5, 1.0), centre=(0.5, 0.8, 1.0), glow=(0.15, 0.35, 1.0), glow2=(0.05, 0.45, 1.0), gk=6.0, res=0.16,
                 grass=(0.012, 0.025, 0.07), stem=(0.015, 0.035, 0.09), soil=(0.004, 0.006, 0.012),
                 sky=(0.004, 0.006, 0.03), band=(0.7, 0.75, 1.0), core=(0.85, 0.85, 1.0),
                 hor=(0.03, 0.05, 0.2), moon=(0.4, 0.5, 1.0), moonE=1.2, fly=(0.5, 0.8, 1.0), fog=(0.4, 0.5, 1.0)),
}
P = PALS[PAL]
sc.view_settings.look = 'AgX - Punchy' if PAL == 'blue' else 'AgX - Medium High Contrast'


# ------------------------------------------------------------------ materials
def principled(name, col, rough=0.5, trans=0.0, glow=False, gcol=None, gk=0.0, col2=None, gcol2=None, ramp=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    out = N['Material Output']; bs = N['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*col, 1); bs.inputs['Roughness'].default_value = rough
    tint = None; rampout = None
    if ramp is not None:
        ta = N.new('ShaderNodeAttribute'); ta.attribute_type = 'INSTANCER'; ta.attribute_name = 'tint'; tint = ta.outputs['Fac']
        cr = N.new('ShaderNodeValToRGB'); L.new(tint, cr.inputs['Fac'])
        el = cr.color_ramp.elements
        while len(el) < len(ramp):
            el.new(0.5)
        for e_, (pos, c_) in zip(el, ramp):
            e_.position = pos; e_.color = (*c_, 1)
        rampout = cr.outputs['Color']; L.new(rampout, bs.inputs['Base Color'])
    elif col2 is not None:
        ta = N.new('ShaderNodeAttribute'); ta.attribute_type = 'INSTANCER'; ta.attribute_name = 'tint'; tint = ta.outputs['Fac']
        cm = N.new('ShaderNodeMix'); cm.data_type = 'RGBA'; L.new(tint, cm.inputs['Factor'])
        cm.inputs['A'].default_value = (*col, 1); cm.inputs['B'].default_value = (*col2, 1)
        L.new(cm.outputs['Result'], bs.inputs['Base Color'])
    sh = bs.outputs[0]
    if trans > 0:
        tr = N.new('ShaderNodeBsdfTranslucent'); tr.inputs['Color'].default_value = (*col, 1)
        mx = N.new('ShaderNodeMixShader'); mx.inputs[0].default_value = trans
        L.new(sh, mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); sh = mx.outputs[0]
    if glow:
        a1 = N.new('ShaderNodeAttribute'); a1.attribute_type = 'INSTANCER'; a1.attribute_name = 'glow'
        a2 = N.new('ShaderNodeAttribute'); a2.attribute_type = 'OBJECT'; a2.attribute_name = 'glow'
        ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'
        L.new(a1.outputs['Fac'], ad.inputs[0]); L.new(a2.outputs['Fac'], ad.inputs[1])
        pa = N.new('ShaderNodeAttribute'); pa.attribute_name = 'pu'
        pg = N.new('ShaderNodeMapRange'); L.new(pa.outputs['Fac'], pg.inputs['Value']); pg.inputs['To Min'].default_value = 1.45; pg.inputs['To Max'].default_value = 0.55
        ad2 = N.new('ShaderNodeMath'); ad2.operation = 'MULTIPLY'; L.new(ad.outputs[0], ad2.inputs[0]); L.new(pg.outputs[0], ad2.inputs[1])
        mu = N.new('ShaderNodeMath'); mu.operation = 'MULTIPLY'; mu.inputs[1].default_value = gk
        L.new(ad2.outputs[0], mu.inputs[0])
        em = N.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*gcol, 1)
        if rampout is not None:
            L.new(rampout, em.inputs['Color'])
        elif tint is not None and gcol2 is not None:
            gm = N.new('ShaderNodeMix'); gm.data_type = 'RGBA'; L.new(tint, gm.inputs['Factor'])
            gm.inputs['A'].default_value = (*gcol, 1); gm.inputs['B'].default_value = (*gcol2, 1)
            L.new(gm.outputs['Result'], em.inputs['Color'])
        L.new(mu.outputs[0], em.inputs['Strength'])
        add = N.new('ShaderNodeAddShader'); L.new(sh, add.inputs[0]); L.new(em.outputs[0], add.inputs[1]); sh = add.outputs[0]
    L.new(sh, out.inputs['Surface'])
    return m


M_PET = principled('petal', P['petal'], 0.45, 0.4, True, P['glow'], P['gk'], P['petal2'], P['glow2'], P.get('ramp'))
M_CEN = principled('centre', P['centre'], 0.6, 0.0, True, P['glow'], P['gk'] * 1.6)
M_STM = principled('stem', P['stem'], 0.5, 0.3)
M_GRS = principled('grass', P['grass'], 0.45, 0.45)
M_SOIL = principled('soil', P['soil'], 0.95)

# ------------------------------------------------------------------ flower variants (12 open states)
NS = 12; HH = 0.32; NP = 18


def flower_mesh(e, name):
    V = []; F = []; MI = []; U = []

    def grid(pts, nu, nv, mi, us=None):
        b = len(V); V.extend(pts); U.extend(us if us is not None else [0.0] * len(pts))
        for i in range(nu - 1):
            for j in range(nv - 1):
                F.append((b + i * nv + j, b + (i + 1) * nv + j, b + (i + 1) * nv + j + 1, b + i * nv + j + 1)); MI.append(mi)

    prng = random.Random(3)
    c0 = Vector((0.012, 0, HH))
    for k in range(NP):
        phi = 2 * math.pi * k / NP + prng.uniform(-0.08, 0.08)
        ang = math.radians(78 - 84 * e + prng.uniform(-5, 5))
        Lp = 0.046 * (0.78 + 0.22 * e) * prng.uniform(0.9, 1.08); Wd = 0.0062
        r = Vector((math.cos(phi), math.sin(phi), 0)); s = Vector((-math.sin(phi), math.cos(phi), 0)); z = Vector((0, 0, 1))
        dr = r * math.cos(ang) + z * math.sin(ang); nr = -r * math.sin(ang) + z * math.cos(ang)
        pts = []; nu, nv = 7, 3; us = []
        for i in range(nu):
            u = i / (nu - 1)
            w = Wd * max(math.sin(math.pi * (0.12 + 0.88 * u)), 0.0) ** 0.5
            for j in range(nv):
                v = -1 + 2 * j / (nv - 1)
                pts.append(c0 + r * 0.006 + dr * (Lp * u) + nr * (0.14 * Lp * u * u + 0.18 * w * abs(v)) + s * (w * v)); us.append(u)
        grid(pts, nu, nv, 0, us)
    nl, nm = 5, 14; pts = []
    for i in range(nl):
        th = (math.pi / 2) * i / (nl - 1)
        for j in range(nm + 1):
            ph = 2 * math.pi * j / nm; rr = 0.0095 * math.cos(th) + 0.0002
            pts.append(c0 + Vector((rr * math.cos(ph), rr * math.sin(ph), 0.0006 + 0.005 * math.sin(th))))
    grid(pts, nl, nm + 1, 1)
    pts = []
    for i in range(6):
        zz = HH * i / 5; off = 0.012 * math.sin(math.pi * zz / HH * 0.5)
        for j in range(7):
            ph = 2 * math.pi * j / 6
            pts.append(Vector((off + 0.0022 * math.cos(ph), 0.0022 * math.sin(ph), zz)))
    grid(pts, 6, 7, 2)
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in V], [], F)
    for m in (M_PET, M_CEN, M_STM):
        me.materials.append(m)
    me.polygons.foreach_set('material_index', MI)
    me.attributes.new('pu', 'FLOAT', 'POINT').data.foreach_set('value', U)
    try:
        me.shade_smooth()
    except Exception:
        me.polygons.foreach_set('use_smooth', [True] * len(F))
    return me


def grass_mesh(seed, name):
    gr = random.Random(seed); V = []; F = []
    for b in range(7):
        bx, by = gr.uniform(-0.03, 0.03), gr.uniform(-0.03, 0.03)
        h = gr.uniform(0.08, 0.3); lean = gr.uniform(0.05, 0.25) * h; lp = gr.uniform(0, 2 * math.pi)
        wd = gr.uniform(0.003, 0.006); fa = lp + math.pi / 2; base = len(V)
        for i in range(6):
            u = i / 5; zz = h * u; dx = lean * u * u
            cx, cy = bx + dx * math.cos(lp), by + dx * math.sin(lp); ww = wd * (1 - u) + 0.0003
            V.append((cx - ww * math.cos(fa), cy - ww * math.sin(fa), zz)); V.append((cx + ww * math.cos(fa), cy + ww * math.sin(fa), zz))
        for i in range(5):
            F.append((base + 2 * i, base + 2 * i + 1, base + 2 * i + 3, base + 2 * i + 2))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.materials.append(M_GRS)
    return me


def src_collection(name, meshes):
    col = bpy.data.collections.new(name); sc.collection.children.link(col)
    for i, me in enumerate(meshes):
        o = bpy.data.objects.new(f'{name}_{i:02d}', me); o.location = (0, 0, -60); col.objects.link(o)
    return col


def ease(x): return x * x * (3 - 2 * x)


FLV = src_collection('flv', [flower_mesh(ease(k / (NS - 1)), f'fl{k}') for k in range(NS)])
GRV = src_collection('grv', [grass_mesh(s, f'gr{s}') for s in range(8)])


# ------------------------------------------------------------------ instancer (points mesh -> GN instance on points)
def instancer(name, col, pts, state, rot, scl, glow):
    n = len(pts)
    me = bpy.data.meshes.new(name); me.vertices.add(n); me.vertices.foreach_set('co', pts.astype(np.float32).ravel())
    for nm, typ, arr, key in (('state', 'INT', state, 'value'), ('rot', 'FLOAT_VECTOR', rot, 'vector'),
                              ('scl', 'FLOAT', scl, 'value'), ('glow', 'FLOAT', glow, 'value'),
                              ('tint', 'FLOAT', rng.random(n) ** 1.5, 'value')):
        at = me.attributes.new(nm, typ, 'POINT'); at.data.foreach_set(key, np.asarray(arr).ravel())
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name + '_gn', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    ci = N.new('GeometryNodeCollectionInfo'); ci.transform_space = 'ORIGINAL'
    ci.inputs['Collection'].default_value = col; ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    iop = N.new('GeometryNodeInstanceOnPoints'); iop.inputs['Pick Instance'].default_value = True

    def na(nm, typ):
        x = N.new('GeometryNodeInputNamedAttribute'); x.data_type = typ; x.inputs['Name'].default_value = nm; return x.outputs['Attribute']
    e2r = N.new('FunctionNodeEulerToRotation')
    L.new(gi.outputs[0], iop.inputs['Points']); L.new(ci.outputs[0], iop.inputs['Instance'])
    L.new(na('state', 'INT'), iop.inputs['Instance Index'])
    L.new(na('rot', 'FLOAT_VECTOR'), e2r.inputs[0]); L.new(e2r.outputs[0], iop.inputs['Rotation'])
    L.new(na('scl', 'FLOAT'), iop.inputs['Scale'])
    L.new(iop.outputs[0], go.inputs[0])
    md = ob.modifiers.new('inst', 'NODES'); md.node_group = ng
    return ob


def scatter(dn, fall, df, y0, y1, patch=0.0):
    xs, ys = [], []
    for yb in np.arange(y0, y1, 1.0):
        w = 2 * (0.78 * max(yb, 0.0) + 2.5)
        n = rng.poisson(w * (dn * math.exp(-max(yb, 0.0) / fall) + df))
        xs.append(rng.uniform(-w / 2, w / 2, n)); ys.append(rng.uniform(yb, yb + 1, n))
    x = np.concatenate(xs); y = np.concatenate(ys)
    if patch > 0:
        p = 0.5 + 0.5 * np.sin(x * 0.45 + 1.3) * np.sin(y * 0.33 + 0.4) + 0.25 * np.sin(x * 1.7 - y * 1.1)
        keep = rng.random(len(x)) < np.clip(1 - patch + patch * p, 0.05, 1)
        x, y = x[keep], y[keep]
    return np.stack([x, y, np.zeros_like(x)], 1)


FP = scatter(60, 35, 8.0, -1.0, 150.0, patch=0.5); nF = len(FP)
F_rot = np.stack([rng.normal(0, 0.12, nF), rng.normal(0, 0.12, nF), rng.uniform(0, 2 * math.pi, nF)], 1)
F_scl0 = rng.uniform(0.8, 1.3, nF)
F_ph = rng.uniform(-1.5, 1.5, nF)
GP = scatter(80, 18, 3.0, -1.0, 120.0); nG = len(GP)
G_rot = np.stack([rng.normal(0, 0.1, nG), rng.normal(0, 0.1, nG), rng.uniform(0, 2 * math.pi, nG)], 1)
print('flowers', nF, 'grass', nG, flush=True)
FOB = instancer('flowers', FLV, FP, np.zeros(nF, np.int32), F_rot, F_scl0, np.zeros(nF))
GOB = instancer('grass', GRV, GP, rng.integers(0, 8, nG).astype(np.int32), G_rot, rng.uniform(0.8, 1.4, nG), np.zeros(nG))

HERO = Vector((0.06, 3.75, 0.0))
hero = bpy.data.objects.new('hero', FLV.objects[f'flv_{NS - 1:02d}'].data); sc.collection.objects.link(hero)
hero.location = HERO; hero.scale = (1.4,) * 3; hero.rotation_euler = (math.radians(22), 0, 0.4); hero['glow'] = 0.0

bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 200, 0)); gnd = bpy.context.object; gnd.data.materials.append(M_SOIL)

# ------------------------------------------------------------------ night sky (world)
wd = bpy.data.worlds.new('night'); sc.world = wd; wd.use_nodes = True
N = wd.node_tree.nodes; L = wd.node_tree.links
bg = N['Background']; bg.inputs['Strength'].default_value = 1.0
tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.vector_type = 'VECTOR'
L.new(tc.outputs['Generated'], mp.inputs['Vector'])
DIR = mp.outputs[0]


def math_(op, x, y=None):
    n = N.new('ShaderNodeMath'); n.operation = op
    if isinstance(x, (int, float)): n.inputs[0].default_value = x
    else: L.new(x, n.inputs[0])
    if y is not None:
        if isinstance(y, (int, float)): n.inputs[1].default_value = y
        else: L.new(y, n.inputs[1])
    return n.outputs[0]


def mrange(x, a0, a1, b0, b1):
    n = N.new('ShaderNodeMapRange'); L.new(x, n.inputs['Value'])
    n.inputs['From Min'].default_value = a0; n.inputs['From Max'].default_value = a1
    n.inputs['To Min'].default_value = b0; n.inputs['To Max'].default_value = b1; return n.outputs[0]


def stars(scale, width, pw, gain):
    vo = N.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = scale; L.new(DIR, vo.inputs['Vector'])
    core = math_('POWER', mrange(vo.outputs['Distance'], 0.0, width, 1.0, 0.0), pw)
    sp = N.new('ShaderNodeSeparateColor'); L.new(vo.outputs['Color'], sp.inputs[0])
    br = math_('MULTIPLY', math_('POWER', sp.outputs[0], 4.0), gain)
    return math_('MULTIPLY', core, br)


st = math_('ADD', math_('ADD', stars(160, 0.12, 8, 30.0), stars(520, 0.16, 10, 6.0)), stars(1100, 0.2, 10, 2.0))
sxyz = N.new('ShaderNodeSeparateXYZ'); L.new(DIR, sxyz.inputs[0]); Z = sxyz.outputs['Z']
above = mrange(Z, -0.01, 0.03, 0.0, 1.0)
h1 = Vector((0.55, 1.0, 0.04)).normalized(); h2 = Vector((-0.55, 0.55, 0.75)).normalized(); NRM = h1.cross(h2).normalized()
dt = N.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'; L.new(DIR, dt.inputs[0]); dt.inputs[1].default_value = tuple(NRM)
dd = dt.outputs['Value']
band = math_('EXPONENT', math_('MULTIPLY', math_('MULTIPLY', dd, dd), -1 / 0.13 ** 2))
core = math_('EXPONENT', math_('MULTIPLY', math_('MULTIPLY', dd, dd), -1 / 0.045 ** 2))
n1 = N.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 6.0; n1.inputs['Detail'].default_value = 12; n1.inputs['Roughness'].default_value = 0.62
L.new(DIR, n1.inputs['Vector'])
clouds = math_('POWER', mrange(n1.outputs['Fac'], 0.35, 0.78, 0.0, 1.0), 1.6)
n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 16.0; n2.inputs['Detail'].default_value = 10; n2.inputs['Roughness'].default_value = 0.6
L.new(DIR, n2.inputs['Vector'])
dust = mrange(n2.outputs['Fac'], 0.47, 0.6, 1.0, 0.12)
dustc = math_('ADD', math_('SUBTRACT', 1.0, core), math_('MULTIPLY', core, dust))
bandv = math_('MULTIPLY', math_('MULTIPLY', math_('MULTIPLY', band, clouds), dustc), above)
corev = math_('MULTIPLY', math_('MULTIPLY', core, clouds), math_('MULTIPLY', dustc, above))
hor = math_('EXPONENT', math_('MULTIPLY', math_('MULTIPLY', Z, Z), -1 / 0.07 ** 2))
stv = math_('MULTIPLY', math_('MULTIPLY', st, above), math_('ADD', 1.0, math_('MULTIPLY', band, 4.0)))
STARG = N.new('ShaderNodeValue'); STARG.outputs[0].default_value = 1.0
stv = math_('MULTIPLY', stv, STARG.outputs[0])


def colscale(val, col, k):
    vm = N.new('ShaderNodeVectorMath'); vm.operation = 'SCALE'; vm.inputs[0].default_value = tuple(c * k for c in col)
    L.new(val, vm.inputs['Scale']); return vm.outputs[0]


def vadd(x, y):
    vm = N.new('ShaderNodeVectorMath'); vm.operation = 'ADD'; L.new(x, vm.inputs[0]); L.new(y, vm.inputs[1]); return vm.outputs[0]


# aurora curtains (animated through AUR_W)
sx2 = N.new('ShaderNodeSeparateXYZ'); L.new(DIR, sx2.inputs[0])
azi = math_('ARCTAN2', sx2.outputs['X'], sx2.outputs['Y'])
cx1 = N.new('ShaderNodeCombineXYZ'); L.new(math_('MULTIPLY', azi, 1.6), cx1.inputs['X'])
na1 = N.new('ShaderNodeTexNoise'); na1.noise_dimensions = '4D'; na1.inputs['Scale'].default_value = 1.3; na1.inputs['Detail'].default_value = 3
L.new(cx1.outputs[0], na1.inputs['Vector']); AUR_W = na1.inputs['W']
cx2 = N.new('ShaderNodeCombineXYZ'); L.new(math_('MULTIPLY', azi, 30.0), cx2.inputs['X'])
na2 = N.new('ShaderNodeTexNoise'); na2.noise_dimensions = '4D'; na2.inputs['Scale'].default_value = 1.0; na2.inputs['Detail'].default_value = 2
L.new(cx2.outputs[0], na2.inputs['Vector']); AUR_W2 = na2.inputs['W']
curt = math_('POWER', mrange(na1.outputs['Fac'], 0.42, 0.72, 0.0, 1.0), 2.0)
rays = mrange(na2.outputs['Fac'], 0.3, 0.75, 0.35, 1.0)
top = math_('ADD', 0.26, math_('MULTIPLY', na1.outputs['Fac'], 0.4))
vlow = mrange(Z, 0.02, 0.09, 0.0, 1.0)
vtop = math_('MINIMUM', math_('MAXIMUM', math_('DIVIDE', math_('SUBTRACT', top, Z), 0.18), 0.0), 1.0)
aur_m = math_('MULTIPLY', math_('MULTIPLY', curt, rays), math_('MULTIPLY', vlow, vtop))
hz = math_('MINIMUM', math_('DIVIDE', Z, top), 1.0)
acr = N.new('ShaderNodeValToRGB'); L.new(hz, acr.inputs['Fac'])
acr.color_ramp.elements[0].color = (0.05, 0.9, 0.75, 1); acr.color_ramp.elements[1].color = (0.75, 0.15, 1.0, 1)
_a = acr.color_ramp.elements.new(0.45); _a.color = (0.1, 0.45, 1.0, 1)
aur_s = N.new('ShaderNodeVectorMath'); aur_s.operation = 'SCALE'; L.new(acr.outputs['Color'], aur_s.inputs[0])
AUR_GAIN = N.new('ShaderNodeValue'); AUR_GAIN.outputs[0].default_value = 0.5
L.new(math_('MULTIPLY', aur_m, AUR_GAIN.outputs[0]), aur_s.inputs['Scale'])
one = math_('ADD', 1.0, 0.0)
sky = vadd(vadd(vadd(vadd(colscale(one, P['sky'], 1.0), colscale(stv, (1.0, 0.97, 0.92), 1.0)),
                     colscale(bandv, P['band'], 0.11)), colscale(corev, P['core'], 0.16)), colscale(hor, P['hor'], 1.0))
sky = vadd(sky, aur_s.outputs[0])
L.new(sky, bg.inputs['Color'])

mo = bpy.data.lights.new('moon', 'SUN'); mo.energy = P['moonE']; mo.color = P['moon']; mo.angle = math.radians(0.6)
moo = bpy.data.objects.new('moon', mo); sc.collection.objects.link(moo); moo.rotation_euler = (math.radians(70), 0, math.radians(200))

bpy.ops.mesh.primitive_cube_add(location=(0, 120, 1.5)); fog = bpy.context.object; fog.scale = (160, 130, 2.0)   # bottom below the ground (no coplanar faces)
fm = bpy.data.materials.new('fog'); fm.use_nodes = True; fn = fm.node_tree.nodes; fn.remove(fn['Principled BSDF'])
pvol = fn.new('ShaderNodeVolumePrincipled'); pvol.inputs['Density'].default_value = 0.006; pvol.inputs['Color'].default_value = (*P['fog'], 1)
fm.node_tree.links.new(pvol.outputs[0], fn['Material Output'].inputs['Volume']); fog.data.materials.append(fm)
fog.visible_shadow = False

ffm = bpy.data.materials.new('fly'); ffm.use_nodes = True; fnn = ffm.node_tree.nodes; fnn.remove(fnn['Principled BSDF'])
fe = fnn.new('ShaderNodeEmission'); fe.inputs['Color'].default_value = (*P['fly'], 1); fe.inputs['Strength'].default_value = 60
ffm.node_tree.links.new(fe.outputs[0], fnn['Material Output'].inputs['Surface'])
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.005); flyme = bpy.context.object.data; flyme.materials.append(ffm)
bpy.data.objects.remove(bpy.context.object)
FLY = []
for i in range(90):
    yy = rng.uniform(1.0, 30.0); o = bpy.data.objects.new(f'fly{i}', flyme); sc.collection.objects.link(o)
    o.location = (rng.uniform(-0.7, 0.7) * (0.8 * yy + 1), yy, rng.uniform(0.12, 1.3)); FLY.append(o)

bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=3.2, depth=60); met = bpy.context.object
mm = bpy.data.materials.new('met'); mm.use_nodes = True; mn = mm.node_tree.nodes; mn.remove(mn['Principled BSDF'])
mtc = mn.new('ShaderNodeTexCoord'); msx = mn.new('ShaderNodeSeparateXYZ'); mm.node_tree.links.new(mtc.outputs['Generated'], msx.inputs[0])
mpw = mn.new('ShaderNodeMath'); mpw.operation = 'POWER'; mpw.inputs[1].default_value = 3.0; mm.node_tree.links.new(msx.outputs['Z'], mpw.inputs[0])
mml = mn.new('ShaderNodeMath'); mml.operation = 'MULTIPLY'; mml.inputs[1].default_value = 40.0; mm.node_tree.links.new(mpw.outputs[0], mml.inputs[0])
mem = mn.new('ShaderNodeEmission')
mcr = mn.new('ShaderNodeValToRGB'); mm.node_tree.links.new(msx.outputs['Z'], mcr.inputs['Fac'])
mcr.color_ramp.elements[0].color = (0.55, 0.1, 1.0, 1); mcr.color_ramp.elements[1].color = (0.85, 0.97, 1.0, 1)
_e = mcr.color_ramp.elements.new(0.6); _e.color = (0.1, 0.6, 1.0, 1)
mm.node_tree.links.new(mcr.outputs['Color'], mem.inputs['Color'])
mm.node_tree.links.new(mml.outputs[0], mem.inputs['Strength']); mm.node_tree.links.new(mem.outputs[0], mn['Material Output'].inputs['Surface'])
met.data.materials.append(mm); met.visible_shadow = False; met.visible_diffuse = False; met.visible_glossy = False


def place_meteor(head_dir, travel_dir, dist=900.0, show=True):
    met.hide_render = not show
    hd = Vector(head_dir).normalized(); td = Vector(travel_dir).normalized()
    met.location = hd * dist - td * 30.0 * met.scale.z
    met.rotation_euler = td.to_track_quat('Z', 'Y').to_euler()


cd = bpy.data.cameras.new('cam'); cd.lens = 26; cd.sensor_width = 36; cd.sensor_fit = 'HORIZONTAL'
cd.dof.use_dof = True; cd.dof.aperture_fstop = 4.0; cd.clip_start = 0.02; cd.clip_end = 2000
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam

ORIGIN = np.array([9.0, 140.0])


F_BPH = rng.uniform(0, 2 * math.pi, nF)


def set_field(R, residual=None, mask=None, gmul=1.0, t=0.0):
    residual = P['res'] if residual is None else residual
    d = np.hypot(FP[:, 0] - ORIGIN[0], FP[:, 1] - ORIGIN[1]) + F_ph
    x = np.clip((R - d) / 5.0, 0, 1); o = x * x * (3 - 2 * x)
    breath = (0.05 + 0.05 * np.sin(1.6 * t + F_BPH)) * (1 - o)
    glow = (1.3 * np.exp(-((R - d) / 2.2) ** 2) * (d < R + 3) + residual * o + breath) * gmul
    state = np.round(o * (NS - 1)).astype(np.int32); scl = F_scl0.copy()
    if mask is not None:
        scl[mask] = 0.0
    me = FOB.data
    me.attributes['state'].data.foreach_set('value', state); me.attributes['scl'].data.foreach_set('value', scl)
    me.attributes['glow'].data.foreach_set('value', glow.astype(np.float32)); me.update()


def look(pos, pitch, yaw=0.0, lens=26, focus=3.0, fstop=4.0):
    cam.location = pos; cam.rotation_euler = (math.radians(90 + pitch), 0, math.radians(yaw))
    cd.lens = lens; cd.dof.focus_distance = focus; cd.dof.aperture_fstop = fstop


for s in SHOTS:
    if s not in ('A', 'B', 'C'):
        continue
    hero.hide_render = True; hero['glow'] = 0.0
    if s == 'A':
        set_field(-50); place_meteor((0.3, 1.0, 0.42), (0.45, 0.1, -0.35))
        look((0, 0, 1.3), -12, lens=24, focus=4.0)
    elif s == 'B':
        R = float(np.hypot(*ORIGIN)) - 5.5
        set_field(R); place_meteor((0, 1, 0), (1, 0, 0), show=False)
        look((0, 0, 1.3), -12, lens=24, focus=5.0)
    elif s == 'C':
        m = (np.hypot(FP[:, 0] - HERO.x, FP[:, 1] - HERO.y) < 0.18) | ((np.abs(FP[:, 0]) < 0.22) & (FP[:, 1] > 2.6) & (FP[:, 1] < 3.6))
        set_field(400.0, mask=m); place_meteor((0, 1, 0), (1, 0, 0), show=False)
        hero.hide_render = False; hero['glow'] = 0.55
        look((0.0, 2.95, 0.62), -14, lens=32, focus=0.82, fstop=2.2)
    sc.render.filepath = f'{OUT}/{PAL}_{s}.png'
    bpy.ops.render.render(write_still=True)
    print('shot', s, flush=True)


# ------------------------------------------------------------------ compositor bloom: soft glow around every light source
def _bloom():
    sc.render.use_compositing = True
    if hasattr(sc, 'compositing_node_group'):
        ng = bpy.data.node_groups.new('comp', 'CompositorNodeTree'); sc.compositing_node_group = ng
        ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = ng.nodes.new('CompositorNodeRLayers'); out = ng.nodes.new('NodeGroupOutput'); out_in = out.inputs[0]
    else:
        sc.use_nodes = True; ng = sc.node_tree; rl = ng.nodes['Render Layers']; out_in = ng.nodes['Composite'].inputs[0]
    g = ng.nodes.new('CompositorNodeGlare')
    try:
        g.glare_type = 'BLOOM'
    except Exception:
        try:
            g.inputs['Type'].default_value = 'Bloom'
        except Exception as e:
            print('glare type', e)
    for k, v in (('Threshold', 0.6), ('Strength', 0.55), ('Size', 0.7), ('Saturation', 1.15)):
        if k in g.inputs:
            try:
                g.inputs[k].default_value = v
            except Exception:
                pass
    for attr, v in (('threshold', 0.6), ('mix', -0.35), ('size', 8), ('quality', 'HIGH')):
        if hasattr(g, attr):
            try:
                setattr(g, attr, v)
            except Exception:
                pass
    ng.links.new(rl.outputs['Image'], g.inputs[0]); ng.links.new(g.outputs[0], out_in)
    print('bloom ok', [i.name for i in g.inputs], flush=True)


try:
    _bloom()
except Exception as e:
    print('bloom failed', e, flush=True)
