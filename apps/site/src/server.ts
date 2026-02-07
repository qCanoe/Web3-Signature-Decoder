import "dotenv/config";
import express from "express";
import { join } from "node:path";

const app = express();
const publicDir = join(__dirname, "..", "public");

// Inject runtime config (snap origin URL) into the page
app.get("/config.js", (_req, res) => {
  const snapUrl = process.env.SNAP_ORIGIN ?? "http://localhost:8080";
  res.type("application/javascript").send(
    `window.__SD_SITE__ = { snapOrigin: "local:${snapUrl}" };`
  );
});

app.use(express.static(publicDir));

const host = process.env.SITE_HOST ?? "0.0.0.0";
const port = Number(process.env.SITE_PORT ?? "8000");

app.listen(port, host, () => {
  console.log(`site listening on http://${host}:${port}`);
});
