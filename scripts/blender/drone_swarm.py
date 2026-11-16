# 0025 "Drone Swarm" (owner pick, Nov 17 2026: cyber/tech direction - "show the new world through objects + VFX";
# no cars, cities, AI video, faces). Hundreds of small quadcopter drones in a dark hangar.
# Beat sheet (~20 s, real seconds) - this file currently builds the look + the cold-open still:
#   0.0-0.6  COLD OPEN: a black flight case snaps open and the swarm ERUPTS at the lens (props a blur, LEDs streaking)
#   0.6-2.0  fast rewind into the closed case
#   2-6      the lid opens, drones lift out in waves, spiral up into the haze
#   6-9      they lock into a spinning RING of light
#   9-12     the ring twists into a double SPIRAL, LEDs turn magenta
#   12-15    a red LASER GRID sweeps the hangar, the swarm splits and threads through the gaps
#   15-17.5  they snap into a rotating TESSERACT (cube in a cube), LEDs white
#   17.5-20  ENDING: they dive back into the case one by one, lights go out in sequence, the lid clicks shut, fade
# Usage: blender -b --factory-startup -P scripts/blender/drone_swarm.py -- <outdir> <samples>
#   env DS_PCT=50 (resolution %), DS_STILL=A (the cold open)
import math
import os
import sys

import bpy
import mathutils
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(argv[0])
SAMPLES = int(argv[1]) if len(argv) > 1 else 64
os.makedirs(OUT, exist_ok=True)
TAU = 2 * math.pi
rng = np.random.default_rng(2525)

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
scene.cycles.max_bounces = 6
scene.cycles.glossy_bounces = 4
scene.cycles.volume_bounces = 1
scene.cycles.volume_step_rate = 4.0
scene.cycles.sample_clamp_indirect = 4.0  # no speckle fireflies on the metal
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.resolution_percentage = int(os.environ.get("DS_PCT", "100"))
scene.view_settings.view_transform = "Khronos PBR Neutral"  # AgX bleaches bright cyan emission to white
scene.view_settings.exposure = -0.6

w = bpy.data.worlds.new("Hangar")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.0025, 0.004, 1)


