# 0028 "Cosmos fired into milk" (owner, Nov 17 2026, confirmed plan): white MILK is the base for the whole video; dark
# cosmic liquids (indigo, violet, near-black, gold, teal) are FIRED into it. Each shot is a self-propelling vortex pair
# (a liquid "bullet") that blasts down through the milk, rolls into a mushroom cap and tears into fingers and spirals;
# the heavy dye keeps sinking and curling (Rayleigh-Taylor). Shots come faster and harder; the camera punches on each.
# 2D incompressible Boussinesq fluid in vorticity form, exact FFT Poisson solve, MacCormack advection (own code).
# Usage: python milk_cosmos.py <outdir> <seconds> <fps> [W H]
import json
import math
import os
import subprocess
import sys

import numpy as np

OUT = os.path.abspath(sys.argv[1]); SECS = float(sys.argv[2]); FPS = int(sys.argv[3])
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1080, 1920)
os.makedirs(OUT, exist_ok=True)
NX, NY = 288, 512
rng = np.random.default_rng(2828)
SUB = int(os.environ.get("MC_SUB", "4"))
G = 520.0                       # how hard the heavy dye sinks / curls
EPS = 0.3
yy, xx = np.mgrid[0:NY, 0:NX].astype(np.float64)
C = np.zeros((5, NY, NX))       # dye channels
COLS = np.array([                # pigment colours (what they look like THICK in milk)
    [0.06, 0.05, 0.32],          # indigo
    [0.26, 0.03, 0.42],          # violet
    [0.004, 0.004, 0.006],       # black
    [0.0, 0.33, 0.38],           # deep teal
    [0.85, 0.52, 0.08],          # gold
])
omega = np.zeros((NY, NX)); u = np.zeros((NY, NX)); v = np.zeros((NY, NX))

# shots: (time, x 0..1, strength, colour). Beat sheet (20 s):
#  0      HOOK: a black bullet tears into the milk (already mid-blast on frame 0), rolls into a mushroom
#  0.7-4.2 shots in pairs and triples, faster and harder; 4.2 the first gold-core blast
#  5.2-10.8 waves from left/right/centre, a run across, a big black one, a rapid burst of five
#  11.8   CLIMAX: a volley across the whole width; 12.6 the giant gold blast in the centre
#  13-16  everything slows down and settles, colours sink and curl
#  16.2   one last small gold drop into the calm; 18.6-20 fade to black
SHOTS = [(-0.42, 0.5, 1.4, 2)]
SHOTS += [(0.75, 0.3, 1.0, 0), (0.95, 0.7, 1.0, 1)]
SHOTS += [(1.6, 0.5, 1.1, 3), (1.85, 0.22, 0.9, 1), (2.05, 0.78, 0.9, 0)]
SHOTS += [(2.7, 0.38, 1.1, 2), (2.7, 0.62, 1.1, 4)]
SHOTS += [(3.3, 0.15, 1.0, 1), (3.4, 0.5, 1.3, 2), (3.5, 0.85, 1.0, 3)]
SHOTS += [(4.2, 0.5, 1.6, 4)]
SHOTS += [(5.2, 0.25, 1.0, 3), (5.2, 0.75, 1.0, 1), (5.9, 0.5, 1.2, 0)]
SHOTS += [(6.4, 0.18, 0.95, 1), (6.6, 0.4, 0.95, 3), (6.8, 0.62, 0.95, 0), (7.0, 0.84, 0.95, 2)]
SHOTS += [(7.7, 0.3, 1.1, 4), (7.7, 0.7, 1.1, 2), (8.4, 0.12, 1.0, 0), (8.45, 0.38, 1.0, 1), (8.5, 0.62, 1.0, 3), (8.55, 0.88, 1.0, 1)]
SHOTS += [(9.3, 0.5, 1.6, 2)]
SHOTS += [(10.0, 0.2, 1.0, 1), (10.2, 0.8, 1.0, 0), (10.4, 0.35, 1.0, 3), (10.6, 0.65, 1.0, 4), (10.8, 0.5, 1.1, 2)]
SHOTS += [(11.8, x, 1.15, c) for x, c in ((0.1, 0), (0.3, 1), (0.5, 2), (0.7, 3), (0.9, 1))]
SHOTS += [(12.6, 0.5, 2.0, 4)]
SHOTS += [(16.2, 0.5, 0.55, 4)]
SHOTS = [(t_ if t_ < 5.0 else 5.0 + (t_ - 5.0) * 0.62, x_, k_, c_) for (t_, x_, k_, c_) in SHOTS[:-1]] + [(11.0, 0.5, 0.55, 4)]
DUR = 21.5


