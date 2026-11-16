# 0025 "Drone Swarm" animation (exec'd by drone_swarm.py when DS_ANIM=1, after the hangar, the realistic drone model,
# add_real(), area() and place() exist). 42 real-looking quadcopters on the hangar floor; beat map in
# src/scenes/drones/timeline.json (shared with the sound). Real time = story + 2.0 after the cold open + rewind.
#   COLD OPEN (0-0.6): mid take-off, the front drones rising at the lens   | rewind 0.6-2.0 back to the floor
#   take-off wave -> a RING facing the camera (cyan) -> a double HELIX (magenta) -> LANES while red LASER planes sweep
#   through the gaps -> a rotating TESSERACT (white) -> they land back in rows, lights go out one by one, fade.
import json

TL = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src", "scenes", "drones", "timeline.json")))
FPS = int(argv[2]) if len(argv) > 2 else 30
K = int(argv[3]) if len(argv) > 3 else 0
NN = int(argv[4]) if len(argv) > 4 else 1
DUR = TL["duration"]
OPEN, REWIND = TL["open"][1], TL["rewind"][1]

for o in list(bpy.data.objects):
    if o.name.startswith(("Case", "Pocket", "Up", "Dr", "Trails")):
        bpy.data.objects.remove(o, do_unlink=True)


def sm(a, b, x):
    k = min(1.0, max(0.0, (x - a) / (b - a)))
    return k * k * (3 - 2 * k)


def story(r):
    if r < OPEN:
        return TL["hookStory"] + r * 0.5
    if r < REWIND:
        k = (r - OPEN) / (REWIND - OPEN)
        return (TL["hookStory"] + OPEN * 0.5) * (1 - k * k * (3 - 2 * k))
    return r - TL["storyOffset"]


# --- the show LED: one bright RGB light under each drone, colour set per object (Object Info -> Color) ---
show_m = bpy.data.materials.new("ShowLED")
show_m.use_nodes = True
_sn, _sl = show_m.node_tree.nodes, show_m.node_tree.links
_sn.clear()
_so = _sn.new("ShaderNodeOutputMaterial")
_se = _sn.new("ShaderNodeEmission")
_oi = _sn.new("ShaderNodeObjectInfo")
_se.inputs["Strength"].default_value = 9.0  # stays coloured (70 burned out to white)
_sl.new(_oi.outputs["Color"], _se.inputs["Color"])
_sl.new(_se.outputs[0], _so.inputs["Surface"])
LV, LF = _cyl((0.0, 0.0, -0.034), 0.03, 0.008, 32)
led_me = bpy.data.meshes.new("ShowLEDMesh")
led_me.from_pydata(LV, [], LF)
led_me.materials.append(show_m)

N_ROWS, N_COLS, SP = 7, 6, 0.62
N = N_ROWS * N_COLS
GRID = np.array([[(c - (N_COLS - 1) / 2) * SP, 0.6 + r * SP, 0.05] for r in range(N_ROWS) for c in range(N_COLS)])
ROW = np.array([r for r in range(N_ROWS) for c in range(N_COLS)])
C = np.array([0.0, 2.6, 2.4])
# owner, Nov 17: a professional drone model from BlendKit ("Drone" by cgi Moon, royalty free) replaces the hand-built one
BK = os.environ.get("DS_BK", "C:/Users/dev8x/blenderkit_data/models/drone_31efc6b2-3eae-4d76-99d5-0eb482c0a94c/drone_62179f23-2cce-430e-8825-c50f29f67f4a.blend")
USE_BK = os.path.exists(BK)
if USE_BK:
    with bpy.data.libraries.load(BK, link=False) as (src, dst):
        dst.objects = list(src.objects)
    col_body = bpy.data.collections.new("BKBody")
    col_props = bpy.data.collections.new("BKProps")
    for o in dst.objects:
        if o is None:
            continue
        mats = [m.name for m in getattr(o.data, "materials", []) if m] if o.type == "MESH" else []
        (col_props if "Helix" in mats else col_body).objects.link(o)
    # centre + scale the model so it matches the scene (~0.42 m across), body facing +x
    import mathutils as _mu
    scene.collection.children.link(col_body)          # evaluate the parent transforms once
    scene.collection.children.link(col_props)
    bpy.context.view_layer.update()
    _big = [o.name for o in col_body.objects if o.type == "MESH" and max(o.dimensions) > 2.0]
    print("BKDEBUG big objects", _big[:8])
    pts = [o.matrix_world @ _mu.Vector(c) for o in col_body.objects
           if o.type == "MESH" and max(o.dimensions) <= 2.0 for c in o.bound_box]
    lo = _mu.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = _mu.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    span = max(hi.x - lo.x, hi.y - lo.y)
    BK_SCALE = 0.42 / max(span, 1e-6)
    print("BKDEBUG span", span, "scale", BK_SCALE, "lo", tuple(lo), "hi", tuple(hi), "n_body", len(col_body.objects), "n_props", len(col_props.objects))
    BK_OFF = -(lo + hi) / 2
    BK_OFF.z = -lo.z
    for c in (col_body, col_props):
        c.instance_offset = -BK_OFF
    scene.collection.children.unlink(col_body)
    scene.collection.children.unlink(col_props)
    for o in col_body.objects:
        if o.type == "MESH" and max(o.dimensions) > 2.0:
            o.hide_render = True                       # a backdrop/ground that came with the model


