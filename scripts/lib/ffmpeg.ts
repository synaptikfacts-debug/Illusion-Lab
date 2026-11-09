import { spawn } from "node:child_process";

/** Runs a command, resolves with stdout/stderr text; rejects on non-zero exit with the stderr tail. */
export function run(cmd: string, args: string[]): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { windowsHide: true });
    let stdout = "", stderr = "";
    p.stdout.on("data", (d) => (stdout += d));
    p.stderr.on("data", (d) => (stderr += d));
    p.on("error", reject);
    p.on("close", (code) =>
      code === 0 ? resolve({ stdout, stderr }) : reject(new Error(`${cmd} exited ${code}\n${stderr.slice(-2000)}`)),
    );
  });
}

/** Streams raw frames (w*h*channels bytes each) from ffmpeg to a callback. */
export function streamFrames(
  file: string,
  vf: string,
  frameBytes: number,
  onFrame: (frame: Buffer, index: number) => void,
): Promise<number> {
  return new Promise((resolve, reject) => {
    const args = ["-v", "error", "-i", file, "-vf", vf, "-fps_mode", "passthrough", "-f", "rawvideo", "-"];
    const p = spawn("ffmpeg", args, { windowsHide: true });
    let pending: Buffer = Buffer.alloc(0), index = 0, stderr = "";
    p.stdout.on("data", (d: Buffer) => {
      pending = pending.length ? Buffer.concat([pending, d]) : d;
      while (pending.length >= frameBytes) {
        onFrame(pending.subarray(0, frameBytes), index++);
        pending = pending.subarray(frameBytes);
      }
    });
    p.stderr.on("data", (d) => (stderr += d));
    p.on("error", reject);
    p.on("close", (code) => (code === 0 ? resolve(index) : reject(new Error(`ffmpeg exited ${code}\n${stderr}`))));
  });
}

export async function probe(file: string): Promise<{ duration: number; fps: number; width: number; height: number; frames: number }> {
  const { stdout } = await run("ffprobe", [
    "-v", "error", "-select_streams", "v:0", "-count_packets",
    "-show_entries", "stream=width,height,r_frame_rate,nb_read_packets:format=duration",
    "-of", "json", file,
  ]);
  const j = JSON.parse(stdout);
  const s = j.streams[0];
  const [n, d] = String(s.r_frame_rate).split("/").map(Number);
  return { duration: Number(j.format.duration), fps: n / (d || 1), width: s.width, height: s.height, frames: Number(s.nb_read_packets) };
}
