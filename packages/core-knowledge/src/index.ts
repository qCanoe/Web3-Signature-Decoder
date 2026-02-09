import {
  ChainsKnowledgeSchema,
  Eip712TypesKnowledgeSchema,
  MaliciousAddressesKnowledgeSchema,
  MaliciousDomainsKnowledgeSchema,
  MessagePatternsKnowledgeSchema,
  ProtocolsKnowledgeSchema,
  RiskRulesKnowledgeSchema,
  SelectorsKnowledgeSchema,
  type ChainsKnowledge,
  type Eip712TypesKnowledge,
  type MaliciousAddressesKnowledge,
  type MaliciousDomainsKnowledge,
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
import maliciousAddressesJson from "./knowledge/malicious_addresses.v2.json";
import maliciousDomainsJson from "./knowledge/malicious_domains.v2.json";
import chainsJson from "./knowledge/chains.v2.json";

export interface KnowledgeBundle {
  selectors: SelectorsKnowledge;
  eip712Types: Eip712TypesKnowledge;
  protocols: ProtocolsKnowledge;
  riskRules: RiskRulesKnowledge;
  messagePatterns: MessagePatternsKnowledge;
  maliciousAddresses: MaliciousAddressesKnowledge;
  maliciousDomains: MaliciousDomainsKnowledge;
  chains: ChainsKnowledge;
}

export function loadKnowledgeOrThrow(): KnowledgeBundle {
  return {
    selectors: SelectorsKnowledgeSchema.parse(selectorsJson),
    eip712Types: Eip712TypesKnowledgeSchema.parse(eip712TypesJson),
    protocols: ProtocolsKnowledgeSchema.parse(protocolsJson),
    riskRules: RiskRulesKnowledgeSchema.parse(riskRulesJson),
    messagePatterns: MessagePatternsKnowledgeSchema.parse(messagePatternsJson),
    maliciousAddresses: MaliciousAddressesKnowledgeSchema.parse(maliciousAddressesJson),
    maliciousDomains: MaliciousDomainsKnowledgeSchema.parse(maliciousDomainsJson),
    chains: ChainsKnowledgeSchema.parse(chainsJson),
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
