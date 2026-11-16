# A realistic consumer quadcopter for 0025 (owner, Nov 17 2026: "look at my photo - THIS is a drone"). Our own design,
# no logos: a compact streamlined body (smooth lofted shell), a gimbal camera at the nose (yoke + housing + glass lens),
# four tapered arms (rear pair mounted higher), motors with chrome caps, two-blade props, front landing legs, a
# status LED and a front light. Built from numpy meshes; exec'd by drone_swarm.py after its `mat` helper exists.
# build_real_drone(spin) -> one mesh; spin=True gives motion-blurred props (in flight), False gives crisp blades.


def _frame_mesh(rings, closed_ends=True):
    """rings: list of (n,3) arrays of equal n -> quad mesh (+ end caps)"""
    n = len(rings[0])
    V = [tuple(p) for r in rings for p in r]
    F = [(i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j)
         for i in range(len(rings) - 1) for j in range(n)]
    if closed_ends:
        F.append(tuple(range(n - 1, -1, -1)))
        last = (len(rings) - 1) * n
        F.append(tuple(range(last, last + n)))
    return V, F


def _superellipse(w, h, n=48, p=2.6, flat_bottom=0.0):
    t = np.linspace(0, TAU, n, endpoint=False)
    c, s_ = np.cos(t), np.sin(t)
    y = w * np.sign(c) * np.abs(c) ** (2 / p)
    z = h * np.sign(s_) * np.abs(s_) ** (2 / p)
    z = np.where(z < 0, z * (1 - flat_bottom), z)
    return y, z


def _body():
    """the streamlined shell along x (nose at +x): width/height swell in the middle, tapered tail, flat belly"""
    xs = np.linspace(-0.115, 0.105, 34)
    rings = []
    for x in xs:
        u = (x + 0.115) / 0.22
        w = 0.056 * (np.sin(np.pi * np.clip(u, 0.02, 0.98)) ** 0.4) * (1 - 0.15 * u)
        h = 0.04 * (np.sin(np.pi * np.clip(u, 0.02, 0.98)) ** 0.45)
        y, z = _superellipse(max(w, 0.004), max(h, 0.003), 48, 3.4, flat_bottom=0.45)  # boxier, flatter belly
        rings.append(np.stack([np.full_like(y, x), y, z + 0.004 * u], 1))
    return _frame_mesh(rings)


