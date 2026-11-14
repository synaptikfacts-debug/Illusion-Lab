# 0016 Midnight Bloom - animation driver (story v3). Builds the scene from bloom.py, then animates it.
# usage: blender -b -P anim.py -- OUT W H SPP PALETTE none T0 T1 [STEP]
# 0.0  macro: one glowing bud trembling, light leaking through its petals (hook)
# 0.9  it bursts open toward the lens, pollen cloud          1.6 a spark lifts out of its centre
# 2.4  spark rises, camera pulls back: a dark field of sleeping buds under the aurora
# 4.4  spark reaches the sky and flashes - the sky answers with a shooting star
# 5.7  impact on the horizon, a wave of light blooms the whole field in colour
# 9.6  camera swoops low over the living field, passing the first flower
# 13   the field gives its light back: motes rise, camera tilts to the sky, aurora flares, new stars   16-17 fade
import os, sys, math
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bloom.py')).read())
from mathutils import Matrix

T0, T1 = float(a[6]), float(a[7]); STEP = int(a[8]) if len(a) > 8 else 1
FPS = 60; END = 17.0
sc.render.fps = FPS


def sm(a_, b_, v):
    x = min(max((v - a_) / (b_ - a_), 0.0), 1.0); return x * x * (3 - 2 * x)


def lerp(p, q, k): return p * (1 - k) + q * k


def emat(name, col, k):
    m_ = bpy.data.materials.new(name); m_.use_nodes = True; nn = m_.node_tree.nodes; nn.remove(nn['Principled BSDF'])
    e_ = nn.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (*col, 1); e_.inputs['Strength'].default_value = k
    m_.node_tree.links.new(e_.outputs[0], nn['Material Output'].inputs['Surface']); return m_


hero.hide_render = True                       # the simple hero from bloom.py is replaced by a detailed one

# ================================================================ detailed hero flower
HERO = Vector((0.0, 4.0, 0.0)); HSC = 1.5
HROT = Euler((math.radians(24), 0, 0.3))
HM = Matrix.Translation(HERO) @ HROT.to_matrix().to_4x4() @ Matrix.Scale(HSC, 4)


