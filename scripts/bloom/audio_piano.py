"""0016 Midnight Bloom - calm, warm sound: sampled concert grand piano + warm pad, every phrase follows the picture. 17 s.
usage: audio_bloom5.py out.wav"""
import math, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve, lfilter

SR = 48000; END = 17.0
n = int(END * SR); t = np.arange(n) / SR
rng = np.random.default_rng(1605); dry = np.zeros((n, 2))


def add(s, p=0.0):
    dry[:, 0] += s * (1 - p); dry[:, 1] += s * (1 + p)


def lp(x, hi, o=2): return sosfilt(butter(o, hi, 'low', fs=SR, output='sos'), x)


def ss(a0, a1):
    x = np.clip((t - a0) / (a1 - a0), 0, 1); return x * x * (3 - 2 * x)


def hz(name):
    names = {'C': -9, 'C#': -8, 'D': -7, 'D#': -6, 'E': -5, 'F': -4, 'F#': -3, 'G': -2, 'G#': -1, 'A': 0, 'A#': 1, 'B': 2}
    return 440.0 * 2 ** ((names[name[:-1]] + 12 * (int(name[-1]) - 4)) / 12)


PIANO_DIR = 'samples/piano'   # MusyngKite acoustic_grand_piano (gleitz/midi-js-soundfonts) decoded to 48 kHz mono wav
_cache = {}


def _sample(note):
    key = note.replace('#', 's')
    if key not in _cache:
        sr_, x = wavfile.read(f'{PIANO_DIR}/{key}.wav'); x = x.astype(np.float64)
        x /= np.abs(x).max() + 1e-9
        on = int(np.argmax(np.abs(x) > 0.02)); x = x[max(on - 48, 0):]
        tail = int(0.25 * SR); x[-tail:] *= np.linspace(1, 0, tail)
        _cache[key] = x
    return _cache[key]


def pluck(t0, note, amp=1.0, pan=0.0, decay=None, bright=2600, dur=None):
    """one note of a real sampled grand piano; softer notes are darker, like a real hammer"""
    x = _sample(note) * 0.11 * amp
    x = lp(x, 1800 + 2200 * min(amp, 1.2), 1)
    i0 = int(t0 * SR); i1 = min(i0 + len(x), n)
    if i0 >= n:
        return
    s_ = np.zeros(n); s_[i0:i1] = x[:i1 - i0]
    add(s_, pan * 0.7)


def strum(t0, notes, amp=1.0, gap=0.035, **kw):
    for i, nt in enumerate(notes):
        pluck(t0 + i * gap, nt, amp * (0.8 + 0.2 * (i == 0)), pan=-0.4 + 0.8 * i / max(len(notes) - 1, 1), **kw)


def pad(freqs, amp, cut=900):
    s = np.zeros(n)
    for i, f in enumerate(freqs):
        for det in (-0.15, 0.0, 0.16):
            s += np.sin(2 * math.pi * (f + det) * t + rng.uniform(0, 6.28) + 0.2 * np.sin(2 * math.pi * 0.08 * t + i)) / (1 + i * 0.35)
    return lp(s, cut) * amp


# ---------------------------------------------------------------- warm pad underneath (soft, low, slow)
PD = [hz(x) for x in ('D2', 'A2', 'D3', 'F#3', 'E4')]
PB = [hz(x) for x in ('B1', 'F#2', 'B2', 'D3', 'A3')]
PG = [hz(x) for x in ('G1', 'D2', 'G2', 'B2', 'F#3', 'A3')]
PE = [hz(x) for x in ('D2', 'A2', 'D3', 'F#3', 'A3', 'E4')]
add(pad(PD, 1.0) * (0.3 + 0.7 * ss(0.6, 2.4)) * (1 - ss(5.4, 6.6)) * 0.035, -0.1)
add(pad(PB, 1.0) * ss(5.4, 6.6) * (1 - ss(9.3, 10.6)) * 0.035, 0.1)
add(pad(PG, 1.0) * ss(9.3, 10.6) * (1 - ss(12.7, 14.0)) * 0.035, -0.05)
add(pad(PE, 1.0, 1100) * ss(12.7, 14.2) * (1 - ss(15.2, 17.0)) * 0.04)
# very soft breath of wind, low only
add(lp(rng.standard_normal(n), 380) * (0.5 + 0.5 * np.sin(0.4 * t) ** 2) * 0.05)

