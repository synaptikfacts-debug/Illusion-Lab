# extra effects for glass.py (exec'd inside glass.py namespace)
import random as _rnd
_rnd.seed(7)

# --- dark mirror floor far below: catches caustics + reflections ---
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -2.3))
_fl = bpy.context.object
_fm = bpy.data.materials.new('floor'); _fm.use_nodes = True
_fb = _fm.node_tree.nodes['Principled BSDF']
_fb.inputs['Base Color'].default_value = (0.006, 0.004, 0.01, 1); _fb.inputs['Roughness'].default_value = 0.12
_fb.inputs['Coat Weight'].default_value = 1.0; _fb.inputs['Coat Roughness'].default_value = 0.02
_fl.data.materials.append(_fm)

# rim strips stop showing as hard white bars in the glass, but keep lighting the gel
for _n in ('rimR', 'rimL'):
    bpy.data.objects[_n].visible_glossy = False

# --- splash crown droplets ---
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
_dm = bpy.context.object.data; _dm.materials.append(gel)
for _p in _dm.polygons:
    _p.use_smooth = True
bpy.data.objects.remove(bpy.context.object)
DROPS = []
for i in range(12):
    a_ = i / 12 * 2 * math.pi + _rnd.uniform(-0.15, 0.15)
    o = bpy.data.objects.new(f'd{i}', _dm); sc.collection.objects.link(o)
    DROPS.append(dict(o=o, a=a_, v=_rnd.uniform(1.0, 1.6), vz=_rnd.uniform(1.6, 2.4), r=_rnd.uniform(0.035, 0.065)))
# droplets that drip off the liquid bridge when it snaps under the pane
SNAP = 6.25
DRIPS = []
for i in range(5):
    o = bpy.data.objects.new(f'p{i}', _dm); sc.collection.objects.link(o)
    DRIPS.append(dict(o=o, x=_rnd.uniform(-0.06, 0.06), y=_rnd.uniform(-0.06, 0.06), r=_rnd.uniform(0.025, 0.05), d=i * 0.07))

# --- air bubbles trapped in the gel ---
_am = bpy.data.materials.new('air'); _am.use_nodes = True
_ab = _am.node_tree.nodes['Principled BSDF']
_ab.inputs['Transmission Weight'].default_value = 1.0; _ab.inputs['IOR'].default_value = 0.76; _ab.inputs['Roughness'].default_value = 0.0
BUBS = []
for i in range(9):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
    o = bpy.context.object; o.data.materials.append(_am); bpy.ops.object.shade_smooth()
    p = Vector((_rnd.uniform(-1, 1), _rnd.uniform(-1, 1), _rnd.uniform(-1, 1))).normalized() * _rnd.uniform(0.1, 0.55)
    BUBS.append(dict(o=o, p=p, r=_rnd.uniform(0.012, 0.035), ph=_rnd.uniform(0, 6.28)))

G = 4.0   # scaled gravity


def update_fx(t):
    zc, sq, sink = gel_state(t)
    # splash crown from the first impact, droplets land on the glass, slide back and merge
    for d in DROPS:
        age = t - HIT
        o = d['o']
        if age < 0 or age > 2.2:
            o.hide_render = True; continue
        o.hide_render = False
        r0 = R * 0.75
        tl = (d['vz'] + math.sqrt(d['vz'] ** 2)) / G     # time to come back to pane level
        if age < tl:
            rr = r0 + d['v'] * age; z = PT + d['r'] + d['vz'] * age - 0.5 * G * age * age
            s = (d['r'], d['r'], d['r'] * (1.0 + 0.4 * min(age * 3, 1)))
        else:
            u = age - tl
            rr0 = r0 + d['v'] * tl
            back = min(u / 1.0, 1.0); back = back * back * (3 - 2 * back)
            rr = rr0 + (r0 - rr0) * back
            z = PT + d['r'] * 0.45
            k = d['r'] * (1 - 0.85 * max(0.0, (u - 0.7) / 0.5)) if u > 0.7 else d['r']
            s = (k * 1.5, k * 1.5, k * 0.45)
        o.location = (rr * math.cos(d['a']), rr * math.sin(d['a']), z)
        o.scale = s
    # air bubbles drift inside the gel (follow its squash)
    for bb in BUBS:
        p = bb['p']
        w = Vector((p.x + 0.04 * math.sin(t * 1.3 + bb['ph']), p.y + 0.04 * math.cos(t * 1.1 + bb['ph']), p.z + 0.05 * math.sin(t * 0.8 + bb['ph'])))
        bb['o'].location = (w.x * R / math.sqrt(sq), w.y * R / math.sqrt(sq), zc + w.z * R * sq)
        bb['o'].scale = (bb['r'],) * 3
    # liquid bridge: while exiting, the top of the gel stays stuck to the underside and stretches, then snaps
    v = np.zeros(len(gs.data.vertices) * 3); gs.data.vertices.foreach_get('co', v); v = v.reshape(-1, 3)
    if 5.3 <= t < SNAP + 0.6:
        hold = sm(5.3, 6.0, t) * (1 - sm(SNAP, SNAP + 0.08, t))
        top = -PT - zc                      # local z of the pane underside
        up = v[:, 2] > 0
        k = np.clip(v[up, 2] / R, 0, 1) ** 3
        v[up, 2] += hold * (top - R) * k
        v[up, 0] *= 1 - 0.55 * hold * k; v[up, 1] *= 1 - 0.55 * hold * k
        if t >= SNAP:                         # recoil wobble after the snap
            u = t - SNAP
            v[:, 2] *= 1 + 0.12 * math.sin(u * 16) * math.exp(-u * 4)
        gs.data.vertices.foreach_set('co', v.ravel()); gs.data.update()
    for d in DRIPS:
        o = d['o']; age = t - SNAP - d['d']
        if age < 0 or age > 1.6:
            o.hide_render = True; continue
        o.hide_render = False
        z = -PT - d['r'] - 0.5 * G * age * age
        o.location = (d['x'], d['y'], z)
        o.scale = (d['r'], d['r'], d['r'] * (1 + min(age * 2, 0.6)))


# slow motion at the signature moment (story time vs. screen time)
_SLOW = [(4.2, 5.9, 0.45)]


def story_time(ts):
    tt, x, dt = 0.0, 0.0, 1 / 240
    while x < ts:
        sp = 1.0
        for a0, a1, s in _SLOW:
            if a0 <= tt < a1:
                sp = s
        tt += dt * sp; x += dt
    return tt

# lights never appear as shapes: not visible to camera, and only the key shows up in reflections
for _o in sc.objects:
    if _o.type == 'LIGHT':
        _o.visible_camera = False
        if _o.name != 'key':
            _o.visible_glossy = False
