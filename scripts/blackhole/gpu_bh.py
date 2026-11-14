"""GPU black hole renderer (moderngl, RTX): per-frame geodesic ray tracing with a flying camera.

usage: python gpu_bh.py OUT.mp4 [--w 1080 --h 1920 --ss 2 --fps 60 --t0 0 --t1 50 --audio wav --stills 0.5,3,...]
"""
import argparse
import math
import os
import subprocess
import sys

import cv2
import moderngl
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import BEATS, STREAMS, IMPACTS, CROSS, CUTS, shatter, sm  # noqa: E402

DUR = 50.0
HOOK, REW = 1.0, 0.8          # cold open at the climax, then a rewind to the start
OFF = HOOK + REW
# one continuous take: the quieter middle plays faster (smooth speed ramps, no cuts)
SPEEDS = [(0.0, 1.0), (11.6, 1.0), (12.6, 2.5), (40.2, 2.5), (41.2, 1.0), (44.8, 1.0), (45.6, 1.25), (50.0, 1.25)]


def speed(tau):
    xs = [a for a, b in SPEEDS]; ys = [b for a, b in SPEEDS]
    v = float(np.interp(tau, xs, ys))
    return v


_tg = np.linspace(0, DUR, 50001)
_sp = np.array([speed(x) for x in _tg])
_og = np.concatenate([[0], np.cumsum((1 / _sp[1:] + 1 / _sp[:-1]) / 2 * np.diff(_tg))])
DUR_OUT = OFF + float(_og[-1])


def edl_tau(t):
    """time after the rewind -> story time (continuous, variable speed)"""
    return float(np.interp(t, _og, _tg))
TAU = 2 * math.pi


