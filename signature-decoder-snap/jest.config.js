/**
 * Jest 配置文件
 */

module.exports = {
  preset: "@metamask/snaps-jest",
  testEnvironment: "node",
  testMatch: ["**/test/**/*.test.ts"],
  transform: {
    "^.+\\.tsx?$": "ts-jest",
  },
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json"],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/**/*.d.ts",
    "!src/data/**",
  ],
  coverageDirectory: "coverage",
  coverageReporters: ["text", "lcov", "html"],
};