def mat(name, color, metal=0.0, rough=0.4, coat=0.0, emit=None, es=0.0, trans=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    b.inputs["Alpha"].default_value = alpha
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = es
    return m


M_BODY = mat("Carbon", (0.012, 0.012, 0.014), rough=0.28, coat=0.8)
M_ARM = mat("ArmChrome", (0.75, 0.76, 0.8), metal=1.0, rough=0.18)
M_LED = mat("LED", (1, 1, 1), emit=(0.55, 0.85, 1.0), es=120.0)
M_RED = mat("NavRed", (1, 0, 0), emit=(1.0, 0.04, 0.03), es=80.0)
M_BLUE = mat("NavBlue", (0, 0, 1), emit=(0.05, 0.25, 1.0), es=80.0)
# spinning props: a thin disc, darker towards the hub, mostly see-through (reads as a motion-blurred propeller)
M_PROP = bpy.data.materials.new("PropBlur")
M_PROP.use_nodes = True
_pn, _pl = M_PROP.node_tree.nodes, M_PROP.node_tree.links
_pb = _pn["Principled BSDF"]
_pb.inputs["Base Color"].default_value = (0.05, 0.05, 0.06, 1)
_pb.inputs["Roughness"].default_value = 0.3
_pb.inputs["Alpha"].default_value = 0.07
M_PROP.blend_method = "BLEND" if hasattr(M_PROP, "blend_method") else None


def box(cx, cy, cz, sx, sy, sz):
    v = [(cx + x * sx, cy + y * sy, cz + z * sz) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return v, f


def cyl(cx, cy, cz, r, h, n=20, axis="z"):
    v, f = [], []
    for k in (-1, 1):
        for i in range(n):
            a = i / n * TAU
            p = [r * math.cos(a), r * math.sin(a), k * h / 2]
            if axis == "x":
                p = [p[2], p[0], p[1]]
            elif axis == "y":
                p = [p[0], p[2], p[1]]
            v.append((cx + p[0], cy + p[1], cz + p[2]))
    for i in range(n):
        f.append((i, (i + 1) % n, (i + 1) % n + n, i + n))
    f.append(tuple(range(n - 1, -1, -1)))
    f.append(tuple(range(n, 2 * n)))
    return v, f


def build_drone():
    """one quadcopter (unit ~0.16 across): carbon body, chrome X-arms, motor cans, blurred props, LEDs"""
    parts = []  # (verts, faces, material index)
    mats = [M_BODY, M_ARM, M_PROP, M_LED, M_RED, M_BLUE]
    parts.append((*box(0, 0, 0, 0.032, 0.022, 0.009), 0))           # body
    parts.append((*box(0, 0, 0.011, 0.02, 0.014, 0.004), 0))        # battery hump
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        ax, ay = sx * 0.055, sy * 0.055
        v, f = cyl(ax / 2, ay / 2, 0, 0.0045, 0.078, 10, "x")
        ang = math.atan2(ay, ax)
        v = [(ax / 2 + (x - ax / 2) * math.cos(ang) - (y - ay / 2) * math.sin(ang),
              ay / 2 + (x - ax / 2) * math.sin(ang) + (y - ay / 2) * math.cos(ang), z) for x, y, z in v]
        parts.append((v, f, 1))                                       # arm
        parts.append((*cyl(ax, ay, 0.006, 0.009, 0.014, 16), 1))       # motor can
        parts.append((*cyl(ax, ay, 0.015, 0.042, 0.0015, 32), 2))      # prop disc
        parts.append((*cyl(ax, ay, -0.003, 0.004, 0.004, 10), 4 if sx > 0 else 5))  # nav light under each motor
    parts.append((*cyl(0, 0, -0.011, 0.012, 0.003, 20), 3))           # main LED ring underneath
    V, F, MI = [], [], []
    for v, f, mi in parts:
        o = len(V)
        V += v
        F += [tuple(i + o for i in face) for face in f]
        MI += [mi] * len(f)
    me = bpy.data.meshes.new("Drone")
    me.from_pydata(V, [], F)
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", MI)
    return me


DRONE = build_drone()


# owner, Nov 17: "bigger and more detailed, fewer (40), futuristic smooth capsules with glowing rings"
M_SHELL = mat("Gunmetal", (0.4, 0.42, 0.46), metal=1.0, rough=0.24, coat=1.0)  # brushed-looking metal: catches the light
M_TRIM = mat("ChromeTrim", (0.85, 0.86, 0.9), metal=1.0, rough=0.06)
M_RING = mat("RingGlow", (0, 0, 0), emit=(0.25, 0.85, 1.0), es=90.0)
M_SEAM = mat("Seam", (0.002, 0.002, 0.003), rough=0.6)


def _lathe(profile, n=72):
    """revolve a (r, z) profile around z -> verts, quad faces"""
    V = [(r * math.cos(a), r * math.sin(a), z) for (r, z) in profile for a in np.linspace(0, TAU, n, endpoint=False)]
    F = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j)
         for i in range(len(profile) - 1) for j in range(n)]
    return V, F


def _torus(R, r, z=0.0, n=96, m=24):
    V = [((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a), z + r * math.sin(b))
         for a in np.linspace(0, TAU, n, endpoint=False) for b in np.linspace(0, TAU, m, endpoint=False)]
    F = [(i * m + j, i * m + (j + 1) % m, ((i + 1) % n) * m + (j + 1) % m, ((i + 1) % n) * m + j)
         for i in range(n) for j in range(m)]
    return V, F


def _rot_x(v, ang):
    c, s_ = math.cos(ang), math.sin(ang)
    return [(x, y * c - z * s_, y * s_ + z * c) for x, y, z in v]


def _place(v, dx=0.0, dy=0.0, dz=0.0, yaw=0.0):
    c, s_ = math.cos(yaw), math.sin(yaw)
    return [(x * c - y * s_ + dx, x * s_ + y * c + dy, z + dz) for x, y, z in v]


