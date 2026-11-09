declare module "*.glsl" {
  const src: string;
  export default src;
}

interface ImportMeta {
  webpackContext(
    dir: string,
    opts: { recursive?: boolean; regExp?: RegExp },
  ): { keys(): string[]; (id: string): { default: unknown } };
}
