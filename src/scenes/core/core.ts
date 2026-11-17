// 0024 "This core is unlocking" (owner, Nov 16 2026: cyber/tech, "something nobody has done, beautiful, keeps everyone
// watching to the end"). A precision-machined sphere, a CRYPTEX: an outer shell of 7 black anodised latitude bands and an
// inner shell of 5 chrome bands. Each band spins like a combination dial and clacks into place when its notch lines up;
// when the whole seam is aligned the shell unlocks: its bands lift off onto their own radii and swing onto their own
// axes - the sphere becomes a gyroscope. The inner shell does the same, revealing a blazing crystal core. Then every band
// comes home, one by one, the last one clacks shut, the seam light fades.
// Last two reels: 0023 crimson ferrofluid lake, 0022 ferrofluid on a steel spiral (violet/aqua). This one: machined
// metal + glass, black/chrome + ice-cyan light, a vault-like studio - no liquid, no spikes.
// Reference to nobody: our own mechanic (cryptex sphere -> gyroscope), no text, no faces.
//
// BEAT SHEET (real time t; story time tau, see tauAt)
//  0-0.6    HOOK: cold open on the climax - the core blazing inside a storm of orbiting bands, one swings past the lens
//  0.6-1.6  fast rewind: everything snaps back into a closed sphere
//  1.6-3    the closed sphere, dials misaligned; the first dial starts to spin
//  3-6.8    OUTER CRYPTEX: 8 dials spin and clack into place, faster and faster; each notch lights up
//  6.8      the seam is complete: a pulse of light runs up it
//  7-8.6    UNLOCK: the outer bands lift off and swing onto their own axes
//  8.6-10   INNER CRYPTEX: 5 chrome dials clack into place (fast); 10-11 they open too
//  11       the crystal core ignites
//  11-14    PAYOFF: 12 bands orbit the blazing core like a gyroscope, the camera arcs in
//  14-17.2  HOMECOMING: inner bands land, then the outer ones, one by one; the top cap clacks shut last at 17.2
//  17.2-20  the seam light fades, the camera eases away, fade to black, silence
export const CORE = { duration: 21, fade: [19.3, 20.95] as [number, number] };

export const OUTER = { r: 0.1, t: 0.008, lats: [-90, -66, -44, -22, 0, 22, 44, 66, 90] }; // 8 bands (a slit opens on the equator)
export const INNER = { r: 0.068, t: 0.006, lats: [-90, -55, -25, 0, 25, 55, 90] }; // 6 bands

const TAU2 = Math.PI * 2;
const hash = (i: number) => { const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return x - Math.floor(x); };
const clamp = (x: number, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const sm = (a: number, b: number, x: number) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };

/** real time -> story time: cold open on the climax, a fast rewind, then the story plays at 1x. */
// v6 (owner, Nov 17: "the opening repeats earlier videos" -> option A): no cold open / rewind any more. The reel opens
// INSIDE the closed sphere on the mercury core; the camera flies out through the equator slit (HOOK_OUT) and the story
// starts once it is outside.
export const HOOK_OUT = 1.8;
export function tauAt(t: number): number {
  if (t < HOOK_OUT) return 1.6;
  // slow motion around the ignition (story runs at 0.4x), so the core lighting up gets its moment
  let tau = 1.6;
  const dt = 0.005;
  for (let x = HOOK_OUT; x < t; x += dt) tau += (1 - 0.6 * slowW(x + dt / 2)) * Math.min(dt, t - x);
  return tau;
}
const slowW = (t: number) => sm(7.4, 7.8, t) * (1 - sm(9.0, 9.4, t)); // ignition at story 7.7 = real ~7.9
/** story time -> real time (for sound events) */
export function realAt(tau: number): number {
  if (tau <= 1.6) return HOOK_OUT;
  let a = HOOK_OUT, b = 30;
  for (let k = 0; k < 40; k++) { const m = (a + b) / 2; if (tauAt(m) < tau) a = m; else b = m; }
  return (a + b) / 2;
}
export const REWIND: [number, number] = [-2, -1]; // v6: no rewind any more

