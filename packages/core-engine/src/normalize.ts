import {
  AnalyzeRequestV2Schema,
  type AnalyzeRequestV2,
} from "@sd/core-schema";

export function normalizeRequest(input: unknown): AnalyzeRequestV2 {
  const parsed = AnalyzeRequestV2Schema.parse(input);
  const timestamp = parsed.context?.timestamp ?? Date.now();

  return {
    ...parsed,
    context: {
      ...parsed.context,
      timestamp,
    },
  };
}
