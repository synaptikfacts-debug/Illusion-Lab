# 0020 "This water falls upward" (owner's pick, Nov 15). Blender Cycles, OptiX. A glass of water on polished black stone,
# in front of a wall of moving blue water-caustic light. The water bulges, rises out of the glass in slow motion, twists
# into a three-strand rope, hits a glass ceiling and splashes across it, then rains back down and the glass refills.
# Real refractive water (IOR 1.333, slight blue absorption), droplets that follow gravity, ripples where they land.
# Timeline: src/scenes/water/timeline.json (story time; this script maps real -> story time for the cold open + rewind)
# Usage: blender -b --factory-startup -P scripts/blender/water_up.py -- <outDir> [samples] [fps] [k] [n] [only]
#        add WATER_EVENTS=1 to only write src/scenes/water/events.json (drop landings for the sound) and quit.
import json
import math
import os
import sys
import time

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 32
FPS = int(argv[2]) if len(argv) > 2 else 60
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
ONLY = [int(x) for x in argv[5].split(",")] if len(argv) > 5 and argv[5] else None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TL = json.load(open(os.path.join(ROOT, "src", "scenes", "water", "timeline.json")))
TAU = 2 * math.pi
GR, GH, CEIL = TL["glassR"], TL["glassH"], TL["ceiling"]
G = 0.9  # slow-motion gravity (m/s^2)


def sm(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def story(r):
    """real time -> story time: cold open on the ceiling hit, a fast rewind, then the story at TL.speed"""
    if r < TL["cold"]:
        return TL["coldFrom"] + r
    if r < TL["cold"] + TL["rewind"]:
        k = (r - TL["cold"]) / TL["rewind"]
        k = k * k * (3 - 2 * k)
        return (TL["coldFrom"] + TL["cold"]) * (1 - k) + TL["rewindTo"] * k
    return TL["rewindTo"] + (r - TL["cold"] - TL["rewind"]) * TL["speed"]


REAL_DUR = TL["cold"] + TL["rewind"] + (TL["storyEnd"] - TL["rewindTo"]) / TL["speed"]


def to_real(s):
    return TL["cold"] + TL["rewind"] + (s - TL["rewindTo"]) / TL["speed"]


# ---------------- the story (deterministic) ----------------
def level(s):
    """water level in the glass (m above the glass floor)"""
    full = GH * 0.82
    drain = sm(TL["rise"][0], 9.0, s)
    refill = sm(TL["refill"][0], TL["refill"][1], s)
    return full * (1 - 0.8 * drain) + full * 0.8 * drain * refill


def tip(s):
    """height of the rising water's tip above the table"""
    a, b = TL["rise"]
    k = sm(a, b, s) ** 0.85
    return level(s) + 0.005 + (CEIL - level(s) - 0.005) * k


def base(s):
    """bottom of the column: the water surface, until the tail lifts off into the ceiling"""
    return level(s) + (CEIL - level(s)) * sm(TL["tailUp"][0], TL["tailUp"][1], s) ** 1.3


rng = np.random.default_rng(2020)
FLIGHTS = []
# the splash under the ceiling: drops flung outward and down
for i in range(26):
    a = i * 2.39996 + 0.3 * rng.random()
    sp = 0.05 + 0.11 * rng.random()
    FLIGHTS.append(dict(t0=TL["hit"] + 0.02 * rng.random(), x0=0.01 * math.cos(a), y0=0.01 * math.sin(a), z0=CEIL - 0.004,
                        vx=math.cos(a) * sp, vy=math.sin(a) * sp, vz=-0.02 - 0.05 * rng.random(), r=0.003 + 0.003 * rng.random()))
# the rain: drops detach from the ceiling sheet and fall back into the glass
for i in range(30):
    t0 = TL["rain"][0] + (TL["rain"][1] - TL["rain"][0]) * (i / 30) ** 0.9 + 0.05 * rng.random()
    a, rr = rng.random() * TAU, GR * 0.8 * math.sqrt(rng.random())
    FLIGHTS.append(dict(t0=t0, x0=rr * math.cos(a), y0=rr * math.sin(a), z0=CEIL - 0.008, vx=0.0, vy=0.0, vz=-0.01, r=0.0035 + 0.0025 * rng.random()))


def landing(f):
    """time, place and target (glass water or table) where a drop lands"""
    zt = level(f["t0"] + 0.4) + 0.0  # into the glass water
    dz = f["z0"] - zt
    T = (f["vz"] + math.sqrt(f["vz"] ** 2 + 2 * G * dz)) / G
    x, y = f["x0"] + f["vx"] * T, f["y0"] + f["vy"] * T
    if math.hypot(x, y) > GR * 0.92:  # missed the glass: lands on the table
        T = (f["vz"] + math.sqrt(f["vz"] ** 2 + 2 * G * f["z0"])) / G
        x, y = f["x0"] + f["vx"] * T, f["y0"] + f["vy"] * T
        return dict(t=f["t0"] + T, x=x, y=y, z=0.0, inGlass=False, r=f["r"])
    return dict(t=f["t0"] + T, x=x, y=y, z=zt, inGlass=True, r=f["r"])


LANDS = [landing(f) for f in FLIGHTS]

if os.environ.get("WATER_EVENTS"):
    ev = dict(realDuration=REAL_DUR, landings=[dict(t=to_real(l["t"]), x=l["x"], inGlass=l["inGlass"], r=l["r"]) for l in LANDS],
              hit=to_real(TL["hit"]), coldHit=TL["hit"] - TL["coldFrom"], rewind=[TL["cold"], TL["cold"] + TL["rewind"]],
              bulge=[to_real(x) for x in TL["bulge"]], rise=[to_real(x) for x in TL["rise"]], braid=[to_real(x) for x in TL["braid"]],
              refill=[to_real(x) for x in TL["refill"]], fade=[to_real(x) for x in TL["fade"]])
    json.dump(ev, open(os.path.join(ROOT, "src", "scenes", "water", "events.json"), "w"), indent=1)
    print("wrote events.json", REAL_DUR)
    sys.exit(0)

# ---------------- scene ----------------
os.makedirs(OUT, exist_ok=True)
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
scene.cycles.max_bounces = 16
scene.cycles.transmission_bounces = 16
scene.cycles.transparent_max_bounces = 16
scene.cycles.caustics_reflective = False
scene.cycles.caustics_refractive = False
scene.render.use_persistent_data = True
res = os.environ.get("WATER_RES", "1080x1920").split("x")
scene.render.resolution_x, scene.render.resolution_y = int(res[0]), int(res[1])
scene.render.image_settings.file_format = "PNG"
try:
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
except Exception:
    pass
scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.03, 0.08, 0.2, 1)  # blue fill so the glass and water never go black inside