// dial schedules (story time): start spinning, clack into place
// v4 (owner, Nov 17: "super boring, just a ball"): the closed sphere lasts ~2 s - all 8 dials rip into place in 1.8 s
const OUT_LOCK = [2.05, 2.3, 2.5, 2.68, 2.85, 3.0, 3.13, 3.25];
const OUT_START = [1.6, 1.65, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95]; // all dials spin from the moment the rewind lands
const IN_LOCK = [5.6, 5.9, 6.15, 6.35, 6.55, 6.7];
const IN_START = [5.0, 5.12, 5.24, 5.36, 5.48, 5.6];
const OUT_OPEN = 3.7, IN_OPEN = 6.8;
const IN_HOME = [14.2, 14.45, 14.7, 14.9, 15.1, 15.3];
const OUT_HOME = [15.5, 15.75, 16.0, 16.25, 16.5, 16.72, 16.92, 17.2]; // outer bands land; the order is set by ORDER
const OUT_ORDER = [3, 4, 2, 5, 1, 6, 0, 7]; // middle bands first, the caps last; the top cap (7) closes it
export const SEAM_PULSE = 3.45;
export const IGNITE = 7.7;
export const FINAL = 17.2;

interface Band { spin: number; scale: number; lift: number; axis: [number, number, number]; angle: number; lock: number }

// a dial: from its offset, a few turns, decelerating into place with a small mechanical settle
function dial(tau: number, start: number, lock: number, offset: number, turns: number, dir: number): number {
  if (tau <= start) return offset;
  if (tau >= lock) { const a = tau - lock; return 0.05 * Math.exp(-a * 18) * Math.sin(a * 60) * dir; }
  const u = (tau - start) / (lock - start);
  const e = 1 - (1 - u) ** 3;
  return offset + (-offset + dir * turns * TAU2) * e;
}

function openAmt(tau: number, o0: number, home: number) {
  return sm(o0, o0 + 1.4, tau) * (1 - sm(home - 1.1, home, tau));
}

// gyroscope: angle about the band's own axis = w * time spent open, rescaled so it lands on a whole number of turns
function gyroAngle(tau: number, o0: number, home: number, w: number): number {
  const total = integ(home, o0, home, w);
  const k = Math.max(1, Math.round(total / TAU2)) * TAU2 / total;
  return k * integ(Math.min(tau, home), o0, home, w);
}
function integ(tau: number, o0: number, home: number, w: number) {
  // integral of openAmt * w from o0 to tau (numeric, cached per band in practice by low step count)
  let s = 0;
  const dt = 0.02;
  for (let x = o0; x < tau; x += dt) s += openAmt(x + dt / 2, o0, home) * w * dt;
  return s;
}

function bands(tau: number, n: number, lock: number[], start: number[], o0: number, home: number[], shell: number, spread: number[]): Band[] {
  const out: Band[] = [];
  for (let i = 0; i < n; i++) {
    const h = (k: number) => hash(shell * 100 + i * 7 + k);
    const offset = (h(1) - 0.5) * 2.4 + (i % 2 ? 0.7 : -0.7);
    const dir = i % 2 ? 1 : -1;
    const spin = dial(tau, start[i], lock[i], offset, 1 + Math.floor(h(2) * 2), dir);
    const oi = o0 + 0.1 * i;
    const op = openAmt(tau, oi, home[i]);
    const cap = i === 0 || i === n - 1;
    // EXPLODED VIEW: the bands spread along the axis (slits open between them, the core shows through), each wobbles on
    // its own tilt axis like a gyroscope and keeps turning like a dial; everything returns to zero on the way home
    const step = shell === 0 ? 0.032 : 0.03;
    const scale = 1 + op * spread[i];
    const lift = op * ((i - (n - 1) / 2) * step + Math.sign(i - (n - 1) / 2) * step * 0.45 + (cap ? (i === 0 ? -1 : 1) * step * 0.8 : 0));
    const az = h(3) * TAU2;
    const axis: [number, number, number] = [Math.cos(az), Math.sin(az), 0];
    const angle = op * (0.22 + 0.18 * h(5)) * Math.sin((0.8 + 0.6 * h(6)) * (tau - oi) + h(7) * TAU2);
    const turn = gyroAngle(tau, oi, home[i], (0.5 + 0.7 * h(8)) * (i % 2 ? 1 : -1));
    out.push({ spin: spin + turn, scale, lift, axis, angle, lock: sm(lock[i] - 0.02, lock[i] + 0.08, tau) * (1 - sm(FINAL + 0.6, FINAL + 2.4, tau)) });
  }
  return out;
}

