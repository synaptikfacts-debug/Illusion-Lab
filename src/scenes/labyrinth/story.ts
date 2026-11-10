// "Ferrofluid Labyrinth" story (owner's pick, Nov 10; ray-traced in Blender, approved look + motion test).
// Reference does (0008, best performer): 3D black ferrofluid spikes reflecting neon rings. Ours does: a macro shot of
// ferrofluid squeezed between glass plates on an LED panel - a drop bursts into a labyrinth that spreads over the
// cell, winds into a tightening spiral, and at the very END the magnet cuts out and the whole maze retracts into one
// mirror drop (the payoff is the last thing you see, so viewers stay to the end).
// Beat sheet (seconds):
//  0-1.0     HOOK: close on the full spiral labyrinth, still turning
//  1.0-2.2   it rewinds: the maze retracts into a single drop
//  2.2-3.2   the drop rests on the glowing glass
//  3.2-14    the field comes on: the drop bursts, fingers branch and spread over the whole cell
//  14-24     the labyrinth turns and winds into a spiral
//  24-26     the spiral tightens hard (climax)
//  26-28.6   PAYOFF: the magnet cuts out - the whole labyrinth pulls back into one round mirror drop
//  28.6-31   ENDING: the drop rests, the camera eases back, fade to black

export const LSTORY = {
  fps: 30,
  total: 31,
  hook: [0, 1.0],
  rewind: [1.0, 2.2],
  burst: 3.2,
  filled: 14.0,
  wind: [14.0, 24.0],
  climax: [24.0, 26.0],
  retract: [26.0, 28.6],
  fade: [29.2, 31.0],
} as const;

const sm = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

/** The picture's state at time t: s = how far the maze has grown (0 drop .. 1 full), twist, rotation, solid drop
 * blend, camera distance (m). */
export function stateAt(t: number) {
  const S = LSTORY;
  let s: number;
  if (t < S.rewind[0]) s = 1;
  else if (t < S.rewind[1]) s = 1 - sm(S.rewind[0], S.rewind[1], t);
  else if (t < S.burst) s = 0;
  else if (t < S.filled) {
    const k = (t - S.burst) / (S.filled - S.burst);
    s = 0.03 + 0.97 * (0.35 * sm(0, 1, k) + 0.65 * k); // bursts, then keeps spreading
  } else if (t < S.retract[0]) s = 1;
  else s = 1 - sm(S.retract[0], S.retract[1], t);

  // the spiral: the hook shows it wound up; it HOLDS while the maze retracts (unwinding fast while retracting strobes -
  // photosensitivity), eases out slowly after the burst while the maze is still small, winds again from 14 s,
  // tightens at the climax, and holds again through the final retraction
  const hookTw = 3.0 + 0.3 * Math.min(1, t / S.hook[1]);
  const hookRot = 0.65 + 0.06 * Math.min(t, S.hook[1]);
  let twist: number, rot: number;
  if (t < S.burst + 3) {
    const early = 1 - sm(S.burst, S.burst + 3, t);
    twist = hookTw * early;
    rot = hookRot * early;
  } else if (t < S.retract[0]) {
    twist = 2.6 * sm(S.wind[0], S.wind[1], t) + 1.0 * sm(S.climax[0], S.climax[1], t);
    rot = 0.5 * sm(S.wind[0], S.climax[1], t) + 0.25 * sm(S.climax[0], S.climax[1], t);
  } else {
    twist = 3.6;
    rot = 0.75;
  }

  // a solid drop while the maze is (nearly) not there
  const solid = Math.max(sm(S.rewind[1] - 0.35, S.rewind[1], t) * (1 - sm(S.burst, S.burst + 0.8, t)), sm(S.retract[1] - 0.6, S.retract[1], t));

  // camera: close for the hook, back for the burst, slow push in through the wind, eases away at the end
  let dist = 0.3 - 0.03 * sm(S.burst, S.filled, t) - 0.03 * sm(S.wind[0], S.climax[1], t) + 0.03 * sm(S.retract[0], S.retract[1], t) + 0.04 * sm(S.retract[1], S.total, t);
  if (t < S.rewind[1]) dist = 0.235 + 0.065 * sm(S.rewind[0], S.rewind[1], t);
  return { s, twist, rot, solid, dist };
}
