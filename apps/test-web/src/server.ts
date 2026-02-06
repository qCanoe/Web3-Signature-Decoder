import "dotenv/config";
import express from "express";
import { join } from "node:path";

const app = express();
const publicDir = join(__dirname, "..", "public");

app.get("/config.js", (_req, res) => {
  const apiBase = process.env.TEST_WEB_API_BASE_URL ?? "http://localhost:4000";
  res.type("application/javascript").send(`window.__SD_CONFIG__ = { apiBase: "${apiBase}" };`);
});

app.use(express.static(publicDir));

const host = process.env.TEST_WEB_HOST ?? "0.0.0.0";
const port = Number(process.env.TEST_WEB_PORT ?? "4173");

app.listen(port, host, () => {
  // eslint-disable-next-line no-console
  console.log(`test-web listening on http://${host}:${port}`);
});