export function bandsAt(tau: number) {
  const outHome = OUT_ORDER.map((_, i) => OUT_HOME[OUT_ORDER.indexOf(i)]);
  return {
    outer: bands(tau, 8, OUT_LOCK, OUT_START, OUT_OPEN, outHome, 0, [0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12]),
    inner: bands(tau, 6, IN_LOCK, IN_START, IN_OPEN, IN_HOME, 1, [0.08, 0.08, 0.08, 0.08, 0.08, 0.08]),
  };
}
export const SCHED = { OUT_LOCK, OUT_START, IN_LOCK, IN_START, OUT_OPEN, IN_OPEN, IN_HOME, OUT_HOME, OUT_ORDER };

export function coreFrame(t: number) {
  const tau = tauAt(t);
  const outHome = OUT_ORDER.map((_, i) => OUT_HOME[OUT_ORDER.indexOf(i)]);
  const outer = bands(tau, 8, OUT_LOCK, OUT_START, OUT_OPEN, outHome, 0, [0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12]);
  const inner = bands(tau, 6, IN_LOCK, IN_START, IN_OPEN, IN_HOME, 1, [0.08, 0.08, 0.08, 0.08, 0.08, 0.08]);
  const locked = (L: number[]) => L.reduce((a, l) => a + sm(l - 0.02, l + 0.08, tau), 0) / L.length;
  const leak = [0.5 + 1.5 * locked(OUT_LOCK), 0.5 + 1.5 * locked(IN_LOCK)];
  // light: the notch strips, a pulse up the seam, the crystal core
  const pulse = Math.exp(-(((tau - SEAM_PULSE) / 0.18) ** 2));
  const core = 0.05 + 0.95 * sm(IGNITE - 0.5, IGNITE + 0.5, tau) * (1 - sm(13.0, 14.3, tau)) // dims before the bands fly home past it (flash check) + 0.12 * (1 - sm(17.4, 19.5, tau)) * sm(14, 15, tau);
  const breathe = 1 + 0.08 * Math.sin(tau * 2.4) * sm(IGNITE, IGNITE + 1, tau);
  // camera (story-driven, plus real-time ease at the end)
  const open = sm(3.7, 5.3, tau) * (1 - sm(14.5, 17.2, tau));
  const payoff = sm(7.2, 9.2, tau) * (1 - sm(14.0, 17.8, tau));
  const end = sm(18.4, 21, t);
  const hookPush = t < 0.6 ? 1 - t / 0.6 : 0; // the cold open starts closer
  const dials = sm(1.6, 2.0, tau) * (1 - sm(3.2, 3.9, tau)); // push in on the dials while they rip into place
  const macro = Math.exp(-(((tau - 2.75) / 0.32) ** 2)); // a fast macro pass along the seam as the last dials clack
  // HOOK (option A): the camera starts inside the sphere, between the core and the inner bands, and flies straight
  // out through the equator slit; the two hemispheres stand a few millimetres apart so the slit is open, and close
  // with a clack the moment the camera is outside. The core glows for the hook, then dims until it is revealed again.
  const hook = t < HOOK_OUT ? 1 : 0;
  const hk = sm(0.15, HOOK_OUT, t);
  const split = (1 - sm(1.45, 1.75, t)) * 0.012;
  if (split > 0) {
    outer.forEach((b, i) => { b.lift += (i < 4 ? -1 : 1) * split; });
    inner.forEach((b, i) => { b.lift += (i < 3 ? -1 : 1) * split * 0.8; });
  }
  const hookCore = 1 - sm(1.3, 1.9, t);
  const fYaw = (1 - macro) * (-28 + 22 * Math.sin(tau * 0.31) + 25 * dials * Math.sin(1.4 * (tau - 1.6)) + 40 * sm(3.7, 6.5, tau) + 150 * sm(7.4, 14.0, tau) - 35 * sm(14.0, 19.5, tau)) * (Math.PI / 180); // slow homecoming camera (fast orbit + chrome glints failed the flash check)
  const fPitch = ((1 - macro) * (12 + 8 * open - 4 * payoff + 6 * end + 6 * dials) + 3 * macro) * (Math.PI / 180);
  const fDist = (1 - macro) * (0.95 + 0.42 * open - 0.62 * payoff + 0.3 * end - 0.2 * dials) + 0.2 * macro; // v6: close on the core in the payoff
  return {
    tau,
    look: [0, -0.096 * macro, 0.03 * macro],
    hook,
    lt: t < HOOK_OUT ? t - (HOOK_OUT - 1.6) : tau, // the mercury keeps moving while story time waits
    liquid: Math.max(sm(6.8, 8.2, tau) * (1 - sm(13.6, 15.3, tau)), hookCore),
    yaw: fYaw,
    pitch: t < HOOK_OUT ? fPitch * sm(1.2, 1.8, t) : fPitch,
    dist: t < HOOK_OUT ? 0.062 + (fDist - 0.062) * hk ** 2.2 : fDist,
    outer, inner, leak,
    seam: pulse,
    core: Math.max(core * breathe, 0.9 * hookCore),
    opened: [open, sm(6.8, 8.2, tau) * (1 - sm(13.6, 15.3, tau))],
    rewind: t >= REWIND[0] && t < REWIND[1] ? Math.sin(Math.PI * (t - REWIND[0]) / (REWIND[1] - REWIND[0])) : 0,
  };
}

