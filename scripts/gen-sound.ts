// npm run sound -- <reel-id>   regenerate a reel's generated audio (SFX + YouTube music) without rendering video
import { generateBounceAudio } from "./gen-bounce-audio";
import { generateMusic } from "./gen-music";
import { generatePinAudio } from "./gen-pin-audio";
import { generateRodAudio } from "./gen-rod-audio";
import { generateDominoAudio } from "./gen-domino-audio";
import { generateFaceAudio } from "./gen-face-audio";
import { generateLiquidAudio } from "./gen-liquid-audio";
import { generateSandAudio } from "./gen-sand-audio";
import { generateGaltonAudio } from "./gen-galton-audio";
import { generateOrbAudio } from "./gen-orb-audio";
import { loadReel } from "./lib/reels";

const id = process.argv[2];
if (!id) {
  console.error("usage: npm run sound -- <reel-id>");
  process.exit(1);
}
const reel = await loadReel(id);
if (reel.illusion.type === "pinWall") generatePinAudio(reel);
if (reel.illusion.type === "rodStory") generateRodAudio(reel);
if (reel.illusion.type === "dominoStory") generateDominoAudio(reel);
if (reel.illusion.type === "faceStory") generateFaceAudio(reel);
if (reel.illusion.type === "liquid") generateLiquidAudio(reel);
if (reel.illusion.type === "sand") generateSandAudio(reel);
if (reel.illusion.type === "galton") generateGaltonAudio(reel);
if (reel.illusion.type === "orbs") generateOrbAudio(reel);
if (reel.illusion.type === "bounceField") generateBounceAudio(reel);
if (reel.audio.musicGen) generateMusic(reel);