def hmat_petal():
    m = bpy.data.materials.new('hpetal'); m.use_nodes = True; N_ = m.node_tree.nodes; L_ = m.node_tree.links
    bs = N_['Principled BSDF']; bs.inputs['Roughness'].default_value = 0.38
    pa = N_.new('ShaderNodeAttribute'); pa.attribute_name = 'pu'
    cr = N_.new('ShaderNodeValToRGB'); L_.new(pa.outputs['Fac'], cr.inputs['Fac'])
    el = cr.color_ramp.elements; el[0].color = (0.55, 0.92, 1.0, 1); el[1].color = (0.62, 0.1, 1.0, 1)
    e2 = el.new(0.45); e2.color = (0.12, 0.3, 1.0, 1)
    L_.new(cr.outputs['Color'], bs.inputs['Base Color'])
    tr = N_.new('ShaderNodeBsdfTranslucent'); L_.new(cr.outputs['Color'], tr.inputs['Color'])
    mx = N_.new('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.45; L_.new(bs.outputs[0], mx.inputs[1]); L_.new(tr.outputs[0], mx.inputs[2])
    og = N_.new('ShaderNodeAttribute'); og.attribute_type = 'OBJECT'; og.attribute_name = 'glow'
    pg = N_.new('ShaderNodeMapRange'); L_.new(pa.outputs['Fac'], pg.inputs['Value']); pg.inputs['To Min'].default_value = 1.8; pg.inputs['To Max'].default_value = 0.45
    m1 = N_.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; L_.new(og.outputs['Fac'], m1.inputs[0]); L_.new(pg.outputs[0], m1.inputs[1])
    m2 = N_.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; L_.new(m1.outputs[0], m2.inputs[0]); m2.inputs[1].default_value = 6.0
    em = N_.new('ShaderNodeEmission'); L_.new(cr.outputs['Color'], em.inputs['Color']); L_.new(m2.outputs[0], em.inputs['Strength'])
    ad = N_.new('ShaderNodeAddShader'); L_.new(mx.outputs[0], ad.inputs[0]); L_.new(em.outputs[0], ad.inputs[1])
    L_.new(ad.outputs[0], N_['Material Output'].inputs['Surface'])
    return m


def hmat_centre():
    m = bpy.data.materials.new('hcentre'); m.use_nodes = True; N_ = m.node_tree.nodes; L_ = m.node_tree.links
    bs = N_['Principled BSDF']; bs.inputs['Base Color'].default_value = (1.0, 0.6, 0.12, 1); bs.inputs['Roughness'].default_value = 0.55
    tc_ = N_.new('ShaderNodeTexCoord'); vo = N_.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 1100
    L_.new(tc_.outputs['Object'], vo.inputs['Vector'])
    bp = N_.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.7; L_.new(vo.outputs['Distance'], bp.inputs['Height'])
    L_.new(bp.outputs['Normal'], bs.inputs['Normal'])
    og = N_.new('ShaderNodeAttribute'); og.attribute_type = 'OBJECT'; og.attribute_name = 'glow'
    mm_ = N_.new('ShaderNodeMath'); mm_.operation = 'MULTIPLY'; L_.new(og.outputs['Fac'], mm_.inputs[0]); mm_.inputs[1].default_value = 9.0
    em = N_.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (1.0, 0.62, 0.18, 1); L_.new(mm_.outputs[0], em.inputs['Strength'])
    ad = N_.new('ShaderNodeAddShader'); L_.new(bs.outputs[0], ad.inputs[0]); L_.new(em.outputs[0], ad.inputs[1])
    L_.new(ad.outputs[0], N_['Material Output'].inputs['Surface'])
    return m


HPET, HCEN = hmat_petal(), hmat_centre()
DEWK = (2, 6, 11, 15, 19)


def hero_mesh(e, tt):
    V = []; F = []; MI = []; U = []; dew = []

    def grid(pts, nu, nv, mi, us=None):
        b_ = len(V); V.extend(pts); U.extend(us if us is not None else [0.0] * len(pts))
        for i in range(nu - 1):
            for j in range(nv - 1):
                F.append((b_ + i * nv + j, b_ + (i + 1) * nv + j, b_ + (i + 1) * nv + j + 1, b_ + i * nv + j + 1)); MI.append(mi)

    pr_ = random.Random(5)
    c0 = Vector((0, 0, HH))
    for layer, (NPl, Lp0, Wd, dly, r0, ph0) in enumerate(((22, 0.05, 0.0078, 0.0, 0.0085, 0.0), (14, 0.036, 0.0062, 0.16, 0.0062, math.pi / 14))):
        for k in range(NPl):
            jit = pr_.uniform(-1, 1)
            ek = min(max((e - dly - 0.06 * (jit + 1) / 2) / (1 - dly - 0.06), 0.0), 1.0); ek = ek * ek * (3 - 2 * ek)
            phi = ph0 + 2 * math.pi * k / NPl + 0.05 * jit
            trem = math.radians(2.5) * math.sin(tt * 23 + k * 1.7) * (1 - ek) * (1.0 if e > 0.02 else 0.0)
            ang = math.radians(84 - 94 * ek + 4 * jit) + trem
            Lp = Lp0 * (0.8 + 0.2 * ek) * (1 + 0.06 * jit)
            r = Vector((math.cos(phi), math.sin(phi), 0)); s = Vector((-math.sin(phi), math.cos(phi), 0)); z = Vector((0, 0, 1))
            dr = r * math.cos(ang) + z * math.sin(ang); nr = -r * math.sin(ang) + z * math.cos(ang)
            pts = []; us = []; nu, nv = 12, 5
            for i in range(nu):
                u = i / (nu - 1)
                w = Wd * max(math.sin(math.pi * (0.08 + 0.92 * u)), 0.0) ** 0.55
                for j in range(nv):
                    v = -1 + 2 * j / (nv - 1)
                    lu = Lp * u * (1 - 0.06 * (1 - abs(v)) * u ** 8)
                    cup = 0.18 * Lp * u * u * (1 - 0.5 * ek) - 0.07 * Lp * u ** 3 * ek + 0.22 * w * v * v
                    p = c0 + r * r0 + dr * lu + nr * (cup + 0.002 * layer) + s * (w * v)
                    pts.append(p); us.append(u)
                    if layer == 0 and k in DEWK and i == 7 and j == 3:
                        dew.append(p + nr * 0.0019)
            grid(pts, nu, nv, 0, us)
    nl, nm = 9, 30; pts = []
    for i in range(nl):
        th = (math.pi / 2) * i / (nl - 1)
        for j in range(nm + 1):
            ph = 2 * math.pi * j / nm; rr = 0.0118 * math.cos(th) + 0.0002
            pts.append(c0 + Vector((rr * math.cos(ph), rr * math.sin(ph), 0.0008 + 0.0068 * (0.6 + 0.4 * e) * math.sin(th))))
    grid(pts, nl, nm + 1, 1)
    pts = []
    for i in range(9):
        zz = HH * i / 8; off = 0.012 * math.sin(math.pi * zz / HH * 0.5)
        for j in range(9):
            ph = 2 * math.pi * j / 8
            pts.append(Vector((off * 0.0 + 0.0028 * math.cos(ph), 0.0028 * math.sin(ph), zz)))
    grid(pts, 9, 9, 2)
    me = bpy.data.meshes.new('heroM'); me.from_pydata([tuple(p) for p in V], [], F)
    for m in (HPET, HCEN, M_STM):
        me.materials.append(m)
    me.polygons.foreach_set('material_index', MI)
    me.attributes.new('pu', 'FLOAT', 'POINT').data.foreach_set('value', U)
    me.shade_smooth()
    return me, dew


hero2 = bpy.data.objects.new('hero2', hero_mesh(0.1, 0.0)[0]); sc.collection.objects.link(hero2)
hero2.location = HERO; hero2.rotation_euler = HROT; hero2.scale = (HSC,) * 3; hero2['glow'] = 0.0
HC = HM @ Vector((0, 0, HH + 0.005))
core = bpy.data.lights.new('core', 'POINT'); core.color = (0.5, 0.85, 1.0); core.shadow_soft_size = 0.004
coreo = bpy.data.objects.new('core', core); coreo.location = HC; sc.collection.objects.link(coreo)
dewm = bpy.data.materials.new('dew'); dewm.use_nodes = True; db = dewm.node_tree.nodes['Principled BSDF']
db.inputs['Transmission Weight'].default_value = 1.0; db.inputs['IOR'].default_value = 1.33; db.inputs['Roughness'].default_value = 0.02
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0); dewme = bpy.context.object.data; dewme.materials.append(dewm)
bpy.ops.object.shade_smooth(); bpy.data.objects.remove(bpy.context.object)
DEW = []
for i in range(len(DEWK)):
    o = bpy.data.objects.new(f'dew{i}', dewme); sc.collection.objects.link(o); o.scale = (0.0017 * HSC * (0.8 + 0.1 * i),) * 3; DEW.append(o)

