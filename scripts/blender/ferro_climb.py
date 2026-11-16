# 0022 "This liquid climbs on its own" (owner, Nov 16 2026: picked idea 1, 20 s, preview first). Ray-traced in Blender
# Cycles. Ruby ferrofluid climbs a polished steel corkscrew tower around a mirror rod, standing on black mirror glass,
# in front of a soft ruby/rose haze with out-of-focus bokeh lights; one strong silver side key, a red rim.
# Look bar = 0021 (owner: "I want the reels to look that good as the last reel"): rich materials that carry the scene
# colour, real surface detail (Rosensweig spike lattice), deep blacks, lit backdrop with detail at the edges.
# Last two reels: 0020 water/blue, 0021 violet/teal space. This one: ruby + silver studio, liquid metal.
# Beat sheet (real seconds, 20 s):
#   0.0-0.6  COLD OPEN: the spiked liquid halo above the tower flares its spikes out
#   0.6-2.0  fast rewind (smooth, no flicker) back to the puddle
#   2.0-3.5  the pool wakes: a spike lattice rises across it
#   3.5-12.5 it CLIMBS the corkscrew, turn by turn (spikes stand up as it grips each turn), a slip at ~10.5, a push
#   12.5-14.5 it reaches the top and BLOOMS into a floating halo ring of spikes
#   14.5-18.5 ENDING: it lets go - spikes melt, the liquid drains back down the spiral into a smooth mirror pool
#   18.0-19.8 fade to black while the last drip settles
# Usage: blender -b --factory-startup -P scripts/blender/ferro_climb.py -- <outdir> <samples> <fps> <k> <n> [frames]
#   env CLIMB_RES=WxH (default 1080x1920), CLIMB_STILL=<real seconds> renders one still at that moment
import math
import os
import sys

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
FPS = int(argv[2]) if len(argv) > 2 else 30
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi
DUR = 20.0
OPEN, REWIND = 0.6, 2.0
rng = np.random.default_rng(2222)


def sm(a, b, x):
    k = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0, 1)
    return k * k * (3 - 2 * k)


# ---------------- geometry constants ----------------
R_H = 0.62          # helix radius
TURNS = 4.5
H = 3.0             # helix height
R_STEEL = 0.075     # corkscrew wire radius
R_COAT = 0.14       # liquid coat radius around the wire
ROD_R = 0.11
CROWN_C = np.array([0.0, 0.0, H + 0.42])
CROWN_R = 0.34
POOL_R = 1.05

# ---------------- story ----------------
def story(r):
    """real seconds -> story seconds (0 = the calm puddle). Cold open shows story 11.4 (crown burst)."""
    if r < OPEN:
        return 11.0 + r
    if r < REWIND:
        k = (r - OPEN) / (REWIND - OPEN)
        return (11.0 + OPEN) * (1 - k * k * (3 - 2 * k))
    return r - REWIND


def state(s):
    """story seconds -> dict of shape parameters"""
    climb = float(sm(1.5, 10.5, s))
    climb -= 0.07 * float(sm(8.2, 8.6, s)) * (1 - float(sm(8.6, 9.4, s)))   # the slip
    drain = float(sm(12.5, 16.0, s))
    front = max(0.0, climb * (1 - drain))
    wake = float(sm(0.0, 1.5, s))
    crown = float(sm(10.2, 11.2, s)) * (1 - float(sm(12.3, 13.6, s)))
    burst = float(sm(11.0, 11.6, s)) * (1 - float(sm(12.0, 13.0, s)))       # the long spikes of the cold open
    calm = float(sm(14.0, 16.5, s))
    return dict(front=front, wake=wake, crown=crown, burst=burst,
                coat_spikes=(0.55 + 0.45 * float(sm(9.5, 11.0, s))) * (1 - calm),
                pool_spikes=wake * (1 - 0.7 * climb) * (1 - calm) + 0.0,
                pool_amt=1.0 - 0.75 * front, t=s)


# ---------------- scene ----------------
scene = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "OPTIX"
prefs.get_devices()
for d in prefs.devices:
    d.use = d.type == "OPTIX"
scene.cycles.device = "GPU"
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPTIX"
scene.cycles.max_bounces = 8
scene.cycles.glossy_bounces = 6
scene.cycles.diffuse_bounces = 2
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.use_persistent_data = True
res = os.environ.get("CLIMB_RES", "1080x1920").split("x")
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.fps = FPS
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = 0.3

