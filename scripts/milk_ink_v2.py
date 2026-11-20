# 0028 v4 "Black ink fired into milk" - the owner's chosen video (milk_cosmos.py, Nov 17) IMPROVED, same look and story
# (owner, Nov 19: "I literally wanted you to improve THIS"): white milk, bullets of ink fired in, each rolls into a
# mushroom and tears into fingers and spirals (Rayleigh-Taylor), shots come faster until the milk is a storm, it
# dissolves, one last drop. Changes vs the original: a finer simulation grid (default 432x768 vs 288x512) shaded at full
# 1080x1920 (the original shaded at half size and doubled pixels), inks as real absorbing pigments in milk
# (Beer-Lambert per colour), a creamy milk surface, slower, a new smooth opening (one drop bursts into flying droplets).
# Colours (owner, Nov 20: "more colour at the start, more effects, dark purple too"): black, deep purple, indigo.
# 2D incompressible Boussinesq fluid in vorticity form, exact FFT Poisson solve, MacCormack advection (own code).
# Usage: python milk_ink_v2.py <outdir> <seconds> <fps> [W H]   env MI_NX (432), MI_SUB (4), MI_PNG=1 for PNG frames
import json
import math
import os
import subprocess
import sys
import time

import numpy as np

OUT = os.path.abspath(sys.argv[1]); SECS = float(sys.argv[2]); FPS = int(sys.argv[3])
W, H = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1080, 1920)
os.makedirs(OUT, exist_ok=True)
NX = int(os.environ.get("MI_NX", "432")); NY = int(round(NX * 512 / 288))
S = NX / 288.0                  # grid scale vs the original (all grid-unit constants scale with it)
SUB = int(os.environ.get("MI_SUB", "4"))
G = 520.0 * S                   # how hard the heavy ink sinks / curls
EPS = 0.3
yy, xx = np.mgrid[0:NY, 0:NX].astype(np.float64)
BLACK, PURPLE, INDIGO, MAGENTA, TEAL = 0, 1, 2, 3, 4
NCH = 5
C = np.zeros((NCH, NY, NX))     # ink densities: black, deep purple, indigo, deep magenta, deep teal
omega = np.zeros((NY, NX)); u = np.zeros((NY, NX)); v = np.zeros((NY, NX))

# shots: (sim time, x 0..1, strength). Same beat sheet as the original: pairs and triples, waves, a rapid burst, the
# climax volley + the giant blast, it all dissolves, one last small drop.
# OPENING (owner, Nov 19-20: "smooth, not chaos - like one drop of ink bursting in the milk and black drops flying",
# like the 0030 glass-ball-into-mesh burst; "more colour, more effects, dark purple"): ONE black drop with a deep purple
# heart glides down on frame 0; at BURST_T it bursts - a refraction shock ring runs through the milk, black / purple /
# indigo droplets fly out radially with silky coloured trails plus a fine spray, the big ones splash again where they
# land, the core blooms purple and the colour glows softly into the milk. The story shots follow OFF later.
DROP = (-0.25, 0.5, 0.9, 0.74)          # sim time, x, strength, start height (0..1)
BURST_T = 0.22
FADE0 = float(os.environ.get("MI_FADE", "31.2"))   # video time the final fade to black starts
OFF = {"massive": 0.9, "splash": 0.9, "pour": 1.95, "ball": 0.4}.get(os.environ.get("MI_OPEN", "burst"), 0.6)
SHOTS = []
SHOTS += [(0.75, 0.3, 1.0), (0.95, 0.7, 1.0)]
SHOTS += [(1.6, 0.5, 1.1), (1.85, 0.22, 0.9), (2.05, 0.78, 0.9)]
SHOTS += [(2.7, 0.38, 1.1), (2.7, 0.62, 1.1)]
SHOTS += [(3.3, 0.15, 1.0), (3.4, 0.5, 1.3), (3.5, 0.85, 1.0)]
SHOTS += [(4.2, 0.5, 1.6)]
SHOTS += [(5.2, 0.25, 1.0), (5.2, 0.75, 1.0), (5.9, 0.5, 1.2)]
SHOTS += [(6.4, 0.18, 0.95), (6.6, 0.4, 0.95), (6.8, 0.62, 0.95), (7.0, 0.84, 0.95)]
SHOTS += [(7.7, 0.3, 1.1), (7.7, 0.7, 1.1), (8.4, 0.12, 1.0), (8.45, 0.38, 1.0), (8.5, 0.62, 1.0), (8.55, 0.88, 1.0)]
SHOTS += [(9.3, 0.5, 1.6)]
SHOTS += [(10.0, 0.2, 1.0), (10.2, 0.8, 1.0), (10.4, 0.35, 1.0), (10.6, 0.65, 1.0), (10.8, 0.5, 1.1)]
SHOTS += [(11.8, x, 1.15) for x in (0.1, 0.3, 0.5, 0.7, 0.9)]
SHOTS += [(12.6, 0.5, 2.0)]
SHOTS = [(t_ if t_ < 5.0 else 5.0 + (t_ - 5.0) * 0.62, x_, k_) for (t_, x_, k_) in SHOTS] + [(11.0, 0.5, 0.55)]
SHOTS = [(t_ + OFF, x_, k_) for (t_, x_, k_) in SHOTS]
HEART = {i: (PURPLE, MAGENTA, TEAL, INDIGO, None)[i % 5] for i in range(len(SHOTS))}   # coloured hearts


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
EVENTS = []
CUR_TT = 0.0
BURST = {}
PARTS = []                                  # flying droplets: real ballistic drops that trail ink into the milk


def win(px, py, rad):
    x0 = max(0, int(px - rad)); x1 = min(NX, int(px + rad) + 2); y0 = max(0, int(py - rad)); y1 = min(NY, int(py + rad) + 2)
    return slice(y0, y1), slice(x0, x1)


def add_ink(ch, px, py, r, amp, crisp=False):
    sy, sx = win(px, py, 3.2 * r)
    d2 = (xx[sy, sx] - px) ** 2 + (yy[sy, sx] - py) ** 2
    C[ch, sy, sx] = np.clip(C[ch, sy, sx] + amp * (np.exp(-(d2 / (r * r)) ** 3) if crisp else np.exp(-d2 / (2 * r * r))), 0, 6.0)


def add_dipole(px, py, r, a, dx, dy):
    ex, ey = -dy, dx
    sy, sx = win(px, py, 4.0 * r)
    for sgn, off in ((-1, -0.8), (1, 0.8)):      # this pair moves ALONG (dx, dy)
        dd = (xx[sy, sx] - (px + off * r * ex)) ** 2 + (yy[sy, sx] - (py + off * r * ey)) ** 2
        omega[sy, sx] += sgn * a / (2 * math.pi * r * r) * np.exp(-dd / (2 * (0.7 * r) ** 2))


def spawn(x, y, ang, r, v0, ch, big, gen, trail, lig=1e9):
    dx, dy = math.cos(ang), math.sin(ang)
    PARTS.append(dict(x=x, y=y, vx=v0 * dx, vy=v0 * dy, r=r, ch=ch, big=big, gen=gen, trail=trail, alive=True, age=0.0, lig=lig))


def burst():
    """the drop bursts: droplets of black, deep purple and indigo fly out radially, slow and smooth, each trailing a
    silky coloured line, plus a fine spray; the core blooms purple"""
    global omega, C
    m = C.sum() + 1e-9
    cs = C.sum(0)
    cx, cy = (cs * xx).sum() / m, (cs * yy).sum() / m
    r0 = 17.0 * (0.8 + 0.3 * DROP[2]) * S
    BURST.update(x=cx / NX, y=cy / NY, tt=CUR_TT)
    omega *= 0.12; C[BLACK] *= 0.08; C[PURPLE] *= 0.3; C[INDIGO] *= 0.3
    add_ink(PURPLE, cx, cy, 0.5 * r0, 0.6)                     # the heart of the drop opens as a purple bloom
    rr = np.random.default_rng(30)
    cols = [PURPLE, BLACK, PURPLE, INDIGO, BLACK, PURPLE]
    n = 22
    for j in range(n):
        ang = 2 * math.pi * (j + 0.35 * rr.uniform(-1, 1)) / n + 0.3
        big = rr.uniform() ** 2                                     # a few big drops, many small ones
        spawn(cx + 0.55 * r0 * math.cos(ang), cy + 0.55 * r0 * math.sin(ang), ang, (0.11 + 0.17 * big) * r0,
              (330 - 150 * big) * S * rr.uniform(0.85, 1.12), cols[j % len(cols)], big, 0, 0.12)
    for j in range(34):                                             # the fine spray: tiny fast droplets
        ang = rr.uniform(0, 2 * math.pi)
        spawn(cx + 0.5 * r0 * math.cos(ang), cy + 0.5 * r0 * math.sin(ang), ang, 0.04 * r0 * rr.uniform(0.8, 1.3),
              470 * S * rr.uniform(0.75, 1.2), (PURPLE, INDIGO, BLACK)[j % 3], 0.0, 1, 0.07)
    EVENTS.append({"t": max(0.0, CUR_TT), "x": (cx / NX - 0.5) * 2.4, "r": 0.15, "spd": 1.2})


