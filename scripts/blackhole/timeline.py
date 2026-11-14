"""Shared 50 s timeline for the Black Hole Heart reel (used by shade.py and audio_space.py)."""
import math
import numpy as np

DUR = 50.0
TAU = 2 * math.pi


def sm(a, b, v):
    x = np.clip((v - a) / (b - a), 0, 1)
    return x * x * (3 - 2 * x)


# ---------- heartbeat (time, amplitude) ----------
BEATS = []


def _pair(t, a, gap=0.32):
    BEATS.append((t, a))
    BEATS.append((t + gap, a * 0.72))


_pair(0.35, 1.0)
_pair(3.0, 1.0)
_pair(5.4, 0.85)
for tb in [7.8, 10.2, 12.6, 15.0, 17.4]:
    _pair(tb, 0.7)
for tb in [18.8, 20.0, 21.0, 21.8, 22.5, 23.05]:          # heartbeat accelerates
    _pair(tb, 0.8, 0.26)
BEATS.append((23.5, 0.9)); BEATS.append((23.72, 0.9))
_pair(24.4, 1.15)                                           # eye re-opens
for tb in [27.0, 29.4, 31.8, 34.2]:
    _pair(tb, 0.65)
for tb, a in [(36.6, 0.75), (38.6, 0.8), (40.3, 0.85), (41.7, 0.9), (42.8, 0.95), (43.5, 1.0)]:
    _pair(tb, a, 0.26)
_pair(44.0, 1.25)                                           # mega impact
_pair(46.0, 0.7, 0.36)
_pair(47.6, 0.55, 0.4)
BEATS.append((48.9, 0.35))

# ---------- tidal-disruption streams: (t0, dur, psi0, r_start, amp, width_mul, star) ----------
STREAMS = [(1.05, 1.95, 0.9, 17.2, 1.0, 1.0, 1.0)]
# three more stars torn apart one after another (keeps the first 13 s busy)
STREAMS += [(3.9, 1.6, 2.6, 15.5, 0.85, 0.8, 0.9), (6.5, 1.6, 4.5, 15.5, 0.85, 0.8, 0.9), (9.2, 1.6, 0.4, 15.5, 0.85, 0.8, 0.9)]
_rs = np.random.default_rng(12)
for t0 in [12.0, 12.9, 13.7, 14.6, 15.5]:                   # debris shower
    STREAMS.append((t0, 1.45, float(_rs.random() * TAU), 15.5 + 1.5 * float(_rs.random()), 0.55, 0.45, 0.45))
STREAMS.append((41.3, 2.7, 0.9, 17.2, 0.75, 1.0, 1.0))      # twin stars
STREAMS.append((41.3, 2.7, 0.9 + math.pi, 17.2, 0.75, 1.0, 1.0))

# ---------- impacts (time, strength) ----------
IMPACTS = [(3.0, 1.0), (24.4, 1.1), (36.0, 0.6), (44.0, 1.3)]
IMPACTS += [(s[0] + s[1], 0.6 if s[4] >= 0.8 else 0.3) for s in STREAMS if s[4] < 1]

# ---------- jets: (on, fade_start, off, strength) ----------
JETS = [(3.0, 6.8, 8.6, 1.0), (24.4, 28.5, 30.5, 1.15), (44.0, 46.8, 48.6, 1.3)]
JETS += [(s[0] + s[1], s[0] + s[1] + 0.25, s[0] + s[1] + 0.9, 0.45) for s in STREAMS if s[4] < 1]
JKN = []
_rk = np.random.default_rng(31)
for on, fs, off, st in JETS:
    tk = on
    while tk < off - 0.3:
        JKN.append((tk, st * (1.0 if tk == on else 0.4 + 0.5 * float(_rk.random()))))
        tk += 0.25 + 0.3 * float(_rk.random())
for tb, a in BEATS:
    if any(on <= tb <= off for on, fs, off, st in JETS):
        JKN.append((tb, a))

