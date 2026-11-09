import type { WebpackOverrideFn } from "@remotion/bundler";

// Lets components `import frag from "./shader.frag.glsl"` as a plain string.
export const webpackOverride: WebpackOverrideFn = (config) => ({
  ...config,
  module: {
    ...config.module,
    rules: [...(config.module?.rules ?? []), { test: /\.(glsl|vert|frag)$/, type: "asset/source" }],
  },
});