# world: near-black with a soft ruby/rose haze (noise), lights the glossy surfaces with colour
w = bpy.data.worlds.new("Studio")
scene.world = w
w.use_nodes = True
wn, wl = w.node_tree.nodes, w.node_tree.links
wn.clear()
wout = wn.new("ShaderNodeOutputWorld")
wbg = wn.new("ShaderNodeBackground")
wtc = wn.new("ShaderNodeTexCoord")
wno = wn.new("ShaderNodeTexNoise")
wno.inputs["Scale"].default_value = 2.6
wno.inputs["Detail"].default_value = 6.0
wno.inputs["Distortion"].default_value = 0.8
wramp = wn.new("ShaderNodeValToRGB")
wramp.color_ramp.elements[0].position = 0.45
wramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
wramp.color_ramp.elements[1].position = 0.8
wramp.color_ramp.elements[1].color = (0.012, 0.02, 0.09, 1)   # 0021 navy/violet haze
wl.new(wtc.outputs["Generated"], wno.inputs["Vector"])
wl.new(wno.outputs["Fac"], wramp.inputs["Fac"])
wl.new(wramp.outputs["Color"], wbg.inputs["Color"])
wbg.inputs["Strength"].default_value = 1.0
wl.new(wbg.outputs[0], wout.inputs[0])


