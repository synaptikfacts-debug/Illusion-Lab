// npm run sound -- <reel-id>   regenerate a reel's generated audio (SFX + YouTube music) without rendering video
import { generateBounceAudio } from "./gen-bounce-audio";
import { generateMusic } from "./gen-music";
import { generatePinAudio } from "./gen-pin-audio";
import { generatePinShowAudio } from "./gen-pinshow-audio";
import { generateRodAudio } from "./gen-rod-audio";
import { generateDominoAudio } from "./gen-domino-audio";
import { generateFaceAudio } from "./gen-face-audio";
import { generateLiquidAudio } from "./gen-liquid-audio";
import { generateSandAudio } from "./gen-sand-audio";
import { generateGaltonAudio } from "./gen-galton-audio";
import { generateOrbAudio } from "./gen-orb-audio";
import { generateRingsAudio } from "./gen-rings-audio";
import { generatePendulumAudio } from "./gen-pendulum-audio";
import { generateFerroAudio } from "./gen-ferro-audio";
import { generateInkAudio } from "./gen-ink-audio";
import { generateLabyrinthAudio } from "./gen-labyrinth-audio";
import { loadReel } from "./lib/reels";

const id = process.argv[2];
if (!id) {
  console.error("usage: npm run sound -- <reel-id>");
  process.exit(1);
}
const reel = await loadReel(id);
if (reel.illusion.type === "pinWall") generatePinAudio(reel);
if (reel.illusion.type === "pinShow" || reel.id.startsWith("0011-singing-pins-show")) generatePinShowAudio(reel);
if (reel.illusion.type === "rodStory") generateRodAudio(reel);
if (reel.illusion.type === "dominoStory") generateDominoAudio(reel);
if (reel.illusion.type === "faceStory") generateFaceAudio(reel);
if (reel.illusion.type === "liquid") generateLiquidAudio(reel);
if (reel.illusion.type === "sand") generateSandAudio(reel);
if (reel.illusion.type === "galton") generateGaltonAudio(reel);
if (reel.illusion.type === "orbs") generateOrbAudio(reel);
if (reel.illusion.type === "rings") generateRingsAudio(reel);
if (reel.illusion.type === "pendulum") generatePendulumAudio(reel);
if (reel.illusion.type === "ferro") generateFerroAudio(reel);
if (reel.illusion.type === "ink") generateInkAudio(reel);
if (reel.audio.musicGen?.style === "labyrinth") generateLabyrinthAudio(reel);
if (reel.illusion.type === "bounceField") generateBounceAudio(reel);
if (reel.audio.musicGen) generateMusic(reel);