# ---------- screen ripples (gravitational waves) ----------
RIPS = [(t, s) for t, s in IMPACTS if s >= 1]

# ---------- lensed background star crossings (t_start, t_end, brightness, colour) ----------
CROSS = [(7.6, 12.4, 1.0, (0.85, 0.9, 1.0), 'star'), (27.0, 33.5, 4.0, (1.0, 0.45, 0.9), 'neb'), (45.0, 49.2, 1.2, (0.7, 0.8, 1.0), 'star')]

# ---------- camera cuts between the three traced viewpoints (hidden by white-out flashes) ----------
CUTS = (24.3, 36.0)

# ---------- eye blink and closing ----------
BLINK = (23.85, 24.12, 24.32, 24.55)      # start close, closed, start open, open
CLOSE = (49.15, 49.85)


def closed(t):
    """0 = open, 1 = closed."""
    b0, b1, b2, b3 = BLINK
    c = float(sm(b0, b1, t)) * (1 - float(sm(b2, b3, t)))
    return max(c, float(sm(CLOSE[0], CLOSE[1], t)))


# ---------- camera ----------
ZK = [(0, 1.0), (6, 1.12), (9.5, 1.03), (12, 1.14), (17.5, 1.08), (23.8, 1.38), (24.45, 1.02), (30, 1.06), (36, 1.0),
      (43.9, 1.32), (44.1, 1.04), (49, 1.14), (50, 1.14)]


def zoom(t):
    for i in range(1, len(ZK)):
        if t <= ZK[i][0]:
            a, b = ZK[i - 1], ZK[i]
            return a[1] + (b[1] - a[1]) * float(sm(a[0], b[0], t))
    return ZK[-1][1]


_tt = np.linspace(0, DUR, 5001)
_rate = 0.055 + 0.12 * sm(25.5, 28, _tt) * (1 - sm(34, 37, _tt)) + 0.05 * sm(44, 45, _tt) * (1 - sm(47, 49, _tt))
_rot = np.concatenate([[0], np.cumsum((_rate[1:] + _rate[:-1]) / 2 * np.diff(_tt))])


def sky_rot(t):
    return float(np.interp(t, _tt, _rot))


def jet_env(t):
    v = 0.0
    for on, fs, off, st in JETS:
        if on - 0.02 < t < off:
            v = max(v, st * float(sm(on - 0.02, on + 0.08, t)) * (1 - float(sm(fs, off, t))))
    return v


def jet_len(t):
    """fraction of max length (grows quickly after each ignition)."""
    best = 0.0
    for on, fs, off, st in JETS:
        if on - 0.02 < t < off:
            best = max(best, 1 - (1 - min(1.0, (t - on) / 0.45)) ** 3)
    return best


# ---------- spark bursts (time, strength) ----------
SPARKS = [(ti, min(s, 1.3)) for ti, s in IMPACTS if s >= 1]


def storm(t):
    """expected number of plasma lightning bolts per flicker slot."""
    return float(1.6 * sm(12.0, 13.0, t) * (1 - sm(16.8, 17.8, t)))


def shatter(t):
    """disk breaks into concentric rings."""
    return float(sm(18.6, 20.5, t) * (1 - sm(23.95, 24.15, t)) + sm(30.5, 31.5, t) * (1 - sm(34.5, 35.8, t)) * 0.9
                 + sm(8.1, 8.45, t) * (1 - sm(9.3, 9.9, t)) + sm(13.8, 14.3, t) * (1 - sm(16.4, 17.0, t)))


def pull(t):
    """gravitational pull: starfield streaks inward."""
    return float(1.4 * sm(21.0, 23.8, t) * (1 - sm(23.9, 24.1, t)) + 1.6 * sm(42.0, 43.9, t) * (1 - sm(44.0, 44.25, t))
                 + 0.8 * sm(35.4, 35.95, t) * (1 - sm(36.0, 36.1, t)))
