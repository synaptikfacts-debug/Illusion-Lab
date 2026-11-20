# 0031 hexagon columns - the sound, from the animation's own event log (events.json from scripts/blender/hex_anim.py):
# the sphere's dive = a soft airy whoosh; the impact = a deep soft thump + a low metal "tunk" + the crater's columns
# collapsing (a short burst of taps); every column the crest lifts = one soft, deep "tunk" (sine body with a slight pitch
# drop + one inharmonic partial so a phone speaker hears it), panned to where it happens. Calm, no bells, no bright clicks.
# Usage: python gen_hex_audio.py <events_dir> <out.wav>
import json
import math
import os
import sys
import wave

import numpy as np

SR = 48000
d = sys.argv[1]; OUT = sys.argv[2]
E = json.load(open(os.path.join(d, "events.json")))
FPS, SECS, T_HIT = E["fps"], E["secs"], E["t_hit"]
N = int(SECS * SR) + SR
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(31)


def add(sig, at, pan=0.5):
    i = int(at * SR)
    if i >= N:
        return
    n = min(len(sig), N - i)
    L[i:i + n] += sig[:n] * math.cos(pan * math.pi / 2); R[i:i + n] += sig[:n] * math.sin(pan * math.pi / 2)


def tunk(f, amp, decay=30.0, length=0.35):
    t = np.arange(int(length * SR)) / SR
    ph = 2 * np.pi * f * (t - 0.03 * t * t * 10)                # a slight pitch drop
    body = np.sin(ph) * np.exp(-t * decay) + 0.28 * np.sin(2.76 * ph) * np.exp(-t * decay * 1.8)
    att = np.minimum(1, t / 0.0015)
    return body * att * amp


def thump(amp):
    t = np.arange(int(1.6 * SR)) / SR
    f = 55 + 45 * np.exp(-t * 9)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + 0.5 * np.sin(2 * ph) * np.exp(-t * 3)) * np.exp(-t * 4.0) * np.minimum(1, t / 0.003) * amp


def whoosh(t0, t1, amp):
    n = int((t1 - t0) * SR); t = np.arange(n) / n
    noise = rng.normal(0, 1, n)
    out = np.zeros(n); y = 0.0; y2 = 0.0
    for i in range(n):                                          # a resonant band sweeping up
        fc = 300 + 2400 * t[i] ** 2
        a = math.exp(-2 * math.pi * fc / SR)
        y = (1 - a) * noise[i] + a * y; y2 = (1 - a) * y + a * y2
        out[i] = y - y2
    return out / (np.abs(out).max() + 1e-9) * (t ** 2.2) * amp


def air_push(amp, length=1.3):
    """the shock ring: a soft, low-passed push of air that swells and fades as the light runs outward"""
    n = int(length * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n); y = np.zeros(n); a = math.exp(-2 * math.pi * 700 / SR); acc = 0.0
    for i in range(n):
        acc = (1 - a) * x[i] + a * acc; y[i] = acc
    y /= np.abs(y).max() + 1e-9
    return y * np.minimum(1, t / 0.05) * np.exp(-t * 2.6) * amp


def sparkle(amp, length=0.9):
    """the sparks: a soft, airy shimmer (band-passed, never a click)"""
    n = int(length * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n); y = np.zeros(n); y2 = 0.0; acc = 0.0
    a1, a2 = math.exp(-2 * math.pi * 5200 / SR), math.exp(-2 * math.pi * 2600 / SR)
    for i in range(n):
        acc = (1 - a1) * x[i] + a1 * acc; y2 = (1 - a2) * acc + a2 * y2; y[i] = acc - y2
    y /= np.abs(y).max() + 1e-9
    flick = 0.6 + 0.4 * np.sin(2 * np.pi * 23 * t) ** 2
    return y * flick * np.minimum(1, t / 0.01) * np.exp(-t * 4.5) * amp


def impact(T, amp, pan):
    add(air_push(0.35 * amp), T + 0.02, pan - 0.05); add(air_push(0.3 * amp), T + 0.05, pan + 0.05)
    add(sparkle(0.06 * amp), T + 0.01, pan - 0.1); add(sparkle(0.05 * amp), T + 0.03, pan + 0.1)
    add(thump(0.7 * amp), T, pan)
    add(tunk(110, 0.35 * amp, decay=9, length=1.2), T, pan)
    for k in range(26):                                         # the crater's columns collapse
        add(tunk(rng.uniform(150, 230), rng.uniform(0.03, 0.06) * amp), T + rng.uniform(0.0, 0.42), float(np.clip(pan + rng.normal(0, 0.12), 0.05, 0.95)))


