# 0027 v3 "This machine runs on milk" (owner, Nov 17 2026: "effects are trash... the liquid should be like milk that
# spreads and splashes every hit - research it"). Physics of a milk crown (Edgerton's coronet; Deegan/Brunet/Eggers 2008):
# a plunger hits a thin layer of milk -> a thin cylindrical SHEET rises and flares; its rim thickens into a torus that breaks
# (Rayleigh-Plateau) into ~20 FINGERS, each throwing a DROPLET; the crown collapses, the cavity closes and a WORTHINGTON
# JET shoots up with a drop pinching off its tip; RIPPLES run out and interfere across the pool. Every hit is shown like
# high-speed footage: real speed into the impact, then a slow-motion ramp through the crown, then back.
# Stage: a wide black glass tray of milk under a ring of nickel plungers on a static steel frame; dark studio, strong
# back/rim light so the thin milk sheets glow (subsurface), black and white.
# Usage: blender -b --factory-startup -P milk_machine.py -- <outdir> <t0> <t1> <fps> <k> <workers>
#   env MM_RES=WxH (default 1080x1920), MM_SAMPLES (64)
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

a_ = sys.argv[sys.argv.index("--") + 1:]
OUTDIR = os.path.abspath(a_[0]); T0, T1, FPS = float(a_[1]), float(a_[2]), int(a_[3]); K, NW = int(a_[4]), int(a_[5])
TAU = 2 * math.pi


def sm(a, b, x):
    k = min(1.0, max(0.0, (x - a) / (b - a)))
    return k * k * (3 - 2 * k)


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"; prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"; scene.cycles.samples = int(os.environ.get("MM_SAMPLES", "64"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.use_denoising = True; scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 8
scene.render.resolution_x, scene.render.resolution_y = [int(v) for v in os.environ.get("MM_RES", "1080x1920").split("x")]
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.image_settings.file_format = "PNG"


def pm(name, col, rough, metal=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Coat Weight"].default_value = coat
    return m


MILK = pm("Milk", (0.92, 0.92, 0.9), 0.18, coat=0.35)
_mb = MILK.node_tree.nodes["Principled BSDF"]
_mb.inputs["Subsurface Weight"].default_value = 1.0
_mb.inputs["Subsurface Radius"].default_value = (1.0, 0.75, 0.5)
_mb.inputs["Subsurface Scale"].default_value = 0.06            # thin sheets glow when back-lit
STEEL = pm("Steel", (0.92, 0.92, 0.94), 0.07, metal=1.0)
NICKEL = pm("Nickel", (0.8, 0.79, 0.76), 0.16, metal=1.0)
TRAY = pm("BlackGlass", (0.005, 0.005, 0.006), 0.04, coat=1.0)
FLOOR = pm("Floor", (0.01, 0.01, 0.011), 0.35)


def new_mesh(name, m):
    me = bpy.data.meshes.new(name); o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); o.data.materials.append(m)
    return o


def set_mesh(o, V, F, smooth=True):
    me = o.data; me.clear_geometry(); me.from_pydata(V.tolist() if hasattr(V, "tolist") else V, [], F)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))


def grid_faces(nu, nv, wrap_v=True):
    f = []
    for i in range(nu - 1):
        for j in range(nv if wrap_v else nv - 1):
            a = i * nv + j; b = i * nv + (j + 1) % nv
            f.append((a, b, b + nv, a + nv))
    return f


# ---- stage ----
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0)); bpy.context.active_object.data.materials.append(FLOOR)
TR, TD = 3.2, 0.32                                   # tray radius, tray height
bpy.ops.mesh.primitive_cylinder_add(radius=TR + 0.12, depth=TD, location=(0, 0, TD / 2), vertices=200)
tray = bpy.context.active_object; tray.data.materials.append(TRAY)
bpy.ops.mesh.primitive_cylinder_add(radius=TR, depth=TD, location=(0, 0, TD / 2 + 0.06), vertices=200)
cut = bpy.context.active_object; cut.hide_render = True
bo = tray.modifiers.new("cut", "BOOLEAN"); bo.object = cut; bo.operation = "DIFFERENCE"
bv = tray.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 4
MZ = TD - 0.06                                       # milk surface height at rest
# plungers: 12 on a ring + 1 in the centre, on a static frame
PR_ = 2.0
PLUNGE_TOP = MZ + 1.25
bpy.ops.mesh.primitive_torus_add(major_radius=PR_, minor_radius=0.05, major_segments=256, minor_segments=24, location=(0, 0, PLUNGE_TOP + 0.9))
bpy.context.active_object.data.materials.append(STEEL)
PL = []
for i in range(13):
    if i < 12:
        a0 = -math.pi / 2 + i * TAU / 12; x, y = PR_ * math.cos(a0), PR_ * math.sin(a0)
    else:
        x, y = 0.0, 0.0
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=1.0, location=(x, y, PLUNGE_TOP + 0.55), vertices=20)
    rod = bpy.context.active_object; rod.data.materials.append(STEEL)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.11 if i < 12 else 0.16, depth=0.12, location=(x, y, PLUNGE_TOP), vertices=48)
    tip = bpy.context.active_object; tip.data.materials.append(NICKEL)
    b2 = tip.modifiers.new("b", "BEVEL"); b2.width = 0.025; b2.segments = 4
    PL.append({"xy": (x, y), "rod": rod, "tip": tip})
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.9, location=(0, 0, PLUNGE_TOP + 0.55 + 0.9 / 2), vertices=20)
bpy.context.active_object.data.materials.append(STEEL)
for i in range(4):                                   # spokes to the centre plunger
    a0 = i * TAU / 4 + TAU / 8
    bpy.ops.mesh.primitive_cube_add(size=1, location=(math.cos(a0) * PR_ / 2, math.sin(a0) * PR_ / 2, PLUNGE_TOP + 0.9))
    s_ = bpy.context.active_object; s_.scale = (PR_, 0.07, 0.05); s_.rotation_euler.z = a0; s_.data.materials.append(STEEL)

