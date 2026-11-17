# 0028 "This liquid is falling into darkness" - a real Rayleigh-Taylor instability (owner pick, Nov 17 2026: new effect,
# dark cosmic colours, nothing reused). A heavy glowing liquid rests on a lighter dark liquid in a tall glass tank; the
# interface is unstable, so the heavy liquid plunges down in mushroom-capped fingers that split again and again and roll
# into curls (Kelvin-Helmholtz) - like nebula pillars upside down. 2D incompressible Boussinesq fluid, own code:
# semi-Lagrangian (MacCormack) advection, buoyancy, vorticity confinement, pressure projection (multigrid-free Jacobi).
# The heavy liquid carries several coloured layers (indigo, violet, teal, gold) that get stretched into filaments.
# Rendered straight to frames: glowing volume on near-black, gradient sheen, soft bloom, dark glass edges.
# Usage: python nebula_rt.py <outdir> <seconds> <fps> [W H]
import math
import os
import subprocess
import sys

import numpy as np

OUT = os.path.abspath(sys.argv[1]); SECS = float(sys.argv[2]); FPS = int(sys.argv[3])
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1080, 1920)
os.makedirs(OUT, exist_ok=True)
NX, NY = 270, 480                       # sim grid (y up)
rng = np.random.default_rng(28)
dt = 1.0 / FPS
SUB = 4                                 # sim substeps per frame (CFL)
G = 700.0                               # baroclinic torque strength
EPS = 0.25                              # vorticity confinement

# fields: u, v velocity; c (4 dye channels, heavy-liquid concentration split into colour layers)
u = np.zeros((NY, NX)); v = np.zeros((NY, NX))
yy, xx = np.mgrid[0:NY, 0:NX].astype(np.float64)
_modes = sum(rng.uniform(1.0, 3.0) * np.sin(xx / NX * 2 * math.pi * k + rng.uniform(0, 6.28)) for k in (3, 5, 7, 11))
iface = NY * 0.66 + _modes + rng.normal(0, 0.6, NX)[None, :]   # perturbed interface: a few big modes -> big mushrooms
heavy = (yy > iface).astype(np.float64)
heavy = 1 / (1 + np.exp(-(yy - iface) / 0.9))
band = (yy - iface) / (NY - iface.mean())          # 0 at the interface -> 1 at the top
C = np.zeros((4, NY, NX))
C[0] = heavy * ((band % 0.5) < 0.17)               # teal  (the leading edge layer)
C[1] = heavy * (((band % 0.5) >= 0.17) & ((band % 0.5) < 0.3))  # violet
C[2] = heavy * (((band % 0.5) >= 0.3) & ((band % 0.5) < 0.43))  # indigo
C[3] = heavy * ((band % 0.5) >= 0.43)              # gold
COLS = np.array([[0.0, 0.55, 0.62], [0.42, 0.08, 0.78], [0.08, 0.1, 0.62], [0.95, 0.55, 0.12]])   # deep teal, violet, indigo, gold


def sample(f, x, y):
    x = np.clip(x, 0, NX - 1.001); y = np.clip(y, 0, NY - 1.001)
    x0 = x.astype(np.int64); y0 = y.astype(np.int64); fx = x - x0; fy = y - y0
    return (f[y0, x0] * (1 - fx) * (1 - fy) + f[y0, x0 + 1] * fx * (1 - fy) + f[y0 + 1, x0] * (1 - fx) * fy + f[y0 + 1, x0 + 1] * fx * fy)


def advect(f, u, v, h):
    xb = xx - u * h; yb = yy - v * h
    f1 = sample(f, xb, yb)
    # MacCormack: advect back and correct, clamp to neighbourhood (crisp filaments, no blur)
    f2 = sample(f1, xx + u * h, yy + v * h)
    fc = f1 + 0.5 * (f - f2)
    lo = np.minimum(np.minimum(f, np.roll(f, 1, 0)), np.minimum(np.roll(f, -1, 0), np.minimum(np.roll(f, 1, 1), np.roll(f, -1, 1))))
    hi = np.maximum(np.maximum(f, np.roll(f, 1, 0)), np.maximum(np.roll(f, -1, 0), np.maximum(np.roll(f, 1, 1), np.roll(f, -1, 1))))
    lo = sample(lo, xb, yb); hi = sample(hi, xb, yb)
    return np.clip(fc, lo, hi)