def sample(f, x, y):
    x = np.clip(x, 0, NX - 1.001); y = np.clip(y, 0, NY - 1.001)
    x0 = x.astype(np.int64); y0 = y.astype(np.int64); fx = x - x0; fy = y - y0
    return (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x0 + 1] * fx * (1 - fy) + f[y0 + 1, x0] * (1 - fx) * fy + f[y0 + 1, x0 + 1] * fx * fy)


def advect(f, h):
    xb = xx - u * h; yb = yy - v * h
    f1 = sample(f, xb, yb)
    f2 = sample(f1, xx + u * h, yy + v * h)
    fc = f1 + 0.5 * (f - f2)
    nb = [f, np.roll(f, 1, 0), np.roll(f, -1, 0), np.roll(f, 1, 1), np.roll(f, -1, 1)]
    lo = sample(np.minimum.reduce(nb), xb, yb); hi = sample(np.maximum.reduce(nb), xb, yb)
    return np.clip(fc, lo, hi)


def dst1(a, axis):
    a = np.moveaxis(a, axis, -1); n = a.shape[-1]
    ext = np.concatenate([np.zeros(a.shape[:-1] + (1,)), a, np.zeros(a.shape[:-1] + (1,)), -a[..., ::-1]], -1)
    return np.moveaxis(-np.fft.rfft(ext, axis=-1).imag[..., 1:n + 1] / 2, -1, axis)


_ky = np.arange(1, NY - 1); _kx = np.arange(1, NX - 1)
LAP = (2 * np.cos(np.pi * _ky / (NY - 1)) - 2)[:, None] + (2 * np.cos(np.pi * _kx / (NX - 1)) - 2)[None, :]


def poisson(rhs):
    f = dst1(dst1(rhs[1:-1, 1:-1], 0), 1) / LAP
    psi = np.zeros_like(rhs)
    psi[1:-1, 1:-1] = dst1(dst1(f, 0), 1) * (2.0 / (NY - 1)) * (2.0 / (NX - 1))
    return psi


fired = set()


def fire(i, s):
    """a liquid bullet: a blob of dye + a counter-rotating vortex pair that drives it down at speed"""
    global omega
    t_, x_, k_, c_ = s
    cx, cy = x_ * NX, NY * 0.86
    r = (17.0 if t_ < 3 else 12.5) * (0.8 + 0.3 * k_)   # big slugs early, a little smaller later so the white survives
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    blob = np.exp(-(d2 / (r * r)) ** 3)        # a crisp-edged slug of dye, not a soft cloud
    jag = 1.0 + 0.06 * np.sin(np.arctan2(yy - cy, xx - cx) * 5 + i)
    # owner: "the main idea is BLACK and WHITE" -> every shot is black; its colour is only a thin heart inside it
    C[2] = np.clip(C[2] + 4.0 * blob * jag, 0, 6.0)
    if c_ != 2:
        C[c_] = np.clip(C[c_] + 0.45 * np.exp(-(d2 / (0.32 * r) ** 2) ** 3), 0, 1.5)
    a = 9000.0 * k_ * (1.0 if t_ < 7.0 else 0.62)   # calmer bullets in the dense middle (flash check)
    for sgn, off in ((1, -0.8), (-1, 0.8)):                 # left vortex CCW? the pair pushes down
        dd = (xx - (cx + off * r)) ** 2 + (yy - cy) ** 2
        omega += sgn * a / (2 * math.pi * r * r) * np.exp(-dd / (2 * (0.7 * r) ** 2)) * 1.0