# ---- hits: (plunger, story time of impact, strength) ----
HITS = [(0, 0.35, 1.0)]                                   # HOOK: the front plunger, the crown fills the frame
HITS += [(6, 1.9, 0.9), (3, 3.1, 0.9), (9, 3.1, 0.9)]
for k, tt in zip((1, 7, 2, 8, 4, 10), (4.4, 4.4, 5.3, 5.3, 6.1, 6.1)):
    HITS.append((k, tt, 0.85))
for k in range(12):                                       # CLIMAX: the whole ring at once
    HITS.append((k, 7.6, 1.0))
HITS.append((12, 10.2, 1.6))                              # the centre plunger: the biggest crown + the tallest jet
CRN_LIFE = 1.35                                           # story seconds a crown/jet lives


# real time -> story time: real speed into each impact, a slow-motion ramp through the crown (x0.3), back to speed
def slow_factor(tau):
    f = 1.0
    for (_, th, _) in HITS:
        u = tau - th
        f = min(f, 1.0 - 0.72 * math.exp(-((u - 0.18) / 0.32) ** 2))
    return f


_tt = [0.0]; _tau = [0.0]
dt = 1 / 600
while _tt[-1] < 20.0:
    _tau.append(_tau[-1] + slow_factor(_tau[-1]) * dt); _tt.append(_tt[-1] + dt)
TT, TAUS = np.array(_tt), np.array(_tau)


def story(t):
    return float(np.interp(t, TT, TAUS))


DUR_STORY = story(20.0)

# ---- milk pool surface (polar grid) ----
NR, NA = 340, 900
pr = np.linspace(0, 1, NR) ** 0.85 * (TR - 0.005)
pa = np.linspace(0, TAU, NA, endpoint=False)
PRg, PAg = np.meshgrid(pr, pa, indexing="ij")
PX, PY = PRg * np.cos(PAg), PRg * np.sin(PAg)
pool = new_mesh("Milk", MILK)
POOL_F = grid_faces(NR, NA)
crowns = new_mesh("Crowns", MILK)
drops = new_mesh("Drops", MILK)


def pool_height(tau):
    z = np.full(PX.shape, MZ)
    for (k, th, s) in HITS:
        age = tau - th
        if age < -0.02 or age > 6.0:
            continue
        x0, y0 = PL[k]["xy"]
        d = np.hypot(PX - x0, PY - y0)
        if age < 0.45:                                   # the cavity under the plunger
            z -= s * 0.09 * math.sin(math.pi * min(1.0, max(0.0, age) / 0.45)) * np.exp(-(d / 0.18) ** 2)
        c = 0.85                                         # ripple speed; decaying rings that interfere
        env = math.exp(-age * 0.55) * s
        rr_ = d - c * age
        z += 0.022 * env * np.cos(32 * rr_) * np.exp(-(rr_ / 0.45) ** 2) / np.sqrt(1 + 3 * d)
    return z


def ring_mesh(V, F, cx, cy, z0, R0, h, flare, nphi, ns, phase):
    """thin crown sheet: a flaring cylindrical wall, fused at the base, thickening rim at the top"""
    base = len(V)
    for i in range(ns):
        s = i / (ns - 1)
        for j in range(nphi):
            ph = j / nphi * TAU
            rr_ = R0 + flare * s ** 2 + 0.006 * math.sin(phase + 7 * ph) * s
            V.append((cx + rr_ * math.cos(ph), cy + rr_ * math.sin(ph), z0 + h * s))
    for i in range(ns - 1):
        for j in range(nphi):
            a = base + i * nphi + j; b = base + i * nphi + (j + 1) % nphi
            F.append((a, b, b + nphi, a + nphi))


