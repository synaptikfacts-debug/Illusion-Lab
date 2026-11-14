"""Liquid Glass v3 sound - five different beats, 22 s seamless loop. usage: audio_v3.py out.wav"""
import math, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000; LOOP = 22.0; EXT = 3.0
n = int((LOOP + EXT) * SR); t = np.arange(n) / SR
rng = np.random.default_rng(21); dry = np.zeros((n, 2))


def env(x, a, d):
    x = np.maximum(x, 0); return (1 - np.exp(-x / a)) * np.exp(-x / d) * (x > 0)


def add(s, p=0.0):
    dry[:, 0] += s * (1 - p); dry[:, 1] += s * (1 + p)


def bp(lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), rng.standard_normal(n))


LO = sosfilt(butter(4, 160, 'low', fs=SR, output='sos'), rng.standard_normal(n))
MID, HI, AIR = bp(250, 2500), bp(2500, 12000), bp(5000, 14000)


def sub(t0, a, f0=80, f1=30, d=0.6):
    x = t - t0; f = f1 + (f0 - f1) * np.exp(-np.maximum(x, 0) * 9)
    add(np.sin(2 * math.pi * np.cumsum(f) / SR) * env(x, 0.003, d) * 0.6 * a)


def clink(t0, a, f0, p=0.0):
    x = t - t0
    for m, g in [(1.0, 1.0), (2.32, 0.5), (4.25, 0.25)]:
        add(np.sin(2 * math.pi * f0 * m * x) * env(x, 0.0004, 0.09 / m ** 0.5) * 0.045 * g * a, p)


def wobble(t0, a, base=70):
    x = t - t0
    add(np.sin(2 * math.pi * np.cumsum(base + 18 * np.sin(np.maximum(x, 0) * 15) * np.exp(-np.maximum(x, 0) * 5)) / SR) * env(x, 0.01, 0.5) * 0.3 * a)


def win(a0, a1):
    x = (t - a0) / (a1 - a0); return np.clip(x, 0, 1), (x > 0) & (x < 1)


def riser(a0, a1, a):
    x, m = win(a0, a1)
    add(AIR * x ** 3 * m * 0.12 * a); add(np.sin(2 * math.pi * np.cumsum(38 + 100 * x ** 2) / SR) * x ** 2 * m * 0.2 * a)


def squelch(a0, a1, a, down=True):
    x, m = win(a0, a1); e = np.sin(np.pi * x) * m
    add(MID * e * 0.1 * a * (0.6 + 0.4 * np.sin(2 * math.pi * 7 * t)))
    add(np.sin(2 * math.pi * np.cumsum((140 - 90 * x) if down else (50 + 90 * x)) / SR) * e * 0.12 * a)


# --- beat 1: fall (wraps from the end), impact, eruption, freeze, shatter
sub(0.32, 1.0, 85, 30, 0.6); add(MID * env(t - 0.32, 0.001, 0.05) * 0.45)
x, m = win(0.32, 1.55)
add((MID * 0.6 + HI * 0.4) * np.sin(np.pi * 0.5 * x) * m * 0.22)
add(np.sin(2 * math.pi * np.cumsum(55 + 150 * x ** 1.5) / SR) * m * x * 0.14)
add(HI * env(t - 1.55, 0.0005, 0.05) * 0.5); sub(1.55, 0.5, 50, 30, 0.35)
for k in range(18):
    clink(1.55 + rng.random() * 0.2, 0.45, 3000 + 3000 * rng.random(), rng.random() * 1.6 - 0.8)
add(AIR * ((t > 1.55) & (t < 3.0)) * 0.02)
wobble(1.6, 0.5); wobble(2.15, 0.5)
riser(2.0, 3.0, 1.0)
sub(3.0, 1.3, 100, 26, 1.0); add(LO * env(t - 3.0, 0.01, 0.6) * 0.7); add((HI + MID * 0.5) * env(t - 3.0, 0.0005, 0.2) * 0.55)
for k in range(110):
    clink(3.02 + rng.random() ** 1.5 * 0.55, 0.3 + 0.5 * rng.random(), 2000 + 5000 * rng.random(), rng.random() * 1.8 - 0.9)
# --- beat 2: time stops (everything drops to a hanging hiss), then a reverse-swell sucks the shards back
x, m = win(3.55, 4.6); add(AIR * m * 0.02 * (0.7 + 0.3 * np.sin(2 * math.pi * 1.5 * t)))
x, m = win(4.6, 6.4)
add((HI * 0.5 + MID * 0.5) * x ** 2.5 * m * 0.22)                       # reversed-crash swell
add(np.sin(2 * math.pi * np.cumsum(30 + 120 * x ** 2) / SR) * x ** 2 * m * 0.25)
for k in range(90):                                                      # clinks accelerate into the snap-back
    tq = 4.6 + 1.8 * (1 - rng.random() ** 2)
    clink(tq, 0.2 + 0.4 * rng.random(), 2500 + 4000 * rng.random(), rng.random() * 1.6 - 0.8)
