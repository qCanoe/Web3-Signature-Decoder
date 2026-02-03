/**
 * 签名分类器
 *
 * 基于 EIP-712 类型和字段进行分类
 */

import type { EIP712TypedData } from "../types";

/**
 * 签名分类结果
 */
export interface ClassificationResult {
  type: SignatureClassType;
  subType?: string;
  confidence: number;
}

/**
 * 签名分类类型
 */
export type SignatureClassType =
  | "permit"
  | "permit2"
  | "order"
  | "delegation"
  | "gasless"
  | "login"
  | "unknown";

/**
 * 协议模式定义
 */
interface ProtocolPattern {
  name: string;
  domainNames: string[];
  primaryTypes: string[];
}

/**
 * 已知协议模式
 */
const PROTOCOL_PATTERNS: ProtocolPattern[] = [
  {
    name: "Uniswap Permit2",
    domainNames: ["Permit2"],
    primaryTypes: ["PermitSingle", "PermitBatch", "PermitWitnessTransferFrom"],
  },
  {
    name: "OpenSea Seaport",
    domainNames: ["Seaport"],
    primaryTypes: ["OrderComponents", "BulkOrder"],
  },
  {
    name: "CoW Protocol",
    domainNames: ["Gnosis Protocol", "CoW Protocol"],
    primaryTypes: ["Order"],
  },
  {
    name: "1inch",
    domainNames: ["1inch Aggregation Router", "1inch Limit Order Protocol"],
    primaryTypes: ["Order"],
  },
  {
    name: "Blur",
    domainNames: ["Blur Exchange"],
    primaryTypes: ["Order", "Root"],
  },
  {
    name: "LooksRare",
    domainNames: ["LooksRare"],
    primaryTypes: ["MakerOrder"],
  },
  {
    name: "Safe",
    domainNames: ["Safe", "GnosisSafe"],
    primaryTypes: ["SafeTx", "SafeMessage"],
  },
  {
    name: "ENS",
    domainNames: ["ENS", "Ethereum Name Service"],
    primaryTypes: ["Registration", "Transfer"],
  },
];

/**
 * 分类 EIP-712 类型化数据
 */
export function classifyEIP712Type(
  typedData: EIP712TypedData
): ClassificationResult {
  const { primaryType, types, message, domain } = typedData;

  // 检测 Permit 类型
  if (isPermitType(primaryType, types, message)) {
    return {
      type: "permit",
      subType: primaryType,
      confidence: 0.95,
    };
  }

  // 检测 Permit2 类型
  if (isPermit2Type(primaryType, domain)) {
    return {
      type: "permit2",
      subType: primaryType,
      confidence: 0.95,
    };
  }

  // 检测订单类型
  if (isOrderType(primaryType, types, message)) {
    return {
      type: "order",
      subType: detectOrderProtocol(domain, primaryType),
      confidence: 0.85,
    };
  }

  // 检测委托类型
  if (isDelegationType(primaryType, types)) {
    return {
      type: "delegation",
      confidence: 0.8,
    };
  }

  // 检测 gasless 交易
  if (isGaslessType(primaryType, types)) {
    return {
      type: "gasless",
      confidence: 0.75,
    };
  }

  return {
    type: "unknown",
    confidence: 0.5,
  };
}

/**
 * 检测协议
 */
export function detectProtocol(typedData: EIP712TypedData): string | undefined {
  const domainName = typedData.domain?.name?.toLowerCase() || "";
  const primaryType = typedData.primaryType;

  for (const pattern of PROTOCOL_PATTERNS) {
    // 检查 domain name
    for (const name of pattern.domainNames) {
      if (domainName.includes(name.toLowerCase())) {
        return pattern.name;
      }
    }

    // 检查 primaryType
    if (pattern.primaryTypes.includes(primaryType)) {
      // 额外验证 domain
      for (const name of pattern.domainNames) {
        if (domainName.includes(name.toLowerCase())) {
          return pattern.name;
        }
      }
    }
  }

  // 基于 domain name 推断
  if (domainName) {
    // 常见 DeFi 协议
    if (domainName.includes("uniswap")) return "Uniswap";
    if (domainName.includes("aave")) return "Aave";
    if (domainName.includes("compound")) return "Compound";
    if (domainName.includes("curve")) return "Curve";
    if (domainName.includes("yearn")) return "Yearn";
    if (domainName.includes("sushi")) return "SushiSwap";

    // NFT 市场
    if (domainName.includes("opensea")) return "OpenSea";
    if (domainName.includes("blur")) return "Blur";
    if (domainName.includes("looksrare")) return "LooksRare";
    if (domainName.includes("rarible")) return "Rarible";

    return typedData.domain?.name;
  }

  return undefined;
}