def fly(h):
    """drag + gravity; each drop lays a thin ink trail and nudges the milk; when slow it lands and curls into a
    mushroom - a big drop splashes again into a few tiny ones"""
    new = []
    for p in PARTS:
        if not p["alive"]:
            continue
        sp = math.hypot(p["vx"], p["vy"])
        dr = math.exp(-2.4 * h); p["age"] += h
        p["vx"] *= dr; p["vy"] = p["vy"] * dr - 140.0 * S * h
        p["x"] += p["vx"] * h; p["y"] += p["vy"] * h
        if sp > 1e-6 and p["age"] < p["lig"]:          # the thread snaps after "lig": then the drop flies free
            add_ink(p["ch"], p["x"], p["y"], max(0.25 * p["r"], 0.6), p["trail"] * min(1.0, sp * h / (0.5 * p["r"])))
            add_dipole(p["x"], p["y"], max(0.9 * p["r"], 1.2), 3.0 * p["r"] * sp * h, p["vx"] / sp, p["vy"] / sp)
        out = not (2 < p["x"] < NX - 3 and 2 < p["y"] < NY - 3)
        if sp < 45.0 * S or out:
            p["alive"] = False
            p["x"] = min(max(p["x"], 3.0), NX - 4.0); p["y"] = min(max(p["y"], 3.0), NY - 4.0)
            add_ink(p["ch"], p["x"], p["y"], max(p["r"], 1.0), 4.5 if p["ch"] == BLACK else 0.9, crisp=True)
            if not out and p["gen"] == 0:
                add_dipole(p["x"], p["y"], p["r"], 260.0 * p["r"] * S * 0.6, p["vx"] / (sp + 1e-6), p["vy"] / (sp + 1e-6))
                if p["big"] > 0.45:
                    EVENTS.append({"t": CUR_TT, "x": (p["x"] / NX - 0.5) * 2.4, "r": 0.03, "spd": 0.5})
                    base = math.atan2(p["vy"], p["vx"])
                    for k in range(5):                              # the second splash
                        new.append((p["x"], p["y"], base + math.pi + (k - 2) * 0.75, 0.32 * p["r"], 210 * S, p["ch"]))
    for (x, y, a, r, v0, ch) in new:
        spawn(x, y, a, r, v0, ch, 0.0, 1, 0.09)


def fire(i, s, start_y=0.86, heart=None, heart_amp=1.2, heart_r=0.45):
    """a liquid bullet: a slug of black ink (with a coloured heart) + a counter-rotating vortex pair driving it down"""
    global omega
    t_, x_, k_ = s
    cx, cy = x_ * NX, NY * start_y
    r = (17.0 if t_ < 3 else 12.5) * (0.8 + 0.3 * k_) * S
    sy, sx = win(cx, cy, 2.5 * r)
    d2 = (xx[sy, sx] - cx) ** 2 + (yy[sy, sx] - cy) ** 2
    blob = np.exp(-(d2 / (r * r)) ** 3)
    jag = 1.0 + 0.06 * np.sin(np.arctan2(yy[sy, sx] - cy, xx[sy, sx] - cx) * 5 + i)
    C[BLACK, sy, sx] = np.clip(C[BLACK, sy, sx] + 4.0 * blob * jag, 0, 6.0)
    if heart is not None:
        C[heart, sy, sx] = np.clip(C[heart, sy, sx] + heart_amp * 4.0 * np.exp(-(d2 / (heart_r * r) ** 2) ** 3), 0, 6.0)
    a = 9000.0 * k_ * (1.0 if t_ < 7.0 else 0.62) * S * S
    for sgn, off in ((1, -0.8), (-1, 0.8)):
        dd = (xx - (cx + off * r)) ** 2 + (yy - cy) ** 2
        omega += sgn * a / (2 * math.pi * r * r) * np.exp(-dd / (2 * (0.7 * r) ** 2))
    EVENTS.append({"t": max(0.0, CUR_TT), "x": (x_ - 0.5) * 2.4, "r": 0.06 * k_, "spd": k_})


# ---- opening variants (owner, Nov 20: "show me other possible effects") - env MI_OPEN ----
OPEN = os.environ.get("MI_OPEN", "burst")
NODES = []                                   # chandelier: self-propelled ink rings that keep splitting in two
SPLIT_T = [0.16, 0.46, 0.76]
GEN_COL = [PURPLE, INDIGO, PURPLE, INDIGO]
RING_T = [-0.34 + 0.09 * k for k in range(9)]
RING_C = [BLACK, None, PURPLE, None, INDIGO, None, BLACK, None, PURPLE]
RING_SPREAD = 0.08
CENTER = {"ball": (0.5, 0.56), "pour": (0.5, 0.56), "splash": (0.5, 0.72), "massive": (0.5, 0.76), "chandelier": (0.5, 0.80), "spiral": (0.5, 0.56), "collide": (0.5, 0.60), "rings": (0.5, 0.58)}


def push_a(v_target, r):
    """dipole strength for a self-propelled ring moving at v_target cells per sim time"""
    return v_target * r / 0.0487


def gauss_vortex(cx, cy, sig, om):
    global omega
    omega += om * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sig * sig))


MASSIVE_LAYERS = ((1.0, BLACK, 1.6), (0.9, MAGENTA, 0.9), (0.8, PURPLE, 1.0), (0.7, None, 0.0), (0.62, TEAL, 0.9),
                  (0.53, INDIGO, 1.0), (0.44, BLACK, 1.4), (0.36, None, 0.0), (0.28, MAGENTA, 1.0), (0.19, PURPLE, 1.2),
                  (0.1, TEAL, 1.0), (0.05, BLACK, 1.4))
VEINS = ((PURPLE, 1, 0.42), (TEAL, 2, 0.36), (MAGENTA, 3, 0.4), (INDIGO, 4, 0.38), (BLACK, 6, 0.3))


def marble_veins():
    """colour veins already floating in the milk on frame 0 (owner, Nov 20: 'too empty, boring, basic - more colour'):
    thin marbled lines of purple, teal, magenta, indigo and black over a faint coloured haze; the stir twists them"""
    for col, seed, amp in VEINS:
        f = blur(np.random.default_rng(100 + seed).normal(0, 1, (NY, NX)), max(3, int(16 * S)))
        f /= np.abs(f).max() + 1e-9
        veins = sum(np.exp(-((f - lv) / 0.05) ** 2) for lv in (-0.45, -0.05, 0.35))
        C[col] += amp * veins + 0.05 * np.clip(f, 0, 1)


SPL = {"acc": 0.0}
BALL = {"hit": False, "t_hit": 0.35, "cx": 0.5 * NX, "cy": 0.56 * NY, "R": 0.27 * NX, "x": 0.5 * NX, "y": 0.56 * NY,
        "r": 0.0846 * NX, "vb": 0.0}
POUR = {"t0": -0.3, "t1": 2.6, "TTHIN": 1.9, "V": 360.0, "VR": 700.0, "YRMAX": 0.45, "W": 0.09, "YP": 0.86, "YSTOP": 0.1, "next": -0.3}   # owner, Nov 20: bottle-thick, slow, smooth


def ink_haze(level):
    """the milk already clouded with ink (owner, Nov 20: 'no white background - ink, ink, ink')"""
    sm = blur(np.random.default_rng(31).normal(0, 1, (NY, NX)), max(3, int(22 * S))); sm /= np.abs(sm).max() + 1e-9
    s2 = blur(np.random.default_rng(32).normal(0, 1, (NY, NX)), max(2, int(8 * S))); s2 /= np.abs(s2).max() + 1e-9
    C[BLACK] += level * np.clip(0.7 * sm + 0.45 * s2 + 0.3, 0, 1) ** 1.8
    pv = blur(np.random.default_rng(33).normal(0, 1, (NY, NX)), max(3, int(18 * S))); pv /= np.abs(pv).max() + 1e-9
    C[PURPLE] += 0.08 * np.clip(pv + 0.1, 0, 1)