mask = np.hypot(FP[:, 0] - HERO.x, FP[:, 1] - HERO.y) < 0.3

# ================================================================ majestic trees (glowing canopies, light up as the wave reaches them)
def _rot_about(v, axis, ang):
    return (Matrix.Rotation(ang, 3, axis.normalized()) @ v)


def make_tree(seed, H):
    tr = random.Random(seed)
    V = []; F = []; LEAF = []
    up = Vector((0, 0, 1))

    def ring_basis(d):
        a_ = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
        u_ = d.cross(a_).normalized(); w_ = d.cross(u_).normalized(); return u_, w_

    def grow(p, d, L, r, depth, maxd):
        NSg = 6 if depth < 2 else 4; NR = 10 if depth < 2 else 6
        path = []; cur = p.copy(); dd = d.normalized(); base = len(V)
        for i in range(NSg + 1):
            rr = r * (1 - 0.38 * i / NSg)
            u_, w_ = ring_basis(dd)
            for j in range(NR):
                ph = 2 * math.pi * j / NR
                V.append(tuple(cur + (u_ * math.cos(ph) + w_ * math.sin(ph)) * rr))
            path.append((cur.copy(), dd.copy(), rr))
            if i < NSg:
                jit = Vector((tr.gauss(0, 1), tr.gauss(0, 1), tr.gauss(0, 1))) * 0.14
                dd = (dd + jit + up * (0.05 if depth > 0 else 0.08)).normalized(); cur = cur + dd * (L / NSg)
        for i in range(NSg):
            for j in range(NR):
                a0 = base + i * NR + j; b0 = base + i * NR + (j + 1) % NR
                F.append((a0, b0, b0 + NR, a0 + NR))
        if depth >= maxd:
            for k in range(28):
                q = path[-1][0] + Vector((tr.gauss(0, 1), tr.gauss(0, 1), tr.gauss(0, 0.7))) * (0.55 * H / 30 + 0.25)
                LEAF.append(tuple(q))
            for (pp, _, _) in path[NSg // 2:-1]:
                for k in range(5):
                    LEAF.append(tuple(pp + Vector((tr.gauss(0, 1), tr.gauss(0, 1), tr.gauss(0, 0.6))) * 0.4 * (H / 30 + 0.4)))
            return
        nch = 3 if depth == 0 else tr.choice((2, 3, 3))
        for c in range(nch):
            idx = tr.randint(NSg // 2 if depth == 0 else 2, NSg)
            pp, pd, pr_ = path[idx]
            az = 2 * math.pi * c / nch + tr.uniform(-0.5, 0.5)
            u_, w_ = ring_basis(pd)
            side = (u_ * math.cos(az) + w_ * math.sin(az))
            ang = math.radians(tr.uniform(38, 62) if depth == 0 else tr.uniform(28, 50))
            nd = (pd * math.cos(ang) + side * math.sin(ang)).normalized()
            nd = (nd + Vector((nd.x, nd.y, 0)) * 0.25).normalized()
            grow(pp, nd, L * tr.uniform(0.62, 0.78), pr_ * 0.72, depth + 1, maxd)

    grow(Vector((0, 0, -0.3)), Vector((0, 0, 1)), 0.34 * H, 0.03 * H, 0, 5)
    me = bpy.data.meshes.new(f'tree{seed}'); me.from_pydata(V, [], F)
    try:
        me.shade_smooth()
    except Exception:
        pass
    return me, np.array(LEAF, np.float32)


bark = bpy.data.materials.new('bark'); bark.use_nodes = True; bkn = bark.node_tree.nodes; bkl = bark.node_tree.links
bkb = bkn['Principled BSDF']; bkb.inputs['Base Color'].default_value = (0.03, 0.026, 0.04, 1); bkb.inputs['Roughness'].default_value = 0.85
bkt = bkn.new('ShaderNodeTexNoise'); bkt.inputs['Scale'].default_value = 3.0; bkt.inputs['Detail'].default_value = 12
bkw = bkn.new('ShaderNodeTexWave'); bkw.inputs['Scale'].default_value = 1.2; bkw.inputs['Distortion'].default_value = 8; bkw.wave_type = 'BANDS'; bkw.bands_direction = 'Z'
bkm = bkn.new('ShaderNodeMath'); bkm.operation = 'MULTIPLY'; bkl.new(bkt.outputs['Fac'], bkm.inputs[0]); bkl.new(bkw.outputs['Fac'], bkm.inputs[1])
bkbump = bkn.new('ShaderNodeBump'); bkbump.inputs['Strength'].default_value = 0.8; bkl.new(bkm.outputs[0], bkbump.inputs['Height']); bkl.new(bkbump.outputs['Normal'], bkb.inputs['Normal'])


def leaf_mesh(k):
    lr = random.Random(100 + k); V = []; F = []
    for q in range(3):
        a0 = lr.uniform(0, math.pi); w = 0.16 + 0.05 * k; h = 0.1
        c, s_ = math.cos(a0), math.sin(a0); tilt = lr.uniform(-0.6, 0.6)
        b = len(V)
        for (x, z) in ((-w, -h), (w, -h), (w, h), (-w, h)):
            V.append((x * c, x * s_, z + x * tilt * 0.3))
        F.append((b, b + 1, b + 2, b + 3))
    me = bpy.data.meshes.new(f'leaf{k}'); me.from_pydata(V, [], F); me.materials.append(M_LEAF); return me


M_LEAF = principled('leafm', (0.02, 0.06, 0.18), 0.5, 0.5, True, P['glow'], 4.0, ramp=P['ramp'])
_lb = M_LEAF.node_tree.nodes['Principled BSDF'].inputs['Base Color']
for _lk in list(_lb.links):
    M_LEAF.node_tree.links.remove(_lk)
_lb.default_value = (0.012, 0.03, 0.06, 1)
LFV = src_collection('lfv', [leaf_mesh(k) for k in range(3)])
TREES = [(4.0, 118.0, 30.0, 1), (-10.0, 24.0, 15.0, 2), (12.0, 33.0, 17.0, 3), (-26.0, 55.0, 18.0, 4), (30.0, 70.0, 20.0, 5),
         (-45.0, 95.0, 22.0, 6), (50.0, 110.0, 22.0, 7), (-70.0, 150.0, 20.0, 8), (80.0, 160.0, 22.0, 9), (-30.0, 172.0, 18.0, 10)]
TLEAF = []
for (tx, ty, th, sd) in TREES:
    me, lp_ = make_tree(sd, th)
    ob = bpy.data.objects.new(f'tree{sd}', me); ob.data.materials.append(bark); ob.location = (tx, ty, 0); ob.rotation_euler = (0, 0, sd * 1.3)
    sc.collection.objects.link(ob)
    Rz = Matrix.Rotation(sd * 1.3, 3, 'Z')
    wl = np.array([tuple(Rz @ Vector(tuple(p))) for p in lp_], np.float32) + np.array([tx, ty, 0], np.float32)
    nL = len(wl)
    lrot = np.stack([rng.uniform(-0.6, 0.6, nL), rng.uniform(-0.6, 0.6, nL), rng.uniform(0, 6.28, nL)], 1)
    lob = instancer(f'leaves{sd}', LFV, wl, rng.integers(0, 3, nL).astype(np.int32), lrot, rng.uniform(0.8, 1.5, nL) * (th / 20.0) ** 0.5, np.zeros(nL))
    TLEAF.append(dict(ob=lob, pts=wl, rot=lrot, zf=np.clip(wl[:, 2] / th, 0, 1), ph=rng.uniform(0, 6.28, nL), x=tx, y=ty, h=th))
    mask_tree = np.hypot(FP[:, 0] - tx, FP[:, 1] - ty) < 0.06 * th + 0.6
    mask = mask | mask_tree
print('trees', [len(d['pts']) for d in TLEAF], flush=True)


def trees_update(t):
    for d in TLEAF:
        tp = 5.85 if d['h'] >= 30 else float(t_pass(math.hypot(d['x'] - ORIGIN[0], d['y'] - ORIGIN[1])))
        tz = tp + 0.9 * d['zf']
        g = 0.9 * np.exp(-((t - tz) / 0.35) ** 2) * (t > tz - 1.0) + 0.28 * np.clip((t - tz) / 0.4, 0, 1)
        g *= (1 - 0.6 * sm(15.0, 17.0, t))
        me = d['ob'].data
        me.attributes['glow'].data.foreach_set('value', g.astype(np.float32))
        r = d['rot'].copy(); r[:, 0] += 0.08 * np.sin(1.3 * t + d['ph']); r[:, 1] += 0.08 * np.sin(1.1 * t + d['ph'] * 1.7)
        me.attributes['rot'].data.foreach_set('vector', r.astype(np.float32).ravel()); me.update()


# ================================================================ the spark
sparkm = emat('spark', (0.7, 0.95, 1.0), 260.0)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0); spme = bpy.context.object.data; spme.materials.append(sparkm)
bpy.data.objects.remove(bpy.context.object)
SPARK = []
for i in range(32):
    o = bpy.data.objects.new(f'spark{i}', spme); sc.collection.objects.link(o); o.visible_shadow = False; SPARK.append(o)
spl = bpy.data.lights.new('sparkL', 'POINT'); spl.color = (0.6, 0.9, 1.0); spl.shadow_soft_size = 0.003
splo = bpy.data.objects.new('sparkL', spl); sc.collection.objects.link(splo)
SP_END = HC + Vector((0.0, 70.0, 24.0))


def spark_pos(t):
    if t < 1.6:
        return None
    if t < 2.4:
        return HC + Vector((0, 0, 0.13 * sm(1.6, 2.4, t)))
    s_ = min((t - 2.4) / 2.0, 1.0); g = s_ ** 2.4
    return HC + Vector((0, 0, 0.13)) + (SP_END - HC - Vector((0, 0, 0.13))) * g


# ================================================================ camera path
def macro_pos(t):
    u = min(t / 2.6, 1.0)
    Rm = 0.2 - 0.03 * sm(0.0, 1.4, t); el = math.radians(30 - 4 * u); az = math.radians(-20 + 14 * u)
    return HC + Vector((Rm * math.cos(el) * math.sin(az), -Rm * math.cos(el) * math.cos(az), Rm * math.sin(el)))


TT = np.linspace(0, END, 3401)
VV = np.array([1.15 * sm(9.4, 10.8, x) - 0.75 * sm(13.3, 15.5, x) for x in TT])
GL = np.concatenate([[0], np.cumsum((VV[1:] + VV[:-1]) / 2 * np.diff(TT))])


def wide_pos(t):
    y = HERO.y - 3.6 + 0.25 * (t - 2.2) + float(np.interp(t, TT, GL))
    z = 1.35 - 0.6 * sm(9.6, 12.0, t) + 0.35 * sm(13.2, 15.4, t)
    x = 0.34 * sm(9.6, 12.0, t) + 0.05 * math.sin(0.5 * t)
    return Vector((x, y, z))


def wide_pitch(t): return -6 + 30 * sm(2.6, 3.9, t) * (1 - sm(4.2, 5.4, t)) - 6 * sm(9.6, 12.0, t) + 52 * sm(13.2, 15.4, t)


def cam_state(t):
    k1 = sm(2.2, 4.6, t)
    c = lerp(macro_pos(t), wide_pos(t), k1)
    p = math.radians(wide_pitch(t))
    wt = c + Vector((0, 10 * math.cos(p), 10 * math.sin(p)))
    sp = spark_pos(t)
    near = lerp(HC, sp if sp is not None else HC, sm(1.6, 2.3, t))
    tgt = lerp(near, wt, sm(2.6, 3.8, t))
    lens = 50 - 26 * k1
    fd = lerp((near - c).length, 5.0, k1) * (1 - sm(9.6, 11, t)) + 2.6 * sm(9.6, 11, t) * (1 - sm(13.2, 15, t)) + 8.0 * sm(13.2, 15, t)
    fs = 2.4 + 2.8 * k1 - 1.2 * sm(9.6, 11, t)
    return c, tgt, lens, fd, fs


# ================================================================ the wave
D0 = float(np.hypot(ORIGIN[0], ORIGIN[1] - 1.5)); TW = 5.7
TG = np.linspace(0, END, 3401)


def R_of(t):
    if t < TW:
        return -60.0
    return D0 - 150.0 * math.exp(-(t - TW) / 0.8) + 9.0 * max(t - 9.7, 0.0)


RGm = np.maximum.accumulate(np.array([R_of(x) for x in TG]))


def t_pass(dist):
    return np.interp(dist, RGm + np.arange(len(RGm)) * 1e-6, TG, left=0.0, right=99.0)


# ================================================================ wind
F_rx, F_ry = F_rot[:, 0].copy(), F_rot[:, 1].copy()
G_rx, G_ry = G_rot[:, 0].copy(), G_rot[:, 1].copy()
F_wp = rng.uniform(0, 2 * math.pi, nF); G_wp = rng.uniform(0, 2 * math.pi, nG)


def wind(t):
    gust = 0.6 + 0.4 * np.sin(0.45 * t - 0.07 * FP[:, 1] + 0.05 * FP[:, 0])
    rx = F_rx + 0.07 * gust * np.sin(1.25 * t + 0.31 * FP[:, 0] + 0.17 * FP[:, 1] + F_wp)
    ry = F_ry + 0.06 * gust * np.sin(1.05 * t + 0.27 * FP[:, 1] + F_wp * 1.3)
    FOB.data.attributes['rot'].data.foreach_set('vector', np.stack([rx, ry, F_rot[:, 2]], 1).astype(np.float32).ravel()); FOB.data.update()
    gg = 0.6 + 0.4 * np.sin(0.45 * t - 0.07 * GP[:, 1])
    gx = G_rx + 0.11 * gg * np.sin(1.4 * t + 0.33 * GP[:, 0] + 0.2 * GP[:, 1] + G_wp)
    gy = G_ry + 0.09 * gg * np.sin(1.15 * t + 0.29 * GP[:, 1] + G_wp)
    GOB.data.attributes['rot'].data.foreach_set('vector', np.stack([gx, gy, G_rot[:, 2]], 1).astype(np.float32).ravel()); GOB.data.update()


# ================================================================ fireflies (gold + cyan)
ffm.node_tree.nodes['Emission'].inputs['Color'].default_value = (1.0, 0.72, 0.22, 1)
fly_c = flyme.copy(); fly_c.materials[0] = emat('flyc', (0.2, 0.85, 1.0), 70)
for i in range(170):
    yy = rng.uniform(0.6, 26.0); o = bpy.data.objects.new(f'flyc{i}', fly_c if i % 2 else flyme); sc.collection.objects.link(o)
    o.location = (rng.uniform(-0.7, 0.7) * (0.8 * yy + 1), yy, rng.uniform(0.1, 1.6)); FLY.append(o)
for o in FLY:
    o.visible_shadow = False
    if math.hypot(o.location.x - HERO.x, o.location.y - HERO.y) < 0.6:
        o.location.y += 1.2
FB = np.array([tuple(o.location) for o in FLY]); FPH = rng.uniform(0, 2 * math.pi, (len(FLY), 4))
FTP = t_pass(np.hypot(FB[:, 0] - ORIGIN[0], FB[:, 1] - ORIGIN[1]))

# ================================================================ motes: pollen from the wave, the hero's burst, and the final ascent
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.0035); m0 = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
MOTE = []
for nm_, col_ in (('mc', (0.15, 0.75, 1.0)), ('mv', (0.6, 0.2, 1.0)), ('mm', (1.0, 0.3, 0.8)), ('mg', (1.0, 0.7, 0.25))):
    mm_ = m0.copy(); mm_.materials.append(emat(nm_, col_, 45)); MOTE.append(mm_)


