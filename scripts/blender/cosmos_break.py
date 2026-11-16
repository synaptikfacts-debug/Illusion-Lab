# 0021 "The Break" - built like a director (owner, Nov 15 2026: "build it like a director please").
# STORYBOARD (real seconds, ~13 s):
#  S1 0-0.4   HOOK  close low 3/4: a glistening cluster of 2000 anodized beads (swirl colours) with a giant mirror-chrome
#                   planet looming behind; a heavy chrome ball streaks in from the lower foreground -> IMPACT at 0.35 s
#  S2 0.4-3.4 slow motion (~0.3x): the cluster explodes in real physics, beads collide and fly at and past the lens
#  S3 3.4-6   speed ramps back; wide: the beads arc into the chrome planet and spray off its surface (real bounces)
#  S4 6-10    the planet's gravity captures them, orbits spin up into rings, the camera skims low past the rings
#  S5 10-13   the rings settle into one crisp ring, last stragglers click in, pull back to the hero shot, fade
# The motion is a SIMULATION, not formulas: gravity, momentum, bead-bead collisions (spatial hash grid), bounces off the
# planet, a heavy cue ball; baked once (BREAK_BAKE=1) to out/break_sim.npz, then rendered. Collision events are written
# to src/scenes/cosmos/break_events.json so every thock in the sound has a visible cause.
# The LOOK (sky, anodized material, lights, star spikes, lens) is the approved one: it is taken unchanged from
# scripts/blender/cosmos.py (everything above its swarm section).
# Usage: [BREAK_BAKE=1] blender -b --factory-startup -P scripts/blender/cosmos_break.py -- <outdir> <samples> <fps> <k> <n> [frames]
#   env COSMOS_RES=WxH
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
_src = open(os.path.join(HERE, "cosmos.py"), encoding="utf-8").read()
_src = _src.replace('("threshold", 6.0)', '("threshold", 30.0)').replace('("Threshold", 6.0)', '("Threshold", 30.0)')
exec(compile(_src.split("# ---------------- the swarm: 4096 elements in one mesh")[0], "cosmos_look", "exec"))  # noqa: S102
import bpy  # noqa: E402  (already imported by the look code)
import mathutils  # noqa: E402

# ---------------- timing: real time -> simulation time (the slow-motion ramp) ----------------
DUR = 60.0  # owner, Nov 16: ~1 minute - acts 3-5 (moon flyby, meteor shower, rain + double ring)
MET_HITS_REAL = (27.0, 29.5, 32.0, 34.5)
T_BOUNCE_REAL = 42.5
T_HIT2_REAL = 9.75
T_IMPACT_REAL = 0.35


def speed(r):
    """playback speed (sim seconds per real second)"""
    s1 = 0.7 * float(sm(0.33, 0.6, r)) * (1 - float(sm(2.0, 2.6, r)))          # slow-mo 1: the break
    s2 = 0.72 * float(sm(9.55, 9.8, r)) * (1 - float(sm(11.4, 12.0, r)))       # slow-mo 2: ball 2 tears the ring
    s3 = max([0.6 * float(sm(h - 0.25, h - 0.05, r)) * (1 - float(sm(h + 0.7, h + 1.0, r))) for h in MET_HITS_REAL])
    s4 = 0.6 * float(sm(T_BOUNCE_REAL - 0.2, T_BOUNCE_REAL, r)) * (1 - float(sm(T_BOUNCE_REAL + 1.0, T_BOUNCE_REAL + 1.5, r)))
    return 1.0 - max(s1, s2, s3, s4)


_rt = np.arange(0, DUR + 0.6, 0.001)
_sp = np.array([speed(x) for x in _rt])
_simt = np.concatenate([[0.0], np.cumsum(_sp[:-1]) * 0.001])


def sim_t(r):
    return float(np.interp(r, _rt, _simt))


def real_t(s):
    return float(np.interp(s, _simt, _rt))


SIM_DUR = sim_t(DUR) + 0.05
DT = 1.0 / 240.0
NSTEP = int(math.ceil(SIM_DUR / DT)) + 1

# ---------------- the scene objects (simulation parameters) ----------------
NB = 2000
RB = 0.06                                          # bead radius: fewer, bigger, readable beads
CUE_R, CUE_M = 0.32, 25.0
PLANET_C = np.array([2.6, 7.6, 1.1])
PLANET_R = 1.7  # recut 2: smaller so every bead hit reads against it
RING_N = np.array([0.22, -0.42, 1.0])
RING_N /= np.linalg.norm(RING_N)
RING_R0, RING_R1 = 2.35, 3.2
RING_N2 = np.array([-0.35, -0.25, 1.0])  # the re-formed ring: tilted the other way
RING_N2 /= np.linalg.norm(RING_N2)
CUE2_R, CUE2_M = 0.45, 60.0
RING_N3 = np.array([0.75, 0.55, 0.35])  # act 5: the second ring, ~90 deg to ring 2 and open to the camera
RING_N3 /= np.linalg.norm(RING_N3)
MOON_R, GM_MOON = 0.85, 12.0  # check 1: bigger, so it reads
MET_R, MET_M = 0.42, 25.0  # check 2: bigger so each meteor reads
MET_SPEED = 6.0             # check 2: slower, so the eye can follow it in
# check 2: all four meteors strike the side of ring 2 that faces the camera, one after another along an arc
_UR = np.cross(RING_N2, [0, 0, 1.0]); _UR /= np.linalg.norm(_UR)
_UT = np.cross(RING_N2, _UR)
_toward = np.array([-0.6, -0.8, 0.0])
_A0 = math.atan2(float(_toward @ _UT), float(_toward @ _UR))
MET_ANG = tuple(_A0 + d for d in (-0.9, -0.3, 0.3, 0.9))
MET_HIT = [PLANET_C + 2.8 * (math.cos(a) * _UR + math.sin(a) * _UT) for a in MET_ANG]
# check 3: the outer ring tilted ~60 deg from the inner one (90 deg + same radius read as a ball)
RING_N3 = 0.5 * RING_N2 + 0.866 * (math.cos(_A0) * _UR + math.sin(_A0) * _UT)  # tilted towards the camera: an open ring, not a slash
RING_N3 /= np.linalg.norm(RING_N3)
GM = 70.0  # recut: the planet pulls hard - the debris slams into it at ~4 s                         # the final ring band (distance from the planet centre)
SIM_PATH = os.path.join(ROOT, "out", "break_sim.npz")
EVENTS_PATH = os.path.join(ROOT, "src", "scenes", "cosmos", "break_events.json")
rngb = np.random.default_rng(2101)


