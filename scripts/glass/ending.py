# finale override for erupt3.py (exec'd before the frame loop)
# burst -> gel pops up and hangs -> shards stop and fly back -> seal into a glass marble around the gel ->
# marble drops onto the slab, rings, settles, glows once -> slow push-in (fade done at encode)
END = 24.5
HANG0, CONV0, CONV1, SEAL, DROP = ST, ST + 0.6, ST + 1.7, ST + 1.75, ST + 1.8
SHELL_R = 0.45
bpy.data.objects['cyan'].visible_transmission = False     # its bar showed through the flat slab in the finale
_zt = PT + jet_top(CT, CT['freeze']) - 0.08 + R          # gel centre on the tower at the burst
ZH = _zt + 0.6                                           # where it hangs
ZL = PT + SHELL_R                                        # resting height of the marble
TF = math.sqrt(2 * (ZH - ZL) / G)
LAND = DROP + TF
print('TIMING', ST, DROP, LAND, flush=True)
RIPS.append((LAND, 0.035)); RIPS.append((LAND + 0.25, 0.012))

for _s in SHT:                                           # each shard gets a slot on the marble surface
    _d = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))).normalized()
    _s['tgt'] = _d * SHELL_R
SHT_END = SHT
SHT = []                                                 # original update() no longer moves them

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=SHELL_R)
shell = bpy.context.object; bpy.ops.object.shade_smooth(); shell.data.materials.append(shardm); shell.hide_render = True

_gel_orig = gel


def gel(t):
    if t < ST:
        return _gel_orig(t)
    if t < DROP:                                         # pops up, hangs, wobbling
        z = _zt + 0.6 * sm(ST, ST + 0.6, t)
        u = t - ST
        return Vector((0, 0, z)), 1 + 0.1 * math.sin(u * 12) * math.exp(-u * 2), 1.0
    return Vector((0, 0, marble_z(t))), 1.0, 1.0


def marble_z(t):
    if t < DROP:
        return ZH
    if t < LAND:
        return ZH - 0.5 * G * (t - DROP) ** 2
    w = t - LAND
    return ZL + 0.12 * abs(math.sin(w * 7.0)) * math.exp(-w * 4.0)


_update_orig = update


def update(t):
    _update_orig(t)
    if t < ST - 0.5:
        for s in SHT_END:
            s['o'].hide_render = True
        return
    pos, _, _ = gel(t)
    # shards: real burst, decelerate, then fly back onto the marble surface
    u = min(t - ST, 0.6)
    for s in SHT_END:
        o = s['o']
        if t < ST or t >= SEAL:
            o.hide_render = True; continue
        o.hide_render = False
        uu = 0.6 * (1 - (1 - u / 0.6) ** 2) if u < 0.6 else 0.6
        p_out = s['p0'] + s['v'] * uu + Vector((0, 0, -0.5 * G * 0.5 * uu * uu))
        k = sm(CONV0, CONV1, t)
        o.location = p_out * (1 - k) + (pos + s['tgt']) * k
        rot = uu * 0.4 + (t - ST) * 0.6 * (1 - k)
        o.rotation_euler = Euler((s['rot'].x + s['w'].x * rot, s['rot'].y + s['w'].y * rot, s['rot'].z + s['w'].z * rot))
        o.scale = s['s'] * (1 - 0.5 * k)
    # the sealed marble
    if t >= SEAL - 0.05:
        shell.hide_render = False; shell.location = pos
        a_ = sm(SEAL - 0.05, SEAL + 0.1, t); shell.scale = (0.96 + 0.04 * a_,) * 3
    else:
        shell.hide_render = True
    # light: inner glow pulses once when it lands
    if t >= LAND:
        w = t - LAND
        pulse = math.exp(-((w - 0.35) / 0.35) ** 2)
        pv.inputs['Emission Strength'].default_value = 0.9 + 0.4 * pulse
        glo.location = pos; gl.energy = 30.0 * pulse
    # camera: follow the gel up while it hangs, ride the marble down, slow push-in to the end
    hang = sm(ST, ST + 0.6, t) * (1 - sm(DROP, LAND, t))
    size = 1.6 - 0.6 * sm(DROP, LAND + 0.3, t)
    d = 3.8 * size ** 0.75 - 0.7 * (1 - sm(ST, ST + 0.8, t)) - 0.6 * sm(LAND + 0.3, END, t)
    hz = 0.95 + (ZH - 0.4 - 0.95) * sm(ST, ST + 0.7, t)
    tz = hz * (1 - sm(DROP, LAND, t)) + ZL * sm(DROP, LAND, t)
    ang = math.radians(-90 + 22 * math.sin(2 * math.pi * t / LOOP) + 6 * math.sin(4 * math.pi * t / LOOP))
    cam.location = (d * math.cos(ang), d * math.sin(ang), tz + 0.55 * size ** 0.5 - 0.15 * sm(LAND, END, t))
    tgt = Vector((0, 0, tz))
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cd.dof.focus_distance = (tgt - cam.location).length