def motes(n_, prefix):
    out = []
    for i in range(n_):
        o = bpy.data.objects.new(f'{prefix}{i}', MOTE[i % 4]); sc.collection.objects.link(o); o.hide_render = True; o.visible_shadow = False; out.append(o)
    return out


NPOL = 700
PY = rng.uniform(0.6, 24.0, NPOL); PX = rng.uniform(-1, 1, NPOL) * (0.75 * PY + 0.8); PZ = rng.uniform(0.3, 0.45, NPOL)
PT = t_pass(np.hypot(PX - ORIGIN[0], PY - ORIGIN[1])) + rng.uniform(0.0, 0.35, NPOL)
PV = rng.uniform(0.18, 0.4, NPOL); PPH = rng.uniform(0, 2 * math.pi, (NPOL, 2)); PS = rng.uniform(0.6, 1.4, NPOL)
POL = motes(NPOL, 'pol')
NB = 170                                                   # the hero's burst, mostly toward the lens and up
bd = rng.normal(0, 1, (NB, 3)); bd[:, 1] = -np.abs(bd[:, 1]) * 0.7; bd[:, 2] = np.abs(bd[:, 2]) + 0.3
bd /= np.linalg.norm(bd, axis=1)[:, None]; BV = bd * rng.uniform(0.05, 0.2, NB)[:, None]
BT = 1.0 + rng.uniform(0, 0.35, NB); BS = rng.uniform(0.25, 0.6, NB); BPH = rng.uniform(0, 6.28, NB)
BUR = motes(NB, 'bur')
NA = 900                                                   # the ascent: the field gives its light back to the sky
AY = rng.uniform(1.0, 30.0, NA); AX = rng.uniform(-1, 1, NA) * (0.8 * AY + 1.0); AZ = rng.uniform(0.3, 0.5, NA)
AT = 12.8 + rng.uniform(0, 1.9, NA); AV = rng.uniform(0.25, 0.8, NA); AA = rng.uniform(0.6, 2.2, NA); AS = rng.uniform(2.5, 5.0, NA)
APH = rng.uniform(0, 6.28, NA)
ASC = motes(NA, 'asc')
NE = 520                                                   # the flower's fountain: rises right after it opens
er = rng.uniform(0, 1, NE) ** 1.6 * 1.6; ea = rng.uniform(0, 2 * math.pi, NE)
EX = HERO.x + er * np.cos(ea); EY = HERO.y + er * np.sin(ea) + 0.3; EZ = rng.uniform(0.35, 0.5, NE)
EX[:60] = HC.x + rng.normal(0, 0.01, 60); EY[:60] = HC.y + rng.normal(0, 0.01, 60); EZ[:60] = HC.z
ET = 1.15 + er * 0.9 + rng.uniform(0, 0.6, NE); EV = rng.uniform(0.3, 1.0, NE); EA = rng.uniform(0.8, 2.6, NE)
ES = rng.uniform(1.5, 3.5, NE); ES[:60] = rng.uniform(0.4, 0.9, 60); EPH = rng.uniform(0, 6.28, NE)
EAR = motes(NE, 'ear')