def opening(t, h):
    global omega, C
    if OPEN == "ball":                        # owner, Nov 20: "the opening like 'A Glass Ball Hit It' - that is the strong one".
        cx, cy = BALL["cx"], BALL["cy"]       # Ref (0030): a dark glass ball flies in from the corner and smashes a glowing net
        R = BALL["R"]                         # that fills the frame. Ours: it plunges into a huge glossy black ink drop with
        if "init" not in fired:               # violet veins floating in the milk; the ink bursts into a slow-motion spray of
            fired.add("init")                 # droplets and silky trails that fill the frame and swirl into the marble, while
            ink_haze(1.05)                    # the ball sinks, dragging an ink wake behind it.
            ang = np.arctan2(yy - cy, xx - cx)
            wob = 1 + 0.035 * np.sin(3 * ang + 0.7) + 0.025 * np.sin(5 * ang + 2.1)
            q = np.hypot(xx - cx, yy - cy) / (R * wob)
            s_ = np.clip((1.0 - q) * R / 1.6, 0, 1)
            fv = blur(np.random.default_rng(21).normal(0, 1, (NY, NX)), max(2, int(5 * S))); fv /= np.abs(fv).max() + 1e-9
            vein = np.exp(-(fv / 0.12) ** 2)
            C *= (1 - s_)[None]
            C[BLACK] += 2.6 * s_ * (1 - 0.55 * vein); C[PURPLE] += 0.45 * s_ * vein   # owner: "more black - ink"
            gauss_vortex(cx, cy, 0.5 * R, 2.5)    # it turns slowly: alive on frame 0
            r2 = np.random.default_rng(14)
            for k in range(14):
                gauss_vortex(r2.uniform(0.05, 0.95) * NX, r2.uniform(0.05, 0.95) * NY, NX * r2.uniform(0.04, 0.1),
                             (1 if r2.uniform() < 0.5 else -1) * r2.uniform(1.0, 2.5))
        if not BALL["hit"] and CUR_TT >= BALL["t_hit"]:
            BALL["hit"] = True; BALL["t_hitsim"] = t   # IMPACT: a shock ring, a hole punched through the drop, the ink blown outwards
            BURST.update(x=cx / NX, y=cy / NY, tt=CUR_TT)
            rr2 = (xx - cx) ** 2 + (yy - cy) ** 2
            a_ = 0.27 * R
            sc = np.sqrt(np.maximum(rr2 - a_ * a_, 0) / (rr2 + 1e-9))          # the ink is shoved outwards (area kept)
            C = np.stack([sample(C[c_], cx + (xx - cx) * sc, cy + (yy - cy) * sc) for c_ in range(NCH)])
            C *= np.clip((np.sqrt(rr2) - a_) / (0.15 * a_), 0, 1)[None]
            omega *= 0.3                      # owner, Nov 20: "after the ball hits I want the effect from second 5" (the
            rb = np.random.default_rng(77)    # dense swirling marble) "- more effects, more happening; I don't like seconds
            for j in range(120):              # 1-2" (no radial spray, no straight streaks): the drop SHATTERS into dozens of
                big_ = j < 6                  # eddies of every size, so the frame fills with swirling marble within a second
                an = rb.uniform(0, 2 * math.pi); rad = R * (rb.uniform(0.2, 1.25) if big_ else rb.uniform(0.0, 1.5))
                px, py = cx + rad * math.cos(an), cy + rad * math.sin(an)
                sg_ = NX * (rb.uniform(0.05, 0.08) if big_ else rb.uniform(0.01, 0.035))
                om_ = (1 if rb.uniform() < 0.5 else -1) * (rb.uniform(7, 12) if big_ else rb.uniform(18, 36))
                sy_, sx_ = win(px, py, 3 * sg_)
                omega[sy_, sx_] += om_ * np.exp(-((xx[sy_, sx_] - px) ** 2 + (yy[sy_, sx_] - py) ** 2) / (2 * sg_ * sg_))
            for j in range(6):                # a lopsided outward blast spreads the ink over the frame
                an = 2 * math.pi * (j + rb.uniform(-0.35, 0.35)) / 6 + 0.9
                rp = 0.3 * R * rb.uniform(0.8, 1.2)
                add_dipole(cx + 0.7 * R * math.cos(an), cy + 0.7 * R * math.sin(an), rp,
                           push_a(rb.uniform(220, 420) * S, rp), math.cos(an), math.sin(an))
            inkm = np.clip((C[BLACK] - 1.3) / 0.8, 0, 1)          # thin colour ribbons inside the drop's ink only
            for c_, sd_, amp_ in ((PURPLE, 41, 0.5), (INDIGO, 42, 0.3)):
                fv_ = blur(np.random.default_rng(sd_).normal(0, 1, (NY, NX)), max(2, int(6 * S))); fv_ /= np.abs(fv_).max() + 1e-9
                C[c_] += amp_ * inkm * np.exp(-(fv_ / 0.1) ** 2)
            BALL["npop"] = t + 0.08
            BALL["vb"] = 150.0 * S          # the drop brakes it for a moment...
            EVENTS.append({"t": max(0.0, CUR_TT), "x": 0.0, "r": 0.2, "spd": 1.5})
        if BALL["hit"] and t >= BALL.get("npop", 9e9) and t < BALL["t_hitsim"] + 1.6:
            BALL["npop"] = t + 0.09; BALL["k"] = BALL.get("k", 0) + 1
            rp_ = np.random.default_rng(500 + BALL["k"])
            ys_, xs_ = np.nonzero(C[BLACK] > 0.9)
            if ys_.size:
                i_ = rp_.integers(ys_.size); px, py = float(xs_[i_]), float(ys_[i_])
                an = rp_.uniform(0, 2 * math.pi); rr_ = NX * rp_.uniform(0.025, 0.05)
                add_dipole(px, py, rr_, push_a(rp_.uniform(250, 450) * S, rr_), math.cos(an), math.sin(an))   # an ink jet
                if rp_.uniform() < 0.3:
                    add_ink((PURPLE, INDIGO)[BALL["k"] % 2], px, py, rr_ * 1.1, 0.9)        # a colour bloom now and then
                else:
                    add_ink(BLACK, px, py, rr_ * 1.1, 1.6)                                  # a fresh puff of black ink
                EVENTS.append({"t": max(0.0, CUR_TT), "x": (px / NX - 0.5) * 2.4, "r": 0.04, "spd": 0.7})
        fly(h)
        if BALL["hit"] and BALL["y"] > -2 * BALL["r"]:   # ...then, heavy glass, it sinks faster and faster, pulling an
            vb = BALL["vb"]                               # ink wake down behind it, and is gone in about a second
            BALL["y"] -= vb * h
            BALL["vb"] = min(1400.0 * S, vb + 2600.0 * S * h)
            if 0 < BALL["y"] < NY:
                add_dipole(BALL["x"], BALL["y"], 0.9 * BALL["r"], 3.0 * BALL["r"] * min(vb, 450.0 * S) * h, 0.0, -1.0)
        return
    if OPEN == "pour":                        # owner pick (Nov 20): a thick stream of ink poured in from above, billowing
        if "init" not in fired and t >= -2.0:  # into curling clouds that fill the frame
            fired.add("init")
            ink_haze(0.85)
            r2 = np.random.default_rng(14)
            for k in range(22):
                gauss_vortex(r2.uniform(0.05, 0.95) * NX, r2.uniform(0.05, 0.95) * NY, NX * r2.uniform(0.04, 0.1),
                             (1 if r2.uniform() < 0.5 else -1) * r2.uniform(1.0, 2.8))   # calm: the stream stays centred
        if POUR["t0"] <= t < POUR["t1"] + 1.5:   # owner, Nov 20: "like a flower STEM - the ink pours down in a straight line
            u_ = t - POUR["t0"]                    # and only then mixes with the white" (the big round head was too much)
            fade = 1.0 - min(1.0, max(0.0, (t - POUR["t1"]) / 0.5))           # the bottle is lifted: the flow eases off
            W = POUR["W"] * NX; Wv = 1.15 * W     # the ink stream, and the plug of milk that carries it (its edges shear)
            xc = (0.5 + 0.018 * math.sin(2.3 * u_ + 0.6) + 0.007 * math.sin(5.9 * u_)) * NX   # a slow hand sway: no mirror shapes
            POUR["xc"] = xc
            sx = slice(max(1, int(xc - 1.8 * Wv)), min(NX - 1, int(xc + 1.8 * Wv) + 1))
            core_ = C[BLACK, :, int(xc - 0.5 * W):int(xc + 0.5 * W)].max(1)
            hit = np.nonzero(core_ > 1.1)[0]
            front = hit.min() if hit.size else POUR["YP"] * NY                  # the tip of the stem
            if "rel" not in POUR and (front < POUR["YSTOP"] * NY or t > 1.8):
                POUR["rel"] = t; POUR["front"] = front   # the stem has reached the bottom: it lets go FROM THE BOTTOM UP,
                EVENTS.append({"t": max(0.0, CUR_TT), "x": 0.0, "r": 0.12, "spd": 1.0})   # still pouring at the top
                rg = np.random.default_rng(5); POUR["seeds"] = []
                for k in range(14):                       # small eddies along both edges: it breaks into silky curls
                    yk = front + (0.95 * NY - front) * (k + rg.uniform(0.2, 0.8)) / 14
                    for sg in (-1, 1):
                        POUR["seeds"].append((yk, xc + sg * W * rg.uniform(0.9, 1.1), W * rg.uniform(0.18, 0.3), sg * rg.uniform(4, 8)))
            yrel = min(POUR["YRMAX"] * NY, POUR["front"] + (t - POUR["rel"]) * POUR["VR"] * S) if "rel" in POUR else 0.0
            if "rel" in POUR:
                for sd in [sd for sd in POUR["seeds"] if sd[0] < yrel]:
                    gauss_vortex(sd[1], sd[0], sd[2], sd[3]); POUR["seeds"].remove(sd)
            POUR["ylo"] = max(front + 0.4 * W, yrel); POUR["Wnow"] = W
            POUR["gloss"] = fade * (1 - min(1.0, max(0.0, (t - POUR["TTHIN"]) / 0.3)))
            yf = max(1.0, front - 1.5 * Wv, yrel)   # the plug runs just AHEAD of the tip: the stem slides down rigid and straight
            sy = slice(int(yf), NY - 1)
            Y = yy[sy, sx]; X = xx[sy, sx] - xc
            P = np.exp(-(X / Wv) ** 8)
            wy = np.clip((Y - yf) / (0.5 * Wv), 0, 1); wy = wy * wy * (3 - 2 * wy)
            band = np.exp(-(X / (1.6 * Wv)) ** 8)
            target = POUR["V"] * S * fade * 8.0 * X ** 7 / Wv ** 8 * P          # = -V dP/dX: two shear sheets = a plug falling at V
            d_ = target - omega[sy, sx]       # only ever push TOWARDS the plug: the curls that roll up on its edges are kept
            core = np.maximum(np.exp(-(X / (0.8 * Wv)) ** 8), np.exp(-((Y - front) / (1.2 * W)) ** 2))   # the middle + the head:
            omega[sy, sx] += (1 - math.exp(-h / 0.04)) * fade * wy * band * d_ * (core + (1 - core) * (target * d_ > 0))   # held
            if fade > 0.5 and t >= POUR.get("nseed", -9.0):   # owner, Nov 20: "it doesn't look like liquid" - real ink billows:
                POUR["nseed"] = t + 0.025                  # small eddies keep peeling off both edges and roll up into curls
                rs = np.random.default_rng(int((t + 5.0) * 1000))
                for sg in (-1, 1):
                    ys = rs.uniform(0.72, 0.84) * NY
                    if ys > front and rs.uniform() < (0.85 if sg > 0 else 0.6):   # uneven sides
                        cxs = xc + sg * W * rs.uniform(0.92, 1.08); sgm = W * rs.uniform(0.14, 0.24)
                        sy_, sx_ = win(cxs, ys, 3 * sgm)
                        omega[sy_, sx_] += sg * rs.uniform(5.0, 10.0) * np.exp(-((xx[sy_, sx_] - cxs) ** 2 + (yy[sy_, sx_] - ys) ** 2) / (2 * sgm * sgm))
            st_ = slice(int(0.9 * NY), NY - 1)    # calm water along the top: no corner eddies rolling stray ink into balls
            Xt = xx[st_, :] - xc
            tt_ = POUR["V"] * S * fade * 8.0 * Xt ** 7 / Wv ** 8 * np.exp(-(Xt / Wv) ** 8)
            wt = np.clip((yy[st_, :] - 0.9 * NY) / (0.04 * NY), 0, 1)
            omega[st_, :] += (1 - math.exp(-h / 0.04)) * wt * (tt_ - omega[st_, :])
            if fade > 0.999:                   # the bottle feeds the ink: deep black with silky grey and violet streaks that flow
                si = slice(int(POUR["YP"] * NY - 0.8 * W), NY - 1)   # down inside it; a rounded tip, no hard edges
                Yi = yy[si, sx]; Xi = xx[si, sx] - xc
                yb = POUR["YP"] * NY - 0.6 * W * np.sqrt(np.clip(1 - (Xi / W) ** 2, 0, 1))
                wv = np.clip((Yi - yb) / (0.05 * NY), 0, 1); wv = wv * wv * (3 - 2 * wv)
                thin = min(1.0, max(0.0, (t - POUR["TTHIN"]) / 0.5))   # the bottle is lifted: the stream thins to a thread
                pr = np.exp(-(Xi / (W * (1 - 0.85 * thin))) ** 6); Pi = pr * wv   # soft profile; Pi = how fast it is fed
                xw = Xi / W; ph = u_ + (Yi - NY) / (POUR["V"] * S)
                grey = sum(np.exp(-((xw - o_ - 0.13 * np.sin(5.3 * ph + 7 * o_) - 0.06 * np.sin(13.1 * ph + 3 * o_)) / 0.07) ** 2)
                           for o_ in (-0.55, 0.12, 0.6))           # soft, wandering wisps - not ruler-straight stripes
                viol = sum(np.exp(-((xw - o_ - 0.15 * np.sin(4.1 * ph + 5 * o_) - 0.07 * np.sin(11.3 * ph + o_)) / 0.1) ** 2) for o_ in (-0.3, 0.35))
                for c_ in (INDIGO, MAGENTA, TEAL):
                    C[c_, si, sx] *= (1 - Pi)
                # settle to the soft PROFILE (Pi * value), not to full strength wherever Pi > 0: otherwise dense ink piles up
                # beside the stem where nothing carries it away, and later drops as a stray black ball
                C[BLACK, si, sx] = C[BLACK, si, sx] * (1 - Pi) + Pi * pr * 1.6 * (1 - 0.38 * np.clip(grey + 0.5 * viol, 0, 1))
                C[PURPLE, si, sx] = C[PURPLE, si, sx] * (1 - Pi) + Pi * pr * 0.7 * np.clip(viol, 0, 1)
            if t >= POUR["next"] and fade > 0.5:
                POUR["next"] = t + 0.22
                if CUR_TT > 0 or t > -0.05:
                    EVENTS.append({"t": max(0.0, CUR_TT), "x": 0.0, "r": 0.05 + 0.03 * math.sin(5 * u_), "spd": 0.6})
        return
    if OPEN == "splash":                    # owner's reference (Nov 20): a massive ink wave of silky, see-through grey
        rr_ = np.random.default_rng(int(t * 1e4) % 100000 + 7)          # layers + a spray of black droplets on threads
        if "drop" not in fired and t >= -0.1:
            fired.add("drop")
            cx, cy = 0.5 * NX, 0.74 * NY
            R = 0.24 * NX
            ang = np.arctan2(yy - cy, xx - cx)
            wob = 1 + 0.04 * np.sin(3 * ang + 0.7) + 0.03 * np.sin(5 * ang + 2.1)
            q = np.hypot(xx - cx, yy - cy) / (R * wob)
            smoke = blur(np.random.default_rng(31).normal(0, 1, (NY, NX)), max(3, int(22 * S))); smoke /= np.abs(smoke).max() + 1e-9
            sm2 = blur(np.random.default_rng(32).normal(0, 1, (NY, NX)), max(2, int(8 * S))); sm2 /= np.abs(sm2).max() + 1e-9
            C[BLACK] += 1.0 * np.clip(0.7 * smoke + 0.45 * sm2 + 0.3, 0, 1) ** 1.8      # the milk is already clouded with ink
            pv = blur(np.random.default_rng(33).normal(0, 1, (NY, NX)), max(3, int(18 * S))); pv /= np.abs(pv).max() + 1e-9
            C[PURPLE] += 0.08 * np.clip(pv + 0.1, 0, 1)
            s_ = np.clip((1.0 - q) * R / 1.6, 0, 1)
            fv = blur(np.random.default_rng(21).normal(0, 1, (NY, NX)), max(2, int(4 * S))); fv /= np.abs(fv).max() + 1e-9
            vein = np.exp(-(fv / 0.12) ** 2)                           # marbled purple veins inside the black drop
            C *= (1 - s_)[None]
            C[BLACK] += 1.8 * s_ * (1 - 0.8 * vein); C[PURPLE] += 0.7 * s_ * vein
            add_dipole(cx, cy, 0.8 * R, push_a(140 * S, 0.8 * R), 0.25, -1.0)
            SPL["R"] = R
            EVENTS.append({"t": 0.0, "x": 0.0, "r": 0.2, "spd": 1.4})
        if "hit" not in fired and t >= 0.14:  # it crashes: the body flattens into a wide wave, the milk churns
            fired.add("hit")
            cs = C.sum(0); m = cs.sum() + 1e-9
            cx, cy = (cs * xx).sum() / m, (cs * yy).sum() / m
            R = SPL["R"]
            SPL.update(cx=cx, cy=cy)
            omega *= 0.5
            for sgn, spd_, dy_ in ((-1, 110, -0.45), (1, 300, 0.25)):   # lopsided: a wave that rolls up to the right
                add_dipole(cx + sgn * 0.45 * R, cy - 0.25 * R, 0.6 * R, push_a(spd_ * S, 0.6 * R), sgn * 1.0, dy_)
            r2 = np.random.default_rng(12)
            for k in range(36):
                a_ = r2.uniform(0, 2 * math.pi); dd = 1.8 * R * math.sqrt(r2.uniform())
                gauss_vortex(cx + dd * math.cos(a_), cy - 0.3 * R + dd * math.sin(a_), NX * r2.uniform(0.02, 0.06),
                             (1 if r2.uniform() < 0.5 else -1) * r2.uniform(12, 26))
            for k in range(24):                # the inky milk all around starts to roll as well
                gauss_vortex(r2.uniform(0.05, 0.95) * NX, r2.uniform(0.05, 0.95) * NY, NX * r2.uniform(0.04, 0.1),
                             (1 if r2.uniform() < 0.5 else -1) * r2.uniform(6, 14))
            EVENTS.append({"t": CUR_TT, "x": 0.0, "r": 0.16, "spd": 1.3})
        if 0.14 <= t < 0.24:                   # the spray: droplets torn off the crest, each pulling a thin ink thread
            SPL["acc"] += 320 * h / 0.1
            R = SPL["R"]
            while SPL["acc"] >= 1:
                SPL["acc"] -= 1
                th = rr_.uniform(0.35, 2.95) if rr_.uniform() < 0.35 else rr_.uniform(1.2, 2.95)   # mostly up-left
                u_ = rr_.uniform()
                r = R * (0.006 + 0.065 * u_ ** 4)                          # a mist of tiny drops, a few big ones
                px = SPL["cx"] + 1.05 * R * math.cos(th); py = SPL["cy"] + 0.55 * R * math.sin(th)
                spawn(px, py, th + rr_.uniform(-0.25, 0.25), r, (720 - 420 * u_) * S * rr_.uniform(0.7, 1.15),
                      BLACK if rr_.uniform() < 0.8 else PURPLE, 0.0, 1, 0.22, lig=0.022 + 0.03 * u_)
        fly(h)
        return
    if OPEN == "massive":                     # ONE massive marbled drop (owner, Nov 20) that rolls up into giant swirls
        if "drop" not in fired and t >= -0.3:
            fired.add("drop")
            marble_veins()
            cx, cy = CENTER[OPEN][0] * NX, CENTER[OPEN][1] * NY
            R = 0.31 * NX
            ang = np.arctan2(yy - cy, xx - cx)
            wob = 1 + 0.05 * np.sin(3 * ang + 0.7) + 0.035 * np.sin(5 * ang + 2.1) + 0.02 * np.sin(9 * ang + 4.0)
            q = np.hypot(xx - cx, yy - cy) / (R * wob)
            for rl, col, amp in MASSIVE_LAYERS:        # layers of black / purple / milk / indigo: marbling once it rolls up
                s_ = np.clip((rl - q) * R / 1.6, 0, 1)
                C *= (1 - s_)[None]
                if col is not None:
                    C[col] += amp * s_
            add_dipole(cx, cy, 0.8 * R, push_a(260 * S, 0.8 * R), 0.0, -1.0)
            nz = blur(np.random.default_rng(5).normal(0, 1, (NY, NX)), max(2, int(5 * S)))
            omega += nz / (np.abs(nz).max() + 1e-9) * 6.0          # tiny disturbances -> organic, uneven swirls
            EVENTS.append({"t": 0.0, "x": 0.0, "r": 0.2, "spd": 1.4})
        if "stir" not in fired and t >= 0.08:  # the impact churns the milk: swirls of every size tear the drop into marble
            fired.add("stir")
            cx, cy = CENTER[OPEN][0] * NX, CENTER[OPEN][1] * NY - 0.04 * NX
            rr_ = np.random.default_rng(11)
            for k in range(46):
                a_ = rr_.uniform(0, 2 * math.pi); dd = 0.29 * NX * 1.45 * math.sqrt(rr_.uniform())
                gauss_vortex(cx + dd * math.cos(a_), cy + dd * math.sin(a_), NX * rr_.uniform(0.03, 0.09),
                             (1 if rr_.uniform() < 0.5 else -1) * rr_.uniform(16, 34))
            for k in range(28):                # gentler swirls all over the tank so the colour veins move from the start
                gauss_vortex(rr_.uniform(0.05, 0.95) * NX, rr_.uniform(0.05, 0.95) * NY, NX * rr_.uniform(0.04, 0.1),
                             (1 if rr_.uniform() < 0.5 else -1) * rr_.uniform(8, 16))
            EVENTS.append({"t": CUR_TT, "x": 0.0, "r": 0.14, "spd": 1.2})
        return
    if OPEN == "burst":
        if "drop" not in fired and t >= DROP[0]:
            fired.add("drop"); fire(-1, DROP[:3], DROP[3], heart=PURPLE, heart_amp=0.9, heart_r=0.62)
        if "burst" not in fired and t >= BURST_T:
            fired.add("burst"); burst()
        fly(h)
    elif OPEN == "chandelier":                # one drop -> 2 -> 4 -> 8 rings, the classic ink "chandelier"
        cx, cy = CENTER[OPEN][0] * NX, CENTER[OPEN][1] * NY
        if "drop" not in fired and t >= -0.3:
            fired.add("drop")
            r = 24.0 * S
            add_ink(BLACK, cx, cy, r, 1.6, crisp=True); add_ink(PURPLE, cx, cy, 0.62 * r, 0.9, crisp=True)
            add_dipole(cx, cy, r, push_a(150 * S, r), 0.0, -1.0)
            NODES.append(dict(x=cx, y=cy, dx=0.0, dy=-1.0, r=r, gen=0, alive=True))
            EVENTS.append({"t": 0.0, "x": 0.0, "r": 0.12, "spd": 1.0})
        for nd in NODES:                      # each ring rides on the flow it makes
            if nd["alive"]:
                nd["x"] += float(sample(u, np.array(nd["x"]), np.array(nd["y"]))) * h
                nd["y"] += float(sample(v, np.array(nd["x"]), np.array(nd["y"]))) * h
        for g, ts in enumerate(SPLIT_T):
            if ("split", g) not in fired and t >= ts:
                fired.add(("split", g))
                born = []
                for nd in NODES:
                    if not nd["alive"] or nd["gen"] != g:
                        continue
                    nd["alive"] = False
                    sy, sx = win(nd["x"], nd["y"], 2.6 * nd["r"]); omega[sy, sx] *= 0.12
                    base = math.atan2(nd["dy"], nd["dx"]); rc = 0.62 * nd["r"]
                    for sgn in (-1, 1):
                        a = base + sgn * 0.52
                        px, py = -math.sin(base), math.cos(base)
                        x = nd["x"] + sgn * 0.55 * nd["r"] * px; y = nd["y"] + sgn * 0.55 * nd["r"] * py
                        add_dipole(x, y, rc, push_a(135 * S, rc), math.cos(a), math.sin(a))
                        add_ink(GEN_COL[g], x, y, 0.55 * rc, 0.45, crisp=True)
                        born.append(dict(x=x, y=y, dx=math.cos(a), dy=math.sin(a), r=rc, gen=g + 1, alive=True))
                    EVENTS.append({"t": CUR_TT, "x": (nd["x"] / NX - 0.5) * 2.4, "r": 0.1 - 0.025 * g, "spd": 1.0})
                NODES.extend(born)
    elif OPEN == "spiral":                    # a slow whirlpool in the milk winds the drops into a spiral galaxy
        cx, cy = CENTER[OPEN][0] * NX, CENTER[OPEN][1] * NY
        if "init" not in fired and t >= -0.3:
            fired.add("init")
            gauss_vortex(cx, cy, 0.2 * NX, 28.0)
            for k, (rad, ang, col, amp) in enumerate(((0.06, 0.3, PURPLE, 0.5), (0.13, 2.4, BLACK, 1.6), (0.13, 4.5, INDIGO, 0.5),
                                                       (0.2, 1.2, BLACK, 1.6), (0.2, 3.3, PURPLE, 0.5), (0.2, 5.4, INDIGO, 0.5))):
                add_ink(col, cx + rad * NX * math.cos(ang), cy + rad * NX * math.sin(ang), (8.0 + 6 * rad / 0.2) * S, amp, crisp=True)
            EVENTS.append({"t": 0.0, "x": 0.0, "r": 0.12, "spd": 1.0})
        for k, (ts, ang, col) in enumerate(((0.25, 0.8, PURPLE), (0.45, 3.9, BLACK), (0.62, 2.2, INDIGO))):
            if ("sd", k) not in fired and t >= ts:      # fresh drops fall into the whirl, one after another
                fired.add(("sd", k))
                add_ink(col, cx + 0.24 * NX * math.cos(ang), cy + 0.24 * NX * math.sin(ang), 11.0 * S, 1.6 if col == BLACK else 0.5, crisp=True)
                EVENTS.append({"t": CUR_TT, "x": 0.6 * math.cos(ang), "r": 0.07, "spd": 0.8})
    elif OPEN == "collide":                   # a black and a purple ring fired at each other: head-on, they swap partners
        cx, cy = CENTER[OPEN][0] * NX, CENTER[OPEN][1] * NY
        if "init" not in fired and t >= -0.1:
            fired.add("init")
            r = 20.0 * S
            for sgn, skin, sa, heart in ((-1, BLACK, 1.6, PURPLE), (1, PURPLE, 0.6, INDIGO)):
                x = cx + sgn * 0.22 * NX
                add_ink(skin, x, cy, r, sa, crisp=True); add_ink(heart, x, cy, 0.55 * r, 0.5, crisp=True)
                add_dipole(x, cy, r, push_a(200 * S, r), -sgn * 1.0, 0.0)
            EVENTS.append({"t": 0.0, "x": 0.0, "r": 0.1, "spd": 1.0})
        if "hit" not in fired and t >= 0.22:
            fired.add("hit"); EVENTS.append({"t": CUR_TT, "x": 0.0, "r": 0.15, "spd": 1.2})
    elif OPEN == "rings":                     # drop after drop in one spot: rings like marbled stone, then a twist into a rose
        cx, cy = CENTER[OPEN][0] * NX, CENTER[OPEN][1] * NY
        rk = 13.0 * S
        dA = 0.0
        for k, ts in enumerate(RING_T):
            if ("ring", k) not in fired and t >= ts:
                fired.add(("ring", k))
                sy, sx = win(cx, cy, 0.5 * rk)
                d2 = (xx[sy, sx] - cx) ** 2 + (yy[sy, sx] - cy) ** 2
                m = d2 < (0.35 * rk) ** 2
                for c_ in range(NCH):
                    C[c_, sy, sx][m] = 0.0
                if RING_C[k] is not None:
                    C[RING_C[k], sy, sx][m] = 1.2 if RING_C[k] == BLACK else 0.35
                EVENTS.append({"t": max(0.0, CUR_TT), "x": 0.0, "r": 0.07, "spd": 0.6})
            if ts <= t < ts + RING_SPREAD:
                dA += math.pi * rk * rk * h / RING_SPREAD
        if dA > 0:                            # every new drop pushes all the older rings outwards (area kept)
            rr2 = (xx - cx) ** 2 + (yy - cy) ** 2 + 1e-9
            sc = np.sqrt(np.maximum(rr2 - dA / math.pi, 0) / rr2)
            X_, Y_ = cx + (xx - cx) * sc, cy + (yy - cy) * sc
            C = np.stack([sample(C[c_], X_, Y_) for c_ in range(NCH)])
        if "twist" not in fired and t >= 0.5:
            fired.add("twist"); gauss_vortex(cx, cy, 0.11 * NX, 16.0)
            EVENTS.append({"t": CUR_TT, "x": 0.0, "r": 0.12, "spd": 1.0})