def cluster_points(n, r):
    """an FCC-packed ball of n bead centres"""
    d = 2 * r * 1.04
    k = int(math.ceil((n * 2.2) ** (1 / 3))) + 2
    g = np.arange(-k, k + 1)
    pts = []
    for ix in g:
        for iy in g:
            for iz in g:
                if (ix + iy + iz) % 2 == 0:
                    pts.append((ix, iy, iz))
    p = np.array(pts, dtype=np.float64) * d / math.sqrt(2)
    p = p[np.argsort(np.linalg.norm(p, axis=1))][:n]
    return p - p.mean(0)


def bake():
    t0 = time.time()
    pos = cluster_points(NB, RB)
    vel = np.zeros_like(pos)
    rc = float(np.max(np.linalg.norm(pos, axis=1)))
    # the cue ball streaks in from the lower foreground (near the camera) and hits slightly off-centre
    hit_pt = np.array([-0.12, -rc - CUE_R + 0.02, -0.08])
    cue_dir = np.array([0.18, 1.0, 0.12])
    cue_dir /= np.linalg.norm(cue_dir)
    cue_v0 = 11.0
    cue_p = hit_pt - cue_dir * cue_v0 * T_IMPACT_REAL
    cue_v = cue_dir * cue_v0
    exploded = False
    P = np.zeros((NSTEP, NB, 3), dtype=np.float32)
    CUE = np.zeros((NSTEP, 3), dtype=np.float32)
    CUE2 = np.zeros((NSTEP, 3), dtype=np.float32)
    t_h2 = sim_t(T_HIT2_REAL)
    # ball 2: crosses the ring band on the camera side, steeply, so it tears straight through it
    _a2 = math.radians(-120)
    _e1 = np.cross(RING_N, [0, 0, 1.0]); _e1 /= np.linalg.norm(_e1)
    _e2 = np.cross(RING_N, _e1)
    hit2 = PLANET_C + (0.5 * (RING_R0 + RING_R1)) * (math.cos(_a2) * _e1 + math.sin(_a2) * _e2)
    cue2_dir = -RING_N * 0.85 + np.array([0.35, 0.25, 0.0]); cue2_dir /= np.linalg.norm(cue2_dir)
    cue2_v = cue2_dir * 9.0
    cue2_p = hit2 - cue2_v * 0.6  # it arrives 0.6 sim-s before the hit
    cue2_on = False
    hit2_done = False
    T_NEW = sim_t(15.6)                      # nothing new may touch the simulation before this (reused frames)
    t_moon = sim_t(20.5)                     # moon closest approach
    _ur = np.cross(RING_N2, [0, 0, 1.0]); _ur /= np.linalg.norm(_ur)
    _ut = np.cross(RING_N2, _ur)
    moon_c = PLANET_C + 3.9 * (-_ur)         # passes just outside the ring band, plowing its outer edge
    moon_v = -_ut * 1.25
    met_t = [sim_t(x) for x in MET_HITS_REAL]
    met_hit = [h_.copy() for h_ in MET_HIT]
    met_dir = []
    for k_, d_ in enumerate(([0.3, 0.2, -1.0], [-0.25, 0.3, -1.0], [0.2, -0.3, -1.0], [-0.3, -0.2, -1.0])):
        dd_ = np.array(d_) - RING_N2 * 0.0
        dd_ = -RING_N2 * 0.9 + np.array([d_[0], d_[1], 0.0])
        met_dir.append(dd_ / np.linalg.norm(dd_))
    met_p = [met_hit[k_] - met_dir[k_] * MET_SPEED * 1.6 for k_ in range(4)]
    met_v = [met_dir[k_] * MET_SPEED for k_ in range(4)]
    met_done = [False] * 4
    t_rain0, t_rain1, t_dbl = sim_t(38.0), sim_t(42.4), sim_t(T_BOUNCE_REAL)
    ODD = (np.arange(NB) % 2) == 1
    MOON = np.zeros((NSTEP, 3), dtype=np.float32)
    MET = np.zeros((NSTEP, 4, 3), dtype=np.float32)
    FAR = np.array([0, -80.0, 0])
    bounced = False
    events = []
    TABLE = 1 << 18
    M = 8
    offs = np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)])
    cs = 2 * RB
    for step in range(NSTEP):
        t = step * DT
        P[step] = pos
        CUE[step] = cue_p
        CUE2[step] = cue2_p if cue2_on else np.array([0, -60.0, 0])
        if not cue2_on and t >= t_h2 - 0.6:
            cue2_on = True
        wmoon = 0.0 if t < T_NEW else float(sm(max(T_NEW, t_moon - 4.5), t_moon - 3.0, t)) * (1 - float(sm(t_moon + 4.0, t_moon + 5.5, t)))
        moon_p = moon_c + moon_v * (t - t_moon)
        MOON[step] = moon_p if (T_NEW <= t and t_moon - 6.0 < t < t_moon + 6.5) else FAR
        for k_ in range(4):
            on_ = met_t[k_] - 1.6 <= t < met_t[k_] + 2.5
            MET[step, k_] = met_p[k_] if on_ else FAR
        # forces: the planet's gravity switches on as the debris arrives, then a ring-forming field settles them
        g = float(sm(0.9, 1.5, t))  # recut: gravity switches on sooner
        if g > 0:
            d = PLANET_C - pos
            r = np.linalg.norm(d, axis=1, keepdims=True)
            wrain = 0.0 if t < T_NEW else float(sm(t_rain0, t_rain0 + 0.6, t)) * (1 - float(sm(t_rain1 - 0.3, t_dbl, t)))
            vel += d / r ** 3 * (GM * g * (1.0 + 1.6 * wrain)) * DT
            if wmoon > 0:
                dm = moon_p - pos
                rm = np.linalg.norm(dm, axis=1, keepdims=True)
                vel += dm / np.maximum(rm, MOON_R) ** 3 * (GM_MOON * wmoon) * DT
            # ring capture: flatten towards the ring plane, steer to a circular orbit inside the ring band
            k = float(sm(2.3, 3.5, t))  # recut 3: the streams follow the hits with no gap
            # act 2: ball 2 shatters the ring - capture lets go, then catches them again in the re-tilted ring
            k *= 1.0 - float(sm(t_h2 - 0.05, t_h2 + 0.15, t)) * (1 - float(sm(t_h2 + 1.1, t_h2 + 2.6, t)))
            if t >= T_NEW:
                k *= 1.0 - 0.45 * float(sm(t_moon - 2.5, t_moon - 1.0, t)) * (1 - float(sm(t_moon + 2.5, t_moon + 4.5, t)))  # check 1: ring must survive
                k *= 1.0 - float(sm(t_rain0 - 0.1, t_rain0 + 0.3, t)) * (1 - float(sm(t_dbl, t_dbl + 0.5, t)))
            RN = RING_N if t < t_h2 + 0.6 else RING_N2
            if k > 0 and t >= t_dbl:   # act 5: odd beads -> the crossed ring
                RNb = np.where(ODD[:, None], RING_N3[None], RN[None])
                rel = pos - PLANET_C
                hn = np.einsum("ij,ij->i", rel, RNb)
                vn = np.einsum("ij,ij->i", vel, RNb)
                vel -= RNb * ((7.0 * k) * vn + (28.0 * k) * hn)[:, None] * DT  # check 3: flatten hard -> thin rings
                inpl = rel - RNb * hn[:, None]
                rr = np.linalg.norm(inpl, axis=1, keepdims=True) + 1e-6
                e_r = inpl / rr
                e_t = np.cross(RNb, e_r)
                _f = (np.arange(NB) % 97) / 96.0   # check 3: inner ring 2.3-2.95, outer ring 3.45-4.1 - they never collide
                target_r = np.where(ODD, 3.45 + 0.65 * _f, 2.3 + 0.65 * _f)
                v_circ = np.sqrt(GM * g / np.maximum(rr[:, 0], 1.0))
                vt = np.sum(vel * e_t, axis=1)
                vr = np.sum(vel * e_r, axis=1)
                vel += e_t * ((v_circ - vt) * 4.0 * k)[:, None] * DT
                vel += e_r * ((-(rr[:, 0] - target_r) * 9.0 - vr * 4.5) * k)[:, None] * DT  # check 2: two crisp rings
            elif k > 0:
                rel = pos - PLANET_C
                hn = rel @ RN
                vn = vel @ RN
                vel -= RN[None] * ((4.0 * k) * vn + (6.0 * k) * hn)[:, None] * DT  # recut 2: lifts beads off the surface
                if t >= T_NEW:  # check 2: after the moon, pull resting beads off the planet back out to the band
                    _rr = np.linalg.norm(rel, axis=1)
                    _lo = _rr < PLANET_R + 0.35
                    if _lo.any():
                        vel[_lo] += (rel[_lo] / _rr[_lo, None]) * (9.0 * k * DT)
                inpl = rel - RN[None] * hn[:, None]
                rr = np.linalg.norm(inpl, axis=1, keepdims=True) + 1e-6
                e_r = inpl / rr
                e_t = np.cross(RN[None], e_r)
                target_r = RING_R0 + (RING_R1 - RING_R0) * (np.arange(NB) % 97) / 96.0
                v_circ = np.sqrt(GM * g / np.maximum(rr[:, 0], 1.0))
                vt = np.sum(vel * e_t, axis=1)
                vr = np.sum(vel * e_r, axis=1)
                vel += e_t * ((v_circ - vt) * 3.0 * k)[:, None] * DT
                vel += e_r * ((-(rr[:, 0] - target_r) * 5.0 - vr * 3.0) * k)[:, None] * DT  # a full, tight ring
        pos += vel * DT
        # cue ball (heavy, no gravity for drama) + collisions with beads
        cue_p = cue_p + cue_v * DT
        dc = pos - cue_p
        dist = np.linalg.norm(dc, axis=1)
        hit = dist < (RB + CUE_R)
        if hit.any():
            n_ = dc[hit] / dist[hit, None]
            rv = vel[hit] - cue_v
            vn = np.sum(rv * n_, axis=1)
            app = vn < 0
            jm = np.zeros_like(vn)
            jm[app] = -(1.6) * vn[app] / (1 + 1 / CUE_M)
            vel[hit] += n_ * jm[:, None]
            cue_v = cue_v - (n_ * jm[:, None]).sum(0) / CUE_M
            pos[hit] = cue_p + n_ * (RB + CUE_R)
            if not exploded:
                exploded = True
                # the hit breaks the cluster's hold: every bead springs outward (stored energy), on top of the hit
                c = pos.mean(0)
                out = pos - c
                out /= np.linalg.norm(out, axis=1, keepdims=True) + 1e-6
                vel += out * rngb.uniform(1.6, 3.6, NB)[:, None]
                vel += rngb.normal(0, 0.25, (NB, 3))
                events.append({"t": real_t(t), "kind": "impact", "s": 1.0, "p": [float(x) for x in cue_p]})
        # ball 2 (heavier, faster) - tears through the ring
        if cue2_on:
            cue2_p = cue2_p + cue2_v * DT
            dc = pos - cue2_p
            dist = np.linalg.norm(dc, axis=1)
            hit = dist < (RB + CUE2_R)
            if hit.any():
                n_ = dc[hit] / dist[hit, None]
                rv = vel[hit] - cue2_v
                vn = np.sum(rv * n_, axis=1)
                app = vn < 0
                jm = np.zeros_like(vn)
                jm[app] = -(1.8) * vn[app] / (1 + 1 / CUE2_M)
                vel[hit] += n_ * jm[:, None]
                pos[hit] = cue2_p + n_ * (RB + CUE2_R)
                if not hit2_done:
                    hit2_done = True
                    events.append({"t": real_t(t), "kind": "impact", "s": 1.0, "p": [float(x) for x in cue2_p]})
            if hit2_done and abs(t - t_h2) < DT:
                pass
            if t >= t_h2 and abs(t - t_h2) < DT * 1.01:  # the shockwave: the whole ring is flung outward and loose
                rel = pos - PLANET_C
                vel += rel / (np.linalg.norm(rel, axis=1, keepdims=True) + 1e-6) * rngb.uniform(0.8, 2.4, NB)[:, None]
                vel += rngb.normal(0, 0.5, (NB, 3))
        # bead-bead collisions via a padded spatial hash
        ci = np.floor(pos / cs).astype(np.int64)
        h = ((ci[:, 0] * 73856093) ^ (ci[:, 1] * 19349663) ^ (ci[:, 2] * 83492791)) % TABLE
        order = np.argsort(h, kind="stable")
        hs = h[order]
        first = np.searchsorted(hs, hs, side="left")
        slot = np.arange(NB) - first
        ok = slot < M
        tab = np.full((TABLE, M), -1, dtype=np.int64)
        tab[hs[ok], slot[ok]] = order[ok]
        nb = ci[:, None, :] + offs[None]
        nh = ((nb[..., 0] * 73856093) ^ (nb[..., 1] * 19349663) ^ (nb[..., 2] * 83492791)) % TABLE
        cand = tab[nh].reshape(NB, -1)
        ii = np.repeat(np.arange(NB), cand.shape[1])
        jj = cand.ravel()
        m = (jj > ii)
        ii, jj = ii[m], jj[m]
        dv = pos[jj] - pos[ii]
        dd = np.einsum("ij,ij->i", dv, dv)
        m = dd < (2 * RB) ** 2
        if m.any():
            ii, jj, dv, dd = ii[m], jj[m], dv[m], np.sqrt(dd[m]) + 1e-9
            n_ = dv / dd[:, None]
            pen = (2 * RB - dd)
            corr = n_ * (pen * 0.5)[:, None]
            np.add.at(pos, ii, -corr)
            np.add.at(pos, jj, corr)
            rvn = np.einsum("ij,ij->i", vel[jj] - vel[ii], n_)
            app = rvn < 0
            if app.any():
                j_ = -(1 + 0.75) * rvn[app] / 2
                imp = n_[app] * j_[:, None]
                np.add.at(vel, ii[app], -imp)
                np.add.at(vel, jj[app], imp)
                big = (-rvn[app]) > 1.2
                if big.any() and (step % 2 == 0):
                    for q in np.nonzero(big)[0][:3]:
                        a_ = ii[app][q]
                        events.append({"t": real_t(t), "kind": "click", "s": float(min(1.0, -rvn[app][q] / 5.0)),
                                       "p": [float(x) for x in pos[a_]]})
        if MOON[step][1] > -70:                      # beads hit the moving moon
            dmn = pos - moon_p
            dml = np.linalg.norm(dmn, axis=1)
            hm = dml < (MOON_R + RB)
            if hm.any():
                n_ = dmn[hm] / dml[hm, None]
                rv = vel[hm] - moon_v
                vn = np.sum(rv * n_, axis=1)
                app = vn < 0
                newv = moon_v + (rv - n_ * vn[:, None]) * 0.9 - n_ * (vn * 0.7)[:, None]
                vel[hm] = np.where(app[:, None], newv, vel[hm])
                pos[hm] = moon_p + n_ * (MOON_R + RB)
                for q in np.nonzero(app & (-vn > 0.8))[0][:2]:
                    if step % 3 == 0:
                        events.append({"t": real_t(t), "kind": "planet", "s": float(min(1.0, -vn[q] / 4.0)), "p": [0, 0, 0]})
        for k_ in range(4):                        # the meteor shower
            if met_t[k_] - 1.6 <= t < met_t[k_] + 2.5:
                met_p[k_] = met_p[k_] + met_v[k_] * DT
                dc = pos - met_p[k_]
                dist = np.linalg.norm(dc, axis=1)
                hit = dist < (RB + MET_R)
                if hit.any():
                    n_ = dc[hit] / dist[hit, None]
                    rv = vel[hit] - met_v[k_]
                    vn = np.sum(rv * n_, axis=1)
                    app = vn < 0
                    jm = np.zeros_like(vn)
                    jm[app] = -(1.8) * vn[app] / (1 + 1 / MET_M)
                    vel[hit] += n_ * jm[:, None]
                    met_v[k_] = met_v[k_] - (n_ * jm[:, None]).sum(0) / MET_M
                    pos[hit] = met_p[k_] + n_ * (RB + MET_R)
                    if not met_done[k_]:
                        met_done[k_] = True
                        near = np.linalg.norm(pos - met_p[k_], axis=1) < 1.1
                        out = pos[near] - met_p[k_]
                        vel[near] += out / (np.linalg.norm(out, axis=1, keepdims=True) + 1e-6) * rngb.uniform(1.4, 2.8, near.sum())[:, None]
                        events.append({"t": real_t(t), "kind": "impact", "s": 0.8, "p": [0, 0, 0]})
        if not bounced and t >= t_dbl:            # the rain lands -> everything bounces back up
            bounced = True
            rel = pos - PLANET_C
            nr = np.linalg.norm(rel, axis=1, keepdims=True)
            low = (nr[:, 0] < PLANET_R + 0.9)
            vel[low] += (rel[low] / nr[low]) * rngb.uniform(4.6, 5.6, low.sum())[:, None]  # check 2: leave the surface, stay catchable
            events.append({"t": real_t(t), "kind": "impact", "s": 1.0, "p": [0, 0, 0]})
        # bounces off the planet
        dp = pos - PLANET_C
        dpl = np.linalg.norm(dp, axis=1)
        hitp = dpl < (PLANET_R + RB)
        if hitp.any():
            n_ = dp[hitp] / dpl[hitp, None]
            vn = np.sum(vel[hitp] * n_, axis=1)
            vt = vel[hitp] - n_ * vn[:, None]
            app = vn < 0
            newv = vt * 0.92 - n_ * (vn * 0.6)[:, None]
            vel[hitp] = np.where(app[:, None], newv, vel[hitp])
            pos[hitp] = PLANET_C + n_ * (PLANET_R + RB)
            strong = app & (-vn > 0.9)
            for q in np.nonzero(strong)[0][:2]:
                if step % 3 == 0:
                    events.append({"t": real_t(t), "kind": "planet", "s": float(min(1.0, -vn[q] / 4.0)),
                                   "p": [float(x) for x in pos[hitp][q]]})
        if step % 240 == 0:
            print(f"bake: sim {t:5.2f}/{SIM_DUR:.2f} s  ({time.time() - t0:5.1f} s)", flush=True)
    os.makedirs(os.path.dirname(SIM_PATH), exist_ok=True)
    np.savez_compressed(SIM_PATH, P=P, CUE=CUE, CUE2=CUE2, MOON=MOON, MET=MET)
    # thin the click events: at most ~14 per real second, strongest first
    ev = sorted(events, key=lambda e: e["t"])
    keep, last = [], {}
    for e in ev:
        b = round(e["t"] * 14)
        if e["kind"] != "impact" and last.get((e["kind"], b)):
            continue
        last[(e["kind"], b)] = True
        keep.append(e)
    meta = {"_": "0021 The Break - collision events from the baked simulation (scripts/blender/cosmos_break.py), real-time seconds. "
                 "kind: impact (cue ball hits the cluster), click (bead-bead), planet (bead bounces off the chrome planet); s = strength 0-1.",
            "duration": DUR, "events": [{"t": round(e["t"], 4), "kind": e["kind"], "s": round(e["s"], 3)} for e in keep]}
    json.dump(meta, open(EVENTS_PATH, "w"), indent=0)
    print(f"bake done in {time.time() - t0:.1f} s, {len(keep)} sound events", flush=True)