def step(t, h):
    global omega, u, v, C
    for i, s in enumerate(SHOTS):
        if i not in fired and t >= s[0]:
            fired.add(i); fire(i, s)
    rho = C.sum(0)
    omega = omega - G * h * 0.5 * (np.roll(rho, -1, 1) - np.roll(rho, 1, 1))
    aw = np.abs(omega)
    gx = 0.5 * (np.roll(aw, -1, 1) - np.roll(aw, 1, 1)); gy = 0.5 * (np.roll(aw, -1, 0) - np.roll(aw, 1, 0))
    n = np.hypot(gx, gy) + 1e-6
    fx, fy = EPS * (gy / n) * omega, -EPS * (gx / n) * omega
    omega = omega + h * 0.5 * ((np.roll(fy, -1, 1) - np.roll(fy, 1, 1)) - (np.roll(fx, -1, 0) - np.roll(fx, 1, 0)))
    omega[:, :1] = omega[:, -1:] = 0; omega[:1, :] = omega[-1:, :] = 0
    psi = poisson(-omega)
    u = 0.5 * (np.roll(psi, -1, 0) - np.roll(psi, 1, 0)); v = -0.5 * (np.roll(psi, -1, 1) - np.roll(psi, 1, 1))
    u[:, :1] = u[:, -1:] = 0; v[:, :1] = v[:, -1:] = 0; u[:1, :] = u[-1:, :] = 0; v[:1, :] = v[-1:, :] = 0
    calm = 0.999 - 0.012 * min(1.0, max(0.0, (t - 10.0) / 1.6))
    omega = advect(omega, h) * calm
    C = np.stack([advect(C[k], h) for k in range(C.shape[0])])
    # old colour slowly dissolves into the milk (keeps the white base; fresh shots stay vivid); clears up after the climax
    tau_ = 3.3 if t < 10.2 else (1.6 if t < 11.0 else 9.0)
    C *= math.exp(-h / tau_)


def blur(img, r):
    out = img.copy()
    for _ in range(2):
        for ax in (0, 1):
            pad = [(r + 1, r) if a == ax else (0, 0) for a in range(img.ndim)]
            acc = np.cumsum(np.pad(out, pad, mode="edge"), axis=ax)
            hi = [slice(None)] * img.ndim; lo = [slice(None)] * img.ndim
            hi[ax] = slice(2 * r + 1, None); lo[ax] = slice(0, -2 * r - 1)
            out = (acc[tuple(hi)] - acc[tuple(lo)]) / (2 * r + 1)
    return out


MILK = np.array([0.97, 0.965, 0.94])