def add_bk(name, loc, rot, props=True):
    e = bpy.data.objects.new(name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = col_body
    scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = rot
    e.scale = (BK_SCALE,) * 3
    pr = bpy.data.objects.new(name + "_props", None)
    pr.instance_type = "COLLECTION"
    pr.instance_collection = col_props
    scene.collection.objects.link(pr)
    pr.parent = e
    pr.hide_render = not props
    return e, pr


drones, leds, prop_objs = [], [], []
for i in range(N):
    if USE_BK:
        b, pr = add_bk(f"Dr{i}", tuple(GRID[i]), (0, 0, math.pi / 2))
        prop_objs.append(pr)
    else:
        b = add_real(f"Dr{i}", tuple(GRID[i]), (0, 0, math.pi / 2), spinning=False)
    lo = bpy.data.objects.new(f"Led{i}", led_me)
    scene.collection.objects.link(lo)
    lo.parent = b
    if USE_BK:
        lo.scale = (1 / BK_SCALE,) * 3
    drones.append(b)
    leds.append(lo)
# props: spin for the whole clip (linear keyframes extrapolated), real motion blur from the shutter
for b in drones:
    for pr in b.children:
        if not pr.name.startswith(b.name + "_p"):
            continue
        a0 = pr.rotation_euler[2]
        sgn = 1 if pr.name.endswith(("p0", "p3")) else -1
        for fr, ang in ((0, a0), (1, a0 + sgn * 1.25)):
            pr.rotation_euler = (0, 0, ang)
            pr.keyframe_insert("rotation_euler", frame=fr)
        for fc in pr.animation_data.action.fcurves if hasattr(pr.animation_data.action, "fcurves") else []:
            fc.extrapolation = "LINEAR"
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        try:  # Blender 5 layered actions
            for layer in pr.animation_data.action.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        for fc in cb.fcurves:
                            fc.extrapolation = "LINEAR"
                            for kp in fc.keyframe_points:
                                kp.interpolation = "LINEAR"
        except Exception:
            pass


# --- formations ---
def f_ground(i, s):
    return GRID[i].copy()


def f_lift(i, s):
    p = GRID[i].copy()
    p[2] = 1.1 + 0.25 * ((i * 7) % 5) / 5
    return p


def f_ring(i, s):
    a = TAU * i / N + 0.55 * s
    return C + np.array([2.0 * math.cos(a), 0.0, 2.0 * math.sin(a)])


def f_helix(i, s):
    strand = i % 2
    u = (i // 2) / (N / 2 - 1)
    a = TAU * 1.6 * u + math.pi * strand + 1.1 * s
    return np.array([1.05 * math.cos(a), C[1] + 1.05 * math.sin(a), 0.7 + 3.4 * u])


def f_lanes(i, s):
    r, c = divmod(i, 7)
    return np.array([-1.8 + c * 0.6, C[1], 0.9 + r * 0.55])


_cube = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
_edges = [(a, b) for a in range(8) for b in range(a + 1, 8) if np.sum(np.abs(_cube[a] - _cube[b])) == 2]
TESS = [*(_cube * 1.25), *(_cube * 0.6)]
TESS += [(_cube[a] + _cube[b]) / 2 * 1.25 for a, b in _edges]
TESS += [(_cube[a] + _cube[b]) / 2 * 0.6 for a, b in _edges]
TESS += [_cube[0] * 0.92, _cube[7] * 0.92]
TESS = np.array(TESS[:N])


def f_tess(i, s):
    t = s - TL["tesseract"][0]
    a, b = 0.7 * t + 0.4, 0.35 * math.sin(0.5 * t) + 0.5
    rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return C + rz @ rx @ TESS[i]


def delay(i, kind):
    if kind == "takeoff":
        return 0.3 * ROW[i]                      # the front row first, a wave towards the back
    if kind == "land":
        return 0.045 * ((i * 17) % N)            # one by one in a scattered order
    return 0.35 * (i / N)


SEQ = [(TL["takeoff"][0], f_lift, "takeoff", 0.9), (TL["ring"][0], f_ring, "ring", 1.4), (TL["helix"][0], f_helix, "helix", 1.4),
       (TL["lanes"][0], f_lanes, "lanes", 1.1), (TL["tesseract"][0], f_tess, "tess", 1.3), (TL["land"][0], f_ground, "land", 1.0)]


def pos(i, s):
    p = f_ground(i, s)
    for t0, fn, kind, dur in SEQ:
        k = sm(t0 + delay(i, kind), t0 + delay(i, kind) + dur, s)
        if k <= 0:
            break
        p = p * (1 - k) + fn(i, s) * k
    flying = 0.0 < s - (TL["takeoff"][0] + delay(i, "takeoff")) and s < TL["land"][0] + delay(i, "land") + 1.0
    if flying:
        p = p + 0.02 * np.array([math.sin(3.1 * s + i), math.cos(2.7 * s + 2 * i), math.sin(2.3 * s + 3 * i)])
    return p


COLS = {"ground": (0.75, 0.9, 1.0), "takeoff": (0.75, 0.9, 1.0), "ring": (0.1, 0.85, 1.0), "helix": (1.0, 0.12, 0.7),
        "lanes": (0.95, 0.97, 1.0), "tess": (0.95, 0.97, 1.0)}


def led_col(i, s):
    c = np.array(COLS["ground"])
    for t0, fn, kind, dur in SEQ[1:5]:
        k = sm(t0 + delay(i, kind), t0 + delay(i, kind) + 0.6, s)
        c = c * (1 - k) + np.array(COLS.get(kind, COLS["ground"])) * k
    off = sm(TL["lightsOff"][0] + 0.028 * ((i * 17) % N), TL["lightsOff"][0] + 0.028 * ((i * 17) % N) + 0.15, s)
    return c * (1 - off)


# --- lasers: a plane of red beams (rows + columns between the lane positions) sweeping through the swarm ---
laser_m = mat("Laser", (0, 0, 0), emit=(1.0, 0.04, 0.05), es=28.0)
lasers = []
for j in range(7):
    v, f = box(0, 0, 0.9 - 0.275 + j * 0.55, 2.4, 0.004, 0.004)
    lasers.append(obj(f"LaserH{j}", (v, f), laser_m))
for j in range(8):
    v, f = box(-1.8 - 0.3 + j * 0.6, 0, 2.3, 0.004, 0.004, 1.9)
    lasers.append(obj(f"LaserV{j}", (v, f), laser_m))
for lz in lasers:
    lz.visible_shadow = False


def laser_y(s):
    a, b = TL["lasers"]
    if s < a - 0.3 or s > b + 0.3:
        return None
    return 7.0 - 8.5 * sm(a, b, s)


# --- camera path (real seconds) ---
SHOTS = [
    (0.0, (0.3, -0.42, 0.22), (0.05, 1.6, 0.75), 22),
    (2.0, (0.3, -0.42, 0.22), (0.05, 1.6, 0.75), 22),
    (5.0, (0.8, -1.6, 1.4), (0.0, 2.4, 2.1), 20),
    (8.0, (0.3, -2.4, 2.4), (0.0, 2.6, 2.4), 20),
    (11.0, (2.2, -1.4, 2.6), (0.0, 2.6, 2.3), 20),
    (14.0, (0.6, -2.0, 2.3), (0.0, 2.6, 2.3), 20),
    (17.0, (-2.0, -1.4, 3.0), (0.0, 2.6, 2.3), 20),
    (20.0, (0.0, -3.4, 2.6), (0.0, 2.2, 0.5), 20),
]


def cam_at(r):
    for (t0, l0, k0, f0), (t1, l1, k1, f1) in zip(SHOTS, SHOTS[1:]):
        if r <= t1:
            k = sm(t0, t1, r) if t1 > t0 else 1.0
            return np.array(l0) * (1 - k) + np.array(l1) * k, np.array(k0) * (1 - k) + np.array(k1) * k, f0 * (1 - k) + f1 * k
    return np.array(SHOTS[-1][1]), np.array(SHOTS[-1][2]), SHOTS[-1][3]


cd.dof.aperture_fstop = 2.8
if os.environ.get("DS_FAST"):  # owner, Nov 17: "I can't wait an hour" -> realtime EEVEE preview, no volume haze
    for _eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            scene.render.engine = _eng
            break
        except Exception:
            pass
    try:
        scene.eevee.taa_render_samples = 16
    except Exception:
        pass
    for o in list(bpy.data.objects):
        if o.name == "HazeBox":
            o.hide_render = True
    scene.render.use_motion_blur = False
    _fm = bpy.data.materials.get("Concrete")
    if _fm:                                  # the glossy floor mirrored the key light as a white blob
        _fmr = [n for n in _fm.node_tree.nodes if n.type == "MAP_RANGE"]
        for n in _fmr:
            n.inputs["To Min"].default_value = 0.45
            n.inputs["To Max"].default_value = 0.8
    for o in list(bpy.data.objects):
        if o.name.startswith("Beam"):
            o.data.energy *= 0.15        # the spot pools were white blobs on the floor without haze
    try:  # glow around the LEDs and lasers (compositor glare), so the show lights bloom like a real drone show
        if hasattr(scene, "compositing_node_group"):
            _ct = bpy.data.node_groups.new("CompFast", "CompositorNodeTree")
            scene.compositing_node_group = _ct
            _ci = _ct.nodes.new("CompositorNodeRLayers")
            _co = _ct.nodes.new("NodeGroupOutput")
            _ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            _g = _ct.nodes.new("CompositorNodeGlare")
            for _nm, _v in (("Type", "Fog Glow"), ("Threshold", 1.0), ("Strength", 0.9), ("Size", 0.6)):
                if _nm in _g.inputs:
                    try:
                        _g.inputs[_nm].default_value = _v
                    except Exception:
                        pass
            _ct.links.new(_ci.outputs["Image"], _g.inputs["Image"])
            _ct.links.new(_g.outputs["Image"], _co.inputs[0])
    except Exception as _e:
        print("glare unavailable", _e)
NF = int(round(DUR * FPS))
frames = list(range(K, NF, NN))
for fr in frames:
    path = os.path.join(OUT, f"f_{fr:04d}.png")
    if os.path.exists(path):
        continue
    r = fr / FPS
    s = story(r)
    scene.frame_set(int(round(r * 30)))                 # prop spin keyed at 30 steps per second
    ds = 1.0 / FPS
    for i, b in enumerate(drones):
        p = pos(i, s)
        q = pos(i, s + ds)
        v = (q - p) / ds
        b.location = tuple(p)
        sp_ = float(np.linalg.norm(v[:2]))
        yaw = math.atan2(v[1], v[0]) if sp_ > 0.15 else math.pi / 2
        pitch = -min(0.35, 0.12 * sp_)
        b.rotation_euler = (0.0, pitch, yaw) if sp_ > 0.15 else (0.0, 0.0, math.pi / 2)
        if USE_BK:
            prop_objs[i].hide_render = bool(p[2] > 0.12)
        c = led_col(i, s)
        leds[i].color = (float(c[0]), float(c[1]), float(c[2]), 1.0)
    ly = laser_y(s)
    for lz in lasers:
        lz.hide_render = ly is None
        if ly is not None:
            lz.location = (0.0, ly, 0.0)
    loc, look, lens = cam_at(r)
    place(tuple(loc), tuple(look), lens, focus=float(np.linalg.norm(look - loc)))
    fade = 1.0 - sm(TL["fade"][0], TL["fade"][1], r)
    scene.view_settings.exposure = -0.6 + math.log2(max(fade, 1e-3))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