# ================================================================ impact burst + light-wave ribbon
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(ORIGIN[0], ORIGIN[1], 0.8)); burst = bpy.context.object
bm_ = emat('burst', (0.35, 0.6, 1.0), 0.0); burst.data.materials.append(bm_); BURST_E = bm_.node_tree.nodes['Emission'].inputs['Strength']
burst.visible_shadow = False
bl = bpy.data.lights.new('burstL', 'POINT'); bl.color = (0.4, 0.55, 1.0); bl.shadow_soft_size = 3.0
blo = bpy.data.objects.new('burstL', bl); blo.location = (ORIGIN[0], ORIGIN[1], 3.0); sc.collection.objects.link(blo)
NSEG = 720
rb = bpy.data.meshes.new('ribbon'); ang_ = np.linspace(0, 2 * math.pi, NSEG, endpoint=False); rv = np.zeros((NSEG * 2, 3), np.float32)
rb.vertices.add(NSEG * 2); rb.loops.add(NSEG * 4); rb.polygons.add(NSEG)
lo_ = []
for i in range(NSEG):
    j = (i + 1) % NSEG; lo_ += [i, j, NSEG + j, NSEG + i]
rb.loops.foreach_set('vertex_index', lo_); rb.polygons.foreach_set('loop_start', list(range(0, NSEG * 4, 4))); rb.update(calc_edges=True)
rb.attributes.new('h', 'FLOAT', 'POINT').data.foreach_set('value', np.r_[np.zeros(NSEG), np.ones(NSEG)].astype(np.float32))
rib = bpy.data.objects.new('ribbon', rb); sc.collection.objects.link(rib); rib.visible_shadow = False
rm = bpy.data.materials.new('ribbon'); rm.use_nodes = True; rn = rm.node_tree.nodes; rl = rm.node_tree.links; rn.remove(rn['Principled BSDF'])
ra = rn.new('ShaderNodeAttribute'); ra.attribute_name = 'h'
rp = rn.new('ShaderNodeMath'); rp.operation = 'POWER'; rl.new(ra.outputs['Fac'], rp.inputs[0]); rp.inputs[1].default_value = 0.6
r1 = rn.new('ShaderNodeMath'); r1.operation = 'SUBTRACT'; r1.inputs[0].default_value = 1.0; rl.new(rp.outputs[0], r1.inputs[1])
rc = rn.new('ShaderNodeValToRGB'); rl.new(ra.outputs['Fac'], rc.inputs['Fac'])
rc.color_ramp.elements[0].color = (0.75, 0.95, 1.0, 1); rc.color_ramp.elements[1].color = (0.45, 0.15, 1.0, 1)
_r = rc.color_ramp.elements.new(0.35); _r.color = (0.1, 0.55, 1.0, 1)
re_ = rn.new('ShaderNodeEmission'); rl.new(rc.outputs['Color'], re_.inputs['Color'])
rk = rn.new('ShaderNodeMath'); rk.operation = 'MULTIPLY'; rl.new(r1.outputs[0], rk.inputs[0]); RIB_E = rk.inputs[1]; RIB_E.default_value = 0.0
rl.new(rk.outputs[0], re_.inputs['Strength'])
rtr = rn.new('ShaderNodeBsdfTransparent'); rad = rn.new('ShaderNodeAddShader')
rl.new(re_.outputs[0], rad.inputs[0]); rl.new(rtr.outputs[0], rad.inputs[1]); rl.new(rad.outputs[0], rn['Material Output'].inputs['Surface'])
rb.materials.append(rm)