def shade(t, zoom, cy, cx):
    w2, h2 = W // 2, H // 2
    ys = cy + np.linspace(0.5, -0.5, h2) / zoom
    xs = cx + np.linspace(-0.5, 0.5, w2) * (W / H) * (NY / NX) / zoom
    X, Y = np.meshgrid(np.clip(xs, 0, 1) * (NX - 1.001), np.clip(ys, 0, 1) * (NY - 1.001))
    dens = np.stack([sample(C[k], X, Y) for k in range(C.shape[0])])
    tot = dens.sum(0)
    colw = np.einsum("kij,kc->ijc", dens, COLS) / (tot[..., None] + 1e-4)
    gyy, gxx = np.gradient(tot)
    edge = np.clip(np.hypot(gxx, gyy) * 4.0, 0, 1)
    # pigment in milk: thin = a light tint of the colour (milk shows through), thick = deep, almost black-coloured
    op = 1 - np.exp(-np.maximum(tot - 0.04, 0) * 9.0)   # faint traces read as clean milk
    thin = MILK * 0.55 + (colw / (colw.max(-1, keepdims=True) + 1e-4)) * 0.45 * MILK
    thick = colw
    pig = thin * (1 - op[..., None]) ** 0.6 + thick * (1 - (1 - op[..., None]) ** 0.6)
    # milk: soft studio light with a creamy falloff + fine fat texture; the dye sheen
    if not hasattr(shade, "bg"):
        gy_, gx_ = np.mgrid[0:h2, 0:w2]
        r = np.hypot((gx_ - w2 * 0.35) / w2, (gy_ - h2 * 0.3) / h2)
        nz = blur(np.random.default_rng(7).normal(0, 1, (h2, w2)), 18); nz /= np.abs(nz).max() + 1e-6
        fine = blur(np.random.default_rng(8).normal(0, 1, (h2, w2)), 3); fine /= np.abs(fine).max() + 1e-6
        shade.bg = MILK * (0.86 + 0.1 * np.exp(-r * r * 2.0) + 0.035 * nz + 0.012 * fine)[..., None]
    img = shade.bg * (1 - op[..., None]) + pig * op[..., None] * (0.85 + 0.25 * shade.bg / MILK)
    n = np.stack([-gxx * 2.5, -gyy * 2.5, np.ones_like(tot)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.45, 0.55, 0.7]); L /= np.linalg.norm(L)
    img = img * (0.82 + 0.18 * np.clip(n @ L, 0, 1))[..., None]
    img += (np.clip(n @ L, 0, 1) ** 40 * op)[..., None] * 0.35          # a glossy highlight on the dye
    img = img * (1 - 0.18 * edge[..., None]) + (edge[..., None] * colw * 0.0)
    k = min(1.0, max(0.0, (t - 31.2) / 1.7)); img = img * (1 - k * k * (3 - 2 * k))
    up = np.repeat(np.repeat(img, 2, 0), 2, 1)[:H, :W]
    return (np.clip(up, 0, 1) ** (1 / 1.02) * 255).astype(np.uint8)


def camera(t):
    """hook tight on the black bullet; pull back to the whole tank by ~3 s; widest at the climax; a slow push in for the
    last drop; a small punch-in kick on every shot (no rotation, ever)"""
    def ss(a_, b_):
        k = min(1.0, max(0.0, (t - a_) / (b_ - a_)))
        return k * k * (3 - 2 * k)
    zoom = 3.0 - 1.95 * ss(0.0, 3.0) - 0.08 * ss(8.4, 9.7) + 0.35 * ss(10.2, 11.6)
    cy = 0.76 - 0.24 * ss(0.0, 3.0) + 0.12 * ss(10.2, 11.6)
    kick = sum(0.05 * s_[2] * math.exp(-(t - s_[0]) * 9) for s_ in SHOTS if 0 <= t - s_[0] < 0.6 and s_[0] < 4.5)   # no kicks in the dense part (flash check)
    return zoom * (1 + kick), cy, 0.5


def rate(t):
    def ss(a_, b_):
        k = min(1.0, max(0.0, (t - a_) / (b_ - a_)))
        return k * k * (3 - 2 * k)
    return 0.6 - 0.28 * ss(4.6, 5.8)          # owner: "everything happens too fast" -> slow motion throughout, slower still once dense


PRE = 0.42
dt = 1.0 / FPS
t = -PRE
while t < 0:
    step(t, dt / SUB); t += dt / SUB
NFR = int(SECS * FPS)
tau = 0.0
for fr in range(NFR):
    tt = fr / FPS
    for k in range(SUB):
        h = dt / SUB * rate(tt + k * dt / SUB)
        step(tau, h); tau += h
    z, cy, cx = camera(tau)
    rgb = shade(tt, z, cy, cx)
    if os.environ.get("MC_MP4"):                       # fast path: one encoder process, no PNGs
        if fr == 0:
            enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                    "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", os.path.join(OUT, "video.mp4")], stdin=subprocess.PIPE)
        enc.stdin.write(rgb.tobytes())
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-",
                        os.path.join(OUT, "f_%04d.png" % fr)], input=rgb.tobytes(), check=True)
if os.environ.get("MC_MP4"):
    enc.stdin.close(); enc.wait()
json.dump({"shots": [{"t": s[0], "x": s[1], "k": s[2], "c": s[3]} for s in SHOTS]}, open(os.path.join(OUT, "events.json"), "w"))
print("done", NFR)