def dst1(a, axis):
    """type-I discrete sine transform along axis via FFT of the odd extension"""
    a = np.moveaxis(a, axis, -1)
    n = a.shape[-1]
    ext = np.concatenate([np.zeros(a.shape[:-1] + (1,)), a, np.zeros(a.shape[:-1] + (1,)), -a[..., ::-1]], -1)
    r = -np.fft.rfft(ext, axis=-1).imag[..., 1:n + 1] / 2
    return np.moveaxis(r, -1, axis)


_ky = np.arange(1, NY - 1); _kx = np.arange(1, NX - 1)
LAP = (2 * np.cos(np.pi * _ky / (NY - 1)) - 2)[:, None] + (2 * np.cos(np.pi * _kx / (NX - 1)) - 2)[None, :]


def poisson(rhs):
    """solve lap(psi) = rhs with psi = 0 on the walls (exact, FFT)"""
    f = dst1(dst1(rhs[1:-1, 1:-1], 0), 1)
    f = f / LAP
    psi = np.zeros_like(rhs)
    psi[1:-1, 1:-1] = dst1(dst1(f, 0), 1) * (2.0 / (NY - 1)) * (2.0 / (NX - 1))
    return psi


omega = np.zeros((NY, NX))


def step(h):
    """2D Boussinesq in vorticity form: d(omega)/dt = -g d(rho)/dx (baroclinic torque), u = curl(psi), lap(psi) = -omega"""
    global u, v, C, omega
    rho = C.sum(0)
    omega = omega - G * h * 0.5 * (np.roll(rho, -1, 1) - np.roll(rho, 1, 1))
    # vorticity confinement (sharper curls)
    aw = np.abs(omega)
    gx = 0.5 * (np.roll(aw, -1, 1) - np.roll(aw, 1, 1)); gy = 0.5 * (np.roll(aw, -1, 0) - np.roll(aw, 1, 0))
    n = np.hypot(gx, gy) + 1e-6
    fx, fy = EPS * (gy / n) * omega, -EPS * (gx / n) * omega
    omega = omega + h * 0.5 * ((np.roll(fy, -1, 1) - np.roll(fy, 1, 1)) - (np.roll(fx, -1, 0) - np.roll(fx, 1, 0)))
    omega[:, 0] = omega[:, -1] = 0; omega[0, :] = omega[-1, :] = 0
    psi = poisson(-omega)
    u = 0.5 * (np.roll(psi, -1, 0) - np.roll(psi, 1, 0)); v = -0.5 * (np.roll(psi, -1, 1) - np.roll(psi, 1, 1))
    u[:, 0] = u[:, -1] = 0; v[:, 0] = v[:, -1] = 0; u[0, :] = u[-1, :] = 0; v[0, :] = v[-1, :] = 0
    omega = advect(omega, u, v, h) * 0.9995
    C = np.stack([advect(C[k], u, v, h) for k in range(4)])


def upsample(f, w, h):
    ys = np.linspace(0, NY - 1.001, h)[::-1]; xs = np.linspace(0, NX - 1.001, w)
    X, Y = np.meshgrid(xs, ys)
    return sample(f, X, Y)


def blur(img, r):
    out = img.copy()
    for _ in range(3):
        for ax in (0, 1):
            acc = np.cumsum(np.pad(out, [(r + 1, r) if a == ax else (0, 0) for a in range(img.ndim)], mode="edge"), axis=ax)
            sl_hi = [slice(None)] * img.ndim; sl_lo = [slice(None)] * img.ndim
            sl_hi[ax] = slice(2 * r + 1, None); sl_lo[ax] = slice(0, -2 * r - 1)
            out = (acc[tuple(sl_hi)] - acc[tuple(sl_lo)]) / (2 * r + 1)
    return out


VIGN = None