def ribbon(R, strength):
    rib.hide_render = strength <= 0.001 or R <= 0.2
    if rib.hide_render:
        return
    x = ORIGIN[0] + R * np.cos(ang_); y = ORIGIN[1] + R * np.sin(ang_)
    rv[:NSEG, 0] = x; rv[:NSEG, 1] = y; rv[:NSEG, 2] = 0.02
    rv[NSEG:, 0] = x; rv[NSEG:, 1] = y; rv[NSEG:, 2] = 0.28 + 0.06 * np.sin(ang_ * 40 + R * 0.7)
    rb.vertices.foreach_set('co', rv.ravel()); rb.update()
    RIB_E.default_value = strength


# meteor: starts where the spark vanished, falls to the horizon
MT0, MT1 = 4.4, 5.7
_c44 = wide_pos(MT0)
S0 = (SP_END - _c44).normalized()
S1 = (Vector((ORIGIN[0], ORIGIN[1], 0.0)) - wide_pos(MT1)).normalized() + Vector((0, 0, 0.01))


def update(t):
    R = R_of(t)
    set_field(R, mask=mask, gmul=1.0 - 0.6 * sm(15.0, 17.0, t), t=t)
    wind(t)
    trees_update(t)
    # sky
    AUR_W.default_value = 0.05 * t; AUR_W2.default_value = 0.22 * t
    AUR_GAIN.outputs[0].default_value = 0.42 + 0.22 * sm(5.8, 7.0, t) + 0.45 * math.exp(-((t - 3.7) / 0.7) ** 2) + 0.5 * math.exp(-((t - 14.6) / 0.6) ** 2) - 0.25 * sm(15.8, 17.0, t)
    STARG.outputs[0].default_value = 1.0 + 0.6 * sm(3.0, 4.2, t) * (1 - sm(6.0, 7.5, t)) + 1.2 * sm(13.6, 15.6, t)
    mp.inputs['Rotation'].default_value = (0.0, 0.0, 0.012 * t)
    # hero flower: trembling bud -> bursts open
    e = 0.06 + 0.22 * sm(0.0, 0.9, t) + 0.72 * sm(0.85, 1.7, t)
    old = hero2.data; me, dew = hero_mesh(e, t); hero2.data = me; bpy.data.meshes.remove(old)
    hg = 0.3 - 0.1 * sm(0.9, 1.7, t) + 0.4 * math.exp(-((t - 1.15) / 0.3) ** 2) + 0.2 * math.exp(-((t - R_hero_t) / 0.4) ** 2)
    hero2['glow'] = hg * (1 - 0.5 * sm(15.0, 17.0, t))
    core.energy = 0.35 * (1 - sm(0.8, 1.6, t)) + 0.1
    for o, p in zip(DEW, dew):
        o.location = HM @ p
    # spark + trail
    sp = spark_pos(t)
    if sp is None or t > MT0 + 0.15:
        for o in SPARK:
            o.hide_render = True
        spl.energy = 0.0
    else:
        dist = (sp - cam_state(t)[0]).length
        flash = 1.0 + 4.0 * math.exp(-((t - MT0) / 0.12) ** 2)
        for i, o in enumerate(SPARK):
            q = spark_pos(max(t - i * 0.008, 1.6)); o.hide_render = False; o.location = q
            o.scale = (max(0.0035 * (1 - i / len(SPARK)) * max(1.0, dist * 1.2) * flash, 1e-5),) * 3
        splo.location = sp; spl.energy = 0.25 * (1 - sm(2.4, 3.2, t))
        sparkm.node_tree.nodes['Emission'].inputs['Strength'].default_value = 260.0 * min(max(dist / 5.0, 0.06), 1.0)
    # meteor
    if MT0 <= t < MT1:
        u = (t - MT0) / (MT1 - MT0); u = 1 - (1 - u) ** 1.4
        hd = (S0 * (1 - u) + S1 * u).normalized(); td = (S1 - S0).normalized()
        met.scale = (1.0, 1.0, 1.2 + 3.0 * min((t - MT0) / 0.4, 1.0)); place_meteor(hd, td)
        mml.inputs[1].default_value = 420.0 * (1 - sm(MT1 - 0.2, MT1, t))
    else:
        met.hide_render = True
    # impact burst + wave ribbon
    tb = MT1 + 0.1
    bu = math.exp(-((t - tb) / 0.28) ** 2) if t < tb else math.exp(-(t - tb) / 0.22)
    burst.hide_render = t < MT1 - 0.08 or bu < 0.02
    burst.scale = (0.6 + 2.0 * sm(MT1, MT1 + 0.4, t),) * 3; BURST_E.default_value = 60.0 * bu
    bl.energy = 6.0e6 * math.exp(-max(t - tb, 0) / 0.5) * (t > MT1 - 0.08)
    ribbon(R, 6.0 * sm(TW, TW + 0.35, t) * (1 - sm(D0 + 3.0, D0 + 14.0, R)))
    # fireflies
    for i, o in enumerate(FLY):
        lift = max(t - FTP[i], 0.0) + 0.6 * max(t - 13.0, 0.0) ** 1.5; ph = FPH[i]
        o.location = (FB[i, 0] + 0.15 * math.sin(0.6 * t + ph[0]), FB[i, 1] + 0.15 * math.sin(0.5 * t + ph[1]),
                      FB[i, 2] + 0.08 * math.sin(0.9 * t + ph[2]) + 0.22 * lift)
        o.scale = (0.55 + 0.45 * math.sin(3.1 * t + ph[3]) ** 2 + 0.6 * math.exp(-((t - FTP[i] - 0.2) / 0.3) ** 2),) * 3
    # wave pollen
    for i, o in enumerate(POL):
        u = t - PT[i]
        if u < 0 or u > 3.4:
            o.hide_render = True; continue
        o.hide_render = False
        o.location = (PX[i] + 0.05 * math.sin(2.1 * u + PPH[i, 0]) + 0.08 * u, PY[i] + 0.05 * math.sin(1.7 * u + PPH[i, 1]), PZ[i] + PV[i] * u)
        o.scale = (PS[i] * sm(0.0, 0.15, u) * (1 - sm(2.0, 3.4, u)) + 1e-4,) * 3
    # hero burst pollen
    for i, o in enumerate(BUR):
        u = t - BT[i]
        if u < 0 or u > 5.0:
            o.hide_render = True; continue
        o.hide_render = False
        dd = (1 - math.exp(-2.2 * u)) / 2.2
        o.location = HC + Vector(BV[i] * dd) + Vector((0.004 * math.sin(3 * u + BPH[i]), 0.0, 0.012 * u))
        o.scale = (BS[i] * sm(0.0, 0.08, u) * (1 - sm(3.5, 5.0, u)) + 1e-4,) * 3
    # the flower's fountain
    for i, o in enumerate(EAR):
        u = t - ET[i]
        if u < 0 or t > 7.6:
            o.hide_render = True; continue
        o.hide_render = False
        o.location = (EX[i] + 0.15 * math.sin(1.3 * u + EPH[i]) * u, EY[i] + 0.15 * math.cos(1.1 * u + EPH[i]) * u, EZ[i] + EV[i] * u + 0.5 * EA[i] * u * u)
        o.scale = (ES[i] * sm(0.0, 0.3, u) * (1.0 + 0.4 * math.sin(5 * u + EPH[i])) * (1 - sm(6.0, 7.5, t)) + 1e-4,) * 3
    # the ascent
    for i, o in enumerate(ASC):
        u = t - AT[i]
        if u < 0:
            o.hide_render = True; continue
        o.hide_render = False
        o.location = (AX[i] + 0.2 * math.sin(1.3 * u + APH[i]) * u, AY[i] + 0.2 * math.cos(1.1 * u + APH[i]) * u, AZ[i] + AV[i] * u + 0.5 * AA[i] * u * u)
        o.scale = (AS[i] * sm(0.0, 0.3, u) * (1.0 + 0.4 * math.sin(5 * u + APH[i])) + 1e-4,) * 3
    # camera
    c, tgt, lens, fd, fs = cam_state(t)
    cam.location = c; cam.rotation_euler = (tgt - c).to_track_quat('-Z', 'Y').to_euler()
    cd.lens = lens; cd.dof.focus_distance = fd; cd.dof.aperture_fstop = fs


R_hero_t = float(t_pass(np.hypot(HERO.x - ORIGIN[0], HERO.y - ORIGIN[1])))
os.makedirs(OUT, exist_ok=True)
for f in range(int(round(T0 * FPS)), int(round(T1 * FPS)), STEP):
    p = f'{OUT}/f{f:05d}.png'
    if os.path.exists(p):
        continue
    update(f / FPS)
    sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    print('frame', f, flush=True)