def principled(name, color, metal=0.0, rough=0.1, coat=0.0, trans=0.0, ior=1.45):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["IOR"].default_value = ior
    return m


water = principled("Water", (1, 1, 1), rough=0.0, trans=1.0, ior=1.333)
wab = water.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
wab.inputs["Color"].default_value = (0.7, 0.88, 1.0, 1)
wab.inputs["Density"].default_value = 2.5
water.node_tree.links.new(wab.outputs[0], water.node_tree.nodes["Material Output"].inputs["Volume"])
glass = principled("Glass", (1, 1, 1), rough=0.0, trans=1.0, ior=1.5)
stone = principled("BlackStone", (0.006, 0.008, 0.012), rough=0.08, coat=0.8)
_sn = stone.node_tree.nodes
_nz = _sn.new("ShaderNodeTexNoise")
_nz.inputs["Scale"].default_value = 40.0
_rr = _sn.new("ShaderNodeMapRange")
_rr.inputs["To Min"].default_value = 0.04
_rr.inputs["To Max"].default_value = 0.16
stone.node_tree.links.new(_nz.outputs["Fac"], _rr.inputs["Value"])
stone.node_tree.links.new(_rr.outputs["Result"], _sn["Principled BSDF"].inputs["Roughness"])

# table
bpy.ops.mesh.primitive_plane_add(size=3.0)
table = bpy.context.active_object
table.data.materials.append(stone)

