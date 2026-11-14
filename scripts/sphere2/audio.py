"""0017 Black Sphere - sound. cracks, heartbeat, slow-motion burst, floating, implosion slam, piano resolve. 16 s.
usage: audio_sphere.py out.wav"""
import math, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000; END = 16.0; TB, TR0, TS = 3.2, 9.6, 12.4
n = int(END * SR); t = np.arange(n) / SR
rng = np.random.default_rng(1717); dry = np.zeros((n, 2))


def add(s, p=0.0):
    dry[:, 0] += s * (1 - p); dry[:, 1] += s * (1 + p)


def filt(x, lo=None, hi=None, o=2):
    if lo and hi:
        return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
    if lo:
        return sosfilt(butter(o, lo, 'high', fs=SR, output='sos'), x)
    return sosfilt(butter(o, hi, 'low', fs=SR, output='sos'), x)


def env(x, a, d):
    x = np.maximum(x, 0); return (1 - np.exp(-x / a)) * np.exp(-x / d) * (x > 0)


def ss(a0, a1):
    x = np.clip((t - a0) / (a1 - a0), 0, 1); return x * x * (3 - 2 * x)


def crack(t0, a, p=0.0):
    """dry stone crack: a few very short filtered noise ticks + a tiny low thump"""
    for k in range(rng.integers(2, 5)):
        tk = t0 + k * rng.uniform(0.004, 0.018)
        i0 = int(tk * SR); L = int(0.03 * SR)
        if i0 + L >= n:
            continue
        b = rng.standard_normal(L) * np.exp(-np.arange(L) / (0.004 * SR))
        b = filt(b, 1200, 9000)
        s = np.zeros(n); s[i0:i0 + L] = b * a * rng.uniform(0.5, 1.0); add(s, p)
    add(np.sin(2 * math.pi * 90 * (t - t0)) * env(t - t0, 0.001, 0.03) * 0.15 * a, p)


def sub(t0, a, f0, f1, d):
    x = t - t0; f = f1 + (f0 - f1) * np.exp(-np.maximum(x, 0) * 7)
    add(np.sin(2 * math.pi * np.cumsum(f) / SR) * env(x, 0.004, d) * a)


# dark space bed
bed = sum(np.sin(2 * math.pi * f * t + rng.uniform(0, 6)) * g for f, g in ((36.7, 1.0), (55.0, 0.5), (73.4, 0.25)))
add(filt(bed, hi=200) * 0.04 * (1 - ss(14.8, 16.0)))
add(filt(rng.standard_normal(n), 80, 400) * 0.012)

# 0-3.2 cracks racing across the sphere, denser toward the burst, heartbeat pulses
for k in range(70):
    u = rng.random() ** 0.6; tq = 0.0 + u * 3.15
    crack(tq, 0.05 + 0.07 * u, rng.uniform(-0.7, 0.7))
for p_ in (1.4, 2.2, 2.85):
    sub(p_, 0.35, 70, 38, 0.35)
x = np.clip(t / TB, 0, 1); m = t < TB
add(filt(rng.standard_normal(n), 200, 2000) * x ** 3 * m * 0.06)                      # rising pressure
add(np.sin(2 * math.pi * np.cumsum(40 + 60 * x ** 2) / SR) * x ** 2 * m * 0.12)
# 3.2 burst: deep impact, shatter, everything slows into a long reverberant drone
sub(TB, 1.0, 120, 28, 1.6)
add(filt(rng.standard_normal(n), 300, 8000) * env(t - TB, 0.002, 0.35) * 0.35)
for k in range(120):
    tq = TB + 0.01 + rng.random() ** 2.0 * 0.9
    crack(tq, 0.03 + 0.05 * rng.random(), rng.uniform(-0.9, 0.9))
add(filt(rng.standard_normal(n), 60, 300) * env(t - TB, 0.3, 3.0) * 0.08)
# 3.6-9.6 floating: dark purple pad, soft crystal shimmer, core flare at 8.6
pad = sum(np.sin(2 * math.pi * (f + d) * t + rng.uniform(0, 6)) / (1 + i * 0.4)
          for i, f in enumerate((73.42, 110.0, 146.83, 174.61, 220.0)) for d in (-0.15, 0.0, 0.16))
add(filt(pad, hi=900) * ss(3.4, 4.6) * (1 - ss(9.4, 10.4)) * 0.035)
add(filt(rng.standard_normal(n), 3500, 11000) * ss(3.5, 5) * (1 - ss(9, 10)) * (0.5 + 0.5 * np.sin(2 * math.pi * 0.3 * t)) * 0.008)
add(filt(rng.standard_normal(n), 200, 3000) * env(t - 8.3, 0.25, 0.8) * 0.05)
sub(8.6, 0.25, 60, 40, 0.8)
# 9.6-12.4 pulled back: reverse swell accelerating into the slam
x = np.clip((t - TR0) / (TS - TR0), 0, 1); m = (t > TR0) & (t < TS)
add(filt(rng.standard_normal(n), 300, 6000) * x ** 3.2 * m * 0.22)
add(np.sin(2 * math.pi * np.cumsum(30 + 120 * x ** 3) / SR) * x ** 2.5 * m * 0.2)
# 12.4 slam shut: heavy impact + a clean stone click, then a resonant hum
sub(TS, 1.1, 110, 30, 1.2)
add(filt(rng.standard_normal(n), 1500, 9000) * env(t - TS, 0.0008, 0.03) * 0.5)
add(np.sin(2 * math.pi * 73.42 * t) * env(t - TS, 0.05, 2.2) * 0.06)
# 12.6-16: calm piano resolve (real sampled grand), seams pulse at 14.2
PD = 'samples/piano'
def piano(t0, note, amp, pan=0.0):
    sr_, x_ = wavfile.read(f'{PD}/{note.replace("#", "s")}.wav'); x_ = x_.astype(float); x_ /= np.abs(x_).max()
    on = int(np.argmax(np.abs(x_) > 0.02)); x_ = x_[max(on - 48, 0):]
    x_ = filt(x_, hi=1800 + 2200 * amp, o=1) * 0.11 * amp
    i0 = int(t0 * SR); i1 = min(i0 + len(x_), n); s = np.zeros(n); s[i0:i1] = x_[:i1 - i0]; add(s, pan)
for tq, nt, am in ((12.75, 'D3', 0.9), (12.8, 'A3', 0.7), (13.2, 'F#4', 0.6), (13.6, 'A4', 0.55), (14.15, 'D4', 0.7), (14.2, 'E5', 0.5), (14.25, 'A4', 0.55)):
    piano(tq, nt, am, rng.uniform(-0.4, 0.4))

Lr = int(3.2 * SR); ir = rng.standard_normal((Lr, 2)) * np.exp(-np.arange(Lr) / SR * 1.6)[:, None]
wet = np.stack([fftconvolve(dry[:, c], filt(ir[:, c], hi=5000))[:n] for c in range(2)], 1)
out = dry / np.abs(dry).max() + 0.4 * wet / np.abs(wet).max()
out *= (np.clip((END - t) / 1.2, 0, 1) ** 1.5)[:, None] * np.minimum(t / 0.004, 1)[:, None]
out /= np.abs(out).max() / 0.85
wavfile.write(sys.argv[1], SR, out.astype(np.float32))