/**
 * 检测是否为 Permit 类型
 */
function isPermitType(
  primaryType: string,
  types: Record<string, Array<{ name: string; type: string }>>,
  message: Record<string, unknown>
): boolean {
  // 检查 primaryType
  if (primaryType.toLowerCase().includes("permit")) {
    return true;
  }

  // 检查 ERC20 Permit 标准字段
  const permitFields = ["owner", "spender", "value", "nonce", "deadline"];
  const hasPermitFields = permitFields.every((field) => field in message);

  if (hasPermitFields) {
    return true;
  }

  // 检查类型定义
  const typeKeys = Object.keys(types);
  if (typeKeys.some((key) => key.toLowerCase().includes("permit"))) {
    return true;
  }

  return false;
}

/**
 * 检测是否为 Permit2 类型
 */
function isPermit2Type(
  primaryType: string,
  domain: EIP712TypedData["domain"]
): boolean {
  // Permit2 合约域名检测
  if (domain?.name?.toLowerCase().includes("permit2")) {
    return true;
  }

  // Permit2 特有的 primaryType
  const permit2Types = [
    "PermitSingle",
    "PermitBatch",
    "PermitWitnessTransferFrom",
    "PermitBatchWitnessTransferFrom",
  ];

  return permit2Types.includes(primaryType);
}

/**
 * 检测是否为订单类型
 */
function isOrderType(
  primaryType: string,
  types: Record<string, Array<{ name: string; type: string }>>,
  message: Record<string, unknown>
): boolean {
  // 检查 primaryType
  if (
    primaryType.toLowerCase().includes("order") ||
    primaryType.toLowerCase().includes("listing")
  ) {
    return true;
  }

  // 检查订单常见字段
  const orderFields = ["maker", "taker", "makerAmount", "takerAmount"];
  const hasOrderFields = orderFields.some((field) => field in message);

  return hasOrderFields;
}

/**
 * 检测订单协议
 */
function detectOrderProtocol(
  domain: EIP712TypedData["domain"],
  primaryType: string
): string {
  const domainName = domain?.name?.toLowerCase() || "";

  if (domainName.includes("seaport")) return "Seaport";
  if (domainName.includes("blur")) return "Blur";
  if (domainName.includes("looksrare")) return "LooksRare";
  if (domainName.includes("cow") || domainName.includes("gnosis protocol")) {
    return "CoW Protocol";
  }
  if (domainName.includes("1inch")) return "1inch";

  return "Unknown DEX/NFT Order";
}

/**
 * 检测是否为委托类型
 */
function isDelegationType(
  primaryType: string,
  types: Record<string, Array<{ name: string; type: string }>>
): boolean {
  // 检查 primaryType
  if (
    primaryType.toLowerCase().includes("delegation") ||
    primaryType.toLowerCase().includes("delegate")
  ) {
    return true;
  }

  // 检查类型定义
  const typeKeys = Object.keys(types);
  return typeKeys.some(
    (key) =>
      key.toLowerCase().includes("delegation") ||
      key.toLowerCase().includes("delegate")
  );
}

/**
 * 检测是否为 Gasless 交易
 */
function isGaslessType(
  primaryType: string,
  types: Record<string, Array<{ name: string; type: string }>>
): boolean {
  // 检查 meta transaction 类型
  const metaTxKeywords = [
    "forward",
    "metatransaction",
    "relay",
    "sponsored",
    "gasless",
  ];

  const lowerPrimaryType = primaryType.toLowerCase();

  if (metaTxKeywords.some((keyword) => lowerPrimaryType.includes(keyword))) {
    return true;
  }

  // 检查类型定义
  const typeKeys = Object.keys(types);
  return typeKeys.some((key) =>
    metaTxKeywords.some((keyword) => key.toLowerCase().includes(keyword))
  );
}