# the caustic wall behind: moving web of light, deep ocean blue -> cyan -> white (fills every edge with detail)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0.9, 0.3), rotation=(math.radians(90), 0, 0))
wall = bpy.context.active_object
wall.scale = (2.4, 1.8, 1)
cw = bpy.data.materials.new("Caustics")
cw.use_nodes = True
cn = cw.node_tree.nodes
cn.clear()
co = cn.new("ShaderNodeOutputMaterial")
ce = cn.new("ShaderNodeEmission")
ctc = cn.new("ShaderNodeTexCoord")
cvo = cn.new("ShaderNodeTexVoronoi")
cvo.voronoi_dimensions = "4D"
cvo.feature = "DISTANCE_TO_EDGE"
cvo.inputs["Scale"].default_value = 22.0
cw_noise = cn.new("ShaderNodeTexNoise")
cw_noise.noise_dimensions = "4D"
cw_noise.inputs["Scale"].default_value = 1.6
cmix = cn.new("ShaderNodeVectorMath")
cmix.operation = "MULTIPLY_ADD"
cmix.inputs[2].default_value = (0, 0, 0)
cramp = cn.new("ShaderNodeValToRGB")
cramp.color_ramp.elements[0].position = 0.0
cramp.color_ramp.elements[0].color = (0.75, 0.95, 1.0, 1)
_e = cramp.color_ramp.elements.new(0.0025)
_e.color = (0.0, 0.55, 1.0, 1)
cramp.color_ramp.elements[2].position = 0.008
cramp.color_ramp.elements[2].color = (0.0, 0.05, 0.22, 1)
L_ = cw.node_tree.links
L_.new(cw_noise.outputs["Color"], cmix.inputs[0])
cmix.inputs[1].default_value = (0.25, 0.25, 0.25)  # a gentle warp, not a blob
L_.new(ctc.outputs["Object"], cmix.inputs[2])
L_.new(ctc.outputs["Object"], cw_noise.inputs["Vector"])
L_.new(cmix.outputs[0], cvo.inputs["Vector"])
L_.new(cvo.outputs["Distance"], cramp.inputs["Fac"])
L_.new(cramp.outputs["Color"], ce.inputs["Color"])
ce.inputs["Strength"].default_value = 2.0
L_.new(ce.outputs[0], co.inputs["Surface"])
wall.data.materials.append(cw)
wall.visible_shadow = False

# the glass (open cylinder with thickness)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=GR + 0.0025, depth=GH, location=(0, 0, GH / 2))
gl = bpy.context.active_object
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
for p in gl.data.polygons:
    p.select = p.normal.z > 0.9
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="FACE")
bpy.ops.object.mode_set(mode="OBJECT")
sol = gl.modifiers.new("Thick", "SOLIDIFY")
sol.thickness = 0.0025
gl.data.materials.append(glass)
bpy.ops.object.shade_smooth()

# the water in the glass: a disc-topped cylinder rebuilt each frame (ripples on the surface)
NR, NA = 40, 96
wv, wf = [], []
for ri in range(NR + 1):
    rr_ = GR * ri / NR
    for ai in range(NA):
        a = TAU * ai / NA
        wv.append((rr_ * math.cos(a), rr_ * math.sin(a), 1.0))
for ri in range(NR):
    for ai in range(NA):
        n_ = (ai + 1) % NA
        wf.append((ri * NA + ai, ri * NA + n_, (ri + 1) * NA + n_, (ri + 1) * NA + ai))
top0 = len(wv)
for ai in range(NA):  # the outer wall down to the bottom
    a = TAU * ai / NA
    wv.append((GR * math.cos(a), GR * math.sin(a), 0.0))
for ai in range(NA):
    n_ = (ai + 1) % NA
    wf.append((NR * NA + ai, NR * NA + n_, top0 + n_, top0 + ai))
wf.append(tuple(top0 + ai for ai in range(NA - 1, -1, -1)))
wmesh = bpy.data.meshes.new("GlassWater")
wmesh.from_pydata(wv, [], wf)
gwater = bpy.data.objects.new("GlassWater", wmesh)
scene.collection.objects.link(gwater)
gwater.data.materials.append(water)
for p in wmesh.polygons:
    p.use_smooth = True
WV0 = np.array(wv)
WR = np.hypot(WV0[:, 0], WV0[:, 1])
WTOP = np.arange(len(wv)) < top0

# the rising column + three braid strands: tubes rebuilt each frame
NS, NV = 220, 24
TUBES = []
for j in range(4):
    tv, tf = [], []
    for i in range(NS):
        for v in range(NV):
            tv.append((0, 0, 0))
    for i in range(NS - 1):
        for v in range(NV):
            n_ = (v + 1) % NV
            tf.append((i * NV + v, i * NV + n_, (i + 1) * NV + n_, (i + 1) * NV + v))
    tm = bpy.data.meshes.new(f"Tube{j}")
    tm.from_pydata(tv, [], tf)
    to = bpy.data.objects.new(f"Tube{j}", tm)
    scene.collection.objects.link(to)
    to.data.materials.append(water)
    for p in tm.polygons:
        p.use_smooth = True
    TUBES.append(to)
ANG = np.linspace(0, TAU, NV, endpoint=False)

# the glass ceiling and the water sheet that spreads under it
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, CEIL + 0.004))
ceil = bpy.context.active_object
ceil.scale = (0.5, 0.5, 0.008)
ceil.data.materials.append(glass)
SR, SA = 30, 96
sv, sf = [], []
for ri in range(SR + 1):
    for ai in range(SA):
        a = TAU * ai / SA
        sv.append((ri / SR * math.cos(a), ri / SR * math.sin(a), 0.0))