/** sound events (real time), same source as the picture */
export function coreEvents() {
  const ev: { t: number; kind: string; i: number; shell: number }[] = [];
  const add = (tau: number, kind: string, i: number, shell: number) => { if (tau >= 1.6) ev.push({ t: realAt(tau), kind, i, shell }); };
  OUT_START.forEach((s, i) => add(s, "spin", i, 0));
  OUT_LOCK.forEach((s, i) => add(s, "lock", i, 0));
  IN_START.forEach((s, i) => add(s, "spin", i, 1));
  IN_LOCK.forEach((s, i) => add(s, "lock", i, 1));
  add(SEAM_PULSE, "seam", 0, 0);
  for (let i = 0; i < 8; i++) add(OUT_OPEN + 0.1 * i, "open", i, 0);
  for (let i = 0; i < 6; i++) add(IN_OPEN + 0.1 * i, "open", i, 1);
  add(IGNITE, "ignite", 0, 2);
  IN_HOME.forEach((s, i) => add(s, "home", i, 1));
  OUT_ORDER.forEach((b, k) => add(OUT_HOME[k], b === 7 ? "final" : "home", b, 0));
  return ev.sort((a, b) => a.t - b.t);
}
export const OUT_LOCKS = OUT_LOCK, IN_LOCKS = IN_LOCK, OUT_STARTS = OUT_START, IN_STARTS = IN_START;