def gfac(t):
    """gravity: full for the falling openings; nearly off for the flat ones until they hand over to the story"""
    if OPEN == "ball":                         # the drop floats still until the ball hits, then gravity takes over
        k = min(1.0, max(0.0, (t - 0.1) / 0.6))
        return 0.04 + 0.96 * k * k * (3 - 2 * k)
    if OPEN in ("burst", "chandelier", "splash"):
        return 1.0
    if OPEN == "pour":                         # owner: "slower, smooth, not dumped in" - light gravity while it pours
        k = min(1.0, max(0.0, (t - POUR.get("rel", 9.0)) / 0.8))
        return 0.15 + 0.85 * k * k * (3 - 2 * k)
    k = min(1.0, max(0.0, (t - 1.0) / 0.6))
    return 0.1 + 0.9 * k * k * (3 - 2 * k)


def step(t, h):
    global omega, u, v, C
    opening(t, h)
    for i, s in enumerate(SHOTS):
        if i not in fired and t >= s[0]:
            fired.add(i); fire(i, s, heart=HEART[i])
    rho = C.sum(0)
    omega = omega - G * gfac(t) * h * 0.5 * (np.roll(rho, -1, 1) - np.roll(rho, 1, 1))
    aw = np.abs(omega)
    gx = 0.5 * (np.roll(aw, -1, 1) - np.roll(aw, 1, 1)); gy = 0.5 * (np.roll(aw, -1, 0) - np.roll(aw, 1, 0))
    n = np.hypot(gx, gy) + 1e-6
    fx, fy = EPS * (gy / n) * omega, -EPS * (gx / n) * omega
    omega = omega + h * 0.5 * ((np.roll(fy, -1, 1) - np.roll(fy, 1, 1)) - (np.roll(fx, -1, 0) - np.roll(fx, 1, 0)))
    omega[:, :1] = omega[:, -1:] = 0; omega[:1, :] = omega[-1:, :] = 0
    psi = poisson(-omega)
    u = 0.5 * (np.roll(psi, -1, 0) - np.roll(psi, 1, 0)); v = -0.5 * (np.roll(psi, -1, 1) - np.roll(psi, 1, 1))
    u[:, :1] = u[:, -1:] = 0; v[:, :1] = v[:, -1:] = 0; u[:1, :] = u[-1:, :] = 0; v[:1, :] = v[-1:, :] = 0
    calm = 0.999 - 0.012 * min(1.0, max(0.0, (t - 10.0 - OFF) / 1.6))
    omega = advect(omega, h) * calm
    C = np.stack([advect(C[k], h) if C[k].max() > 1e-4 else C[k] for k in range(NCH)])
    tau_ = (7.0 if OPEN in ("massive", "splash", "pour", "ball") else 3.3) if t < 10.2 + OFF else (1.6 if t < 11.0 + OFF else 9.0)     # old ink slowly dissolves into the milk
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