if os.environ.get("BREAK_BAKE") == "1":
    bake()
    sys.exit(0)

SIM = np.load(SIM_PATH)
PSIM, CSIM, C2SIM = SIM["P"], SIM["CUE"], SIM["CUE2"]
MOONSIM, METSIM = SIM["MOON"], SIM["MET"]

# ---------------- render objects ----------------
PV, PF = uv_sphere(16, 10)
NV = len(PV)
faces = [tuple(i * NV + k for k in face) for i in range(NB) for face in PF]
bmesh_ = bpy.data.meshes.new("Beads")
bmesh_.from_pydata(np.zeros((NB * NV, 3)).tolist(), [], faces)
bmesh_.polygons.foreach_set("use_smooth", [True] * len(bmesh_.polygons))
beads = bpy.data.objects.new("Beads", bmesh_)
scene.collection.objects.link(beads)
beads.data.materials.append(swarm_m)
_c0 = PSIM[0].astype(np.float64)
_th = np.arctan2(_c0[:, 2], _c0[:, 0])
HUE = np.clip((_c0[:, 2] - _c0[:, 2].min()) / np.ptp(_c0[:, 2]) * 0.85 + 0.15 * (np.sin(3 * _th) * 0.5 + 0.5), 0, 1)
_ha = bmesh_.attributes.new("hue", "FLOAT", "POINT")
# director's review: colour each bead by the ring band it settles in (target_r index in the bake) -> the final ring
# carries the owner's swirl gradient, mint outside -> aqua -> blue -> violet inside; the cluster is a mix of them
_band = (np.arange(NB) % 97) / 96.0
_ha.data.foreach_set("value", np.repeat(1 - _band, NV).astype(np.float32))
_rj = bmesh_.attributes.new("rj", "FLOAT", "POINT")
_rj.data.foreach_set("value", np.repeat(rngb.uniform(0.0, 0.06, NB), NV).astype(np.float32))
SIZE_J = rngb.uniform(0.9, 1.1, NB)
mix1.inputs["Fac"].default_value = 1.0
mix2.inputs["Fac"].default_value = 0.0          # iridescent anodized metal
strip.energy = 0
backl.energy = 0