def _tube(a, b, ra, rb, n=16, p=2.4):
    """a tapered rounded-rectangle tube from point a to b (arms, legs)"""
    a, b = np.array(a, float), np.array(b, float)
    ra, rb = np.array(ra, float), np.array(rb, float)
    d = b - a
    L = np.linalg.norm(d)
    x = d / L
    up = np.array([0, 0, 1.0]) if abs(x[2]) < 0.9 else np.array([1.0, 0, 0])
    y = np.cross(up, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    rings = []
    for k in np.linspace(0, 1, 6):
        r = ra * (1 - k) + rb * k
        yy, zz = _superellipse(r[0], r[1], n, p)
        c = a + d * k
        rings.append(c + yy[:, None] * y + zz[:, None] * z)
    return _frame_mesh(rings)


def _cyl(c, r, h, n=32, axis=2):
    t = np.linspace(0, TAU, n, endpoint=False)
    rings = []
    for k in (-0.5, 0.5):
        p = np.zeros((n, 3))
        o = [i for i in range(3) if i != axis]
        p[:, o[0]] = r * np.cos(t)
        p[:, o[1]] = r * np.sin(t)
        p[:, axis] = k * h
        rings.append(p + np.array(c))
    return _frame_mesh(rings)


def _blade(hub, ang, length=0.115, z=0.0):
    """one prop blade: thin, twisted, tapering towards a rounded tip"""
    rings = []
    for k in np.linspace(0.08, 1.0, 14):
        chord = 0.022 * (1.15 - 0.75 * k) * (1 - (k > 0.92) * (k - 0.92) * 6)
        twist = math.radians(22 * (1 - k) + 6)
        r = k * length
        t = np.linspace(0, TAU, 10, endpoint=False)
        cx = chord / 2 * np.cos(t)
        cz = 0.0018 * np.sin(t) * (1 - 0.5 * k)
        bx, bz = cx * math.cos(twist), cx * math.sin(twist) + cz
        pts = np.stack([np.full_like(bx, r), bx, bz], 1)
        ca, sa = math.cos(ang), math.sin(ang)
        rot = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
        rings.append(pts @ rot.T + np.array([hub[0], hub[1], hub[2] + z]))
    return _frame_mesh(rings)


M_SHELL_R = mat("DroneShell", (0.055, 0.058, 0.064), rough=0.42, coat=0.25)
M_DARK_R = mat("DroneDark", (0.012, 0.012, 0.014), rough=0.5)
M_METAL_R = mat("MotorMetal", (0.35, 0.36, 0.4), metal=1.0, rough=0.3)
M_CHROME_R = mat("Chrome", (0.9, 0.9, 0.92), metal=1.0, rough=0.08)
M_GLASS_R = mat("LensGlass", (0.004, 0.006, 0.012), rough=0.02, coat=1.0)
M_PROP_R = mat("PropBlade", (0.06, 0.062, 0.068), rough=0.38)
M_GREEN_R = mat("StatusLED", (0, 0, 0), emit=(0.1, 1.0, 0.25), es=60.0)
M_WHITE_R = mat("FrontLight", (0, 0, 0), emit=(0.85, 0.95, 1.0), es=50.0)
M_BLUR_R = mat("PropBlur", (0.08, 0.08, 0.09), rough=0.4, alpha=0.018)  # a faint disc
M_GHOST_R = mat("PropGhost", (0.07, 0.07, 0.08), rough=0.4, alpha=0.035)  # blade ghosts of a spinning prop


MOTOR_POS = [(0.13, 0.148, 0.028), (0.13, -0.148, 0.028), (-0.118, 0.14, 0.05), (-0.118, -0.14, 0.05)]


def build_prop():
    """two crisp blades around the origin; spun by keyframes so Cycles renders a REAL motion blur"""
    V, F, MI = [], [], []
    for b in (0, math.pi):
        v, f = _blade((0, 0, 0), b)
        o = len(V)
        V += list(v)
        F += [tuple(i + o for i in face) for face in f]
    parts_cap = _cyl((0, 0, 0.002), 0.008, 0.006, 20)
    o = len(V)
    V += list(parts_cap[0])
    F += [tuple(i + o for i in face) for face in parts_cap[1]]
    me = bpy.data.meshes.new("Prop")
    me.from_pydata(V, [], F)
    me.materials.append(M_PROP_R)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


def build_real_drone(spin=True, props=True):
    mats = [M_SHELL_R, M_DARK_R, M_METAL_R, M_CHROME_R, M_GLASS_R, M_PROP_R, M_GREEN_R, M_WHITE_R, M_BLUR_R, M_GHOST_R]
    parts = [(*_body(), 0)]
    # battery cover: a slightly raised, darker top panel -> a crisp seam all round, like a real drone
    xs = np.linspace(-0.1, 0.06, 20)
    rings = []
    for x in xs:
        u = (x + 0.115) / 0.22
        w = 0.056 * (np.sin(np.pi * np.clip(u, 0.02, 0.98)) ** 0.4) * (1 - 0.15 * u) * 0.78
        h = 0.04 * (np.sin(np.pi * np.clip(u, 0.02, 0.98)) ** 0.45)
        t = np.linspace(-1.0, 1.0, 24)
        y = w * t
        z = h * np.clip(1 - np.abs(t) ** 3.4, 0, 1) ** (1 / 3.4) + 0.004 * u + 0.0018
        rings.append(np.stack([np.full_like(y, x), y, z], 1))
    V_, F_ = _frame_mesh(rings, closed_ends=False)
    F_ = [f for f in F_]
    parts.append((V_, [ (a, b, c, d) for (a, b, c, d) in F_ if True ], 1))
    for sg in (-1, 1):                                                                              # side vents
        for j in range(4):
            parts.append((*_tube((-0.04 + j * 0.012, sg * 0.05, 0.004), (-0.04 + j * 0.012, sg * 0.05, 0.02), (0.0025, 0.004), (0.0025, 0.004)), 1))
    for sx, sy in ((0.03, 0.033), (-0.05, 0.03)):                                                    # side sensors
        for sg in (-1, 1):
            parts.append((*_cyl((sx, sg * sy, 0.026), 0.0055, 0.004, 20), 4))
    # gimbal at the nose: yoke + camera housing + big lens + small second lens
    # gimbal tucked under the nose (it stuck out like a pod before)
    parts.append((*_tube((0.085, 0, -0.012), (0.1, 0, -0.02), (0.014, 0.008), (0.012, 0.007)), 1))
    parts.append((*_cyl((0.104, 0, -0.024), 0.024, 0.034, 40, axis=0), 1))
    parts.append((*_cyl((0.122, 0, -0.024), 0.019, 0.004, 40, axis=0), 3))                           # lens ring
    parts.append((*_cyl((0.1245, 0.003, -0.022), 0.0145, 0.003, 40, axis=0), 4))                    # main lens
    parts.append((*_cyl((0.123, -0.012, -0.036), 0.005, 0.004, 24, axis=0), 4))                     # second lens
    parts.append((*_cyl((0.108, 0, 0.0), 0.004, 0.002, 12, axis=0), 7))                             # front light
    # arms (front low and forward, rear higher), motors, legs, props
    motors = [(0.13, 0.148, 0.012), (0.13, -0.148, 0.012), (-0.118, 0.14, 0.034), (-0.118, -0.14, 0.034)]
    roots = [(0.045, 0.04, 0.0), (0.045, -0.04, 0.0), (-0.07, 0.035, 0.012), (-0.07, -0.035, 0.012)]
    for k, (m, r0) in enumerate(zip(motors, roots)):
        parts.append((*_tube(r0, (m[0], m[1], m[2] - 0.006), (0.009, 0.007), (0.007, 0.006)), 0))
        parts.append((*_cyl((m[0], m[1], m[2]), 0.0175, 0.02, 36), 2))                               # motor bell
        parts.append((*_cyl((m[0], m[1], m[2] + 0.012), 0.009, 0.005, 24), 3))                     # chrome cap
        if k < 2:
            parts.append((*_tube((m[0], m[1], m[2] - 0.01), (m[0] + 0.004, m[1], m[2] - 0.05), (0.006, 0.006), (0.003, 0.003)), 0))
        if spin and props:
            parts.append((*_cyl((m[0], m[1], m[2] + 0.017), 0.115, 0.001, 64), 8))                 # blur disc
        a0 = (k * 1.3) % TAU
        ghosts = tuple(np.linspace(0.0, math.pi, 24, endpoint=False)) if spin else (0.0,)  # a smooth smear
        for g in (ghosts if props else ()):
            for b in (0, math.pi):
                parts.append((*_blade((m[0], m[1], m[2] + 0.016), a0 + b + g), 9 if spin else 5))
    parts.append((*_cyl((-0.118, -0.14, 0.012), 0.003, 0.003, 12), 6))                             # status LED
    V, F, MI = [], [], []
    for v, f, mi in parts:
        o = len(V)
        V += list(v)
        F += [tuple(i + o for i in face) for face in f]
        MI += [mi] * len(f)
    me = bpy.data.meshes.new("RealDrone" + ("Spin" if spin else ""))
    me.from_pydata(V, [], F)
    for m_ in mats:
        me.materials.append(m_)
    me.polygons.foreach_set("material_index", MI)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me