MILK = np.array([0.975, 0.962, 0.93])          # creamy, faintly warm white
KABS = {"massive": 3.2, "splash": 2.4, "pour": 2.4, "ball": 3.0}.get(OPEN, 8.0)   # softer pigment: ink MIXES into the milk as greys
THR = {"massive": 0.015, "splash": 0.01, "pour": 0.01, "ball": 0.01}.get(OPEN, 0.035)
SIG = np.array([[1.02, 1.0, 0.95],             # carbon black: neutral, a hair cool when thin
                [0.55, 1.25, 0.32],            # deep purple: lilac when thin, royal violet when thick
                [1.1, 0.88, 0.28],             # indigo: periwinkle when thin, deep blue-violet when thick
                [0.22, 1.3, 0.62],             # deep magenta: rose-pink when thin, berry-crimson when thick
                [1.35, 0.42, 0.36]])           # deep teal: aqua when thin, petrol blue-green when thick
_gy, _gx = np.mgrid[0:H, 0:W].astype(np.float64)
_r = np.hypot((_gx - W * 0.33) / W, (_gy - H * 0.28) / H)
_nz = blur(np.random.default_rng(7).normal(0, 1, (H, W)), 36); _nz /= np.abs(_nz).max() + 1e-6
_fine = blur(np.random.default_rng(8).normal(0, 1, (H, W)), 4); _fine /= np.abs(_fine).max() + 1e-6
BG = MILK * (0.925 + 0.07 * np.exp(-_r * _r * 2.0) + 0.022 * _nz + 0.008 * _fine)[..., None]   # bright milk, soft light
del _r, _nz, _fine
GI, GJ = _gx, _gy
L = np.array([-0.45, 0.55, 0.7]); L /= np.linalg.norm(L)


