module.exports = {
  preset: "@metamask/snaps-jest",
  testMatch: ["**/test/**/*.test.ts"],
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        useESM: false,
      },
    ],
  },
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json"],
  testEnvironmentOptions: {
    customEnvironment: "@metamask/snaps-jest",
  },
};
