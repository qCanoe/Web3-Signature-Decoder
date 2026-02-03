module.exports = {
  root: true,
  extends: ["@metamask/eslint-config"],
  overrides: [
    {
      files: ["*.ts", "*.tsx"],
      extends: ["@metamask/eslint-config-typescript"],
      parserOptions: {
        tsconfigRootDir: __dirname,
        project: ["./tsconfig.json"],
      },
    },
    {
      files: ["*.test.ts", "*.test.tsx"],
      extends: ["@metamask/eslint-config-jest"],
    },
  ],
  ignorePatterns: ["dist/", "node_modules/", "coverage/", "*.js"],
  rules: {
    "import/no-unassigned-import": "off",
  },
};
