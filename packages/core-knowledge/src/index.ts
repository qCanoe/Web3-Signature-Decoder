import {
  Eip712TypesKnowledgeSchema,
  MessagePatternsKnowledgeSchema,
  ProtocolsKnowledgeSchema,
  RiskRulesKnowledgeSchema,
  SelectorsKnowledgeSchema,
  type Eip712TypesKnowledge,
  type MessagePatternsKnowledge,
  type ProtocolsKnowledge,
  type RiskRulesKnowledge,
  type SelectorsKnowledge,
} from "@sd/core-schema";
import selectorsJson from "./knowledge/selectors.v2.json";
import eip712TypesJson from "./knowledge/eip712_types.v2.json";
import protocolsJson from "./knowledge/protocols.v2.json";
import riskRulesJson from "./knowledge/risk_rules.v2.json";
import messagePatternsJson from "./knowledge/message_patterns.v2.json";

export interface KnowledgeBundle {
  selectors: SelectorsKnowledge;
  eip712Types: Eip712TypesKnowledge;
  protocols: ProtocolsKnowledge;
  riskRules: RiskRulesKnowledge;
  messagePatterns: MessagePatternsKnowledge;
}

export function loadKnowledgeOrThrow(): KnowledgeBundle {
  return {
    selectors: SelectorsKnowledgeSchema.parse(selectorsJson),
    eip712Types: Eip712TypesKnowledgeSchema.parse(eip712TypesJson),
    protocols: ProtocolsKnowledgeSchema.parse(protocolsJson),
    riskRules: RiskRulesKnowledgeSchema.parse(riskRulesJson),
    messagePatterns: MessagePatternsKnowledgeSchema.parse(messagePatternsJson),
  };
}

let singleton: KnowledgeBundle | null = null;

export function getKnowledge(): KnowledgeBundle {
  if (!singleton) {
    singleton = loadKnowledgeOrThrow();
  }
  return singleton;
}

export function resetKnowledgeForTests(): void {
  singleton = null;
}