def erupt(T):
    """the tower: a deep soft boom, a rising push of air, a cascade of columns shooting up, the gold fountain"""
    add(thump(0.9), T)
    t = np.arange(int(1.6 * SR)) / SR
    f = 60 + 120 * (1 - np.exp(-t * 5))                                     # a soft rising "whoomp"
    rise = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.08) * np.exp(-t * 2.2) * 0.35
    add(rise, T)
    for k in range(60):                                         # the columns racing up into the tower
        add(tunk(rng.uniform(170, 300), rng.uniform(0.03, 0.065)), T + 0.02 + 0.5 * rng.uniform() ** 1.5, rng.uniform(0.3, 0.7))
    for k in range(5):
        add(sparkle(0.05), T + 0.05 + 0.18 * k, 0.3 + 0.1 * k)
    add(air_push(0.4, 1.8), T + 0.03, 0.5)


add(whoosh(0.0, T_HIT, 0.22), 0.0, 0.62)
for B in E.get("beats", [{"t": T_HIT, "kind": "impact", "x": 0.0, "amp": 1.0}]):
    pan_b = float(np.clip(0.5 + 0.22 * B["x"], 0.1, 0.9))
    if B["kind"] == "impact":
        impact(B["t"], B["amp"], pan_b)
    elif B["kind"] == "bounce":                                 # the sphere flies out and over: an arc of air
        add(whoosh(0.0, 0.8, 0.16)[::-1] * 0.6 + whoosh(0.0, 0.8, 0.16) * 0.6, B["t"], 0.55)
    elif B["kind"] == "spiral":                                 # the field starts to turn: a soft swirl of air
        add(air_push(0.22, 2.4), B["t"], 0.4); add(air_push(0.2, 2.4), B["t"] + 0.3, 0.6)
    elif B["kind"] == "erupt":
        erupt(B["t"])
    elif B["kind"] == "land":                                   # a sphere settles softly: a gentle thump + a few taps
        add(thump(0.45), B["t"], pan_b)
        add(tunk(120, 0.2, decay=10, length=1.0), B["t"], pan_b)
        for k in range(10):
            add(tunk(rng.uniform(160, 240), rng.uniform(0.025, 0.045)), B["t"] + rng.uniform(0.0, 0.3), float(np.clip(pan_b + rng.normal(0, 0.1), 0.05, 0.95)))
    elif B["kind"] == "swirl":                                  # the field starts to turn: a slow swirl of air
        add(air_push(0.22, 3.0), B["t"], 0.4); add(air_push(0.2, 3.0), B["t"] + 0.4, 0.6); add(air_push(0.18, 3.0), B["t"] + 1.2, 0.5)
    elif B["kind"] == "wave":                                   # the giant wave: a deep soft swell rolling past
        t_ = np.arange(int(2.6 * SR)) / SR
        f_ = 55 + 70 * (1 - np.exp(-t_ * 3))
        swell = np.sin(2 * np.pi * np.cumsum(f_) / SR) * np.minimum(1, t_ / 0.25) * np.exp(-t_ * 1.4) * 0.3
        add(swell, B["t"]); add(air_push(0.4, 2.6), B["t"] + 0.05, 0.45); add(air_push(0.35, 2.6), B["t"] + 0.2, 0.55)
for fr in E["frames"]:
    n = fr["n"]
    if n <= 0 or fr["t"] < T_HIT:
        continue
    k = min(9, int(round(1.6 * math.sqrt(n))))
    pan = float(np.clip(0.5 + 0.22 * fr["x"], 0.1, 0.9))
    for j in range(k):
        add(tunk(rng.uniform(160, 270), rng.uniform(0.035, 0.07)), fr["t"] + rng.uniform(0, 1.0 / FPS), float(np.clip(pan + rng.normal(0, 0.08), 0.05, 0.95)))

# a small, soft room
ir_n = int(0.9 * SR); ti = np.arange(ir_n) / SR
for ch in (L, R):
    ir = rng.normal(0, 1, ir_n) * np.exp(-ti * 5.5); ir[0] = 0
    wet = np.fft.irfft(np.fft.rfft(ch, 2 * N) * np.fft.rfft(ir, 2 * N))[:N]
    ch += 0.012 * wet
fade = int(0.6 * SR); end = int(SECS * SR)
env = np.ones(N); env[end - fade:end] = np.linspace(1, 0, fade); env[end:] = 0
L *= env; R *= env
st = np.stack([L[:end], R[:end]], 1); st /= (np.abs(st).max() + 1e-9) / 0.8
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print("wrote", OUT)