def shade(t, zoom, cy):
    global VIGN
    w2, h2 = W // 2, H // 2                           # shade at half res, upscale at the end (soft, cheap)
    # camera: zoom into the tank around (0.5, cy)
    ys = cy + (np.linspace(0.5, -0.5, h2)) / zoom
    xs = 0.5 + (np.linspace(-0.5, 0.5, w2) * (W / H) * (NY / NX)) / zoom * (NX / NY)
    X, Y = np.meshgrid(np.clip(xs, 0, 1) * (NX - 1.001), np.clip(ys, 0, 1) * (NY - 1.001))
    dens = np.stack([sample(C[k], X, Y) for k in range(4)])
    tot = dens.sum(0)
    colw = np.einsum("kij,kc->ijc", dens, COLS) / (tot[..., None] + 1e-4)
    # depth: thin liquid glows translucent, thick is deep and saturated (Beer-Lambert), edges brighter (rim of each plume)
    gyy, gxx = np.gradient(tot)
    edge = np.clip(np.hypot(gxx, gyy) * 6.0, 0, 1)
    op = 1 - np.exp(-tot * 2.4)
    glow = colw * (0.12 + 0.6 * op[..., None]) * (0.45 + 1.1 * edge[..., None] ** 1.5)   # dark bodies, glowing rims
    # sheen: light from upper left on the density "surface"
    n = np.stack([-gxx * 3, -gyy * 3, np.ones_like(tot)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.45, 0.55, 0.7]); L /= np.linalg.norm(L)
    spec = np.clip((n @ L), 0, 1) ** 24 * op
    img = glow * 0.85 + spec[..., None] * np.array([0.75, 0.82, 1.0]) * 0.4
    # background: near-black blue with a faint deep-space gradient + very fine dust (the dark liquid)
    if VIGN is None:
        gy_, gx_ = np.mgrid[0:h2, 0:w2]
        r = np.hypot((gx_ - w2 * 0.5) / w2, (gy_ - h2 * 0.42) / h2)
        VIGN = (np.exp(-r * r * 3.2)[..., None] * np.array([0.022, 0.016, 0.05]) + np.array([0.004, 0.004, 0.009]))
    img = VIGN * (1 - op[..., None] * 0.9) + img
    # bloom on the bright parts only
    bright = np.clip(img - 0.4, 0, None)
    img = img + 0.55 * blur(bright, 9) + 0.25 * blur(bright, 30)
    # glass tank edges: two faint vertical highlights
    img = 1 - np.exp(-img * 1.6)                     # tone map
    up = np.repeat(np.repeat(img, 2, 0), 2, 1)[:H, :W]
    return (np.clip(up, 0, 1) ** (1 / 1.05) * 255).astype(np.uint8)


def camera(t):
    """hook: tight on the first finger diving and splitting; pull back to the whole tank by ~2.5 s"""
    u_ = min(1.0, max(0.0, (t - 0.3) / 2.4)); u_ = u_ * u_ * (3 - 2 * u_)
    zoom = 2.6 - 1.6 * u_
    cy = 0.5 + 0.08 * (1 - u_) - 0.0 * u_
    return zoom, cy


# pre-roll: let the instability grow off-screen so frame 0 already has fingers plunging
PRE = float(os.environ.get("RT_PRE", "1.1"))
for _ in range(int(PRE * FPS * SUB)):
    step(dt / SUB)
events = []
proc = None
NFR = int(SECS * FPS)
for fr in range(NFR):
    t = fr / FPS
    for _ in range(SUB):
        step(dt / SUB)
    z, cy = camera(t)
    rgb = shade(t, z, cy)
    from_bytes = rgb.tobytes()
    path = os.path.join(OUT, "f_%04d.png" % fr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-", path], input=from_bytes, check=True)
    # sound events: when the leading front crosses depth marks, a soft deep note
    lead = np.where(C.sum(0).max(1) > 0.3)[0]
    events.append({"t": t, "front": float(lead.min() / NY) if len(lead) else 1.0, "energy": float(np.mean(u * u + v * v))})
import json
json.dump(events, open(os.path.join(OUT, "events.json"), "w"))
print("done", NFR)