def principled(name, color, metal=0.0, rough=0.1, coat=0.0, film=0.0, emit=None, es=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if film:
        b.inputs["Thin Film Thickness"].default_value = film
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = es
    return m


def mesh_obj(name, verts, faces, mat, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist() if hasattr(faces, "tolist") else faces)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(mat)
    return o


def grid_faces(nu, nv, wrap_v=True):
    f = []
    vv = nv if wrap_v else nv - 1
    for i in range(nu - 1):
        for j in range(vv):
            a = i * nv + j
            b = i * nv + (j + 1) % nv
            f.append((a, b, b + nv, a + nv))
    return np.array(f, dtype=np.int64)


steel = principled("Steel", (0.9, 0.9, 0.93), metal=1.0, rough=0.05, film=180.0)
ferro = principled("RubyFerro", (0.11, 0.004, 0.014), metal=0.55, rough=0.08, coat=1.0, film=380.0)
# owner, Nov 16: "only this colour looks boring" -> the liquid shifts colour with height (ruby at the pool ->
# magenta -> violet-blue at the crown) and carries an iridescent thin-film sheen on every highlight
_fn, _fl = ferro.node_tree.nodes, ferro.node_tree.links
_geo = _fn.new("ShaderNodeNewGeometry")
_sep = _fn.new("ShaderNodeSeparateXYZ")
_mr = _fn.new("ShaderNodeMapRange")
_mr.inputs["From Min"].default_value = 0.0
_mr.inputs["From Max"].default_value = 4.0
_cr = _fn.new("ShaderNodeValToRGB")
_cr.color_ramp.elements[0].position = 0.0
# owner, Nov 16: "use the colours from the previous video" -> 0021's swirl palette, violet low -> blue -> aqua -> mint high
_cr.color_ramp.elements[0].color = (0.07, 0.02, 0.2, 1)        # violet
_cr.color_ramp.elements.new(0.35).color = (0.02, 0.05, 0.24, 1)   # blue
_cr.color_ramp.elements.new(0.62).color = (0.01, 0.15, 0.2, 1)    # aqua
_cr.color_ramp.elements.new(0.82).color = (0.015, 0.17, 0.22, 1)  # teal (green crown read as a plant)
_cr.color_ramp.elements[-1].position = 1.0
_cr.color_ramp.elements[-1].color = (0.04, 0.21, 0.22, 1)       # aqua-mint crown tips
_fl.new(_geo.outputs["Position"], _sep.inputs[0])
_fl.new(_sep.outputs["Z"], _mr.inputs["Value"])
_fl.new(_mr.outputs["Result"], _cr.inputs["Fac"])
_fl.new(_cr.outputs["Color"], _fn["Principled BSDF"].inputs["Base Color"])
ferro.node_tree.nodes["Principled BSDF"].inputs["Coat Roughness"].default_value = 0.02
floor_m = principled("BlackMirror", (0.004, 0.002, 0.003), rough=0.09, coat=0.6)

# ---------------- helix frame ----------------
NS, NPHI = 4200, 168  # fine enough that every spike is a smooth cone (owner: "I don't like crystals, use spikes")
u = np.linspace(0.0, 1.0, NS)
th = u * TURNS * TAU
CEN = np.stack([R_H * np.cos(th), R_H * np.sin(th), 0.12 + u * (H - 0.12)], 1)
dth = TURNS * TAU
TAN = np.stack([-R_H * np.sin(th) * dth, R_H * np.cos(th) * dth, np.full(NS, H - 0.12)], 1)
TAN /= np.linalg.norm(TAN, axis=1, keepdims=True)
NOR = np.stack([-np.cos(th), -np.sin(th), np.zeros(NS)], 1)          # towards the rod
NOR -= TAN * np.sum(NOR * TAN, 1, keepdims=True)
NOR /= np.linalg.norm(NOR, axis=1, keepdims=True)
BIN = np.cross(TAN, NOR)
seg = np.linalg.norm(np.diff(CEN, axis=0), axis=1)
ARC = np.concatenate([[0.0], np.cumsum(seg)])
LTOT = ARC[-1]
TAPER = (np.sqrt(sm(0.0, 0.05, ARC)) * np.sqrt(sm(LTOT, LTOT - 0.05, ARC)))[:, None]  # closed tube ends
phi = np.linspace(0, TAU, NPHI, endpoint=False) + math.pi   # seam on the rod side, out of sight
CP, SP = np.cos(phi), np.sin(phi)
DIRS = CP[None, :, None] * NOR[:, None, :] + SP[None, :, None] * BIN[:, None, :]   # (NS, NPHI, 3) radial dirs
FACES_T = grid_faces(NS, NPHI)

# the steel wire
wire = mesh_obj("Wire", (CEN[:, None, :] + (R_STEEL * TAPER)[:, :, None] * DIRS).reshape(-1, 3), FACES_T, steel)
# the rod + a polished cap the crown sits on
rv, rf = [], []
NR = 64
for i, z in enumerate((0.0, H + 0.3)):
    for j in range(NR):
        a = j / NR * TAU
        rv.append((ROD_R * math.cos(a), ROD_R * math.sin(a), z))
rf = [(j, (j + 1) % NR, (j + 1) % NR + NR, j + NR) for j in range(NR)]
rod = mesh_obj("Rod", np.array(rv), rf, steel)
# floor: a big black mirror disc
fv = [(0, 0, 0)] + [(30 * math.cos(a), 30 * math.sin(a), 0) for a in np.linspace(0, TAU, 128, endpoint=False)]
ff = [(0, i + 1, (i + 1) % 128 + 1) for i in range(128)]
floor = mesh_obj("Floor", np.array(fv), ff, floor_m, smooth=False)

# ---------------- liquid on the wire ----------------
# Real ferrofluid spikes: individual smooth cones (sharp tip, concave flanks, soft fillet into the liquid) standing in
# staggered rows on the outer/upper side of the tube. Each vertex takes the tallest cone it is under.
LAM = 0.19          # spacing along the wire (owner: bigger spikes)
RB = 0.088          # cone base radius
OUTW = np.stack([np.cos(th), np.sin(th), np.zeros(NS)], 1)
UPP = np.cross(TAN, OUTW)                                        # perpendicular to wire + outward, roughly "up"
UPP *= np.sign(UPP[:, 2:3] + 1e-9)
ALPHA = np.arctan2(np.einsum("ijk,ik->ij", DIRS, UPP), np.einsum("ijk,ik->ij", DIRS, OUTW))  # 0 = outward
ROWS = (-0.65, 0.6, 1.85)                                        # cone rows around the tube (radians from outward)
SPIKE_SHAPE = np.zeros((NS, NPHI))
for j, a0 in enumerate(ROWS):
    off = (j % 2) * LAM / 2
    da = np.mod(ARC[:, None] - off + LAM / 2, LAM) - LAM / 2
    dy = (ALPHA - a0) * R_COAT
    rr = np.sqrt(da * da + dy * dy)
    x = np.clip(1 - rr / RB, 0, 1)
    cone = x ** 2.4 + 0.12 * sm(0.0, 1.0, x)                     # concave cone + a little fillet at the base
    SPIKE_SHAPE = np.maximum(SPIKE_SHAPE, cone * (1.0 - 0.2 * j / 2))
SPIKE_SHAPE /= SPIKE_SHAPE.max()
facing = np.ones((NS, NPHI))
coat = mesh_obj("Coat", (CEN[:, None, :] + R_COAT * DIRS).reshape(-1, 3), FACES_T, ferro)


def update_coat(st):
    front = st["front"] * (LTOT + 0.2)
    cover = sm(front + 0.02, front - 0.35, ARC)                      # 1 behind the front, 0 ahead
    head = np.exp(-((ARC - (front - 0.18)) / 0.12) ** 2) * (st["front"] > 0.002) * (1 - st["front"] * 0.0)
    rad = R_STEEL * 0.8 + (R_COAT - R_STEEL * 0.8) * cover + 0.05 * head
    spikes = 0.25 * st["coat_spikes"] * SPIKE_SHAPE * facing * cover[:, None]
    grip = 0.5 + 0.5 * np.cos(ARC / (LTOT / TURNS) * TAU * 1.0 - st["t"] * 2.0)  # spikes breathe as it grips each turn
    spikes *= (0.75 + 0.25 * grip[:, None])
    r2 = (rad[:, None] + spikes) * TAPER
    v = CEN[:, None, :] + r2[:, :, None] * DIRS
    coat.data.vertices.foreach_set("co", v.reshape(-1).astype(np.float32))
    coat.data.update()
    coat.hide_render = st["front"] < 0.003


# ---------------- crown ----------------
def ico_sphere(sub):
    t = (1 + math.sqrt(5)) / 2
    vs = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
          (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    fs = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
          (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
          (8, 6, 7), (9, 8, 1)]
    vs = [np.array(v) / np.linalg.norm(v) for v in vs]
    for _ in range(sub):
        cache, nf = {}, []

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = vs[a] + vs[b]
                vs.append(m / np.linalg.norm(m))
                cache[key] = len(vs) - 1
            return cache[key]
        for a, b, c in fs:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        fs = nf
    return np.array(vs), np.array(fs)


# owner, Nov 16: the needle crown read as crystals -> a liquid HALO: a ring of ferrofluid that blooms out of a smooth
# mirror drop on the rod top and floats above the tower, wearing the same smooth cone spikes as the spiral
ZH = H + 0.42                 # halo height
RT_FULL, RM = 0.9, 0.15       # halo major / minor radius (a wide, readable ring)
NU, NV = 1500, 150
hu = np.linspace(0, TAU, NU, endpoint=False)
hv = np.linspace(0, TAU, NV, endpoint=False)
HU, HV = np.meshgrid(hu, hv, indexing="ij")
H_ALPHA = np.mod(HV + math.pi, TAU) - math.pi                  # 0 = outward, +pi/2 = up
_nsp = int(round(TAU * RT_FULL / 0.2))                         # spikes per row, whole number so the ring closes
HSHAPE = np.zeros((NU, NV))
for j, a0 in enumerate((-0.55, 0.55, 1.65)):
    off = (j % 2) * 0.5
    dth = np.mod(HU / TAU * _nsp - off + 0.5, 1.0) - 0.5       # in spike units along the ring
    da = dth * TAU * RT_FULL / _nsp
    dy = (H_ALPHA - a0) * RM
    x = np.clip(1 - np.sqrt(da * da + dy * dy) / 0.085, 0, 1)
    HSHAPE = np.maximum(HSHAPE, (x ** 2.4 + 0.12 * sm(0.0, 1.0, x)) * (1.0 - 0.15 * j))
HSHAPE /= HSHAPE.max()
_hfaces = np.concatenate([grid_faces(NU, NV), np.array([((NU - 1) * NV + j, (NU - 1) * NV + (j + 1) % NV, (j + 1) % NV, j) for j in range(NV)])])
halo = mesh_obj("Halo", np.zeros((NU * NV, 3)), _hfaces, ferro)
SV, SF = ico_sphere(5)
drop = mesh_obj("Drop", SV * 0.2 + np.array([0, 0, H + 0.3]), SF, ferro)
CAM_DIR = None  # set after the camera exists


def update_crown(st):
    amt = max(st["crown"], st["burst"])
    drop.hide_render = amt < 0.01 and st["front"] < 0.98
    dz = 0.2 * (0.6 + 0.4 * float(sm(0.0, 0.4, amt)))
    dv = SV * dz
    dv[:, 2] = np.maximum(dv[:, 2], -0.02)                      # a drop sitting on the rod's top
    drop.data.vertices.foreach_set("co", (dv + np.array([0, 0, H + 0.3])).reshape(-1).astype(np.float32))
    drop.data.update()
    if amt < 0.01:
        halo.hide_render = True
        return
    halo.hide_render = False
    k = float(sm(0.0, 0.6, amt))
    rt = 0.22 + (RT_FULL - 0.22) * k
    rm = RM * (0.4 + 0.6 * k)
    spin = 0.45 * st["t"] + 1.6 * float(sm(10.2, 13.6, st["t"]))   # the halo turns (runs backwards in the rewind)
    hu_ = HU + spin
    toward = np.clip(np.cos(hu_ - math.atan2(CAM_DIR[1], CAM_DIR[0])), 0, 1)
    pulse = 0.85 + 0.15 * np.sin(st["t"] * 7.0 - HU * 3.0)          # a ripple of spike height running round the ring
    spk = HSHAPE * (0.14 * st["crown"] * pulse + st["burst"] * (0.08 + 0.1 * toward)) * k  # short spikes: the RING reads
    r = rm + spk
    ox = np.cos(hu_) * (rt + r * np.cos(HV))
    oy = np.sin(hu_) * (rt + r * np.cos(HV))
    oz = ZH + r * np.sin(HV) + 0.08 * st["burst"] * np.sin(3 * HU + st["t"] * 4)
    v = np.stack([ox, oy, oz], -1)
    halo.data.vertices.foreach_set("co", v.reshape(-1).astype(np.float32))
    halo.data.update()


# ---------------- pool ----------------
NPR, NPA = 260, 900
pr = np.linspace(0, 1, NPR)
pa = np.linspace(0, TAU, NPA, endpoint=False)
PR, PA = np.meshgrid(pr, pa, indexing="ij")
PX, PY = PR * np.cos(PA), PR * np.sin(PA)
pool = mesh_obj("Pool", np.zeros((NPR * NPA, 3)), grid_faces(NPR, NPA), ferro)
# a hexagonal field of smooth cones (two offset square sub-lattices -> nearest tip)
_pl = 0.17 / POOL_R
_qx, _qy = PX / _pl, PY / (_pl * math.sqrt(3))
_d1 = np.hypot((_qx - np.round(_qx)) * _pl, (_qy - np.round(_qy)) * _pl * math.sqrt(3))
_d2 = np.hypot((_qx - 0.5 - np.round(_qx - 0.5)) * _pl, (_qy - 0.5 - np.round(_qy - 0.5)) * _pl * math.sqrt(3))
_x = np.clip(1 - np.minimum(_d1, _d2) * POOL_R / 0.08, 0, 1)
PHEX = _x ** 2.4 + 0.12 * sm(0.0, 1.0, _x)
PHEX /= PHEX.max()


def update_pool(st):
    rr = POOL_R * (0.45 + 0.55 * st["pool_amt"])
    dome = 0.09 * st["pool_amt"] * np.sqrt(np.clip(1 - PR ** 2, 0, 1)) + 0.004
    spk = 0.2 * st["pool_spikes"] * PHEX * sm(1.0, 0.75, PR)
    z = dome + spk
    v = np.stack([PX * rr, PY * rr, z], -1).reshape(-1, 3)
    pool.data.vertices.foreach_set("co", v.reshape(-1).astype(np.float32))
    pool.data.update()


# ---------------- lights ----------------
def area(name, loc, look, size, energy, color, shape="RECTANGLE", sy=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size = size
    if sy is not None:
        ld.size_y = sy
    ld.energy = energy
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    lo.location = loc
    d = np.array(look) - np.array(loc)
    lo.rotation_euler = (np.array([0, 0, -1.0]) * 0).tolist()
    import mathutils
    lo.rotation_euler = mathutils.Vector(d.tolist()).to_track_quat("-Z", "Y").to_euler()
    lo.visible_camera = False
    return lo


area("Key", (-4.2, -3.0, 4.6), (0, 0, 1.6), 2.6, 2200, (0.92, 0.94, 1.0))
area("Strip", (-2.6, -3.4, 1.8), (0, 0, 1.6), 0.25, 700, (1.0, 1.0, 1.0), sy=5.0)
area("RimRed", (2.6, 4.2, 3.4), (0, 0, 1.8), 2.2, 2200, (0.45, 0.2, 1.0))        # violet rim
area("RimTeal", (-3.4, 3.6, 2.6), (0, 0, 2.0), 2.0, 1600, (0.15, 0.95, 0.85))    # aqua/mint rim from the other side
area("FillRose", (4.0, -2.4, 0.4), (0, 0, 1.0), 2.0, 260, (0.2, 0.4, 1.0))       # soft blue fill from below
area("FrontSoft", (1.6, -5.5, 4.2), (0, 0, 3.0), 1.6, 380, (1.0, 0.92, 0.95))  # catches the spike tips facing the lens

# bokeh lights far behind the tower (soft discs in the depth of field) - detail on the edges of the frame
def bokeh_mat(name, color, strength):
    """a soft glowing orb: bright centre fading to transparent at the rim (reads as an out-of-focus light)"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l_ = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    em = n.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = strength
    tr = n.new("ShaderNodeBsdfTransparent")
    lw = n.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    pw = n.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 0.35  # fades out early: soft orb, no hard rim
    mx = n.new("ShaderNodeMixShader")
    l_.new(lw.outputs["Facing"], pw.inputs[0])
    l_.new(pw.outputs[0], mx.inputs["Fac"])
    l_.new(em.outputs[0], mx.inputs[1])
    l_.new(tr.outputs[0], mx.inputs[2])
    l_.new(mx.outputs[0], out.inputs["Surface"])
    return m


bok_m = [bokeh_mat(f"Bokeh{i}", c, s) for i, (c, s) in enumerate((((0.3, 0.35, 1.0), 1.6), ((0.55, 0.2, 1.0), 1.6),
                                                                   ((0.9, 0.95, 1.0), 0.9), ((0.1, 0.9, 0.8), 1.6)))]
BV, BF = ico_sphere(3)
for i in range(80):
    p = np.array([rng.uniform(-9, 9), rng.uniform(7, 16), rng.uniform(-2.5, 9.0)])
    r = rng.uniform(0.12, 0.32)
    o = mesh_obj(f"Bok{i}", BV * r + p, BF, bok_m[[0, 3, 1, 0, 3, 0, 3, 2][i % 8]])
    o.visible_shadow = False

# ---------------- camera ----------------
import mathutils  # noqa: E402

cd = bpy.data.cameras.new("Cam")
cd.lens = 50
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 1.8
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


def place_cam(loc, look, lens):
    cam.location = loc
    d = mathutils.Vector(look) - mathutils.Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.dof.focus_distance = d.length


# camera keys (real seconds): (t, loc, look, lens)
SHOTS = [
    (0.0, (2.9, -4.8, 4.3), (0.0, 0.0, 2.9), 35),     # cold open: the bursting crown + the top of the spiral
    (0.6, (2.8, -4.7, 4.2), (0.0, 0.0, 2.9), 35),
    (2.0, (2.0, -5.2, 0.9), (0.0, 0.0, 0.5), 40),      # the puddle at the foot of the tower
    (4.5, (3.2, -6.6, 1.6), (0.0, 0.0, 1.2), 45),
    (9.0, (4.6, -6.8, 2.6), (0.0, 0.0, 2.2), 45),      # follows it up
    (12.5, (3.6, -6.4, 5.0), (0.0, 0.0, 2.7), 45),
    (14.5, (5.0, -8.2, 2.6), (0.0, 0.0, 1.9), 42),     # pulls back for the drain
    (20.0, (5.6, -9.0, 2.2), (0.0, 0.0, 1.6), 42),
]


def cam_at(r):
    for (t0, l0, k0, f0), (t1, l1, k1, f1) in zip(SHOTS, SHOTS[1:]):
        if r <= t1:
            k = float(sm(t0, t1, r)) if t1 > t0 else 1.0
            lerp = lambda a, b: tuple(np.array(a) * (1 - k) + np.array(b) * k)  # noqa: E731
            return lerp(l0, l1), lerp(k0, k1), f0 * (1 - k) + f1 * k
    return SHOTS[-1][1], SHOTS[-1][2], SHOTS[-1][3]


def render_at(r, path):
    global CAM_DIR
    loc, look, lens = cam_at(r)
    place_cam(loc, look, lens)
    cdir = np.array(loc) - CROWN_C
    CAM_DIR = cdir / np.linalg.norm(cdir)
    st = state(story(r))
    update_coat(st)
    update_crown(st)
    update_pool(st)
    fade = 1.0 - float(sm(18.0, 19.8, r))
    scene.view_settings.exposure = 0.3 + math.log2(max(fade, 1e-3))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


still = os.environ.get("CLIMB_STILL")
if still is not None:
    for i, tt in enumerate(still.split(",")):
        render_at(float(tt), os.path.join(OUT, f"still_{float(tt):05.2f}.png"))
else:
    NF = int(round(DUR * FPS))
    frames = ONLY if ONLY else list(range(K, NF, NN))
    for f in frames:
        p = os.path.join(OUT, f"f_{f:04d}.png")
        if os.path.exists(p):
            continue
        render_at(f / FPS, p)