def tube(V, F, p0, p1, r0, r1, n=10):
    """a tapered tube (finger / jet column) from p0 to p1"""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    if d.length < 1e-6:
        return
    zax = d.normalized(); xax = zax.orthogonal().normalized(); yax = zax.cross(xax)
    base = len(V)
    rings = 5
    for i in range(rings):
        u = i / (rings - 1)
        c = p0 + d * u; r = r0 + (r1 - r0) * u
        for j in range(n):
            ph = j / n * TAU
            q = c + (xax * math.cos(ph) + yax * math.sin(ph)) * r
            V.append(tuple(q))
    for i in range(rings - 1):
        for j in range(n):
            a = base + i * n + j; b = base + i * n + (j + 1) % n
            F.append((a, b, b + n, a + n))
    tip = len(V); V.append(tuple(p1 + zax * r1)); last = base + (rings - 1) * n
    for j in range(n):
        F.append((last + j, last + (j + 1) % n, tip))


def sphere(V, F, c, r, n=10):
    base = len(V)
    for i in range(1, n):
        th = math.pi * i / n
        for j in range(n * 2):
            ph = TAU * j / (n * 2)
            V.append((c[0] + r * math.sin(th) * math.cos(ph), c[1] + r * math.sin(th) * math.sin(ph), c[2] + r * math.cos(th)))
    top = len(V); V.append((c[0], c[1], c[2] + r)); bot = len(V); V.append((c[0], c[1], c[2] - r))
    m = n * 2
    for i in range(n - 2):
        for j in range(m):
            a = base + i * m + j; b = base + i * m + (j + 1) % m
            F.append((a, b, b + m, a + m))
    for j in range(m):
        F.append((top, base + (j + 1) % m, base + j))
        lb = base + (n - 2) * m
        F.append((bot, lb + j, lb + (j + 1) % m))


def splashes(tau):
    CV, CF, DV, DF = [], [], [], []
    for hi, (k, th, s) in enumerate(HITS):
        age = tau - th
        if age < 0 or age > CRN_LIFE + 1.2:
            continue
        x0, y0 = PL[k]["xy"]
        nf = 20 if k < 12 else 26                         # Rayleigh-Plateau: ~20 fingers on the rim
        R0 = (0.09 + 0.26 * math.sqrt(min(age, 0.6) / 0.6)) * (0.8 + 0.25 * s)
        hgt = s * 0.36 * math.sin(math.pi * min(1.0, age / 0.75)) if age < 0.75 else 0.0
        flare = 0.1 * s * min(1.0, age / 0.3)
        if hgt > 0.01:
            ring_mesh(CV, CF, x0, y0, MZ - 0.01, R0, hgt, flare, 96, 9, hi * 1.7)
            rim_r = R0 + flare
            for f in range(nf):                            # fingers growing out of the rim, a droplet on each tip
                ph = f / nf * TAU + hi * 0.37
                jitter = 0.75 + 0.5 * ((f * 7 + hi * 3) % 11) / 11.0
                L = 0.13 * s * jitter * min(1.0, age / 0.35) * (1.0 - min(1.0, max(0.0, age - 0.45) / 0.3))
                if L < 0.005:
                    continue
                p0 = (x0 + rim_r * math.cos(ph), y0 + rim_r * math.sin(ph), MZ + hgt)
                dirv = Vector((math.cos(ph) * 0.55, math.sin(ph) * 0.55, 0.83)).normalized()
                p1 = Vector(p0) + dirv * L
                tube(CV, CF, p0, tuple(p1), 0.012 * s, 0.006 * s, 8)
                if age < 0.42:
                    sphere(CV, CF, tuple(p1 + dirv * 0.008), 0.012 * s * jitter, 6)
        # detached droplets: thrown from each finger tip at ~0.42, ballistic, gone into the milk
        for f in range(nf):
            ph = f / nf * TAU + hi * 0.37
            jitter = 0.75 + 0.5 * ((f * 7 + hi * 3) % 11) / 11.0
            ta = age - 0.42
            if ta < 0:
                continue
            v_out, v_up = 0.55 * jitter * s, 1.05 * jitter * s
            rr_ = R0 + 0.12 * s + v_out * ta
            zz = MZ + 0.36 * s + v_up * ta - 4.9 * ta * ta
            if zz < MZ:
                continue
            sphere(DV, DF, (x0 + rr_ * math.cos(ph), y0 + rr_ * math.sin(ph), zz), 0.014 * s * jitter, 6)
        # Worthington jet after the crown falls: a column rises from the centre, pinches a drop off its tip
        ja = age - 0.6
        if 0 < ja < 1.1:
            jh = s * 0.55 * math.sin(math.pi * min(1.0, ja / 0.9))
            if jh > 0.02:
                tube(CV, CF, (x0, y0, MZ - 0.02), (x0, y0, MZ + jh), 0.05 * s, 0.022 * s, 16)
            tp = ja - 0.42
            if tp > 0:
                zz = MZ + s * 0.62 + 0.9 * s * tp - 4.9 * tp * tp
                if zz > MZ:
                    sphere(DV, DF, (x0, y0, zz), 0.035 * s, 12)
    if CV:
        set_mesh(crowns, CV, CF)
    else:
        crowns.data.clear_geometry()
    if DV:
        set_mesh(drops, DV, DF)
    else:
        drops.data.clear_geometry()