for ri in range(SR):
    for ai in range(SA):
        n_ = (ai + 1) % SA
        sf.append((ri * SA + ai, ri * SA + n_, (ri + 1) * SA + n_, (ri + 1) * SA + ai))
smesh = bpy.data.meshes.new("Sheet")
smesh.from_pydata(sv, [], sf)
sheet = bpy.data.objects.new("Sheet", smesh)
scene.collection.objects.link(sheet)
sheet.data.materials.append(water)
for p in smesh.polygons:
    p.use_smooth = True
SV0 = np.array(sv)
SRAD = np.hypot(SV0[:, 0], SV0[:, 1])

# droplets
DROPS = []
for i in range(len(FLIGHTS)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
    d = bpy.context.active_object
    d.data.materials.append(water)
    bpy.ops.object.shade_smooth()
    d.scale = (0, 0, 0)
    DROPS.append(d)


def area(name, loc, size, power, color, target=(0, 0, 0.15)):
    l = bpy.data.lights.new(name, "AREA")
    l.shape = "RECTANGLE"
    l.size, l.size_y = size
    l.energy = power
    l.color = color
    o = bpy.data.objects.new(name, l)
    o.location = loc
    scene.collection.objects.link(o)
    o.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False
    return o


area("Key", (-0.45, -0.35, 0.6), (0.3, 0.6), 60, (0.95, 0.97, 1.0))
area("Rim", (0.4, 0.4, 0.35), (0.06, 0.6), 30, (0.4, 0.8, 1.0))
area("Fill", (0.5, -0.4, 0.2), (0.4, 0.4), 12, (0.6, 0.75, 1.0))

cd = bpy.data.cameras.new("Cam")
cd.lens = 42
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 2.2
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


def ripple_h(x, y, s, lands, cx=0.0, cy=0.0):
    h = np.zeros_like(x)
    for l in lands:
        a = s - l["t"]
        if 0 < a < 1.2:
            d = np.hypot(x - l["x"], y - l["y"])
            h += (0.0012 + 0.25 * l["r"]) * np.exp(-a * 3.2) * np.sin(TAU * (d / 0.008 - a * 3.0)) * np.exp(-((d - 0.06 * a) / 0.012) ** 2)
    return h


def frame(f):
    r = f / FPS
    s = story(r)
    lv, tp, bs = level(s), tip(s), base(s)
    # --- glass water: surface with a bulge where the column leaves, ripples where drops land ---
    v = WV0.copy()
    z = np.full(len(v), lv)
    bul = sm(TL["bulge"][0], TL["bulge"][1], s) * (1 - sm(TL["tailUp"][0], TL["tailUp"][0] + 0.6, s))
    z += 0.006 * bul * np.exp(-(WR / 0.012) ** 2)
    z += 0.0008 * math.sin(TAU * 1.7 * s) * np.cos(WR / GR * math.pi) * (1 - sm(16.5, 18.0, s))  # a living slosh
    z += ripple_h(v[:, 0], v[:, 1], s, [l for l in LANDS if l["inGlass"]])
    v[:, 2] = np.where(WTOP, z, 0.0005)
    gwater.data.vertices.foreach_set("co", v.astype(np.float32).ravel())
    gwater.data.update()
    # --- the column and the braid ---
    show = tp > bs + 0.004
    braid = sm(TL["braid"][0], TL["braid"][1], s)
    for j, to in enumerate(TUBES):
        if not show or (j == 0 and braid > 0.98) or (j > 0 and braid < 0.02):
            to.hide_render = True
            continue
        to.hide_render = False
        u = np.linspace(0, 1, NS)
        zc = bs + (tp - bs) * u
        thin = 1 - 0.3 * sm(TL["rise"][0], TL["rise"][1], s)
        rad0 = 0.024 * thin * (1 - 0.3 * u)  # a thick, unmistakable column of water
        rad0 *= np.sqrt(np.clip((1 - u) / 0.06, 0, 1)) * 0.6 + 0.4 * (u < 0.94)  # a rounded tip
        rad0 *= 1 + 0.08 * np.sin(TAU * (zc / 0.03 - s * 1.4))  # travelling surface waves (it is liquid)
        tw = TAU * (zc - bs) / 0.12 + s * 1.6  # a slow, wide twist (water rope, not a chain)  # the twist climbs with the water
        if j == 0:
            rad = rad0 * (1 - braid)
            cx = 0.0015 * np.sin(zc * 60 + s * 2)
            cy = 0.0015 * np.cos(zc * 50 + s * 1.7)
        else:
            rad = rad0 * 0.6 * braid
            br = 0.011 * braid * np.clip(u / 0.08, 0, 1)
            ph = tw + TAU * (j - 1) / 3
            cx, cy = br * np.cos(ph), br * np.sin(ph)
        rad = np.maximum(rad, 1e-5)
        X = cx[:, None] + rad[:, None] * np.cos(ANG)[None, :]
        Y = cy[:, None] + rad[:, None] * np.sin(ANG)[None, :]
        Z = np.repeat(zc[:, None], NV, axis=1)
        co_ = np.stack([X, Y, Z], -1).reshape(-1, 3)
        to.data.vertices.foreach_set("co", co_.astype(np.float32).ravel())
        to.data.update()
    # --- the sheet under the ceiling ---
    hk = s - TL["hit"]
    if hk > 0:
        R = 0.02 + 0.16 * (1 - math.exp(-hk * 2.4)) * (1 - 0.6 * sm(TL["rain"][0], TL["rain"][1] + 1, s))
        thick = 0.007 * (1 - sm(TL["rain"][1] - 0.5, TL["rain"][1] + 1.2, s))
        sv_ = SV0.copy()
        sv_[:, 0] *= R
        sv_[:, 1] *= R
        rad_ = SRAD * R
        edge = np.clip(1 - SRAD, 0, 1) ** 0.5
        sv_[:, 2] = CEIL - thick * edge - 0.0012 * np.sin(TAU * (rad_ / 0.012 - hk * 2.5)) * np.exp(-hk * 1.2) * edge
        sheet.data.vertices.foreach_set("co", sv_.astype(np.float32).ravel())
        sheet.data.update()
        sheet.hide_render = thick < 2e-4
    else:
        sheet.hide_render = True
    # --- droplets ---
    for d, fl in zip(DROPS, FLIGHTS):
        a = s - fl["t0"]
        l = LANDS[FLIGHTS.index(fl)]
        if a < 0 or s > l["t"]:
            d.scale = (0, 0, 0)
            continue
        vz = fl["vz"] - G * a
        sp = math.sqrt(fl["vx"] ** 2 + fl["vy"] ** 2 + vz * vz)
        st = 1 + 1.3 * min(1.0, sp / 0.5)
        d.location = (fl["x0"] + fl["vx"] * a, fl["y0"] + fl["vy"] * a, fl["z0"] + fl["vz"] * a - 0.5 * G * a * a)
        d.rotation_euler = (mathutils.Vector((fl["vx"], fl["vy"], vz)).to_track_quat("Z", "Y")).to_euler()
        d.scale = (fl["r"] / math.sqrt(st), fl["r"] / math.sqrt(st), fl["r"] * st)
    # --- the wall caustics move like light through a pool ---
    cvo.inputs["W"].default_value = r * 0.35
    cw_noise.inputs["W"].default_value = r * 0.2
    # --- camera: follows the water up, wider for the splash, back down with the rain; low and close ---
    follow = min(tp, CEIL - 0.015)  # keep the ceiling splash in frame
    up = sm(TL["rise"][0] + 0.5, TL["rise"][1], s) * (1 - sm(TL["rain"][0] + 0.8, TL["refill"][1], s))
    look = mathutils.Vector((0, 0, 0.06 + (follow - 0.03 - 0.06) * up))
    dist = 0.3 + 0.07 * up + 0.04 * sm(TL["fade"][0], TL["fade"][1], s)
    yaw = math.radians(-12 + 24 * min(1.0, r / REAL_DUR))
    elv = math.radians(6 + 4 * up)
    pos = look + mathutils.Vector((math.sin(yaw) * math.cos(elv), -math.cos(yaw) * math.cos(elv), math.sin(elv))) * dist
    cam.location = pos
    cam.rotation_euler = (look - pos).to_track_quat("-Z", "Y").to_euler()
    cd.dof.focus_distance = (look - pos).length
    scene.render.filepath = os.path.join(OUT, f"f_{f:04d}.png")
    bpy.ops.render.render(write_still=True)


N = int(round(REAL_DUR * FPS))
todo = ONLY if ONLY is not None else list(range(K, N, NN))
t_start = time.time()
for i, f in enumerate(todo):
    if ONLY is None and os.path.exists(os.path.join(OUT, f"f_{f:04d}.png")):
        continue
    frame(f)
    if i % 20 == 0:
        print(f"frame {f} ({i + 1}/{len(todo)}) {(time.time() - t_start) / (i + 1):.2f} s/frame", flush=True)
print(f"done {len(todo)} frames in {time.time() - t_start:.0f} s", flush=True)