# ---------------------------------------------------------------- plucked phrases, following the picture
# 0-0.9 the bud trembles: three gentle notes
for tq, nt in ((0.02, 'D4'), (0.32, 'F#4'), (0.62, 'A4')):
    pluck(tq, nt, 0.8, pan=-0.2)
# 0.95 it opens: a soft rolled chord
strum(0.95, ['D3', 'A3', 'D4', 'F#4', 'A4', 'E5'], 1.0, gap=0.045)
# 1.2-4.4 the lights rise into the sky: a slow arpeggio climbing note by note
RISE = ['D4', 'E4', 'F#4', 'A4', 'B4', 'D5', 'E5', 'F#5', 'A5', 'B5', 'D6', 'E6', 'F#6', 'A6']
for i, nt in enumerate(RISE):
    tq = 1.3 + i * 0.235
    pluck(tq, nt, 0.7 - 0.022 * i, pan=0.6 * math.sin(i * 1.3))
# 4.4 the top light flashes; 4.4-5.7 it falls: three notes stepping down
for tq, nt in ((4.45, 'A5'), (4.85, 'F#5'), (5.25, 'D5')):
    pluck(tq, nt, 0.6, pan=0.3)
# 5.75 the landing: a deep warm root
pluck(5.75, 'D2', 1.1); pluck(5.78, 'A2', 0.7)
# 5.9-9.7 the wave: flowing B minor pattern, slowly building
PAT_B = ['B3', 'D4', 'F#4', 'A4', 'F#4', 'D4']
for i in range(10):
    tq = 6.0 + i * 0.37
    pluck(tq, PAT_B[i % 6], 0.4 + 0.3 * i / 9, pan=-0.5 + (i % 6) / 5.0)
# 9.7 passing under the camera: a soft rolled G chord, then a relaxed glide pattern
strum(9.75, ['G2', 'D3', 'B3', 'F#4', 'A4'], 0.9, gap=0.05)
PAT_G = ['G3', 'B3', 'D4', 'F#4', 'A4', 'F#4', 'D4', 'B3']
for i in range(8):
    tq = 10.3 + i * 0.38
    pluck(tq, PAT_G[i % 8], 0.5, pan=-0.5 + (i % 8) / 7.0)
# 13-14.6 the field rises: the climbing arpeggio returns, then the final chord rings out
for i, nt in enumerate(['D4', 'F#4', 'A4', 'D5', 'E5', 'F#5', 'A5']):
    pluck(13.05 + i * 0.2, nt, 0.6, pan=0.5 * math.sin(i * 1.7))
strum(14.55, ['D2', 'A2', 'D3', 'F#3', 'A3', 'E4', 'F#4', 'A4'], 1.0, gap=0.07)

# ---------------------------------------------------------------- warm hall
Lr = int(3.6 * SR); ir = rng.standard_normal((Lr, 2)) * np.exp(-np.arange(Lr) / SR * 1.5)[:, None]
wet = np.stack([fftconvolve(dry[:, c], lp(ir[:, c], 3500))[:n] for c in range(2)], 1)
out = dry / np.abs(dry).max() + 0.45 * wet / np.abs(wet).max()
out = np.stack([lp(out[:, c], 9000) for c in range(2)], 1)
out *= (np.clip((END - t) / 1.6, 0, 1) ** 1.5)[:, None] * np.minimum(t / 0.008, 1)[:, None]
out /= np.abs(out).max() / 0.85
wavfile.write(sys.argv[1], SR, out.astype(np.float32))
