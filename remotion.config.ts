// Used by `npm run studio` (Remotion CLI). scripts/render.ts passes the same settings to the Node API.
import { Config } from "@remotion/cli/config";
import { webpackOverride } from "./src/webpack-override";

Config.setPublicDir("./assets");
Config.setChromiumOpenGlRenderer("angle"); // GPU WebGL on Windows (D3D11)
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.overrideWebpackConfig(webpackOverride);