sub(6.4, 1.0, 60, 30, 0.4); add(HI * env(t - 6.4, 0.0005, 0.04) * 0.5)    # click: perfect fit
squelch(6.6, 7.6, 0.6); wobble(7.6, 0.8)
# --- beat 3: sinks through the glass, splits, drops patter, rise back up, merge
squelch(8.0, 9.0, 1.0)
for k in range(5):
    tq = 9.05 + k * 0.04; xx = t - tq
    add(np.sin(2 * math.pi * (1100 + 150 * k) * np.exp(-np.maximum(xx, 0) * 25) * xx) * env(xx, 0.0008, 0.06) * 0.25, (k - 2) * 0.3)
riser(9.6, 10.3, 0.5); squelch(9.85, 10.8, 0.7, down=False)
for k in range(5):
    tq = 10.3 + k * 0.05; xx = t - tq
    add(np.sin(2 * math.pi * (700 + 180 * k) * xx) * env(xx, 0.0008, 0.05) * 0.2, (k - 2) * 0.3)
sub(11.4, 0.7, 70, 32, 0.4); wobble(11.45, 0.9)
# --- beat 4: vortex whirl (panning swirl), sucked down, spike shoots up and freezes, melts
x, m = win(12.2, 13.9)
sw = (MID * 0.6 + LO * 0.6) * np.sin(np.pi * x) * m * 0.2
pan = np.sin(2 * math.pi * (1.0 + 3.0 * x) * (t - 12.2)) * 0.8
dry[:, 0] += sw * (1 - pan); dry[:, 1] += sw * (1 + pan)
add(np.sin(2 * math.pi * np.cumsum(45 + 40 * x) / SR) * np.sin(np.pi * x) * m * 0.18)
riser(13.3, 13.9, 0.7)
sub(13.9, 0.9, 40, 90, 0.4)                                              # upward whoomp
x, m = win(13.9, 14.6); add(AIR * np.sin(np.pi * x) * m * 0.1)
add(HI * env(t - 14.6, 0.0005, 0.05) * 0.45); sub(14.6, 0.4, 50, 30, 0.3)
for k in range(12):
    clink(14.6 + rng.random() * 0.15, 0.4, 3000 + 3000 * rng.random(), rng.random() * 1.6 - 0.8)
squelch(15.6, 16.3, 0.6); wobble(16.3, 0.7)
# --- beat 5: tower, light pours down, burst, gel shoots up
sub(16.5, 1.2, 95, 26, 0.8); add(MID * env(t - 16.5, 0.001, 0.05) * 0.4)
x, m = win(16.5, 17.75)
add((MID * 0.6 + HI * 0.4) * np.sin(np.pi * 0.5 * x) * m * 0.28)
add(np.sin(2 * math.pi * np.cumsum(50 + 170 * x ** 1.5) / SR) * m * x * 0.18)
add(HI * env(t - 17.75, 0.0005, 0.06) * 0.55); sub(17.75, 0.6, 50, 28, 0.4)
for k in range(24):
    clink(17.75 + rng.random() * 0.25, 0.45, 3000 + 3000 * rng.random(), rng.random() * 1.6 - 0.8)
x, m = win(18.3, 19.8)                                                   # light pouring: deep rising energy hum
hum = sum(np.sin(2 * math.pi * f * t) * g for f, g in [(55, 1), (110.4, .5), (165.2, .25)])
add(hum * x ** 1.5 * m * 0.12 + AIR * x ** 2 * m * 0.06)
riser(18.8, 19.8, 1.5)
sub(19.8, 1.6, 110, 24, 1.3); add(LO * env(t - 19.8, 0.01, 1.0) * 1.0); add((HI + MID * 0.5) * env(t - 19.8, 0.0005, 0.3) * 0.6)
for k in range(240):
    clink(19.82 + rng.random() ** 1.6 * 1.6, 0.2 + 0.5 * rng.random(), 2000 + 5000 * rng.random(), rng.random() * 1.8 - 0.9)
x, m = win(19.8, 20.7); add(AIR * (1 - x) * m * 0.12, 0.0)              # gel shooting up and away
x, m = win(21.2, 22.2); add(HI * np.sin(np.pi * x) * m * 0.03)           # shards melting
x, m = win(21.62, 22.32); add(AIR * x ** 2 * m * 0.1)                    # falls back in (wraps to frame 1)
# bed
for f, g in [(49.0, 1), (73.5, .5)]:
    add(np.sin(2 * math.pi * f * t) * 0.03 * g)
Lr = int(2.4 * SR); ir = rng.standard_normal((Lr, 2)) * np.exp(-np.arange(Lr) / SR * 2.3)[:, None]
wet = np.stack([fftconvolve(dry[:, c], sosfilt(butter(2, 5000, 'low', fs=SR, output='sos'), ir[:, c]))[:n] for c in range(2)], 1)
out = dry / np.abs(dry).max() + 0.3 * wet / np.abs(wet).max()
N = int(LOOP * SR)
loop = out[:N].copy(); loop[:n - N] += out[N:]
loop /= np.abs(loop).max() / 0.85
wavfile.write(sys.argv[1], SR, loop.astype(np.float32))
