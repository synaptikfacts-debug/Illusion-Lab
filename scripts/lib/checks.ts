import { LOUDNESS } from "../../config/platforms";
import { run, streamFrames } from "./ffmpeg";

/** Mean absolute difference (0-255, grayscale 270x480) between the first and the last frame. */
export async function loopDiff(file: string, totalFrames: number): Promise<number> {
  const w = 270, h = 480, frames: Buffer[] = [];
  await streamFrames(
    file,
    `select='eq(n\\,0)+eq(n\\,${totalFrames - 1})',scale=${w}:${h}:flags=area,format=gray`,
    w * h,
    (f) => frames.push(Buffer.from(f)),
  );
  if (frames.length !== 2) throw new Error(`loop check expected 2 frames, got ${frames.length}`);
  let sum = 0;
  for (let i = 0; i < w * h; i++) sum += Math.abs(frames[0][i] - frames[1][i]);
  return sum / (w * h);
}

export interface LoudnessResult {
  inputLUFS: number;
  outputLUFS: number;
  truePeak: number;
  silent: boolean;
}

/** Two-pass EBU R128 normalisation to the house target. Writes a 48 kHz stereo WAV. */
export async function normaliseLoudness(input: string, output: string, lufs: number = LOUDNESS.integratedLUFS): Promise<LoudnessResult> {
  const target = `I=${lufs}:TP=${LOUDNESS.truePeakDb}:LRA=${LOUDNESS.lra}`;
  const p1 = await run("ffmpeg", ["-hide_banner", "-i", input, "-af", `loudnorm=${target}:print_format=json`, "-f", "null", "-"]);
  const m = lastJson(p1.stderr);
  const inputI = Number(m.input_i);
  if (!Number.isFinite(inputI) || inputI < -60) {
    await run("ffmpeg", ["-y", "-v", "error", "-i", input, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", output]);
    return { inputLUFS: inputI, outputLUFS: inputI, truePeak: Number(m.input_tp), silent: true };
  }
  const measured = `measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}`;
  await run("ffmpeg", [
    "-y", "-v", "error", "-i", input,
    "-af", `loudnorm=${target}:${measured}:linear=true,aresample=48000`,
    "-ac", "2", "-c:a", "pcm_s16le", output,
  ]);
  const p3 = await run("ffmpeg", ["-hide_banner", "-i", output, "-af", `loudnorm=${target}:print_format=json`, "-f", "null", "-"]);
  const o = lastJson(p3.stderr);
  return { inputLUFS: inputI, outputLUFS: Number(o.input_i), truePeak: Number(o.input_tp), silent: false };
}

/** loudnorm prints its JSON block in stderr, followed by other lines. */
function lastJson(text: string) {
  const a = text.lastIndexOf("{"), b = text.lastIndexOf("}");
  return JSON.parse(text.slice(a, b + 1));
}