def plungers(tau):
    for k, p in enumerate(PL):
        down = 0.0
        for (kk, th, s) in HITS:
            if kk != k:
                continue
            u = tau - th
            if -0.12 < u < 0.5:
                down = max(down, sm(-0.12, 0.0, u) * (1.0 - sm(0.08, 0.45, u)))
        dz = -(PLUNGE_TOP - MZ - 0.05) * down
        x, y = p["xy"]
        p["tip"].location = (x, y, PLUNGE_TOP + dz)
        p["rod"].location = (x, y, PLUNGE_TOP + 0.55 + dz)


# ---- light: dark studio, strong back light through the splashes, a soft key, a rim ----
def area(name, loc, size, power, sy=None, target=(0, 0, 0.4), col=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.shape = "RECTANGLE"; l.size = size; l.size_y = sy or size; l.energy = power; l.color = col
    o = bpy.data.objects.new(name, l); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); scene.collection.objects.link(o)


area("Back", (0.5, 6.0, 2.2), 4.0, 2400)
area("Key", (-4.5, -3.5, 5.0), 3.0, 900)
area("Rim", (5.0, 1.0, 1.4), 0.6, 700, sy=5.0)
world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.004, 0.005, 1)

camd = bpy.data.cameras.new("Cam"); camd.sensor_width = 36
cam = bpy.data.objects.new("Cam", camd); scene.collection.objects.link(cam); scene.camera = cam
KEYS = [  # story time, camera, look-at, lens
    (0.0, (0.35, -3.05, MZ + 0.32), (0.0, -2.0, MZ + 0.2), 50),
    (1.4, (0.9, -3.9, MZ + 0.75), (0.0, -1.6, MZ + 0.15), 40),
    (3.0, (1.4, -5.6, 2.4), (0.0, -0.4, MZ), 34),
    (6.5, (1.0, -6.4, 3.4), (0.0, 0.0, MZ), 32),
    (8.6, (0.6, -6.0, 4.4), (0.0, 0.2, MZ), 30),
    (10.0, (0.3, -2.0, MZ + 0.6), (0.0, 0.0, MZ + 0.3), 45),
    (12.5, (0.4, -2.4, MZ + 0.9), (0.0, 0.0, MZ + 0.25), 45),
    (99.0, (1.6, -6.8, 3.0), (0.0, 0.0, MZ), 34),
]


def _cr(p0, p1, p2, p3, u):
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)


def camera(tau):
    ks = KEYS
    i = max(k for k in range(len(ks) - 1) if ks[k][0] <= tau)
    t1, t2 = ks[i][0], ks[i + 1][0]
    u = min(1.0, max(0.0, (tau - t1) / (t2 - t1)))
    g = lambda k, idx: Vector(ks[max(0, min(len(ks) - 1, k))][idx])
    return _cr(g(i - 1, 1), g(i, 1), g(i + 1, 1), g(i + 2, 1), u), _cr(g(i - 1, 2), g(i, 2), g(i + 1, 2), g(i + 2, 2), u), ks[i][3] + (ks[i + 1][3] - ks[i][3]) * u


os.makedirs(OUTDIR, exist_ok=True)
REAL = lambda tau: float(np.interp(tau, TAUS, TT))
json.dump({"hits": [{"t": REAL(th), "k": k, "s": s} for (k, th, s) in HITS], "dur": 20.0}, open(os.path.join(OUTDIR, "events.json"), "w"))

frames = list(range(int(round(T0 * FPS)), int(round(T1 * FPS))))
for fr in frames[K::NW]:
    t = fr / FPS
    tau = story(t)
    pos, look, lens = camera(tau)
    cam.location = pos; cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler(); camd.lens = lens
    camd.dof.use_dof = True; camd.dof.focus_distance = (look - pos).length; camd.dof.aperture_fstop = 3.5
    z = pool_height(tau)
    set_mesh(pool, np.stack([PX, PY, z], -1).reshape(-1, 3), POOL_F)
    splashes(tau); plungers(tau)
    scene.render.filepath = os.path.join(OUTDIR, "f_%04d.png" % fr)
    bpy.ops.render.render(write_still=True)
print("done")