def build_capsule():
    """detailed futuristic pod ~0.4 m tall (owner, Nov 17: "more details"): gunmetal egg shell with vertical panel
    seams, a chrome waist band, a thin VERTICAL gyro ring on two chrome pivots (no Saturn ring), side vents, a cyan
    light strip, three small thrusters with a blue glow underneath (no single eye-like light), a top antenna"""
    parts = []
    prof = [(0.0, 0.17)] + [(0.13 * math.sin(t) * (1 - 0.15 * math.cos(t)), 0.17 * math.cos(t)) for t in np.linspace(0.06, math.pi - 0.06, 30)] + [(0.0, -0.17)]
    parts.append((*_lathe(prof, 96), 0))                               # shell
    parts.append((*_torus(0.131, 0.007, 0.0), 1))                      # chrome waist band
    parts.append((*_torus(0.118, 0.0025, 0.075), 3))                   # horizontal seams
    parts.append((*_torus(0.118, 0.0025, -0.075), 3))
    for k in range(6):                                                 # vertical panel seams
        yaw = k / 6 * TAU
        v, f = box(0.0, 0.0, 0.0, 0.0022, 0.0022, 0.155)
        v = [(x + 0.123 * (1 - (z / 0.17) ** 2) ** 0.5 + 0.004, y, z) for x, y, z in v]
        parts.append((_place(v, yaw=yaw), f, 3))
    for k in range(4):                                                 # side vents: dark slots with chrome lips
        yaw = k / 4 * TAU + math.pi / 4
        for j in range(3):
            v, f = box(0.128, 0.0, 0.035 - j * 0.016, 0.006, 0.026, 0.0035)
            parts.append((_place(v, yaw=yaw), f, 3))
        v, f = box(0.13, 0.0, 0.019, 0.004, 0.032, 0.03)
        parts.append((_place(v, yaw=yaw), f, 1))
    v, f = box(0.0, 0.0, 0.0, 0.004, 0.06, 0.004)                      # cyan light strip along the front
    parts.append((_place([(x + 0.131, y, z + 0.05) for x, y, z in v]), f, 2))
    ring_v, ring_f = _torus(0.215, 0.0075, 0.0, 128, 16)               # the thin vertical gyro ring
    parts.append((_rot_x(ring_v, math.pi / 2), ring_f, 0))
    for gr in (0.2045, 0.2255):                                         # glowing strips on the ring's inner + outer edge
        glow_v, glow_f = _torus(gr, 0.0042, 0.0, 128, 10)
        parts.append((_rot_x(glow_v, math.pi / 2), glow_f, 2))
    for sx in (-1, 1):                                                 # chrome pivots holding the ring
        parts.append((*cyl(sx * 0.17, 0, 0, 0.012, 0.09, 16, "x"), 1))
        parts.append((*cyl(sx * 0.21, 0, 0, 0.018, 0.02, 20, "x"), 1))
    for k in range(3):                                                 # three small thrusters underneath
        yaw = k / 3 * TAU
        tx, ty = 0.06 * math.cos(yaw), 0.06 * math.sin(yaw)
        parts.append((*cyl(tx, ty, -0.15, 0.022, 0.035, 20), 1))
        parts.append((*cyl(tx, ty, -0.168, 0.015, 0.004, 20), 2))
    parts.append((*cyl(0, 0, 0.2, 0.0025, 0.07, 8), 1))                # antenna
    parts.append((*cyl(0, 0, 0.236, 0.006, 0.006, 12), 2))             # antenna tip light
    V, F, MI = [], [], []
    for v, f, mi in parts:
        o = len(V)
        V += v
        F += [tuple(i + o for i in face) for face in f]
        MI += [mi] * len(f)
    me = bpy.data.meshes.new("Capsule")
    me.from_pydata(V, [], F)
    for m in (M_SHELL, M_TRIM, M_RING, M_SEAM):
        me.materials.append(m)
    me.polygons.foreach_set("material_index", MI)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


DRONE = build_capsule()