def up2(f):
    """2x Catmull-Rom upsampling (separable) so the ink edges stay smooth curves when the camera is close"""
    for ax in (0, 1):
        a = np.moveaxis(f, ax, 0)
        p = np.concatenate([a[:1], a, a[-1:], a[-1:]], 0)
        mid = (-p[:-3] + 9 * p[1:-2] + 9 * p[2:-1] - p[3:]) / 16.0
        o = np.empty((2 * a.shape[0] - 1,) + a.shape[1:]); o[0::2] = a; o[1::2] = mid[:-1]
        f = np.moveaxis(o, 0, ax)
    return np.maximum(f, 0)


def draw_ball(img, t, zoom, cy, cx, spx, ppc):
    """the dark glass ball: flies in from the lower-left corner close to the lens, then sinks through the ink. Real
    glass cues: an inverted, magnified view of the scene inside it, violet-tinted dark glass, Fresnel reflection of the
    bright milk at its rim, a sharp key highlight + a soft one, a thin back-light rim"""
    if not BALL["hit"]:
        s_ = min(1.0, max(0.0, t / BALL["t_hit"]))
        d_ = 1 + 3.55 * s_                                   # flying away from the lens: it shrinks with distance
        bi = (-0.06 + 0.56 * s_) * (W - 1); bj = (1.04 - 0.54 * s_) * (H - 1); R = 0.5 / d_ * W
    else:
        bi = ((BALL["x"] / (NX - 1) - cx) / spx + 0.5) * (W - 1); bj = (0.5 - (BALL["y"] / (NY - 1) - cy) * zoom) * (H - 1)
        dt_ = t - BALL["t_hit"]
        R = BALL["r"] * ppc * (1 - 0.18 * min(1.0, dt_ / 1.2))      # sinking away from us
        yi_, xi_ = int(min(max(BALL["y"], 0), NY - 1)), int(min(max(BALL["x"], 0), NX - 1))
        cover = min(0.85, max(0.0, (C[BLACK, yi_, xi_] - 1.0) / 1.5))   # the black ink closes over it
        vis = (1 - min(1.0, max(0.0, (dt_ - 0.7) / 0.6))) * (1 - cover)
        if vis <= 0.01:
            return img
    if R < 2 or bj - R > H or bj + R < 0 or bi + R < 0 or bi - R > W:
        return img
    x0, x1 = max(0, int(bi - R - 2)), min(W, int(bi + R + 3)); y0, y1 = max(0, int(bj - R - 2)), min(H, int(bj + R + 3))
    gy_, gx_ = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    dx_, dy_ = (gx_ - bi) / R, (gy_ - bj) / R
    rr = np.sqrt(dx_ * dx_ + dy_ * dy_)
    al = np.clip((1 - rr) * R + 0.5, 0, 1)[..., None] * (vis if BALL["hit"] else 1.0)
    nz = np.sqrt(np.clip(1 - rr * rr, 0, 1))
    k_ = -0.5 - 0.4 * (1 - nz)                               # a crystal ball: the world inside, upside down and magnified
    si = np.clip(np.rint(bi + dx_ * R * k_), 0, W - 1).astype(np.int64); sj = np.clip(np.rint(bj + dy_ * R * k_), 0, H - 1).astype(np.int64)
    refr = img[sj, si]
    fr = (0.04 + 0.96 * (1 - nz) ** 3)[..., None]
    env = (0.18 + 0.7 * np.clip(0.5 - 0.6 * dy_, 0, 1))[..., None] * np.array([0.96, 0.95, 0.98])
    col = refr * np.array([0.17, 0.15, 0.23]) * (1 - fr) + env * fr
    spec = 1.4 * np.exp(-((dx_ + 0.36) ** 2 + (dy_ + 0.42) ** 2) / 0.003) + 0.16 * np.exp(-((dx_ + 0.3) ** 2 + (dy_ + 0.34) ** 2) / 0.03) \
        + 0.12 * np.exp(-((dx_ - 0.42) ** 2 + (dy_ - 0.5) ** 2) / 0.02)     # + a small warm kick from below-right
    rim = 0.22 * np.exp(-((rr - 0.95) / 0.035) ** 2) * np.clip(0.3 + dx_ + dy_, 0, 1)
    col = col + (spec + rim)[..., None] * np.array([0.97, 0.97, 1.0])
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - al) + col * al
    return img


