"""Shade the traced black hole: disk texture, beaming, sky, eye opening, ignition, heartbeat. Writes frames to ffmpeg."""
import sys
import math
import subprocess
import numpy as np
import cv2

cv2.setNumThreads(2)
TAU = 2 * math.pi
FPS = int(__import__("os").environ.get("FPS", 60))
OW, OH = int(__import__("os").environ.get("OW",1080)), int(__import__("os").environ.get("OH",1920))
RIN, ROUT = 6.0, 18.0
rng = np.random.default_rng(3)

d = np.load(sys.argv[1])
TW, TH = int(d['W']), int(d['H'])
hit_r, hit_psi, hit_g, nh, esc, state = d['hit_r'], d['hit_psi'], d['hit_g'], d['nh'], d['esc'], d['state']
NHIT = hit_r.shape[0]


def sm(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def eo(t):
    t = np.clip(t, 0, 1)
    return 1 - (1 - t) ** 3


# ---------- disk texture (polar, tileable in angle) ----------
TR, TP = 768, 8192


def wrap_noise(nr, npsi, out_r, out_p, seed):
    g = np.random.default_rng(seed).random((nr, npsi)).astype(np.float32)
    g = np.concatenate([g, g[:, :3]], 1)                      # wrap padding in psi
    big = cv2.resize(g, (int(out_p * (npsi + 3) / npsi), out_r), interpolation=cv2.INTER_CUBIC)
    return big[:, :out_p]


tex = np.zeros((TR, TP), np.float32)
amp = 1.0
for o, (nr, npsi) in enumerate([(6, 10), (12, 20), (24, 40), (48, 80), (96, 150), (190, 300), (380, 560)]):
    tex += amp * wrap_noise(nr, npsi, TR, TP, 10 + o)
    amp *= 0.6
tex = (tex - tex.min()) / (tex.max() - tex.min())
rr = np.linspace(0, 1, TR)[:, None]
warp = 2.5 * wrap_noise(10, 24, TR, TP, 99) + 0.8 * wrap_noise(40, 120, TR, TP, 98)
ring = 0.5 + 0.5 * np.sin(rr * 170 + warp)
ring2 = 0.5 + 0.5 * np.sin(rr * 520 + 2.2 * warp)
ring3 = 0.5 + 0.5 * np.sin(rr * 1400 + 4.0 * warp + 1.3 * wrap_noise(200, 900, TR, TP, 97))
tex = np.clip(0.4 * tex + 0.38 * ring * tex * 1.7 + 0.14 * ring2 * tex + 0.14 * ring3 * tex, 0, 1) ** 1.25
# bright knots of hot plasma
kn = np.zeros((TR, TP), np.float32)
kr = np.random.default_rng(5)
for _ in range(2600):
    y0, x0 = kr.integers(0, TR), kr.integers(0, TP)
    cv2.ellipse(kn, (int(x0), int(y0)), (int(kr.integers(10, 110)), int(kr.integers(1, 5))), 0, 0, 360, float(kr.random() * 0.8 + 0.2), -1)
kn = np.concatenate([kn, kn[:, :400]], 1)
kn = cv2.GaussianBlur(kn, (0, 0), sigmaX=10, sigmaY=1.5)[:, :TP]
# dark dust filaments (ridged noise)
dust = np.abs(wrap_noise(300, 50, TR, TP, 123) - 0.5) * 2
dust = 1 - 0.35 * np.clip(1 - dust * 5, 0, 1)
tex = np.clip((tex + 0.6 * kn) * dust, 0, 1.4)
tex_soft = cv2.GaussianBlur(tex, (0, 0), 3)

# ---------- sky (equirectangular) ----------
SW, SH = 4096, 2048
sky = np.zeros((SH, SW, 3), np.float32)
neb = np.zeros((SH, SW), np.float32)
amp = 1.0
for o, (a, b) in enumerate([(4, 8), (8, 16), (16, 32), (32, 64), (64, 128)]):
    n0 = wrap_noise(a, b, SH, SW, 50 + o)
    neb += amp * n0
    amp *= 0.55
neb = (neb - neb.min()) / (neb.max() - neb.min())
neb2 = wrap_noise(6, 12, SH, SW, 77)
neb2 = (neb2 - neb2.min()) / (neb2.max() - neb2.min())
nebc = np.stack([0.35 * neb2 + 0.15, 0.12 + 0.1 * neb, 0.55 + 0.25 * (1 - neb2)], -1)
sky += nebc * (np.clip(neb - 0.45, 0, 1) ** 1.6)[..., None] * 0.55
NS = 14000
sxs = rng.random(NS) * SW
sys_ = np.arccos(rng.random(NS) * 2 - 1) / math.pi * SH
sb = rng.pareto(2.2, NS) * 0.06 + 0.02
sc = np.array([[0.8, 0.85, 1.0], [1.0, 0.95, 0.9], [0.75, 0.8, 1.0], [1.0, 0.85, 0.95]], np.float32)[rng.integers(0, 4, NS)]
starimg = np.zeros((SH, SW, 3), np.float32)
xi, yi = sxs.astype(int) % SW, np.clip(sys_.astype(int), 0, SH - 1)
np.add.at(starimg, (yi, xi), sc * sb[:, None])
starimg = cv2.GaussianBlur(starimg, (0, 0), 0.8) * 6
sky += starimg

# per-pixel sky lookup; the sky slowly rotates (camera orbit) so lensed stars stream around the hole
ex0, ey0, ez0 = esc[..., 0], esc[..., 1], esc[..., 2]
LON0 = (np.arctan2(ex0, ez0) + math.pi).astype(np.float64)
LAT0 = np.arcsin(np.clip(ey0, -1, 1)).astype(np.float64)
ESCM = state == 2
NEBTEX = sky - starimg
BDT = wrap_noise(40, 80, SH, SW, 321)
BGT = wrap_noise(20, 40, SH, SW, 322)
ndir = np.array([0.35, 0.82, -0.45]); ndir /= np.linalg.norm(ndir)
gdir = np.array([-0.55, 0.42, 0.72]); gdir /= np.linalg.norm(gdir)


def star_layer(lon64, lat64, cs, prob, bmul, sig, seed):
    ci = np.floor(lon64 / cs); cj = np.floor(lat64 / cs)
    v = np.sin(ci * 127.1 + cj * 311.7 + seed) * 43758.5453
    on = (v - np.floor(v)) < prob
    out = np.zeros((lon64.shape[0], 3), np.float32)
    if not on.any():
        return out
    ci, cj, lo, la = ci[on], cj[on], lon64[on], lat64[on]

    def hsh(a):
        w = np.sin(ci * (127.1 + a) + cj * (311.7 + 3 * a) + seed) * 43758.5453
        return w - np.floor(w)
    ox_, oy_ = 0.2 + 0.6 * hsh(1.7), 0.2 + 0.6 * hsh(4.3)
    b = bmul * (0.08 / (hsh(7.9) + 0.03))
    dl = (lo / cs - ci - ox_) * cs * np.cos(la)
    dt = (la / cs - cj - oy_) * cs
    I = b * np.exp(-(dl * dl + dt * dt) / (sig * sig))
    tint = hsh(9.1)
    out[on] = (I[:, None] * np.stack([0.8 + 0.2 * tint, 0.85 + 0.1 * tint, 1.0 - 0.15 * tint], -1)).astype(np.float32)
    return out


def rmp(tex, mx, my):
    n = mx.size
    pad = (-n) % 2048
    mx2 = np.pad(mx.ravel(), (0, pad)).reshape(-1, 2048)
    my2 = np.pad(my.ravel(), (0, pad)).reshape(-1, 2048)
    o = cv2.remap(tex, mx2, my2, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    return o.reshape((-1,) + tex.shape[2:])[:n]


def sky_at(rot):
    out = np.zeros((TH, TW, 3), np.float32)
    lon = (LON0[ESCM] + rot) % TAU
    lat = LAT0[ESCM]
    mx = (lon / TAU * SW).astype(np.float32)
    my = ((0.5 - lat / math.pi) * SH).astype(np.float32)
    sk = rmp(NEBTEX, mx, my)
    cl = np.cos(lat)
    ex, ey, ez = np.sin(lon - math.pi) * cl, np.sin(lat), np.cos(lon - math.pi) * cl
    band = np.exp(-((ex * ndir[0] + ey * ndir[1] + ez * ndir[2]) / 0.17) ** 2).astype(np.float32)
    bdust = rmp(BDT, mx, my)
    bglow = rmp(BGT, mx, my)
    mw = band * (0.5 + 0.8 * bglow) * np.clip(0.25 + 1.3 * (bdust - 0.25), 0.2, 1)
    sk += mw[:, None] * np.array([0.16, 0.11, 0.24], np.float32)
    ga = np.arccos(np.clip(ex * gdir[0] + ey * gdir[1] + ez * gdir[2], -1, 1))
    sk += (np.exp(-(ga / 0.012) ** 2) * 0.5 + np.exp(-(ga / 0.035) ** 2) * 0.12)[:, None] * np.array([0.85, 0.8, 1.0], np.float32)
    sk += star_layer(lon, lat, 0.004, 0.02, 1.0, 0.0006, 1.0) + star_layer(lon, lat, 0.0016, 0.012, 0.35, 0.00045, 2.0)
    sk += star_layer(lon, lat, 0.0011, 0.03, 0.18, 0.0004, 3.0) * (0.3 + 2.5 * band)[:, None]
    out[ESCM] = sk
    return out

# ---------- palette ----------
PT = np.array([0.0, 0.3, 0.55, 0.8, 1.05, 1.4])
PC = np.array([[0.20, 0.04, 0.32], [0.48, 0.10, 0.70], [0.32, 0.30, 1.00], [0.45, 0.70, 1.00], [0.85, 0.93, 1.0], [1.0, 1.0, 1.0]], np.float32)


def palette(t):
    return np.stack([np.interp(t, PT, PC[:, c]) for c in range(3)], -1).astype(np.float32)


# static per-hit quantities
valid = hit_r > 0
rr_ = np.where(valid, hit_r, RIN)
ty_ = ((rr_ - RIN) / (ROUT - RIN) * (TR - 1)).astype(np.float32)
prof = (RIN / rr_) ** 2.4 * (0.3 + 0.7 * sm(RIN, 8.5, rr_)) * (1 - sm(9, 14, rr_))
gg = np.where(valid, hit_g, 0)
beam = np.clip(gg, 0, 2) ** 3.6
temp = (RIN / rr_) ** 0.75 * gg
OM = 0.95 * (RIN / rr_) ** 1.5           # rad/s (visual)
HS = [(6.6, 0.0, 1.0), (7.3, 2.1, 0.8), (8.2, 4.0, 0.7), (6.9, 3.3, 0.6), (9.5, 1.2, 0.5)]
cxs, cys = TW / 2, TH / 2
YY, XX = np.mgrid[0:TH, 0:TW].astype(np.float32)
rotA = math.radians(-4)
xr = (XX - cxs) * math.cos(rotA) + (YY - cys) * math.sin(rotA)
yr = -(XX - cxs) * math.sin(rotA) + (YY - cys) * math.cos(rotA)

from timeline import BEATS, STREAMS, IMPACTS, JKN, RIPS, CROSS, closed, zoom, sky_rot, jet_env, BLINK, CLOSE, CUTS, SPARKS, storm, shatter, pull
import os as _os
RAD = np.sqrt(xr * xr + yr * yr)
SC = TW / 1440.0
CAM_EL = math.radians(float(_os.environ.get('EL', 7.0)))
CAM_ROLL = math.radians(float(_os.environ.get('ROLL', -4)))
_f = np.array([0.0, -math.sin(CAM_EL), math.cos(CAM_EL)])
_rt = np.cross(_f, [0.0, 1.0, 0.0]); _rt /= np.linalg.norm(_rt)
_up = np.cross(_rt, _f)
ESCV = esc[ESCM].astype(np.float32)
MAJOR = [(ti, s) for ti, s in IMPACTS if s >= 1]
_cap = state == 1
SCY, SCX = [float(v.mean()) for v in np.nonzero(_cap)]
RSH = math.sqrt(_cap.sum() / math.pi)
RADC = np.sqrt((XX - SCX) ** 2 + (YY - SCY) ** 2)
SQ = min(0.9, math.sin(CAM_EL) * 1.3 + 0.12)
# palettes per act: A violet-blue, B magenta-violet, C icy blue-violet
PAL = [PC,
       np.array([[0.25, 0.03, 0.25], [0.62, 0.10, 0.62], [0.58, 0.25, 0.98], [0.70, 0.60, 1.00], [0.95, 0.88, 1.0], [1.0, 1.0, 1.0]], np.float32),
       np.array([[0.10, 0.05, 0.35], [0.25, 0.14, 0.78], [0.22, 0.45, 1.00], [0.50, 0.82, 1.00], [0.88, 0.96, 1.0], [1.0, 1.0, 1.0]], np.float32)]


def pal_at(t):
    a = float(sm(CUTS[0] - 0.05, CUTS[0] + 0.05, t)); b = float(sm(CUTS[1] - 0.05, CUTS[1] + 0.05, t))
    return PAL[0] * (1 - a) + PAL[1] * (a - b) + PAL[2] * b


def palette(x):
    return np.stack([np.interp(x, PT, CUR_PC[:, c]) for c in range(3)], -1).astype(np.float32)


CUR_PC = PC


def pulse(t):
    return sum(a * math.exp(-((t - b) * 7) ** 2) for b, a in BEATS if abs(t - b) < 1)


def wrapa(x):
    return (x + math.pi) % TAU - math.pi


def stream(hp_, r, t, S):
    t0, dur, p0, RS, amp, wm, starA = S
    tj = t0 + dur
    if t < t0 - 0.23 or t > tj + 1.6:
        return 0.0, 0.0
    KS = 1.9
    u = float(np.clip((t - t0) / dur, 0, 1))
    rh = RS - (RS - 6.15) * u ** 1.7
    qh = KS * math.log(RS / rh)
    rot = 0.35 * max(0.0, t - t0)
    q = (hp_ - p0 - rot) % TAU
    span = 1.9 * float(sm(t0, t0 + 0.6 * dur, t)) * (1 - float(sm(tj, tj + 1.2, t))) + 0.02
    s = (qh - q) / span
    rs_ = RS * np.exp(-np.clip(q, 0, qh + 0.3) / KS)
    dr = r - rs_
    wr = (0.7 + 1.9 * np.clip(s, 0, 1)) * wm
    fil = 0.65 + 0.35 * np.sin(dr / wr * 4.0 + q * 9 - t * 3) * np.sin(q * 23 + t * 5)
    band = np.exp(-(dr / wr) ** 2) * fil * np.exp(-1.6 * np.clip(s, 0, 1)) * sm(-0.04, 0.02, s) * (1 - sm(0.85, 1.0, s))
    I = band * float(sm(t0 - 0.1, t0 + 0.2, t)) * 1.5
    dq = wrapa(hp_ - p0 - rot - qh)
    sw = 0.45 * max(wm, 0.6)
    star = np.exp(-((r - rh) / sw) ** 2 - (dq * r / sw) ** 2) * (2.0 + 5.0 * float(sm(t0 - 0.23, t0 - 0.05, t)) * (1 - float(sm(t0, t0 + 0.7, t))))
    I = (I + star * starA * float(sm(t0 - 0.23, t0 - 0.1, t))) * (1 - float(sm(tj + 0.1, tj + 1.6, t))) * amp
    return I, np.clip(I * 0.9, 0, 0.85)


# ---------- plasma lightning: bolts drawn in disk (r, psi) space, so they get lensed with the disk ----------
LTR, LTP = 256, 2048


_BOLT_CACHE = {}
SLOT = 0.7


def _bolt_tex(slot):
    if slot in _BOLT_CACHE:
        return _BOLT_CACHE[slot]
    lam = storm(slot * SLOT + SLOT / 2)
    rg = np.random.default_rng(1000 + slot)
    n = rg.poisson(lam * 1.2)
    LT = None
    if n:
        LT = np.zeros((LTR, LTP), np.float32)
        for _ in range(n):
            p = rg.random() * LTP
            r0 = 6.3 + rg.random() * 6
            L = (0.35 + rg.random() * 1.0) / TAU * LTP
            steps = 24
            pts = []
            rr = r0
            for i in range(steps + 1):
                pts.append([p + L * i / steps, (rr - RIN) / (ROUT - RIN) * (LTR - 1)])
                rr += rg.normal(0, 0.12)
            pts = np.array(pts, np.float32)
            br = 0.6 + rg.random() * 0.6
            for sh in (0, LTP, -LTP):
                q = pts.copy(); q[:, 0] += sh
                cv2.polylines(LT, [q.astype(np.int32)], False, br, 2, cv2.LINE_AA)
        LT = LT * 1.2 + cv2.GaussianBlur(LT, (0, 0), 5) * 3.0
    if len(_BOLT_CACHE) > 8:
        _BOLT_CACHE.clear()
    _BOLT_CACHE[slot] = LT
    return LT


def bolts(t):
    """glowing plasma veins that fade smoothly in and out (no flicker), drifting with the orbit."""
    out = None
    for slot in (int(t / SLOT) - 1, int(t / SLOT)):
        if slot < 0:
            continue
        LT = _bolt_tex(slot)
        if LT is None:
            continue
        u = (t - slot * SLOT) / (2 * SLOT)          # each vein lives two slots
        if not 0 <= u <= 1:
            continue
        w = math.sin(math.pi * u) ** 2
        sh = int((t - slot * SLOT) * 0.5 / TAU * LTP)    # slide along the orbit
        L2 = np.roll(LT, sh, axis=1) * w
        out = L2 if out is None else out + L2
    return out


# ---------- screen-space particles: impact sparks and infalling debris ----------
_pr = np.random.default_rng(404)
SPK_P = []
for tb, s in SPARKS:
    n = int(260 * s)
    SPK_P.append((tb, s, _pr.random(n) * TAU, 0.6 + _pr.random(n) * 1.6, _pr.random(n), (_pr.random(n) - 0.5) * 1.6, _pr.integers(0, 3, n)))
DEB = []
tsp = 0.6
while tsp < 50:
    DEB.append((tsp, 2.5 + _pr.random() * 2.8, _pr.random() * TAU, 2.0 + _pr.random() * 2.2, _pr.random(), _pr.integers(0, 3)))
    tsp += 0.05 + _pr.random() * 0.12
PCOL = np.array([[0.95, 0.97, 1.0], [0.6, 0.75, 1.0], [0.8, 0.5, 1.0]], np.float32)


_gr = np.random.default_rng(808)
NG = 2200
G_RHO = 1.9 + _gr.random(NG) ** 1.4 * 2.6
G_PH = _gr.random(NG) * TAU
G_BAND = np.floor(_gr.random(NG) * 5)
G_RHO = np.where(_gr.random(NG) < 0.75, 2.0 + G_BAND * 0.42 + _gr.normal(0, 0.035, NG), G_RHO)   # mostly in thin rings
G_TW = _gr.random(NG) * TAU
G_C = _gr.integers(0, 3, NG)


def glitter_env(t):
    return float(0.9 * sm(5.5, 7.5, t) * (1 - sm(11.5, 13, t)) + 0.9 * sm(36.8, 38.5, t) * (1 - sm(43.6, 44.8, t)))


def particles(t):
    lay = np.zeros((TH, TW, 3), np.float32)
    drew = False
    cr_, sr_ = math.cos(CAM_ROLL), math.sin(CAM_ROLL)
    lw = max(1, int(round(1.6 * SC * 1.4)))
    P = pulse(t)
    # glitter rings orbiting in the disk plane (keplerian, breathing with the heartbeat)
    ge = glitter_env(t)
    if ge > 0.02:
        drew = True
        rho = G_RHO * (1 + 0.05 * P) * (1 + 0.04 * math.sin(t * 0.9))
        phi = G_PH + 0.9 * t / rho ** 1.5
        X, Y = rho * np.cos(phi), rho * np.sin(phi) * SQ
        xs = SCX + RSH * (X * cr_ - Y * sr_); ys = SCY + RSH * (X * sr_ + Y * cr_)
        vis = ~((np.sin(phi) < 0) & (np.hypot(xs - SCX, ys - SCY) < RSH * 1.08))
        ok = vis & (xs >= 0) & (xs < TW - 1) & (ys >= 0) & (ys < TH - 1)
        tw = 0.45 + 0.55 * np.sin(G_TW + t * 2.2) ** 2
        for c in range(3):
            m = ok & (G_C == c)
            mono = np.zeros((TH, TW), np.float32)
            np.add.at(mono, (ys[m].astype(int), xs[m].astype(int)), (tw[m] * ge * 1.6 * (1 + 0.8 * P)).astype(np.float32))
            lay += mono[..., None] * PCOL[c]
    for tb, s, th, v, rnd, sw, ci in SPK_P:     # soft glitter bloom drifting out after big moments
        dt = t - tb
        if not (0 < dt < 4.5):
            continue
        drew = True
        g = (1 - np.exp(-dt * 0.9)) / 0.9
        rr = RSH * 1.1 + v * TH * 0.16 * g
        a = th + sw * g * 0.8 + 0.3 * dt
        xs = SCX + rr * np.cos(a); ys = SCY + rr * np.sin(a) * (1 - 0.35 * rnd)
        fade = math.sin(math.pi * min(1.0, dt / 4.5)) ** 1.5 * s * (0.5 + 0.5 * np.sin(rnd * 40 + dt * 3) ** 2)
        ok = (xs >= 0) & (xs < TW - 1) & (ys >= 0) & (ys < TH - 1)
        for c in range(3):
            m = ok & (ci == c)
            mono = np.zeros((TH, TW), np.float32)
            np.add.at(mono, (ys[m].astype(int), xs[m].astype(int)), (fade[m] * 2.2).astype(np.float32))
            lay += mono[..., None] * PCOL[c]
    for ts_, T, ph0, rho0, rnd, ci in []:
        tau = t - ts_
        if not (0 < tau < T) or rnd > dens:
            continue
        drew = True

        def pp(x):
            u = min(x / T, 0.999)
            rho = rho0 * (1 - u) ** 0.55 + 1.0 * u
            phi = ph0 + 2.2 * x / (rho ** 1.5) + 1.5 * u
            X, Y = rho * math.cos(phi), rho * math.sin(phi) * SQ
            return SCX + RSH * (X * cr_ - Y * sr_), SCY + RSH * (X * sr_ + Y * cr_), rho, phi
        trail = [pp(max(0.0, tau - j * 0.035)) for j in range(7)]
        rho, phi = trail[0][2], trail[0][3]
        if rho < 1.15 or (math.sin(phi) < 0 and rho < 1.4):
            continue
        a = min(1.0, tau / 0.5) * float(sm(1.15, 1.5, rho)) * (0.25 + 0.5 * rnd)
        for j in range(6):
            x1, y1 = trail[j][:2]; x0, y0 = trail[j + 1][:2]
            if math.hypot(x0 - SCX, y0 - SCY) < RSH * 1.12 or math.hypot(x1 - SCX, y1 - SCY) < RSH * 1.12:
                continue
            cv2.line(lay, (int(x0), int(y0)), (int(x1), int(y1)), (PCOL[ci] * a * 1.0 * (1 - j / 6)).tolist(), lw, cv2.LINE_AA)
    if not drew:
        return None
    lay = cv2.GaussianBlur(lay, (0, 0), 0.6 + 0.4 * SC)
    return lay + cv2.GaussianBlur(lay, (0, 0), 3.0 * SC + 0.8) * 1.0


def echoes(t):
    out = None
    for tb, a in [(ti, s * 1.3) for ti, s in IMPACTS if s >= 1]:
        dt = t - tb
        if 0 < dt < 2.4:
            R = RSH * (1.03 + dt * 1.1 + 0.6 * dt * dt)
            w = (2.0 + 6 * dt) * SC * 2
            e = np.exp(-((RADC - R) / w) ** 2) * a * math.exp(-dt * 1.4) * 0.9
            out = e if out is None else out + e
    return out


def crossing(t):
    out = None
    for a0, a1, br, c, kind in CROSS:
        if a0 < t < a1:
            u = (t - a0) / (a1 - a0)
            sd = _f + (u - 0.5) * 0.16 * _rt + 0.006 * _up
            sd /= np.linalg.norm(sd)
            env = float(sm(a0, a0 + 0.6, t) * (1 - sm(a1 - 0.6, a1, t)))
            if kind == 'star':
                cosang = ESCV @ sd.astype(np.float32)
                ang2 = np.maximum(0, 2 * (1 - cosang))
                I = br * (np.exp(-ang2 / (0.0035 ** 2)) * 6 + np.exp(-ang2 / (0.012 ** 2)) * 0.6) * env
                cc = I[:, None] * np.array(c, np.float32)
            else:   # extended nebula: lensed into giant coloured arcs
                e1 = np.cross(sd, _up); e1 /= np.linalg.norm(e1); e2 = np.cross(e1, sd)
                aa = ESCV @ e1.astype(np.float32); bb = ESCV @ e2.astype(np.float32)
                g = np.exp(-(aa * aa + bb * bb) / (0.06 ** 2))
                nz = rmp(NEB_T, ((aa / 0.09 + 0.5) * 255).astype(np.float32), ((bb / 0.09 + 0.5) * 255).astype(np.float32))
                I = br * g * (0.3 + 1.4 * nz ** 2) * env * (ESCV @ sd.astype(np.float32) > 0)
                cc = I[:, None] * (np.array(c, np.float32) * (0.6 + 0.6 * nz[:, None]) + np.array([0.3, 0.5, 1.0], np.float32) * (1 - nz[:, None]) * 0.6)
            img = np.zeros((TH, TW, 3), np.float32)
            img[ESCM] = cc
            out = img if out is None else out + img
    return out


_nr = np.random.default_rng(9)
NEB_T = cv2.resize(_nr.random((8, 8)).astype(np.float32), (256, 256), interpolation=cv2.INTER_CUBIC) * 0.6 + \
    cv2.resize(_nr.random((24, 24)).astype(np.float32), (256, 256), interpolation=cv2.INTER_CUBIC) * 0.4
NEB_T = np.clip((NEB_T - NEB_T.min()) / (NEB_T.max() - NEB_T.min()), 0, 1)


def ripple(col, t):
    disp = np.zeros((TH, TW), np.float32)
    crest = np.zeros((TH, TW), np.float32)
    any_ = False
    for tb, a in RIPS:
        dt = t - tb
        if 0 < dt < 1.8:
            any_ = True
            R = dt * TH * 0.7
            w = 0.035 * TH * (1 + dt)
            x = (RADC - R) / w
            e = np.exp(-x * x) * a * math.exp(-dt * 1.3)
            disp += e * x * 0.04 * TH
            crest += e
    if not any_:
        return col
    nx = RADC + 1e-3
    mx = (XX - disp * (XX - SCX) / nx).astype(np.float32)
    my = (YY - disp * (YY - SCY) / nx).astype(np.float32)
    col = cv2.remap(col, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return col * (1 + 0.35 * crest)[..., None]


def zoom_blur(img, amt):
    smax = 1 + amt * 0.05 * 5
    acc = img
    K = 5
    for k in range(K):
        s = smax ** (2 ** k / 2 ** K)
        M = np.float32([[s, 0, SCX * (1 - s)], [0, s, SCY * (1 - s)]])
        acc = 0.57 * acc + 0.43 * cv2.warpAffine(acc, M, (TW, TH), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)
    return acc


RIBS = [(14.6, 1.1, 3, 0.55, 0.5, 5, 0.8, 0.0), (16.3, 0.8, 2, -0.4, 0.6, 7, 0.6, 2.1), (12.6, 0.6, 4, 0.7, 0.35, 6, -0.5, 4.0)]


def aurora(t):
    return float(0.6 * sm(25.0, 27.0, t) * (1 - sm(35.2, 35.9, t)) + 0.8 * sm(44.8, 46.5, t) * (1 - sm(48.6, 49.4, t)))


def cwave(t):
    return float(0.8 * sm(26, 28, t) * (1 - sm(33.5, 35, t)))


KS_ = [k for k in range(NHIT) if valid[k].any()]
IDX = {k: np.flatnonzero(valid[k]) for k in KS_}
CHP = {k: hit_psi[k].ravel()[IDX[k]] for k in KS_}
CR = {k: rr_[k].ravel()[IDX[k]] for k in KS_}
CPROF = {k: prof[k].ravel()[IDX[k]] for k in KS_}
CBEAM = {k: beam[k].ravel()[IDX[k]] for k in KS_}
CTEMP = {k: temp[k].ravel()[IDX[k]] for k in KS_}
CGG = {k: gg[k].ravel()[IDX[k]] for k in KS_}
CTY = {k: ty_[k].ravel()[IDX[k]] for k in KS_}
COM = {k: OM[k].ravel()[IDX[k]] for k in KS_}


def frame(t):
    global CUR_PC
    CUR_PC = pal_at(t)
    P = pulse(t)
    rf = RIN + 14 * eo((t - 0.42) / 1.7)
    ign_on = t > 0.42
    imp = sum(s * math.exp(-(t - ti) * 2.2) for ti, s in IMPACTS if t > ti)
    E = jet_env(t)
    G = shatter(t)
    LT = bolts(t)
    AU = aurora(t)
    CW = cwave(t)
    colf = np.zeros((TH * TW, 3), np.float32)
    transf = np.ones(TH * TW, np.float32)
    act = [S for S in STREAMS if S[0] - 0.25 < t < S[0] + S[1] + 1.6]
    for k in KS_:
        ix = IDX[k]
        hp_ = CHP[k]
        psi = hp_ - COM[k] * t
        tx_ = ((psi / TAU) % 1.0 * TP).astype(np.float32)
        T = tex if k == 0 else tex_soft
        dens = rmp(T, tx_, CTY[k])
        r = CR[k]
        if G > 0.01:
            gap = (0.5 + 0.5 * np.cos(TAU * r / 1.15 - t * 2.5)) ** 6
            dens = dens * (1 - G * 0.92 * (1 - gap)) * (1 + G * 0.8 * gap)
        ign = (1 - sm(rf - 0.9, rf + 0.25, r)) if ign_on else np.zeros_like(r)
        if k >= 1:
            ign = np.maximum(ign, sm(0.33, 0.5, t))
        front = 1.5 * np.exp(-((r - rf) / 0.55) ** 2) * (t < 2.4) * ign_on
        wave = 0
        for b, a in BEATS:
            dt = t - b
            if 0 < dt < 2.5:
                rw = RIN + dt * 7.5
                wave = wave + 3.2 * a * math.exp(-dt * 0.9) * np.exp(-((r - rw) / 0.7) ** 2)
        hot = 0
        for (hr, ha, hb) in HS:
            dpsi = wrapa(hp_ - (ha + 0.95 * (RIN / hr) ** 1.5 * t))
            hot = hot + hb * np.exp(-((r - hr) / 0.35) ** 2 - (dpsi * hr / 0.9) ** 2)
        for ti, s in MAJOR:
            if ti < t < ti + 8:
                dpsi = wrapa(hp_ - (1.0 + ti + 2.6 * (t - ti)))
                hot = hot + 2.2 * s * float(sm(ti, ti + 0.25, t) * (1 - sm(ti + 6, ti + 8, t))) * np.exp(-((r - 6.5) / 0.4) ** 2 - (dpsi * 6.5 / 1.6) ** 2)
        boost = 1 + 0.35 * imp * np.exp(-(r - RIN) / 2.5) + 0.5 * E * np.exp(-(r - RIN) / 4.0)
        em = CPROF[k] * (0.2 + 1.45 * dens + 2.2 * hot) * CBEAM[k] * (ign + front) * (1 + wave + P * 0.4) * boost
        if k >= 1:
            em = em * (1.3 + P * 2.2 + 0.6 * imp + 0.4 * E)
        sa = 0
        si = 0
        for S in act:
            a_, b_ = stream(hp_, r, t, S)
            si = si + a_
            sa = np.maximum(sa, b_)
        if LT is not None:
            lt = rmp(LT, ((hp_ / TAU) % 1.0 * LTP).astype(np.float32), CTY[k] * ((LTR - 1) / (TR - 1)))
            si = si + lt * (0.7 if k == 0 else 0.4) * (r < 13)
        em = em + si * 9.0 * np.clip(CGG[k], 0.3, 2) ** 3
        rib = 0
        if AU > 0.01:
            for (r0, a1, f1, s1, a2, f2, s2, ph) in RIBS:
                rc = r0 + a1 * np.sin(f1 * hp_ - s1 * t + ph) + a2 * np.sin(f2 * hp_ + s2 * t + 2 * ph)
                rib = rib + np.exp(-((r - rc) / 0.32) ** 2) * (0.35 + 0.65 * np.sin(hp_ * 9 - t * 1.6 + ph) ** 2)
            rib = rib * AU
            em = em + rib * 1.4 * np.clip(CGG[k], 0.4, 1.8) ** 2
        alpha = np.clip(np.maximum((0.2 + 0.7 * dens) * ign * (1 - sm(9, 14.5, r)), sa), 0, 0.9)
        cwv = CW * np.sin(r * 1.4 - t * 2.6) if CW > 0.01 else 0
        tcol = palette(CTEMP[k] * (1 + 0.15 * front + 0.1 * (dens - 0.5) + 0.25 * hot + 0.28 * cwv) + 0.08 * P + 0.5 * si + 0.06 * imp + 0.05 * E + 0.6 * rib)
        colf[ix] += (transf[ix] * em)[:, None] * tcol * 2.6
        transf[ix] *= (1 - alpha)
    col = colf.reshape(TH, TW, 3)
    trans = transf.reshape(TH, TW)
    sk = sky_at(sky_rot(t)) * (0.15 + 0.85 * sm(0.45, 1.6, t))
    cr = crossing(t)
    if cr is not None:
        sk = sk + cr
    pl = pull(t)
    if pl > 0.02:
        sk = zoom_blur(sk, pl)
    col += sk * trans[..., None]
    pt = particles(t)
    if pt is not None:
        col += pt * (0.55 + 0.45 * CUR_PC[3])[None, None]
    ec = echoes(t)
    if ec is not None:
        col += ec[..., None] * CUR_PC[4] * 0.8
    col = ripple(col, t)
    # ---- eyelid (screen space, fixed -4 deg so the loop matches) ----
    c = closed(t)
    a = 0.0 if t < 0.35 else float(np.clip(1.08 * eo((t - 0.35) / 0.28) - 0.08 * max(0, min(1, (t - 0.63) / 0.15)), 0, 1.1))
    a2 = (a + 2.6 * sm(0.75, 1.5, t)) * (1 - c) ** 1.5
    Ws = TW * (0.42 + 0.35 * a2)
    Hs = TH * 0.15 * a2
    lid = Hs * np.clip(1 - (xr / Ws) ** 2, 0, None)
    dist = np.abs(yr) - lid
    mask = np.maximum(1 - sm(-6 * SC, 3 * SC, dist), sm(1.25, 1.8, t) * (1 - min(1.0, c * 4)))
    slitA = (0.3 + 0.7 * sm(0.0, 0.33, t)) * (1 - sm(0.4, 0.75, t))
    slitA += 1.0 * float(sm(BLINK[0], BLINK[1], t) * (1 - sm(BLINK[2], BLINK[3], t)))
    slitA += 0.3 * float(sm(CLOSE[0] + 0.3, CLOSE[1], t))
    slit = np.exp(-(yr / (3.0 * SC + 0.12 * lid)) ** 2) * np.clip(1 - (xr / (TW * 0.48)) ** 2, 0, None) ** 0.7
    col = col * mask[..., None] + (slit * slitA * 1.6)[..., None] * np.array([0.75, 0.82, 1.0], np.float32)
    rimA = (1 - sm(0.6, 1.3, t)) * (t > 0.35) + 4 * c * (1 - c)
    rim = np.exp(-(dist / (5.0 * SC)) ** 2) * rimA
    col += (rim * 0.8)[..., None] * np.array([0.7, 0.75, 1.0], np.float32)
    return col


SPK = np.zeros((61, 61), np.float32)
for i in range(61):
    w_ = math.exp(-abs(i - 30) / 9)
    SPK[30, i] += w_; SPK[i, 30] += w_
    if abs(i - 30) < 22:
        SPK[i, i] += 0.35 * w_; SPK[i, 60 - i] += 0.35 * w_
SPK *= 0.025
_gy, _gx = np.mgrid[0:OH, 0:OW].astype(np.float32)
_dx, _dy = _gx - OW / 2, _gy - OH / 2
CAX_R, CAY_R = OW / 2 + _dx * 0.9985, OH / 2 + _dy * 0.9985
CAX_B, CAY_B = OW / 2 + _dx * 1.0015, OH / 2 + _dy * 1.0015


_dark = ((state == 1) & (nh == 0)).astype(np.uint8)
_dt = cv2.distanceTransform(_dark, cv2.DIST_L2, 5)
DVY, DVX = np.unravel_index(np.argmax(_dt), _dt.shape)


def dive(t):
    """0..1 amount of the 'dive through the black hole' transition around each camera cut."""
    d = 0.0
    for tc in CUTS:
        if tc - 0.9 < t < tc:
            d = max(d, float(sm(tc - 0.9, tc, t)) ** 2)
        elif tc <= t < tc + 1.1:
            d = max(d, 1 - float(sm(tc, tc + 1.1, t)) ** 0.7)
    return d


_bk = np.random.default_rng(2024)
NBK = 18
BK = dict(x=_bk.random(NBK), y=_bk.random(NBK), r=0.02 + _bk.random(NBK) ** 2 * 0.07, vx=(_bk.random(NBK) - 0.5) * 0.012,
          vy=-0.004 - _bk.random(NBK) * 0.01, ph=_bk.random(NBK) * TAU, c=_bk.integers(0, 3, NBK), d=0.4 + _bk.random(NBK) * 0.6)


def bokeh(t):
    lay = np.zeros((OH // 2, OW // 2, 3), np.float32)
    W2, H2 = OW // 2, OH // 2
    for i in range(NBK):
        d = BK['d'][i]
        x = ((BK['x'][i] + BK['vx'][i] * t - 0.006 * d * math.sin(t * 0.7)) % 1.2 - 0.1) * W2
        y = ((BK['y'][i] + BK['vy'][i] * t) % 1.2 - 0.1) * H2
        rad = BK['r'][i] * W2 * d
        a = 0.035 + 0.05 * math.sin(BK['ph'][i] + t * 0.5) ** 2
        cv2.circle(lay, (int(x), int(y)), max(2, int(rad)), (PCOL[BK['c'][i]] * a).tolist(), -1, cv2.LINE_AA)
        cv2.circle(lay, (int(x), int(y)), max(2, int(rad)), (PCOL[BK['c'][i]] * a * 0.8).tolist(), max(1, int(rad * 0.08)), cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.2 + 2 * (OW / 1080))
    return cv2.resize(lay, (OW, OH), interpolation=cv2.INTER_LINEAR)


def radial_blur(img, amt, cx, cy):
    """smooth zoom streaks: recursive doubling -> 64 log-spaced samples, no visible copies."""
    smax = 1 + amt * 0.035 * 7
    acc = img
    K = 6
    for k in range(K):
        s_ = smax ** (2 ** k / 2 ** K)
        M = np.float32([[1 / s_, 0, cx * (1 - 1 / s_)], [0, 1 / s_, cy * (1 - 1 / s_)]])
        acc = 0.56 * acc + 0.44 * cv2.warpAffine(acc, M, (acc.shape[1], acc.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return acc


_yy, _xx = np.mgrid[0:OH, 0:OW].astype(np.float32)
RDIST = np.hypot(_xx - OW / 2, _yy - OH / 2)
DMAX = float(RDIST.max())


def finish(col, t, f):
    z = max(zoom(t), 1.07)
    dv = dive(t)
    z = z * (1 + 1.6 * dv ** 1.4)
    cx = TW / 2 + (DVX - TW / 2) * min(1.0, dv * 3)
    cy = TH / 2 + (DVY - TH / 2) * min(1.0, dv * 3)
    sx = cx - TW / z / 2 + SC * (4 * math.sin(t * 0.7) + 2 * math.sin(t * 1.9))
    syy = cy - TH / z / 2 + SC * (3 * math.sin(t * 0.5 + 1) + 1.5 * math.sin(t * 1.6))
    M = np.float32([[1 / z * TW / OW, 0, sx], [0, 1 / z * TH / OH, syy]])
    spin = 0.0
    for tc in CUTS:
        if tc - 0.9 < t < tc:
            spin += 14 * float(sm(tc - 0.9, tc, t)) ** 2
        elif tc <= t < tc + 1.1:
            spin -= 14 * (1 - float(sm(tc, tc + 1.1, t)) ** 0.7) ** 1.3
    ang = math.radians(-3.0 * math.sin(t * TAU / 50) * float(sm(0.5, 6.0, t)) + 0.4 * math.sin(t * 0.8) + spin)
    Rm = np.float32([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    oc = np.float32([OW / 2, OH / 2])
    M = np.concatenate([M[:, :2] @ Rm, (M[:, :2] @ (oc - Rm @ oc) + M[:, 2])[:, None]], 1).astype(np.float32)
    img = cv2.warpAffine(col, M, (OW, OH), flags=(cv2.INTER_LINEAR if z > 1.5 else cv2.INTER_AREA) | cv2.WARP_INVERSE_MAP)
    br = np.maximum(img - 0.75, 0)
    q = cv2.resize(br, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA)
    bl = 0.45 * cv2.GaussianBlur(q, (0, 0), 2.5) + 0.3 * cv2.GaussianBlur(q, (0, 0), 10) + 0.08 * cv2.GaussianBlur(q, (0, 0), 36)
    img = img + cv2.resize(bl, (OW, OH), interpolation=cv2.INTER_LINEAR)
    if dv > 0.05:         # warp-tunnel streaks while diving through the hole
        img = radial_blur(img, dv * 1.6, OW / 2, OH / 2)
        # the shadow swallows the screen: soft black disc grows from the centre
        rin = DMAX * 1.15 * dv ** 1.25
        m = np.clip((RDIST - rin) / (0.18 * DMAX + 0.25 * rin), 0, 1) ** 1.5
        img = img * m[..., None]
    img = img + bokeh(t) * (1 - dv) * float(sm(1.2, 3.0, t)) * (1 - float(sm(49.0, 49.8, t)))
    img = 1 - np.exp(-img * 1.25)
    img[..., 0] = cv2.remap(img[..., 0], CAX_R, CAY_R, cv2.INTER_LINEAR)
    img[..., 2] = cv2.remap(img[..., 2], CAX_B, CAY_B, cv2.INTER_LINEAR)
    img = np.clip(img, 0, 1) ** (1 / 2.0)
    yy = (np.arange(OH)[:, None] - OH / 2) / OH
    xx = (np.arange(OW)[None] - OW / 2) / OH
    img *= (1 - 0.35 * (xx * xx + yy * yy))[..., None]
    noise = np.random.default_rng(f).standard_normal((OH, OW, 1)).astype(np.float32)
    return np.clip(img * 255 + noise * 1.6, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    mode = sys.argv[2]
    if mode == 'still':
        for ts in sys.argv[3:]:
            t = float(ts)
            cv2.imwrite(f'st_{ts}.png', cv2.cvtColor(finish(frame(t), t, 0), cv2.COLOR_RGB2BGR))
    else:
        out = sys.argv[3]
        dur = float(sys.argv[4])
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-profile:v', 'high', out]
        pp = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        nf = int(dur * FPS)
        f0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
        f1 = int(sys.argv[6]) if len(sys.argv) > 6 else nf
        for f in range(f0, f1):
            t = f / FPS
            pp.stdin.write(finish(frame(t), t, f).tobytes())
            if f % 30 == 0:
                print('frame', f, nf, flush=True)
        pp.stdin.close()
        pp.wait()
        print('done', out)