# owner, Nov 17: "THIS is a drone" (photo of a real consumer quadcopter) -> realistic quad replaces the capsules
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "drone_model.py"), encoding="utf-8").read())
DRONE = build_real_drone(spin=os.environ.get("DS_SPIN", "1") == "1")
DRONE_IDLE = build_real_drone(spin=False)
DRONE_SPIN = build_real_drone(spin=True)
DRONE_BODY = build_real_drone(spin=False, props=False)
PROP = build_prop()
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5
scene.frame_set(1)


def add_real(name, loc, rot, spinning=True):
    """a drone body + 4 separate props parented to it; spinning props get keyframes so Cycles blurs them for real"""
    body = bpy.data.objects.new(name, DRONE_BODY)
    scene.collection.objects.link(body)
    body.location = loc
    body.rotation_euler = rot
    for j, mp in enumerate(MOTOR_POS):
        pr = bpy.data.objects.new(f"{name}_p{j}", PROP)
        scene.collection.objects.link(pr)
        pr.parent = body
        pr.location = mp
        a0 = rng.uniform(0, TAU)
        sgn = 1 if j in (0, 3) else -1
        pr.rotation_euler = (0, 0, a0)
        if spinning:
            for fr, ang in ((0, a0 - sgn * 1.4), (1, a0), (2, a0 + sgn * 1.4)):
                pr.rotation_euler = (0, 0, ang)
                pr.keyframe_insert("rotation_euler", frame=fr)
    return body


def add_drone(i, p, yaw, tilt, scale=1.0):
    o = bpy.data.objects.new(f"Dr{i}", DRONE)
    scene.collection.objects.link(o)
    o.location = p
    o.rotation_euler = (tilt[0], tilt[1], yaw)
    o.scale = (scale, scale, scale)
    return o