def ball(name, radius, material, seg=64):
    v, f = uv_sphere(seg, seg // 2)
    me = bpy.data.meshes.new(name)
    me.from_pydata((v * radius).tolist(), [], f)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.data.materials.append(material)
    return o


chrome = principled("Chrome", (0.86, 0.88, 0.92), metal=1.0, rough=0.035)
chrome.node_tree.nodes["Principled BSDF"].inputs["Thin Film Thickness"].default_value = 240.0
cue = ball("Cue", CUE_R, chrome)
cue2 = ball("Cue2", CUE2_R, chrome)  # act 2: the bigger ball that tears the ring
# owner, Nov 16: the white stone moon looked out of place -> anodized violet metal with a teal/violet thin-film sheen
# and a light hammered surface, so it carries the scene's colours like the planet and the beads
moon_m = principled("Moon", (0.42, 0.38, 0.82), metal=1.0, rough=0.38)  # rough enough to catch light from any side
_mn = moon_m.node_tree.nodes
_mn["Principled BSDF"].inputs["Thin Film Thickness"].default_value = 320.0
_mb = _mn.new("ShaderNodeBump")
_mb.inputs["Strength"].default_value = 0.2
_mt = _mn.new("ShaderNodeTexVoronoi")
_mt.inputs["Scale"].default_value = 7.0
moon_m.node_tree.links.new(_mt.outputs["Distance"], _mb.inputs["Height"])
moon_m.node_tree.links.new(_mb.outputs["Normal"], _mn["Principled BSDF"].inputs["Normal"])
moon = ball("Moon", MOON_R, moon_m)
mets = [ball(f"Meteor{i}", MET_R, chrome) for i in range(4)]
planet_m = principled("PlanetCoated", (0.5, 0.6, 0.9), metal=0.0, rough=0.35, coat=1.0)  # review 2: colour in the surface, a clear coat on top
# review: polished chrome in black space reflected black (read as a black hole) -> anodized metal in the swirl
# gradient (teal top -> blue -> violet bottom), slightly rough so it catches the light broadly; still mirrors the beads
_pn = planet_m.node_tree.nodes
_pb = _pn["Principled BSDF"]
_pb.inputs["Thin Film Thickness"].default_value = 380.0
# review 3: a GAS GIANT - swirling cloud bands in the owner's swirl palette (latitude bands distorted by turbulence,
# like the reference swirl), dark and saturated so the side light gives it a real day/night terminator
_L = planet_m.node_tree.links
_ptc = _pn.new("ShaderNodeTexCoord")
_turb = _pn.new("ShaderNodeTexNoise")
_turb.inputs["Scale"].default_value = 1.6
_turb.inputs["Detail"].default_value = 14.0
_turb.inputs["Roughness"].default_value = 0.66
_turb.inputs["Distortion"].default_value = 3.4
_sep = _pn.new("ShaderNodeSeparateXYZ")
_mixz = _pn.new("ShaderNodeMath")
_mixz.operation = "MULTIPLY_ADD"
_mixz.inputs[1].default_value = 1.1  # strong turbulence: storms, not stripes
_bands = _pn.new("ShaderNodeMath")
_bands.operation = "SINE"
_bscale = _pn.new("ShaderNodeMath")
_bscale.operation = "MULTIPLY"
_bscale.inputs[1].default_value = 3.6
_bmr = _pn.new("ShaderNodeMapRange")
_bmr.inputs["From Min"].default_value = -1.0
_bmr.inputs["From Max"].default_value = 1.0
_pr = _pn.new("ShaderNodeValToRGB")
_stops = ((0.0, (0.05, 0.02, 0.22)), (0.3, (0.02, 0.12, 0.45)), (0.55, (0.0, 0.38, 0.42)), (0.8, (0.08, 0.55, 0.4)), (1.0, (0.3, 0.8, 0.62)))
_pr.color_ramp.elements[0].position, _pr.color_ramp.elements[0].color = _stops[0][0], (*_stops[0][1], 1)
_pr.color_ramp.elements[1].position, _pr.color_ramp.elements[1].color = _stops[-1][0], (*_stops[-1][1], 1)
for _p, _c in _stops[1:-1]:
    _e = _pr.color_ramp.elements.new(_p)
    _e.color = (*_c, 1)
_L.new(_ptc.outputs["Object"], _turb.inputs["Vector"])
_L.new(_ptc.outputs["Object"], _sep.inputs[0])
_L.new(_turb.outputs["Fac"], _mixz.inputs[0])
_L.new(_sep.outputs["Z"], _mixz.inputs[2])
_L.new(_mixz.outputs[0], _bscale.inputs[0])
_L.new(_bscale.outputs[0], _bands.inputs[0])
_L.new(_bands.outputs[0], _bmr.inputs["Value"])
_L.new(_bmr.outputs["Result"], _pr.inputs["Fac"])
_L.new(_pr.outputs["Color"], _pb.inputs["Base Color"])
planet = ball("Planet", PLANET_R, planet_m, seg=128)
planet.location = tuple(PLANET_C)
# a key light for the planet so it reads as a huge polished sphere (its reflections carry the beads and the stars)
_pk = area("PlanetKey", (PLANET_C[0] - 11, PLANET_C[1] + 1.5, PLANET_C[2] + 3), 6.0, 1500, (0.9, 0.96, 1.0), target=tuple(PLANET_C))  # raking side light: a real terminator
# light linking (review 2): the bead/cue lights never touch the planet (no hot reflections on its coat); the planet key
# lights only the planet and is not seen in its reflection - the coat mirrors the beads and the stars instead
_bead_only = bpy.data.collections.new("BeadOnly")
_planet_only = bpy.data.collections.new("PlanetOnly")
_planet_only.objects.link(planet)
for _o in list(scene.objects):
    if _o.type == "LIGHT" and _o.name != "PlanetKey":
        _o.light_linking.receiver_collection = _bead_only
bpy.data.objects["PlanetKey"].light_linking.receiver_collection = _planet_only
bpy.data.objects["PlanetKey"].visible_glossy = False
_bead_only.objects.link(beads)
_bead_only.objects.link(cue)
_bead_only.objects.link(cue2)
_bead_only.objects.link(moon)
for _o in mets:
    _bead_only.objects.link(_o)

cd = bpy.data.cameras.new("Cam")
cd.lens = 32
cd.dof.use_dof = True
cam = bpy.data.objects.new("Cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam

MID = (PLANET_C * 0.45)
_ur_r = np.cross(RING_N2, [0, 0, 1.0]); _ur_r /= np.linalg.norm(_ur_r)
MOON_MID = PLANET_C + 1.95 * (-_ur_r)   # midway planet -> moon closest approach (check 1: keep the moon in frame)
SHOTS = [  # real t, camera position, look-at, lens, f-stop  (recut 2)
    (0.00, (-1.25, -3.0, -0.42), (0.05, 0.0, 0.05), 32, 4.0),     # S1 close, low 3/4 on the cluster, planet behind
    (0.40, (-1.32, -3.2, -0.36), (0.05, 0.3, 0.1), 32, 4.0),
    (2.20, (-1.7, -3.8, 0.1), (0.6, 2.4, 0.4), 30, 5.6),          # S2 drifts back, debris flies past towards the planet
    (2.90, tuple(PLANET_C + np.array([-2.0, -3.4, -0.2])), tuple(PLANET_C + np.array([0, -0.6, 0])), 30, 5.6),  # S3 low, beside the near face
    (4.20, tuple(PLANET_C + np.array([-2.6, -3.6, 0.3])), tuple(PLANET_C), 30, 5.6),   #    the debris rains in and splashes off
    (5.90, tuple(PLANET_C + np.array([-4.4, -1.8, 0.45])), tuple(PLANET_C), 30, 8.0),  # S4 low skim past the forming ring
    (7.30, tuple(PLANET_C + np.array([-4.0, -4.4, 1.3])), tuple(PLANET_C), 30, 8.0),
    (9.00, tuple(PLANET_C + np.array([-4.4, -5.4, 1.9])), tuple(PLANET_C), 30, 8.0),   # act 2: ring in view, ball 2 comes in
    (9.75, tuple(PLANET_C + np.array([-3.6, -4.6, 1.3])), tuple(PLANET_C + np.array([0.2, -0.8, -0.3])), 30, 5.6),  # HIT 2 (slow-mo)
    (11.6, tuple(PLANET_C + np.array([-4.4, -5.6, 1.8])), tuple(PLANET_C), 30, 8.0),   #    the ring shatters into a cloud
    (14.4, tuple(PLANET_C + np.array([-5.0, -1.6, -0.6])), tuple(PLANET_C), 30, 8.0),  # low skim: it re-forms, tilted
    (17.0, tuple(PLANET_C + np.array([-4.2, -4.8, 1.6])), tuple(PLANET_C), 30, 8.0),
    (19.5, tuple(MOON_MID + np.array([-6.6, -8.6, 2.8])), tuple(MOON_MID), 28, 8.0),   # act 3: wide - planet AND moon in frame
    (21.5, tuple(MOON_MID + np.array([-5.6, -7.4, 1.6])), tuple(MOON_MID), 28, 8.0),   # the moon tears the ring
    (24.8, tuple(PLANET_C + np.array([-4.6, -5.8, 1.9])), tuple(PLANET_C), 30, 8.0),   #    the stream slingshots back
] + [  # act 4 (check 2): the camera arcs to each meteor's strike point, ring edge in front, planet behind
    (h - 0.6, tuple(PLANET_C + 6.2 * (math.cos(a) * _UR + math.sin(a) * _UT) + RING_N2 * 1.5), tuple(PLANET_C * 0.35 + MET_HIT[i] * 0.65), 24, 8.0)
    for i, (h, a) in enumerate(zip(MET_HITS_REAL, MET_ANG))
] + [
    (36.6, tuple(PLANET_C + 7.4 * (math.cos(MET_ANG[3]) * _UR + math.sin(MET_ANG[3]) * _UT) + RING_N2 * 2.4), tuple(PLANET_C), 30, 8.0),
    (40.0, tuple(PLANET_C + np.array([-2.6, -4.4, 5.4])), tuple(PLANET_C), 30, 8.0),   # act 5: from above - the rain spirals in
    (42.6, tuple(PLANET_C + np.array([-3.4, -4.0, 1.5])), tuple(PLANET_C), 28, 5.6),   #    they bounce back up at the lens
    (46.0, tuple(PLANET_C + np.array([-7.2, -7.6, 2.0])), tuple(PLANET_C), 30, 8.0),   #    two crossed rings form
    (50.0, tuple(PLANET_C + np.array([-7.0, -8.4, 2.8])), tuple(PLANET_C), 30, 8.0),
    (60.0, tuple(PLANET_C + np.array([-6.4, -10.5, 3.8])), tuple(PLANET_C), 32, 8.0),  # ENDING: hero pull-back, fade
]


def shot_at(r):
    for (t0, p0, l0, f0, a0), (t1, p1, l1, f1, a1) in zip(SHOTS, SHOTS[1:]):
        if r <= t1:
            k = float(sm(t0, t1, r))
            lerp_ = lambda a, b: tuple(x + (y - x) * k for x, y in zip(a, b))  # noqa: E731
            return lerp_(p0, p1), lerp_(l0, l1), f0 + (f1 - f0) * k, a0 + (a1 - a0) * k
    t, p, l_, f, a = SHOTS[-1]
    return p, l_, f, a


def sim_state(r):
    s = sim_t(r) / DT
    i = int(min(max(math.floor(s), 0), NSTEP - 2))
    k = min(max(s - i, 0.0), 1.0)
    return PSIM[i] * (1 - k) + PSIM[i + 1] * k, CSIM[i] * (1 - k) + CSIM[i + 1] * k


def apply(r):  # noqa: F811
    pos, cpos = sim_state(r)
    v = PV[None] * (RB * SIZE_J)[:, None, None] + pos[:, None, :]
    bmesh_.vertices.foreach_set("co", v.astype(np.float32).ravel())
    bmesh_.update()
    cue.location = tuple(cpos)
    cue.rotation_euler = (4.0 * r, 2.2 * r, 0.0)
    cue.hide_render = r > 2.5
    s_ = sim_t(r) / DT
    i_ = int(min(max(math.floor(s_), 0), NSTEP - 2))
    k_ = min(max(s_ - i_, 0.0), 1.0)
    cue2.location = tuple(C2SIM[i_] * (1 - k_) + C2SIM[i_ + 1] * k_)
    cue2.rotation_euler = (3.0 * r, 1.6 * r, 0.0)
    cue2.hide_render = not (T_HIT2_REAL - 0.9 < r < T_HIT2_REAL + 1.6)
    mpos = MOONSIM[i_] * (1 - k_) + MOONSIM[i_ + 1] * k_
    moon.location = tuple(mpos)
    moon.rotation_euler = (0.2 * r, 0.1 * r, 0.3 * r)
    moon.hide_render = bool(mpos[1] < -70)
    for j_, mo in enumerate(mets):
        mp_ = METSIM[i_, j_] * (1 - k_) + METSIM[i_ + 1, j_] * k_
        mo.location = tuple(mp_)
        mo.rotation_euler = (4.0 * r, 2.0 * r, 0.0)
        mo.hide_render = bool(mp_[1] < -70)
    p, look, lens, fstop = shot_at(r)
    shake = 0.0
    for th_, amp_ in ((T_IMPACT_REAL, 0.05), (T_HIT2_REAL, 0.06), (T_BOUNCE_REAL, 0.05)) + tuple((h, 0.04) for h in MET_HITS_REAL):
        a_ = r - th_
        if a_ > 0:
            shake += amp_ * math.exp(-a_ * 6.0) * math.sin(a_ * 60)
    pv_ = mathutils.Vector(p) + mathutils.Vector((shake, 0, shake * 0.6))
    cam.location = pv_
    cam.rotation_euler = (mathutils.Vector(look) - pv_).to_track_quat("-Z", "Y").to_euler()
    cd.lens = lens
    cd.dof.aperture_fstop = fstop
    cd.dof.focus_distance = (mathutils.Vector(look) - pv_).length
    scene.view_settings.exposure = 0.5


def travel(r):  # noqa: F811 - screen-space-ish: near beads move faster on screen
    a, _ = sim_state(r - 0.5 / FPS)
    b, _ = sim_state(r + 0.5 / FPS)
    p, _, _, _ = shot_at(r)
    dcam = np.linalg.norm(b - np.array(p), axis=1)
    return float(np.percentile(np.linalg.norm(b - a, axis=1) / np.maximum(dcam, 0.4) * 7.0, 97))


scene.render.fps = FPS
scene.render.use_motion_blur = False
SUB_STEP = 0.035
SUB_MAX = 12


def render_to(path):  # noqa: F811
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def frame(f):  # noqa: F811 - accumulated motion blur (real shutter) where things move fast on screen
    r = f / FPS
    subs = int(np.clip(math.ceil(travel(r) / SUB_STEP), 1, SUB_MAX))
    if T_IMPACT_REAL - 0.25 < r < T_IMPACT_REAL + 0.1 or T_HIT2_REAL - 0.5 < r < T_HIT2_REAL + 0.1 or any(h - 0.5 < r < h + 0.1 for h in MET_HITS_REAL):
        subs = max(subs, 10)                        # a cue ball streaking in
    span = 1.0
    for w0, w1 in ((2.0, 2.7), (4.5, 5.6), (9.55, 11.2), (11.9, 13.4), (19.0, 22.5), (38.0, 44.5)) + tuple((h - 0.1, h + 1.2) for h in MET_HITS_REAL):  # flash check
        if w0 <= r <= w1:
            span, subs = 2.6, max(subs, 20)
    out = os.path.join(OUT, f"f_{f:04d}.png")
    if subs == 1:
        apply(r)
        render_to(out)
        return
    scene.cycles.samples = max(12, int(SAMPLES * 2 / subs))
    acc = None
    for j in range(subs):
        apply(r + ((j + 0.5) / subs - 0.5) * span / FPS)
        tmp = os.path.join(OUT, f"_sub_{f:04d}_{j}.png")
        render_to(tmp)
        img = bpy.data.images.load(tmp)
        px = np.empty(len(img.pixels), dtype=np.float32)
        img.pixels.foreach_get(px)
        acc = px if acc is None else acc + px
        bpy.data.images.remove(img)
        os.remove(tmp)
    scene.cycles.samples = SAMPLES
    im = bpy.data.images.new(f"acc_{f}", scene.render.resolution_x, scene.render.resolution_y)
    im.pixels.foreach_set(acc / subs)
    im.filepath_raw = out
    im.file_format = "PNG"
    im.save()
    bpy.data.images.remove(im)


NF = int(round(DUR * FPS))
todo = ONLY if ONLY is not None else list(range(K, NF, NN))
t0_ = time.time()
for i_, f_ in enumerate(todo):
    if ONLY is None and os.path.exists(os.path.join(OUT, f"f_{f_:04d}.png")):
        continue
    frame(f_)
    if i_ % 20 == 0:
        print(f"frame {f_} ({i_ + 1}/{len(todo)}) {(time.time() - t0_) / (i_ + 1):.2f} s/frame", flush=True)