# ---------------------------------------------------------------- smooth keyframe interpolation (PCHIP)
def pchip(ts, vs):
    ts = np.asarray(ts, float)
    vs = np.asarray(vs, float)
    h = np.diff(ts)
    d = np.diff(vs) / h
    m = np.zeros_like(vs)
    for i in range(1, len(vs) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    m[0], m[-1] = d[0], d[-1]

    def f(t):
        i = int(np.clip(np.searchsorted(ts, t) - 1, 0, len(ts) - 2))
        u = (t - ts[i]) / h[i]
        u = min(max(u, 0.0), 1.0)
        h00, h10, h01, h11 = 2 * u ** 3 - 3 * u ** 2 + 1, u ** 3 - 2 * u ** 2 + u, -2 * u ** 3 + 3 * u ** 2, u ** 3 - u ** 2
        return h00 * vs[i] + h10 * h[i] * m[i] + h01 * vs[i + 1] + h11 * h[i] * m[i + 1]
    return f


# ---------------------------------------------------------------- camera path (t, dist, elevation, azimuth, vfov, roll)
CAM = [
    (0.0, 78.0, 14.0, -75, 40, -28),  # hook: rushing in from deep space, stars swirling into the lens
    (0.45, 46.0, 9.0, -50, 42, -16),
    (1.2, 27.5, 6.0, -33, 44, -9),    # star torn apart
    (2.6, 24.0, 7.0, -15, 44, -4),    # first impact at 3 s
    (4.2, 21.0, 28.0, 25, 46, 6),     # orbit + rise: the lensed back of the disk morphs over the hole
    (5.6, 20.0, 9.0, 50, 46, 10),     # a planet crosses in front of the hole
    (6.6, 22.0, 12.0, 170, 46, -12),  # whip orbit 120 degrees
    (7.2, 26.0, 1.5, 190, 44, 0),      # edge-on: a star passes behind -> Einstein ring
    (9.0, 16.0, 3.0, 205, 48, -8),     # push in to the photon ring
    (10.6, 24.0, 14.0, 225, 46, -14), # roll swing
    (12.0, 26.5, 25.0, 245, 44, 0),
    (14.0, 25.0, 65.0, 260, 46, -4),   # top-down vortex while debris spirals in
    (16.5, 25.0, 78.0, 275, 46, 60),
    (18.5, 25.0, 35.0, 290, 44, -4),   # disk shatters into rings
    (21.0, 23.4, 10.0, 305, 44, 0),
    (23.6, 16.0, 10.0, 320, 50, 6),   # falling toward the photon ring
    (24.12, 10.5, 16.0, 328, 60, 10),
    (24.3, 9.5, 20.0, 332, 56, 12),   # through the shadow (brief dark pass) -> white-blue act
    (24.48, 10.5, 16.0, 336, 60, 9),
    (24.9, 16.0, 10.0, 342, 52, 7),
    (26.0, 21.8, 8.0, 352, 44, 4),
    (28.0, 25.7, 14.0, 370, 44, 0),
    (31.0, 27.3, 4.0, 390, 44, -4),   # nebula passes behind the hole
    (33.5, 25.0, 12.0, 408, 44, -6),
    (35.4, 16.0, 12.0, 425, 50, -2),
    (35.82, 10.5, 16.0, 431, 60, 4),
    (36.0, 9.5, 20.0, 435, 56, 8),    # second dive -> golden act
    (36.18, 10.5, 16.0, 439, 60, 7),
    (36.6, 16.0, 8.0, 445, 52, 5),
    (37.5, 21.8, 5.0, 452, 44, 3),
    (40.0, 25.7, 7.0, 465, 44, 0),
    (42.0, 23.4, 18.0, 478, 44, -3),  # twin stars torn apart
    (43.9, 19.5, 12.0, 488, 46, -6),
    (44.1, 19.9, 12.0, 489, 46, -6),
    (46.0, 25.0, 8.0, 502, 44, -4),   # ending: the hole swallows its disk, camera eases away
    (48.0, 29.6, 10.0, 513, 44, -2),
    (50.0, 35.9, 12.0, 522, 44, 0),
]
_ct = [k[0] for k in CAM]
F_DIST, F_EL, F_AZ, F_FOV, F_ROLL = (pchip(_ct, [k[i] for k in CAM]) for i in range(1, 6))


def camera(t):
    return cam_from(F_DIST(t), F_EL(t), F_AZ(t), F_FOV(t), F_ROLL(t), t)


def hook_cam(t):
    """cold open: a fast, close fly-past of the photon ring during the climax."""
    u = t / HOOK
    e = u * u * (3 - 2 * u)
    return cam_from(15.5 - 3.5 * e, 17.0 - 7.0 * e, 235.0 + 60.0 * u, 56.0, -18.0 + 12.0 * e, 43.15 + t)


def story(t):
    """output time -> (story time, camera override or None, rewind amount 0..1)"""
    if t < HOOK:
        return 43.15 + t, hook_cam(t), 0.0
    if t < OFF:
        u = (t - HOOK) / REW
        e = 1 - (1 - u) ** 1.7
        # the camera flies back out to the opening position while time runs backwards (no dark dive frames)
        k = u * u * (3 - 2 * u)
        cam = cam_from(12.0 + 66.0 * k, 10.0 + 4.0 * k, 295.0 - 10.0 * k, 56.0 - 16.0 * k, -6.0 - 22.0 * k, 44.15 * (1 - e))
        return 44.15 * (1 - e) + 0.001, cam, float(math.sin(math.pi * min(u * 1.15, 1.0)) ** 0.5) * 0.6
    return edl_tau(t - OFF), None, 0.0


def cam_from(d, el, az, fov, roll, t):
    el, az, roll = math.radians(el), math.radians(az), math.radians(roll)
    pos = np.array([d * math.cos(el) * math.cos(az), d * math.sin(el), d * math.cos(el) * math.sin(az)])
    # gentle hand-held drift of the aim point
    tgt = np.array([0.25 * math.sin(t * 0.7), 0.18 * math.sin(t * 0.53 + 1.0), 0.25 * math.cos(t * 0.61)])
    fwd = tgt - pos
    fwd /= np.linalg.norm(fwd)
    up0 = np.array([0.0, 1.0, 0.0])
    if abs(fwd @ up0) > 0.98:
        up0 = np.array([math.cos(az + math.pi), 0.0, math.sin(az + math.pi)])
    right = np.cross(fwd, up0)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    cr, sr = math.cos(roll), math.sin(roll)
    right, up = cr * right + sr * up, -sr * right + cr * up
    return pos, right, up, fwd, math.tan(math.radians(fov) / 2)


# ---------------------------------------------------------------- palettes per act
def disk_temp(t):
    """disk temperature per act: golden (A), white-hot blue (B), golden-white (C); smooth morphs at the swoops."""
    a = float(sm(CUTS[0] - 0.35, CUTS[0] + 0.35, t))
    c = float(sm(CUTS[1] - 0.35, CUTS[1] + 0.35, t))
    return 11000.0 + (22000.0 - 11000.0) * a + (9500.0 - 22000.0) * c


def heat(t):
    """each impact heats the whole disk: it flares blue-white, then cools back."""
    h = 0.0
    for ti, s in IMPACTS:
        if s >= 0.6 and -0.15 < t - ti < 2.5 and not any(abs(ti - c) < 0.5 for c in CUTS):
            a = t - ti
            h += s * (sm(-0.15, 0.1, a) * math.exp(-max(a, 0.0) / 0.9))
    return 1.0 + 1.1 * min(h, 1.3)


def bg_neb(t):
    return float(sm(CUTS[0] - 0.4, CUTS[0] + 0.6, t) * (1 - sm(CUTS[1] - 0.6, CUTS[1] + 0.4, t)))


def end_k(t):
    return float(sm(45.0, 49.3, t))


def planet(t):
    """a planet on an inclined orbit; it crosses in front of the hole at 5.6 s."""
    R = 11.5
    tt = math.radians(50.0)
    th = tt + TAU * (t - 5.6) / 34.0
    return (R * math.cos(th), 1.6 * math.cos(th - tt), R * math.sin(th), 0.32)


# ---------------------------------------------------------------- effects from the shared timeline
SPIN = 15.0       # visual speed-up of the orbital motion
FLOWP = 50.0 / 6  # flow-map period (divides the loop length)


def omega(r):
    return math.sqrt(0.5 / r ** 3) * SPIN


_rng = np.random.default_rng(7)
CLUMPS = []   # (t_birth, life, r, phase0, intensity, size)
for k in range(4):  # always-on, gentle
    CLUMPS.append((-1e9, 1e12, 3.6 + 1.2 * k, _rng.random() * TAU, 0.9 - 0.15 * k, 0.35))
for k in range(3):  # opening: bright clumps racing around the inner edge
    CLUMPS.append((-1.0, 9.5, 3.3 + 0.55 * k, k * TAU / 3, 2.2, 0.28))
for ti, s in IMPACTS:
    if s >= 0.6:
        for k in range(4):
            CLUMPS.append((ti, 7.0, 3.3 + 0.9 * k + 0.4 * _rng.random(), _rng.random() * TAU, 2.6 * s, 0.32 + 0.08 * k))


def clumps(t):
    out = []
    for tb, life, r, p0, amp, size in CLUMPS:
        age = t - tb
        if age < 0 or age > life:
            continue
        env = amp * (min(1.0, age / 0.35) if life < 1e6 else 1.0) * (1 - float(sm(life * 0.55, life, age)))
        ph = p0 + omega(r) * t
        for j in range(4):                      # head + fading trail
            pj = ph - j * 0.09 * (3.6 / r)
            out.append((r * math.cos(pj), r * math.sin(pj), env * (1.0, 0.55, 0.3, 0.14)[j], size * (1 + 0.25 * j)))
    out.sort(key=lambda q: -q[2])
    out = out[:16]
    while len(out) < 16:
        out.append((0, 0, 0, 1))
    return out


def ripples(t):
    out = []
    for tb, a in BEATS:
        age = t - tb
        if 0 <= age < 2.6:
            out.append((2.9 + age * 7.5, 1.8 * a * (1 - age / 2.6) ** 1.5, 0.22 + 0.1 * age, 0))
    for ti, s in IMPACTS:
        age = t - ti
        if s >= 0.3 and 0 <= age < 3.2:
            out.append((2.9 + age * 6.0, 3.2 * s * (1 - age / 3.2) ** 1.4, 0.3 + 0.15 * age, 0))
    out = sorted(out, key=lambda q: -q[1])[:6]
    while len(out) < 6:
        out.append((0, 0, 1, 0))
    return out


def beat_gain(t):
    g = 1.0
    for tb, a in BEATS:
        if 0 <= t - tb < 1.0:
            g += 0.28 * a * math.exp(-(t - tb) * 7)
    return g


STREAM_COL = [(0.55, 0.85, 1.6), (1.6, 0.55, 1.2), (0.5, 1.5, 1.05), (1.4, 1.2, 0.7)]


def streams(t):
    """tidal-disruption streams; each star gets its own tilted orbit and colour."""
    A, B, N, U, C = [], [], [], [], []
    for i, (t0, dur, psi0, rs, amp, wm, star) in enumerate(STREAMS):
        pre = 1.05 if t0 < 12 else 0.6
        if t0 - pre <= t <= t0 + dur + 1.4:
            c = 1.9
            psi_end = psi0 + c * math.log(rs / 2.6)
            u = float(np.clip((t - t0) / dur, 0, 1))
            head = psi0 + (psi_end - psi0) * u ** 1.6
            if t < t0:
                head = psi0 - 0.5 * (t0 - t) / pre
            tail = psi0 + (psi_end - psi0) * max(0.0, (t - t0 - 0.35 * dur) / (0.65 * dur + 1.2)) ** 1.3
            fade = 1 - float(sm(t0 + dur, t0 + dur + 1.4, t))
            big = t0 < 12 or t0 > 40
            rs = min(rs, 12.5) if big else rs
            psi_end = psi0 + c * math.log(rs / 2.6)
            head = psi0 + (psi_end - psi0) * u ** 1.6 if t >= t0 else head
            tail = psi0 + (psi_end - psi0) * max(0.0, (t - t0 - 0.35 * dur) / (0.65 * dur + 1.2)) ** 1.3
            A.append((psi0, rs, c, (0.55 if big else 0.45) * wm))
            B.append((head, tail, (7.0 if big else 3.0) * amp * fade * float(sm(t0 - pre, t0, t)),
                      (14.0 if big else 6.0) * star * (1 - u) * float(sm(t0 - pre, t0 - pre + 0.25, t))))
            inc = math.radians((28, -35, 40, -24)[i % 4] if big else 8)
            rot = (0.3, 1.9, 3.6, 5.0)[i % 4]
            n = np.array([math.sin(inc) * math.cos(rot), math.cos(inc), math.sin(inc) * math.sin(rot)])
            uu = np.cross(n, [0.0, 0.0, 1.0]); uu /= np.linalg.norm(uu)
            N.append(tuple(n)); U.append(tuple(uu)); C.append(STREAM_COL[i % 4] if big else (1.2, 1.0, 0.8))
    A, B, N, U, C = A[:3], B[:3], N[:3], U[:3], C[:3]
    while len(A) < 3:
        A.append((0, 1, 1, 1)); B.append((0, 0, 0, 0)); N.append((0, 1, 0)); U.append((1, 0, 0)); C.append((0, 0, 0))
    return A, B, N, U, C


def glitter(t):
    return float(0.9 * sm(5.0, 6.5, t) * (1 - sm(12.0, 13.5, t)) + 0.9 * sm(36.8, 38.5, t) * (1 - sm(43.6, 44.8, t))
                 + 0.4 * sm(0.4, 1.2, t) * (1 - sm(3.0, 4.0, t)))


def crossing(t, pos, right):
    """direction/brightness of a star or nebula sliding behind the hole as seen from the camera."""
    back = -pos / np.linalg.norm(pos)
    star = (np.zeros(3), 0.0, (1, 1, 1))
    neb = (np.zeros(3), 0.0, (1, 1, 1))
    for t0, t1, br, colr, kind in CROSS:
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            a = 0.30 * (1 - 2 * u) * (1.6 if kind == 'neb' else 1.0)
            d = back * math.cos(a) + right * math.sin(a) + np.cross(right, back) * 0.012
            d /= np.linalg.norm(d)
            env = float(sm(0, 0.15, u) * (1 - sm(0.85, 1, u)))
            if kind == 'neb':
                neb = (d, 0.35 * br * env, colr)
            else:
                star = (d, 1.4 * br * env, colr)
    return star, neb


def cwave(t):
    return float(sm(26.0, 28.0, t) * (1 - sm(33.5, 35.0, t)))


def sky_rot(t):
    return 0.012 * t + 1.1 * (1 - math.exp(-t / 0.8))


# ---------------------------------------------------------------- post (bloom, tone map, lens)
def make_post(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H / 2
    k = 0.0012
    dx, dy = (xx - cx) / H, (yy - cy) / H
    mapR = (cx + (xx - cx) * (1 + k), cy + (yy - cy) * (1 + k))
    mapB = (cx + (xx - cx) * (1 - k), cy + (yy - cy) * (1 - k))
    vig = (1 - 0.32 * (dx * dx + dy * dy) * 2.2).astype(np.float32)[..., None]

    def post(img):
        lum = (img @ np.float32([0.2126, 0.7152, 0.0722]))[..., None]
        img = np.maximum(lum + (img - lum) * 1.25, 0)          # richer colour
        br = np.maximum(img - 0.75, 0)
        q = cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        bl = 0.40 * cv2.GaussianBlur(q, (0, 0), 2.0) + 0.25 * cv2.GaussianBlur(q, (0, 0), 9) + 0.10 * cv2.GaussianBlur(q, (0, 0), 34)
        img = img + cv2.resize(bl, (W, H), interpolation=cv2.INTER_LINEAR)
        # ACES-like filmic curve
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        x = img * 0.9
        img = np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)
        img[..., 0] = cv2.remap(img[..., 0], mapR[0], mapR[1], cv2.INTER_LINEAR)
        img[..., 2] = cv2.remap(img[..., 2], mapB[0], mapB[1], cv2.INTER_LINEAR)
        img = img ** (1 / 2.2) * vig
        return np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    return post


# ---------------------------------------------------------------- GPU
class Renderer:
    def __init__(self, W, H, ss):
        self.W, self.H, self.ss = W, H, ss
        self.ctx = moderngl.create_standalone_context(require=330, **({'backend': 'egl'} if os.environ.get('BH_EGL') else {}))
        vs = """#version 330
in vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }"""
        fs = open(os.path.join(HERE, 'bh.frag')).read()
        self.prog = self.ctx.program(vertex_shader=vs, fragment_shader=fs)
        quad = np.array([-1, -1, 1, -1, -1, 1, 1, 1], 'f4')
        self.vao = self.ctx.simple_vertex_array(self.prog, self.ctx.buffer(quad), 'p')
        N = 128
        rng = np.random.default_rng(5)
        k = np.fft.fftfreq(N) * N
        kk = np.sqrt(k[:, None, None] ** 2 + k[None, :, None] ** 2 + k[None, None, :] ** 2)
        spec = (np.fft.fftn(rng.standard_normal((N, N, N))) / np.maximum(kk, 1.0) ** 1.55)
        spec[0, 0, 0] = 0
        vol = np.real(np.fft.ifftn(spec))
        vol = (vol - vol.mean()) / (vol.std() * 4.0) + 0.5
        vol = np.clip(vol, 0, 1).astype('f4')
        self.noise = self.ctx.texture3d((N, N, N), 1, vol.tobytes(), dtype='f4')
        self.noise.repeat_x = self.noise.repeat_y = self.noise.repeat_z = True
        self.noise.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.noise.use(0)
        self.RW, self.RH = W * ss, H * ss
        self.tex = self.ctx.texture((self.RW, self.RH), 4, dtype='f4')
        self.fbo = self.ctx.framebuffer([self.tex])
        self.level = int(round(math.log2(ss)))

    def set(self, name, val):
        if name in self.prog:
            self.prog[name].value = val

    def frame(self, t, cam=None):
        pos, right, up, fwd, tanf = cam if cam is not None else camera(t)
        S = self.set
        S('res', (float(self.RW), float(self.RH)))
        S('camPos', tuple(pos)); S('camR', tuple(right)); S('camU', tuple(up)); S('camF', tuple(fwd)); S('tanF', tanf)
        S('T', t)
        fa = t % FLOWP
        fb = (t + FLOWP / 2) % FLOWP
        wa = 1 - abs(2 * fa / FLOWP - 1)
        S('flowA', fa); S('flowB', fb); S('flowW', wa)
        S('spinK', SPIN)
        S('T0', disk_temp(t) * heat(t)); S('expo', 1.0); S('bgNeb', bg_neb(t))
        S('diskGain', 1.0 * beat_gain(t)); S('beamK', 0.35)
        S('endK', end_k(t)); S('planet', (0, 0, 0, 0)); S('wave', 1.0)
        S('noiseTex', 0)
        self.prog['rip'].value = ripples(t)
        self.prog['spot'].value = clumps(t)
        A, B, N, U, C = streams(t)
        self.prog['strA'].value = A
        self.prog['strB'].value = B
        self.prog['strN'].value = N
        self.prog['strU'].value = U
        self.prog['strC'].value = C
        sh = shatter(t)
        S('shat', sh); S('shatPh', 0.9 * t)
        S('glit', glitter(t))
        (sd, sb, sc), (nd, nb, nc) = crossing(t, pos, right)
        S('star1', (*sd, sb)); S('star1c', tuple(sc))
        S('neb', (*nd, nb)); S('nebc', tuple(nc)); S('nebSize', 0.16)
        S('skyRot', sky_rot(t))
        self.fbo.use()
        self.vao.render(moderngl.TRIANGLE_STRIP)
        self.tex.build_mipmaps(0, self.level)
        raw = self.tex.read(level=self.level)
        img = np.frombuffer(raw, np.float32).reshape(self.H, self.W, 4)[::-1, :, :3]
        return np.nan_to_num(img, nan=0.0, posinf=50.0, neginf=0.0)


def render_out(R, t):
    tau, cam, rew = story(t)
    return R.frame(tau, cam)


def blurred(R, t, fps):
    """real motion blur: cold open, rewind and the rush-in."""
    if t < HOOK:
        n, sh = 6, 0.8
    elif t < OFF:
        n, sh = 8, 1.0
    elif t < OFF + 1.0:
        n, sh = 8, 0.8
    elif t < OFF + 1.6:
        n, sh = 4, 0.8
    elif speed(story(t)[0]) > 1.3 or abs(F_AZ(story(t)[0] + 0.03) - F_AZ(story(t)[0] - 0.03)) / 0.06 > 45:
        n, sh = 3, 0.8
    else:
        return render_out(R, t)
    acc = None
    for k in range(n):
        im = render_out(R, t + sh / fps * (k / n - 0.5)).copy()
        acc = im if acc is None else acc + im
    return acc / n


def tape(img, amt, f):
    """VHS-style rewind look: wobbling bands, scanlines, colour split."""
    rng = np.random.default_rng(f)
    H, W = img.shape[:2]
    out = img.copy()
    for _ in range(int(6 * amt) + 1):
        y0 = int(rng.integers(0, H - 40)); hh = int(rng.integers(8, 60))
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-40, 40) * amt), axis=1)
    out[..., 0] = np.roll(out[..., 0], int(6 * amt), axis=1)
    out[..., 2] = np.roll(out[..., 2], -int(6 * amt), axis=1)
    sl = np.ones((H, 1, 1), np.float32)
    sl[::3] = 1 - 0.18 * amt
    out = out.astype(np.float32) * sl
    out = out * (1 - 0.25 * amt) + out.mean(axis=2, keepdims=True) * 0.25 * amt
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--w', type=int, default=1080)
    ap.add_argument('--h', type=int, default=1920)
    ap.add_argument('--ss', type=int, default=2)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--t0', type=float, default=0)
    ap.add_argument('--t1', type=float, default=DUR_OUT)
    ap.add_argument('--audio', default=None)
    ap.add_argument('--stills', default=None)
    ap.add_argument('--crf', default='14')
    a = ap.parse_args()
    R = Renderer(a.w, a.h, a.ss)
    post = make_post(a.w, a.h)
    if a.stills:
        for ts in a.stills.split(','):
            t = float(ts)
            cv2.imwrite(f'{a.out}_{ts}.png', cv2.cvtColor(post(blurred(R, t, 60)), cv2.COLOR_RGB2BGR))
        return
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{a.w}x{a.h}', '-r', str(a.fps), '-i', '-']
    if a.audio:
        cmd += ['-ss', str(a.t0), '-t', str(a.t1 - a.t0), '-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '320k']
    cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', a.crf, '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart', a.out]
    pp = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    f0, f1 = int(round(a.t0 * a.fps)), int(round(a.t1 * a.fps))
    import time
    tic = time.time()
    for f in range(f0, f1):
        t = f / a.fps
        img = post(blurred(R, t, a.fps))
        rew = story(t)[2]
        if rew > 0.01:
            img = tape(img, rew, f)
        fade = 1 - float(sm(48.6, 50.0, story(t)[0])) if t > OFF else 1.0
        if fade < 1:
            img = (img * fade).astype(np.uint8)
        pp.stdin.write(img.tobytes())
        if f % 60 == 0:
            print(f'frame {f}/{f1}  {time.time() - tic:.1f}s', flush=True)
    pp.stdin.close()
    pp.wait()
    print('done', a.out, f'{time.time() - tic:.1f}s', flush=True)


if __name__ == '__main__':
    main()