# --- hangar: glossy dark concrete floor, a far back wall with vertical light strips, haze ---
floor_m = bpy.data.materials.new("Concrete")
floor_m.use_nodes = True
fn, fl = floor_m.node_tree.nodes, floor_m.node_tree.links
fb = fn["Principled BSDF"]
fb.inputs["Base Color"].default_value = (0.02, 0.021, 0.024, 1)
fno = fn.new("ShaderNodeTexNoise")
fno.inputs["Scale"].default_value = 3.0
fno.inputs["Detail"].default_value = 10.0
fmr = fn.new("ShaderNodeMapRange")
fmr.inputs["To Min"].default_value = 0.08
fmr.inputs["To Max"].default_value = 0.45
fl.new(fno.outputs["Fac"], fmr.inputs["Value"])
fl.new(fmr.outputs["Result"], fb.inputs["Roughness"])
fv = [(-40, -40, 0), (40, -40, 0), (40, 40, 0), (-40, 40, 0)]
fme = bpy.data.meshes.new("Floor")
fme.from_pydata(fv, [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new("Floor", fme)
scene.collection.objects.link(floor)
floor.data.materials.append(floor_m)

wall_m = mat("Wall", (0.015, 0.016, 0.02), rough=0.7)
wv, wf = box(0, 14, 6, 30, 0.2, 6)
wme = bpy.data.meshes.new("Wall")
wme.from_pydata(wv, [], wf)
wall = bpy.data.objects.new("Wall", wme)
scene.collection.objects.link(wall)
wall.data.materials.append(wall_m)
strip_m = mat("Strip", (1, 1, 1), emit=(0.8, 0.9, 1.0), es=0.8)
for i in range(13):
    x = -12 + i * 2.0
    sv, sf = box(x, 13.75, 4.5, 0.06, 0.05, 4.0)
    sme = bpy.data.meshes.new(f"S{i}")
    sme.from_pydata(sv, [], sf)
    so = bpy.data.objects.new(f"S{i}", sme)
    scene.collection.objects.link(so)
    so.data.materials.append(strip_m)
    so.visible_camera = False  # light the scene, never seen directly (grey bars flattened the background)
# ceiling light bars (seen as reflections on the floor and the carbon)
for i in range(5):
    sv, sf = box(-4 + i * 2.0, 4.0, 7.5, 0.08, 6.0, 0.03)
    sme = bpy.data.meshes.new(f"C{i}")
    sme.from_pydata(sv, [], sf)
    so = bpy.data.objects.new(f"C{i}", sme)
    scene.collection.objects.link(so)
    so.data.materials.append(strip_m)
    so.visible_camera = False  # light the scene, never seen directly (grey bars flattened the background)

# haze: a thin volume box over the stage so light strips and LEDs glow in the air
haze_m = bpy.data.materials.new("Haze")
haze_m.use_nodes = True
hn = haze_m.node_tree.nodes
hn.remove(hn["Principled BSDF"])
hv = hn.new("ShaderNodeVolumePrincipled")
hv.inputs["Density"].default_value = 0.012
hv.inputs["Anisotropy"].default_value = 0.55
haze_m.node_tree.links.new(hv.outputs[0], hn["Material Output"].inputs["Volume"])
hzv, hzf = box(0, 4, 4, 14, 11, 4)
hme = bpy.data.meshes.new("HazeBox")
hme.from_pydata(hzv, [], hzf)
haze = bpy.data.objects.new("HazeBox", hme)
scene.collection.objects.link(haze)
haze.data.materials.append(haze_m)

# --- the flight case: black ribbed shell with aluminium edges, lid open, grey foam inside ---
case_m = mat("CaseShell", (0.006, 0.006, 0.007), rough=0.6)
alu_m = mat("Alu", (0.8, 0.8, 0.82), metal=1.0, rough=0.25)
foam_m = mat("Foam", (0.03, 0.03, 0.035), rough=0.95)


def obj(name, vf, m, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata(*vf[:1], [], vf[1]) if False else me.from_pydata(vf[0], [], vf[1])
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(m)
    o.location = loc
    o.rotation_euler = rot
    return o


obj("CaseBase", box(0, 0, 0.16, 0.7, 0.45, 0.16), case_m)
obj("CaseFoam", box(0, 0, 0.3, 0.66, 0.41, 0.03), foam_m)
for sx in (-1, 1):
    obj(f"CaseEdgeX{sx}", box(sx * 0.7, 0, 0.32, 0.015, 0.46, 0.015), alu_m)
    obj(f"CaseEdgeY{sx}", box(0, sx * 0.45, 0.32, 0.71, 0.015, 0.015), alu_m)
lid = obj("CaseLid", box(0, 0.0, 0.45, 0.7, 0.04, 0.45), case_m, loc=(0, 0.47, 0.32), rot=(math.radians(-100), 0, 0))  # flung open flat behind
# foam cut-outs: a grid of empty pockets the drones came out of
for ix in range(6):
    for iy in range(4):
        obj(f"Pocket{ix}_{iy}", box(-0.55 + ix * 0.22, -0.3 + iy * 0.2, 0.331, 0.08, 0.07, 0.002),
            mat(f"PocketM{ix}{iy}", (0.004, 0.004, 0.005), rough=1.0))

# --- lights ---
def area(name, loc, look, size, energy, color, sy=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size = size
    if sy is not None:
        ld.size_y = sy
    ld.energy = energy
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    scene.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = (mathutils.Vector(look) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    lo.visible_camera = False


area("Key", (-3.0, -1.5, 5.0), (0, 1.0, 1.0), 1.5, 500, (0.85, 0.9, 1.0))
area("Rim", (2.5, 6.0, 3.0), (0, 1.0, 1.2), 2.0, 900, (0.5, 0.7, 1.0))
area("Up", (0.0, 0.0, 0.36), (0, 0, 3.0), 0.9, 60, (0.5, 0.8, 1.0))
# light beams from high behind the stage, cutting through the haze (the classic hangar look)
for _i, (_x, _c) in enumerate(((-2.5, (0.3, 0.7, 1.0)), (0.0, (0.9, 0.95, 1.0)), (2.5, (0.3, 0.7, 1.0)))):
    _sd = bpy.data.lights.new(f"Beam{_i}", "SPOT")
    _sd.energy = 4000
    _sd.color = _c
    _sd.spot_size = math.radians(18)
    _sd.spot_blend = 0.4
    _sd.shadow_soft_size = 0.05
    _so = bpy.data.objects.new(f"Beam{_i}", _sd)
    scene.collection.objects.link(_so)
    _so.location = (_x, 6.0, 7.5)
    _so.rotation_euler = (mathutils.Vector((0.4 * _x, 0.0, 0.0)) - mathutils.Vector(_so.location)).to_track_quat("-Z", "Y").to_euler()
      # glow from inside the open case

# --- camera ---
cd = bpy.data.cameras.new("Cam")
cd.sensor_fit = "VERTICAL"
cd.sensor_height = 24
cd.dof.use_dof = True
cd.dof.aperture_fstop = 2.0
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam


def place(loc, look, lens, focus=None):
    cam.location = loc
    d = mathutils.Vector(look) - mathutils.Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.dof.focus_distance = focus if focus else d.length


# light trails: thin glowing ribbons behind each drone (a long-exposure look); brightness fades towards the tail
trail_m = bpy.data.materials.new("Trail")
trail_m.use_nodes = True
_tn, _tl = trail_m.node_tree.nodes, trail_m.node_tree.links
_tn.clear()
_to = _tn.new("ShaderNodeOutputMaterial")
_te = _tn.new("ShaderNodeEmission")
_ta = _tn.new("ShaderNodeAttribute")
_ta.attribute_name = "fade"
_tc = _tn.new("ShaderNodeAttribute")
_tc.attribute_name = "col"
_tm = _tn.new("ShaderNodeMath")
_tm.operation = "MULTIPLY"
_tm.inputs[1].default_value = 60.0
_tl.new(_ta.outputs["Fac"], _tm.inputs[0])
_tl.new(_tm.outputs[0], _te.inputs["Strength"])
_tl.new(_tc.outputs["Color"], _te.inputs["Color"])
_tl.new(_te.outputs[0], _to.inputs["Surface"])


def add_trails(paths, cols, width=0.004):
    """paths: list of (n,3) point arrays (tail -> head); builds one mesh of flat camera-facing-ish ribbons"""
    V, F, FADE, COL = [], [], [], []
    for pts, c in zip(paths, cols):
        n = len(pts)
        tang = np.gradient(pts, axis=0)
        tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-9
        side = np.cross(tang, cam_dir_global)
        side /= np.linalg.norm(side, axis=1, keepdims=True) + 1e-9
        o = len(V)
        for j in range(n):
            wj = width * (0.3 + 0.7 * j / (n - 1))
            V += [tuple(pts[j] + side[j] * wj), tuple(pts[j] - side[j] * wj)]
            f = (j / (n - 1)) ** 2.5
            FADE += [f, f]
            COL += [c, c]
        for j in range(n - 1):
            F.append((o + 2 * j, o + 2 * j + 1, o + 2 * j + 3, o + 2 * j + 2))
    me = bpy.data.meshes.new("Trails")
    me.from_pydata(V, [], F)
    fa = me.attributes.new("fade", "FLOAT", "POINT")
    fa.data.foreach_set("value", FADE)
    ca = me.attributes.new("col", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", [x for c in COL for x in (*c, 1.0)])
    o = bpy.data.objects.new("Trails", me)
    scene.collection.objects.link(o)
    o.data.materials.append(trail_m)
    o.visible_shadow = False
    return o


cam_dir_global = np.array([0.0, 1.0, 0.0])


def still_a():
    """cold open: the swarm erupts out of the case in glowing streaks, curling up and straight at the lens"""
    global cam_dir_global
    cam_p = np.array([0.35, -1.75, 0.42])
    cam_dir_global = np.array([0.0, 1.0, 0.3])
    n = 34
    offs = rng.normal(0, 1, (n, 3))
    phase = rng.uniform(0, TAU, n)

    def path(k, i):
        base = np.array([0.0, 0.0, 0.4]) * (1 - k) + np.array([0.9, -1.4, 1.1]) * k   # a diagonal arc
        base[2] += 1.7 * math.sin(k * math.pi) * (1 - 0.3 * k)
        base[0] += -0.45 * math.sin(k * math.pi)
        spread = 0.15 + 1.4 * k
        sw = 0.12 * k * np.array([math.cos(phase[i] + 9 * k), math.sin(phase[i] + 9 * k), 0])  # a little swirl
        return base + offs[i] * np.array([spread, spread * 0.6, spread * 0.6]) + sw

    paths, cols = [], []
    for i in range(n):
        k = (i + rng.uniform()) / n
        p = path(k, i)
        if np.linalg.norm(p - cam_p) < 0.6:
            continue
        q = path(min(1.0, k + 0.01), i) - p
        yaw = math.atan2(q[1], q[0])
        add_drone(i, tuple(p), yaw, (rng.normal(0, 0.15) - 0.55, rng.normal(0, 0.2)), scale=0.75)  # pitched forward in flight
        ks = np.linspace(max(0.0, k - 0.07), k - 0.012, 24)
        paths.append(np.array([path(kk, i) for kk in ks]))
        cols.append((0.25, 0.8, 1.0) if i % 9 else (1.0, 0.2, 0.25))
    add_trails(paths, cols)
    place(tuple(cam_p), (0.15, 0.3, 1.4), 18, focus=1.6)


def still_b():
    """a 3/4 front view of one drone (to judge the design against a real one), a few more out of focus behind it"""
    c = np.array([0.0, 0.0, 1.3])
    yaw = 0.5
    view = yaw - math.radians(40)
    cam_p = c + 0.9 * np.array([math.cos(view), math.sin(view), 0.0]) + np.array([0, 0, 0.32])
    add_drone(0, tuple(c), yaw, (0.0, 0.0), scale=1.0)
    for i in range(1, 9):
        add_drone(i, (rng.uniform(-2.5, -0.5), rng.uniform(0.5, 3.0), rng.uniform(0.8, 2.6)), rng.uniform(0, 6), (-0.15, 0.05), 1.0)
    if os.environ.get("DS_LAND"):
        scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    place(tuple(cam_p), tuple(c), 50, focus=float(np.linalg.norm(cam_p - c)))


def still_c():
    """cold open (realistic): 42 drones in rows on the hangar floor take off in a wave from the back towards the lens;
    the front ones are already rising, props a blur, status lights on"""
    for o in list(bpy.data.objects):
        if o.name.startswith(("Case", "Pocket", "Up")):
            bpy.data.objects.remove(o, do_unlink=True)
    rows, cols, sp = 7, 6, 0.62
    k = 0
    for r in range(rows):
        for cidx in range(cols):
            x = (cidx - (cols - 1) / 2) * sp
            y = 0.6 + r * sp
            lift = float(np.clip(1.4 - 0.32 * r + rng.normal(0, 0.05), 0, 1.4))   # the near rows are up already
            z = 0.05 + lift ** 1.6 * 0.9
            add_real(f"Dr{k}", (x + rng.normal(0, 0.03), y, z),
                     (rng.normal(0, 0.03) - 0.06 * min(lift, 1), rng.normal(0, 0.03), math.pi / 2 + rng.normal(0, 0.04)),
                     spinning=lift > 0.05)
            k += 1
    area("HeroKey", (1.8, -1.5, 2.2), (0, 1.5, 0.4), 1.6, 140, (0.95, 0.97, 1.0))
    area("HeroFill", (0.6, -0.9, 0.15), (0.12, 0.25, 0.58), 0.6, 30, (0.9, 0.95, 1.0))  # lifts the near drone out of silhouette
    add_real("DrHero", (0.12, 0.25, 0.58), (-0.12, 0.05, math.pi / 2 + 0.35))  # one rising right in front of the lens
    place((0.3, -0.42, 0.22), (0.05, 1.6, 0.75), 22, focus=0.75)


if os.environ.get("DS_ANIM"):
    exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "drone_anim.py"), encoding="utf-8").read())
    raise SystemExit(0)
STILL = os.environ.get("DS_STILL", "A")
if STILL == "A":
    still_a()
elif STILL == "B":
    still_b()
elif STILL == "C":
    still_c()
scene.render.filepath = os.path.join(OUT, f"still_{STILL}.png")
bpy.ops.render.render(write_still=True)
