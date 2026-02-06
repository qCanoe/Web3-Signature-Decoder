import "dotenv/config";
import express from "express";
import cors from "cors";
import { CoreEngine } from "@sd/core-engine";
import {
  OpenAiReasoningProvider,
  type LlmReasoningInput,
} from "@sd/core-llm";
import { loadFixtures } from "@sd/test-fixtures";

const app = express();
app.use(cors());
app.use(express.json({ limit: "2mb" }));

const openAiProvider = new OpenAiReasoningProvider({
  apiKey: process.env.OPENAI_API_KEY ?? "",
  model: process.env.OPENAI_MODEL ?? "gpt-5.2",
  timeoutMs: Number(process.env.OPENAI_TIMEOUT_MS ?? "12000"),
  promptVersion: "reasoning-v2",
});

const engine = new CoreEngine({
  llmProvider: openAiProvider,
});

const gatewayToken = process.env.SNAP_GATEWAY_TOKEN ?? "";

app.get("/v2/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "signature-decoder-test-api",
    llmModel: openAiProvider.model,
    timestamp: Date.now(),
  });
});

app.post("/v2/analyze", async (req, res) => {
  try {
    const result = await engine.analyze(req.body);
    res.json(result);
  } catch (error) {
    res.status(400).json({
      error: error instanceof Error ? error.message : "analyze_failed",
    });
  }
});

app.post("/v2/fixtures/validate", async (_req, res) => {
  const fixtures = loadFixtures();
  const report: Array<{
    name: string;
    expected: string;
    actual: string;
    pass: boolean;
  }> = [];

  for (const fixture of fixtures) {
    try {
      const result = await engine.analyze(fixture.request);
      report.push({
        name: fixture.name,
        expected: fixture.expected.decision,
        actual: result.decision.value,
        pass: fixture.expected.decision === result.decision.value,
      });
    } catch (error) {
      report.push({
        name: fixture.name,
        expected: fixture.expected.decision,
        actual: "error",
        pass: false,
      });
    }
  }

  const pass = report.every((entry) => entry.pass);
  res.status(pass ? 200 : 500).json({ pass, report });
});

app.post("/v2/reason", async (req, res) => {
  try {
    if (gatewayToken) {
      const auth = req.header("authorization") || "";
      if (auth !== `Bearer ${gatewayToken}`) {
        res.status(401).json({ error: "unauthorized" });
        return;
      }
    }

    const input = req.body?.input as LlmReasoningInput | undefined;
    if (!input) {
      res.status(400).json({ error: "missing_input" });
      return;
    }

    const result = await openAiProvider.reason(input);
    res.json(result);
  } catch (error) {
    res.status(503).json({
      error: error instanceof Error ? error.message : "reason_failed",
    });
  }
});

const host = process.env.TEST_API_HOST ?? "0.0.0.0";
const port = Number(process.env.TEST_API_PORT ?? "4000");

app.listen(port, host, () => {
  // eslint-disable-next-line no-console
  console.log(`test-api listening on http://${host}:${port}`);
});
