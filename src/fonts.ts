import { continueRender, delayRender, staticFile } from "remotion";

export const FONT = "Outfit";

const faces: [string, string][] = [
  ["700", "fonts/Outfit-700.ttf"],
  ["900", "fonts/Outfit-900.ttf"],
];

if (typeof document !== "undefined") {
  const handle = delayRender("Loading fonts");
  Promise.all(
    faces.map(([weight, file]) => {
      const face = new FontFace(FONT, `url(${staticFile(file)}) format("truetype")`, { weight });
      return face.load().then((f) => document.fonts.add(f));
    }),
  )
    .then(() => continueRender(handle))
    .catch((e) => {
      console.error(e);
      continueRender(handle);
    });
}
