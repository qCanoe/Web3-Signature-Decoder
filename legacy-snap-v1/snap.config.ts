import type { SnapConfig } from "@metamask/snaps-cli";

const config: SnapConfig = {
  bundler: "webpack",
  input: "./src/index.ts",
  server: {
    port: 8080,
  },
  polyfills: {
    buffer: true,
  },
  // 自动修复 manifest 中的 shasum
  evaluate: true,
  manifest: {
    update: true,
  },
};

export default config;