def shade(t, zoom, cy, cx):
    spx = (W / H) * (NY / NX) / zoom
    ys = cy + np.linspace(0.5, -0.5, H) / zoom
    xs = cx + np.linspace(-0.5, 0.5, W) * spx
    X, Y = np.meshgrid(np.clip(xs, 0, 1) * (2 * NX - 2.001), np.clip(ys, 0, 1) * (2 * NY - 2.001))
    bg = BG
    tb = t - BURST.get("tt", 1e9)
    if 0 <= tb < 1.8:                                          # the burst's shock ring refracts the milk as it passes
        bi = ((BURST["x"] - cx) / spx + 0.5) * (W - 1); bj = (0.5 - (BURST["y"] - cy) * zoom) * (H - 1)
        dxp, dyp = GI - bi, GJ - bj
        rp = np.hypot(dxp, dyp) + 1e-6
        R = 20 + 1150 * (1 - math.exp(-tb * 1.3)); wd = 24 + 70 * tb; A = 15 * math.exp(-tb * 1.7)
        q = (rp - R) / wd
        disp = A * 2 * q * np.exp(-q * q)
        ux, uy = dxp / rp, dyp / rp
        X = np.clip(X - disp * ux * (2 * NX - 2.001) * spx / (W - 1), 0, 2 * NX - 2.001)
        Y = np.clip(Y + disp * uy * (2 * NY - 2.001) / zoom / (H - 1), 0, 2 * NY - 2.001)
        jj = np.clip(np.rint(GJ - disp * uy), 0, H - 1).astype(np.int64); ii = np.clip(np.rint(GI - disp * ux), 0, W - 1).astype(np.int64)
        bg = BG[jj, ii] + (0.06 * math.exp(-tb * 1.7) * np.exp(-q * q))[..., None]
    halo = blur(C[1:].sum(0), max(2, int(5 * S)))              # colour scattering softly into the milk around the ink
    f2 = np.stack([up2(C[k]) for k in range(NCH)] + [up2(halo)], -1)
    x0 = X.astype(np.int64); y0 = Y.astype(np.int64); fx = (X - x0)[..., None]; fy = (Y - y0)[..., None]
    d = (f2[y0, x0] * (1 - fx) * (1 - fy) + f2[y0, x0 + 1] * fx * (1 - fy) + f2[y0 + 1, x0] * (1 - fx) * fy + f2[y0 + 1, x0 + 1] * fx * fy)
    dens = np.maximum(d[..., :NCH] - THR, 0)
    tot = d[..., :NCH].sum(-1)
    T = np.exp(-KABS * (dens @ SIG) - 0.9 * d[..., NCH:NCH + 1] * SIG[PURPLE])  # Beer-Lambert per pigment + the soft glow
    img = bg * (0.004 + 0.996 * T)
    op = 1 - T.mean(-1)
    gyy, gxx = np.gradient(tot)
    pg = 2.0 * zoom / S
    n = np.stack([-gxx * pg, -gyy * pg, np.ones_like(tot)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    nl = np.clip(n @ L, 0, 1)
    img = img * (0.84 + 0.16 * nl)[..., None]                 # the ink's slight relief on the milk
    img += (nl ** 40 * op * 0.22)[..., None]                  # a soft wet sheen on thick ink
    if OPEN == "pour" and POUR.get("gloss", 0.0) > 0.01:               # owner: "it does not look like liquid from a bottle":
        gxc = X * 0.5; gyc = Y * 0.5                                    # the stream is a round, wet rope - a soft highlight runs
        nxp = (gxc - POUR["xc"]) / POUR["Wnow"] + 0.05 * np.sin(gyc / NY * 23.0 - t * 7.0)   # down it, its sides turn darker
        ins = np.clip(1 - nxp ** 2, 0, 1)
        mg = np.clip(ins / 0.15, 0, 1) * np.clip((gyc - POUR["ylo"]) / (0.05 * NY), 0, 1) * POUR["gloss"] * op   # no seam
        img = img * (1 - (mg * 0.3 * (1 - np.sqrt(ins)))[..., None])
        spec = 0.34 * np.exp(-((nxp + 0.36) / 0.13) ** 2) + 0.1 * np.exp(-((nxp - 0.64) / 0.07) ** 2)
        img += (spec * mg)[..., None] * np.array([0.88, 0.9, 1.0])
    if OPEN in ("splash", "pour", "ball"):                             # silky sheets: darker rims where the thin ink folds
        eg = np.clip(np.hypot(gxx, gyy) * pg * 1.4, 0, 1) * (1 - op) ** 0.5
        img = img * (1 - 0.32 * eg)[..., None]
    ppc = (W - 1) / ((NX - 1) * spx)                           # pixels per grid cell
    for p in PARTS:                                            # the flying drops: glossy beads, stretched by speed
        if not p["alive"]:
            continue
        i = ((p["x"] / (NX - 1) - cx) / spx + 0.5) * (W - 1); j = (0.5 - (p["y"] / (NY - 1) - cy) * zoom) * (H - 1)
        R = max(p["r"] * ppc, 1.2)
        sp = math.hypot(p["vx"], p["vy"]); st = 1.0 + min(0.9, sp / (500.0 * S))
        ca, sa = (p["vx"] / sp, -p["vy"] / sp) if sp > 1e-6 else (1.0, 0.0)
        a_, b_ = R * st, R / math.sqrt(st)
        x0_, x1_ = max(0, int(i - a_ - 3)), min(W, int(i + a_ + 4)); y0_, y1_ = max(0, int(j - a_ - 3)), min(H, int(j + a_ + 4))
        if x0_ >= x1_ or y0_ >= y1_:
            continue
        gy_, gx_ = np.mgrid[y0_:y1_, x0_:x1_]
        dx_, dy_ = gx_ - i, gy_ - j
        uu = (dx_ * ca + dy_ * sa) / a_; ww = (-dx_ * sa + dy_ * ca) / b_
        al = np.clip((1 - np.sqrt(uu * uu + ww * ww)) * b_ + 0.5, 0, 1)[..., None]
        hl = 0.45 * np.exp(-((dx_ + 0.3 * R) ** 2 + (dy_ + 0.35 * R) ** 2) / (2 * (0.2 * R + 0.6) ** 2))[..., None]
        ink = MILK * np.exp(-4.5 * SIG[p["ch"]])
        img[y0_:y1_, x0_:x1_] = img[y0_:y1_, x0_:x1_] * (1 - al) + (ink + hl) * al
    if OPEN == "ball":
        img = draw_ball(img, t, zoom, cy, cx, spx, ppc)
    k = min(1.0, max(0.0, (t - FADE0) / 1.7)); img = img * (1 - k * k * (3 - 2 * k))
    return (np.clip(img, 0, 1) ** (1 / 1.02) * 255).astype(np.uint8)


CAM = {"y": CENTER.get(OPEN, (0.5, DROP[3]))[1]}


def camera(t):
    """smooth, no kicks: close on the falling drop (following it), then a slow pull back with the burst until the whole
    tank shows; widest at the climax; a slow push in for the last drop (no rotation, ever)"""
    def ss(a_, b_):
        k = min(1.0, max(0.0, (t - a_) / (b_ - a_)))
        return k * k * (3 - 2 * k)
    late = - 0.08 * ss(8.4 + OFF, 9.7 + OFF) + 0.35 * ss(10.2 + OFF, 11.6 + OFF)
    if OPEN == "splash":                       # never an empty frame: so close the drop fills the screen, then the camera
        cs = C.sum(0); m = cs.sum()            # backs off exactly as fast as the splash spreads, centred on the ink
        if m > 1e-6:
            CAM["y"] += ((cs * yy).sum() / m / NY - CAM["y"]) * 0.12
        o = ss(0.12, 1.3)
        zoom = 2.25 - 1.2 * o + late
        hz = 0.5 / zoom
        cy = min(max(CAM["y"], hz), 1 - hz)
        o2 = ss(1.0, 2.2)
        cy = cy * (1 - o2) + 0.52 * o2
        cy += 0.12 * ss(10.2 + OFF, 11.6 + OFF)
        return zoom, cy, 0.5
    if OPEN == "burst":
        if "burst" not in fired:
            cs = C.sum(0); m = cs.sum()
            if m > 1e-6:
                CAM["y"] += ((cs * yy).sum() / m / NY - CAM["y"]) * 0.25
        o = ss(BURST_T + 0.02, BURST_T + 1.25)
        zoom = 2.3 - 1.25 * o + late
        cy = CAM["y"] if "burst" not in fired else BURST["y"] * (1 - o) + 0.52 * o
    elif OPEN == "chandelier":
        if ("split", 0) not in fired:
            cs = C.sum(0); m = cs.sum()
            if m > 1e-6:
                CAM["y"] += ((cs * yy).sum() / m / NY - CAM["y"]) * 0.25
            CAM["y0"] = CAM["y"]
        o = ss(SPLIT_T[0], SPLIT_T[0] + 1.2)
        zoom = 2.1 - 1.05 * o + late
        cy = CAM["y"] if ("split", 0) not in fired else CAM["y0"] * (1 - o) + 0.5 * o
    else:
        z0, p0 = {"spiral": (1.75, 0.45), "collide": (1.7, 0.32), "rings": (2.0, 0.5), "massive": (1.3, 0.05), "pour": (1.35, 0.35), "splash": (1.25, 0.2), "ball": (1.3, 0.12)}[OPEN]
        o = ss(p0, p0 + 1.05)
        zoom = z0 - (z0 - 1.05) * o + late
        cy = CENTER[OPEN][1] * (1 - o) + 0.52 * o
    cy += 0.12 * ss(10.2 + OFF, 11.6 + OFF)
    zoom = max(zoom, 1.0)                     # never frame wider than the tank: no smeared rows at the edges
    cy = min(max(cy, 0.5 / zoom), 1 - 0.5 / zoom)
    return zoom, cy, 0.5


def rate(t):
    def ss(a_, b_):
        k = min(1.0, max(0.0, (t - a_) / (b_ - a_)))
        return k * k * (3 - 2 * k)
    if OPEN == "ball":                 # slow motion through the impact and the burst, then real speed, then a brisk story
        return 0.3 + 0.25 * ss(0.55, 1.3) - 0.15 * ss(4.5, 5.7)
    if OPEN == "pour":                 # owner, Nov 20: "speed it up, it looks super slow" - a real-speed pour, a brisker story
        return 0.6 - 0.2 * ss(4.5, 5.7)
    return 0.35 + 0.25 * ss(2.2, 3.6) - 0.28 * ss(5.6, 6.8)   # slow-motion burst, then the original (slow) pace


PRE = 0.42
SHADE_FROM = float(os.environ.get("MI_SHADE_FROM", "-1"))
dt = 1.0 / FPS
t = -PRE
while t < 0:
    step(t, dt / SUB); t += dt / SUB
NFR = int(SECS * FPS)
tau = 0.0
t0 = time.time()
if os.environ.get("MI_PNG"):
    enc = None
else:
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", os.path.join(OUT, "video.mp4")], stdin=subprocess.PIPE)
for fr in range(NFR):
    tt = fr / FPS
    for k in range(SUB):
        CUR_TT = tt + k * dt / SUB
        h = dt / SUB * rate(CUR_TT)
        step(tau, h); tau += h
    z, cy, cx = camera(tau)
    if tt < SHADE_FROM - 1e-6:            # stills (e.g. the 4K cover): simulate up to the moment, shade only from there
        continue
    rgb = shade(tt, z, cy, cx)
    if enc:
        enc.stdin.write(rgb.tobytes())
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-i", "-",
                        os.path.join(OUT, "f_%04d.png" % fr)], input=rgb.tobytes(), check=True)
    if fr % 30 == 29:
        print(f"frame {fr + 1}/{NFR}  {(time.time() - t0) / (fr + 1):.2f} s/frame", flush=True)
if enc:
    enc.stdin.close(); enc.wait()
json.dump({"pre": 0, "fps": FPS, "secs": SECS, "shots": EVENTS}, open(os.path.join(OUT, "events.json"), "w"))
print("done", NFR, f"{time.time() - t0:.0f} s")
