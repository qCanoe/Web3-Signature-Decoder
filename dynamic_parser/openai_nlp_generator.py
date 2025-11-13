"""
OpenAI GPT-4.1-mini集成的NLP生成器
基于参数提取的英文自然语言生成
"""

import openai
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time
from functools import lru_cache
import hashlib

@dataclass
class EnglishNLOutput:
    """英文自然语言输出结果"""
    title: str
    summary: str
    detailed_description: str
    technical_details: str
    context: str
    risk_level: str
    risk_explanation: str

class OpenAINLPGenerator:
    """基于OpenAI GPT-4.1-mini的英文NLP生成器"""
    
    def __init__(self, api_key: str):
        """初始化OpenAI客户端"""
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4-1106-preview"  # GPT-4.1-mini
        
        # 成本跟踪
        self.total_cost = 0.0
        self.request_count = 0
    
    def extract_key_parameters(self, eip712_data: Dict[str, Any]) -> Dict[str, Any]:
        """从EIP712数据中提取关键参数"""
        primary_type = eip712_data.get("primaryType", "")
        domain = eip712_data.get("domain", {})
        message = eip712_data.get("message", {})
        
        # 提取核心信息
        extracted = {
            "operation_type": primary_type.lower(),
            "app_name": domain.get("name", "Unknown App"),
            "version": domain.get("version", ""),
            "chain_id": domain.get("chainId", ""),
            "contract": domain.get("verifyingContract", "")[:10] + "..." if domain.get("verifyingContract") else "",
        }
        
        # 根据操作类型提取特定字段
        if "permit" in primary_type.lower():
            extracted.update({
                "owner": self._format_address(message.get("owner", "")),
                "spender": self._format_address(message.get("spender", "")),
                "amount": self._format_amount(message.get("value", 0)),
                "deadline": self._format_timestamp(message.get("deadline", 0)),
                "nonce": message.get("nonce", "")
            })
        elif "order" in primary_type.lower():
            extracted.update({
                "offerer": self._format_address(message.get("offerer", "")),
                "start_time": self._format_timestamp(message.get("startTime", 0)),
                "end_time": self._format_timestamp(message.get("endTime", 0)),
                "order_type": message.get("orderType", ""),
                "items_count": len(message.get("offer", [])) + len(message.get("consideration", []))
            })
        elif "vote" in primary_type.lower():
            extracted.update({
                "voter": self._format_address(message.get("voter", "")),
                "proposal_id": message.get("proposal", message.get("proposalId", "")),
                "support": message.get("support", ""),
                "reason": message.get("reason", "")[:50] + "..." if len(message.get("reason", "")) > 50 else message.get("reason", "")
            })
        elif "mint" in primary_type.lower() or "voucher" in primary_type.lower():
            # NFT mint 操作
            extracted.update({
                "recipient": self._format_address(message.get("to", message.get("recipient", message.get("redeemer", "")))),
                "token_id": message.get("tokenId", message.get("minPrice", "")),
                "amount": message.get("amount", "1")
            })
        elif "bridge" in primary_type.lower() or "destinationchainid" in str(message).lower():
            # Bridge/跨链桥 操作
            token_address = message.get("token", "")
            token_symbol = self._get_token_symbol(token_address)
            amount_raw = message.get("amount", message.get("value", 0))
            bridge_fee_raw = message.get("bridgeFee", message.get("fee", 0))
            
            extracted.update({
                "sender": self._format_address(message.get("sender", message.get("from", ""))),
                "recipient": self._format_address(message.get("recipient", message.get("to", ""))),
                "token": self._format_address(token_address),
                "token_symbol": token_symbol,
                "amount": self._format_token_amount(amount_raw, token_symbol),
                "destination_chain": self._get_chain_name(message.get("destinationChainId", message.get("targetChain", ""))),
                "bridge_fee": self._format_token_amount(bridge_fee_raw, token_symbol),
                "deadline": self._format_timestamp(message.get("deadline", 0))
            })
        elif "intent" in primary_type.lower() or "relay" in primary_type.lower() or "metatx" in primary_type.lower():
            # Meta Transaction / Relay 操作
            extracted.update({
                "from": self._format_address(message.get("from", "")),
                "to": self._format_address(message.get("to", "")),
                "value": self._format_amount(message.get("value", 0)),
                "has_calldata": bool(message.get("callData") or message.get("data")),
                "calldata_length": len(str(message.get("callData", message.get("data", "0x")))) - 2,  # 减去 0x
                "gas_fee": self._format_amount(message.get("gasFee", message.get("fee", 0))),
                "deadline": self._format_timestamp(message.get("deadline", 0)),
                "note": message.get("note", "")[:50] + "..." if len(message.get("note", "")) > 50 else message.get("note", "")
            })
        
        return extracted
    
    @lru_cache(maxsize=50)
    def generate_english_description(self, params_hash: str, params_json: str) -> EnglishNLOutput:
        """生成英文描述（带缓存）"""
        params = json.loads(params_json)
        
        # 构建精简的提示词
        prompt = self._build_prompt(params)
        
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are helping users understand what they are signing. Explain in 1-2 COMPLETE sentences from the user's perspective. Include key details (amounts, destinations, risks). Write FULL sentences with proper endings. IMPORTANT: Do NOT add currency symbols like $ or €. Just write the amount and token name (e.g., '100.00 USDC' not '$100.00 USDC'). Be direct, clear, and finish every thought."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=100,  # 增加到100，避免描述被截断
                timeout=15
            )
            
            # 计算成本
            usage = response.usage
            cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
            self.total_cost += cost
            self.request_count += 1
            
            response_time = time.time() - start_time
            print(f"✅ OpenAI API call completed in {response_time:.2f}s, Cost: {cost:.6f}")
            
            # 解析响应
            return self._parse_response(response.choices[0].message.content, params)
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            # 降级到模板生成
            return self._fallback_template_generation(params)
    
    def _build_prompt(self, params: Dict[str, Any]) -> str:
        """构建优化的提示词"""
        operation_type = params.get("operation_type", "operation")
        app_name = params.get("app_name", "Unknown")
        
        # 构建简洁的核心信息
        if operation_type == "permit":
            amount = params.get("amount", "tokens")
            deadline = params.get("deadline", "")
            
            # 格式化deadline信息
            deadline_text = ""
            if deadline:
                try:
                    import datetime
                    deadline_timestamp = int(deadline)
                    deadline_date = datetime.datetime.fromtimestamp(deadline_timestamp)
                    deadline_text = f" until {deadline_date.strftime('%Y-%m-%d')}"
                except:
                    deadline_text = f" until deadline {deadline}"
            
            # 特别处理无限授权
            if "UNLIMITED" in str(amount):
                return f"User is signing a permit for UNLIMITED spending authorization in {app_name}{deadline_text}. This is an infinite approval that allows spending any amount. Explain this clearly including the unlimited nature and deadline:"
            else:
                return f"User is signing a permit to allow spending {amount} in {app_name}{deadline_text}. Explain in 1 simple sentence what they are authorizing, including the deadline:"
        
        elif operation_type == "order":
            return f"User is signing to create a trade order in {app_name}. Explain in 1 simple sentence what they are authorizing:"
            
        elif operation_type == "vote":
            return f"User is signing to cast a vote in {app_name}. Explain in 1 simple sentence what they are authorizing:"
        
        elif "mint" in operation_type or "voucher" in operation_type:
            return f"User is signing to mint/claim an NFT in {app_name}. Explain in 1 simple sentence what they are doing:"
        
        elif "bridge" in operation_type:
            amount = params.get("amount", "unknown")
            dest_chain = params.get("destination_chain", "unknown")
            bridge_fee = params.get("bridge_fee", "unknown")
            return f"User is signing to bridge {amount} from current chain to {dest_chain} (bridge fee: {bridge_fee}) via {app_name}. Explain in 1-2 sentences: what they're transferring. Skip repeating 'irreversible' - just state the action clearly:"
        
        elif "intent" in operation_type or "relay" in operation_type or "metatx" in operation_type:
            has_calldata = params.get("has_calldata", False)
            to_address = params.get("to", "unknown")
            value = params.get("value", "0")
            gas_fee = params.get("gas_fee", "unknown")
            
            # 检测可疑地址
            is_suspicious = "9999" in to_address or "0000" in to_address
            
            if has_calldata:
                return f"User is signing to authorize {app_name} to execute a contract call on their behalf to {to_address}. Explain in 1-2 clear sentences: what they're authorizing and the key risk (arbitrary execution):"
            elif is_suspicious and value == "0":
                return f"User is signing to authorize {app_name} to submit transactions to suspicious address {to_address} with zero transfer amount. Explain in 1-2 sentences: why this is risky (suspicious address + zero-amount trap tricks users):"
            else:
                return f"User is signing to authorize {app_name} to relay transactions on their behalf (gas fee: {gas_fee}). Explain in 1 sentence what relay authorization means:"
            
        else:
            return f"User is signing a {operation_type} operation in {app_name}. Explain in 1 simple sentence what they are authorizing:"
    
    def _parse_response(self, response_text: str, params: Dict[str, Any]) -> EnglishNLOutput:
        """解析GPT响应为结构化输出"""
        operation_type = params.get("operation_type", "operation")
        app_name = params.get("app_name", "Unknown App")
        
        # 生成标题
        title = f"{app_name} - {operation_type.title()} Operation"
        
        # 使用GPT响应作为主要描述
        description = response_text.strip()
        
        # 生成技术细节
        tech_details = self._generate_technical_details(params)
        
        # 生成上下文
        context = self._generate_context(params)
        
        # 评估风险等级和解释
        risk_level, risk_explanation = self._assess_risk_level(params)
        
        return EnglishNLOutput(
            title=title,
            summary=description,
            detailed_description=description,
            technical_details=tech_details,
            context=context,
            risk_level=risk_level,
            risk_explanation=risk_explanation
        )
    
    def _fallback_template_generation(self, params: Dict[str, Any]) -> EnglishNLOutput:
        """API失败时的模板生成"""
        operation_type = params.get("operation_type", "operation")
        app_name = params.get("app_name", "Unknown App")
        
        templates = {
            "permit": f"You are authorizing another address to spend your tokens in {app_name}.",
            "order": f"You are creating a trade order in {app_name}.",
            "vote": f"You are casting a vote in {app_name}.",
            "transfer": f"You are transferring assets in {app_name}."
        }
        
        description = templates.get(operation_type, f"This is a blockchain operation in {app_name}.")
        
        return EnglishNLOutput(
            title=f"{app_name} - {operation_type.title()} Operation",
            summary=description,
            detailed_description=description,
            technical_details=f"Operation type: {operation_type}",
            context=f"Executed on {app_name}",
            risk_level="Medium",
            risk_explanation="Unlimited approval"
        )
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算API调用成本"""
        # GPT-4.1-mini pricing: $0.40/1M input, $1.60/1M output
        input_cost = (input_tokens / 1_000_000) * 0.40
        output_cost = (output_tokens / 1_000_000) * 1.60
        return input_cost + output_cost
    
    def _get_token_symbol(self, token_address: str) -> str:
        """根据合约地址识别常见 token"""
        if not token_address or not isinstance(token_address, str):
            return "tokens"
        
        # 常见的 token 地址（以太坊主网）
        KNOWN_TOKENS = {
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
            "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
            "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
            "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599": "WBTC",
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
            "0x514910771af9ca656af840dff83e8264ecf986ca": "LINK",
            "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": "UNI",
        }
        
        return KNOWN_TOKENS.get(token_address.lower(), "tokens")
    
    def _format_token_amount(self, amount: Any, token_symbol: str = "tokens") -> str:
        """根据 token 类型格式化金额"""
        try:
            amount_int = int(amount)
            
            # 根据 token 类型使用不同的小数位
            if token_symbol in ["USDC", "USDT"]:
                # 6位小数
                token_amount = amount_int / 10**6
                if token_amount >= 1:
                    return f"{token_amount:,.2f} {token_symbol}"
                else:
                    return f"{token_amount:.6f} {token_symbol}"
            elif token_symbol in ["WBTC"]:
                # 8位小数
                token_amount = amount_int / 10**8
                return f"{token_amount:.8f} {token_symbol}".rstrip('0').rstrip('.')
            elif token_symbol in ["DAI", "WETH", "LINK", "UNI"]:
                # 18位小数
                token_amount = amount_int / 10**18
                if token_amount >= 1:
                    return f"{token_amount:,.4f} {token_symbol}"
                else:
                    return f"{token_amount:.6f} {token_symbol}"
            else:
                # 默认显示为 units（无法确定小数位）
                if amount_int >= 1000:
                    return f"{amount_int:,} units"
                else:
                    return f"{amount_int} units"
        except:
            return str(amount)
    
    def _format_address(self, address: str) -> str:
        """格式化地址"""
        if not address or len(address) < 10:
            return address
        return f"{address[:6]}...{address[-4:]}"
    
    def _format_amount(self, amount: Any) -> str:
        """格式化金额，识别无限授权"""
        try:
            amount_int = int(amount)
            
            # 检测无限授权 (常见的无限授权值)
            # uint256 max: 2^256 - 1
            # 也检测常见的"近似无限"值，如 2^255, 2^128 等
            MAX_UINT256 = 2**256 - 1
            NEAR_MAX_THRESHOLD = MAX_UINT256 - 10**15  # 允许一些浮动
            
            # 常见的"无限授权"模式
            COMMON_UNLIMITED_VALUES = [
                MAX_UINT256,  # 完整的 uint256 最大值
                2**255 - 1,   # 一些协议使用的值
                2**128 - 1,   # 更保守的无限值
            ]
            
            # 检查是否为无限授权
            # 1. 检查是否接近 uint256 最大值
            if amount_int >= NEAR_MAX_THRESHOLD:
                return "UNLIMITED (infinite approval)"
            # 2. 检查是否是常见的无限授权值
            elif amount_int in COMMON_UNLIMITED_VALUES:
                return "UNLIMITED (infinite approval)"
            # 3. 任何超过 10^50 的值都视为"实质上的无限"（比所有可能的代币供应量都大）
            elif amount_int > 10**50:
                return "UNLIMITED (infinite approval)"
            # 4. 正常的代币金额
            elif amount_int >= 10**18:  # 18位小数 (ETH, DAI, etc.)
                eth_amount = amount_int / 10**18
                return f"{eth_amount:,.6f} tokens".rstrip('0').rstrip('.')
            elif amount_int >= 10**6:  # 6位小数 (USDC, USDT)
                token_amount = amount_int / 10**6
                if token_amount >= 1:
                    return f"{token_amount:,.2f} tokens"
                else:
                    return f"{token_amount:.6f} tokens"
            elif amount_int >= 1000:  # 大数字，添加千分位
                return f"{amount_int:,} units"
            else:
                return f"{amount_int} units"
        except:
            return str(amount)
    
    def _get_chain_name(self, chain_id: Any) -> str:
        """获取链名称"""
        try:
            chain_id_str = str(chain_id)
            chain_names = {
                "1": "Ethereum",
                "137": "Polygon",
                "56": "BSC",
                "42161": "Arbitrum",
                "10": "Optimism",
                "43114": "Avalanche",
                "250": "Fantom",
                "42220": "Celo"
            }
            return chain_names.get(chain_id_str, f"Chain {chain_id}")
        except:
            return str(chain_id)
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """格式化时间戳"""
        try:
            ts = int(timestamp)
            if ts > 1000000000:
                import datetime
                dt = datetime.datetime.fromtimestamp(ts)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
        return str(timestamp)
    
    def _generate_technical_details(self, params: Dict[str, Any]) -> str:
        """生成技术细节"""
        details = []
        for key, value in params.items():
            if value and key != "operation_type":
                details.append(f"{key.replace('_', ' ').title()}: {value}")
        return " | ".join(details[:5])  # 限制长度
    
    def _generate_context(self, params: Dict[str, Any]) -> str:
        """生成执行上下文"""
        app_name = params.get("app_name", "Unknown")
        chain_id = params.get("chain_id", "")
        
        chain_names = {
            "1": "Ethereum Mainnet",
            "137": "Polygon",
            "56": "BSC",
            "42161": "Arbitrum"
        }
        
        chain_name = chain_names.get(str(chain_id), f"Chain ID {chain_id}")
        return f"Executed on {chain_name} via {app_name}"
    
    def _assess_risk_level(self, params: Dict[str, Any]) -> tuple[str, str]:
        """使用GPT评估风险等级和解释"""
        try:
            # 构建风险评估提示词
            risk_prompt = self._build_risk_assessment_prompt(params)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a blockchain security expert. Identify the PRIMARY hidden risk with SPECIFIC details. Guidelines: PERMITS with UNLIMITED = HIGH ('Unlimited approval'); BRIDGE operations = MEDIUM ('Cross-chain transfer' or 'Irreversible bridge'); BRIDGE with large amount = HIGH ('Large irreversible transfer'); META-TX with callData = HIGH ('Hidden contract call' or 'Arbitrary execution'); META-TX with SUSPICIOUS address (0x9999...) = HIGH ('Suspicious relay address' or 'Phishing relay risk'); META-TX with value=0 + suspicious address = HIGH ('Unknown relay + Zero trap'); META-TX standard = MEDIUM ('Third-party relay'); MINTING = LOW ('NFT mint'). Use 2-6 words describing the ACTUAL danger, not generic warnings. Format: 'Risk: [Low/Medium/High] - [specific risk]'"
                    },
                    {
                        "role": "user",
                        "content": risk_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=20,
                timeout=10
            )
            
            risk_response = response.choices[0].message.content.strip()
            
            # 解析风险等级和解释
            if "Risk:" in risk_response and "-" in risk_response:
                parts = risk_response.split("Risk:", 1)[1].split("-", 1)
                if len(parts) == 2:
                    risk_level = parts[0].strip()
                    risk_explanation = parts[1].strip()
                    
                    # 验证风险等级
                    if risk_level in ["Low", "Medium", "High"]:
                        return risk_level, risk_explanation
            
            # 解析失败，使用默认值
            return "High", "Unlimited approval"
                
        except Exception as e:
            print(f"Risk assessment failed: {e}")
            return "Medium", "Check needed"
    
    def _build_risk_assessment_prompt(self, params: Dict[str, Any]) -> str:
        """构建风险评估提示词"""
        operation_type = params.get("operation_type", "unknown")
        app_name = params.get("app_name", "Unknown")
        
        prompt_parts = [f"Operation: {operation_type} in {app_name}"]
        
        # 根据操作类型添加特定风险考虑因素
        if operation_type == "permit":
            amount = params.get("amount", "unknown")
            deadline = params.get("deadline", "unknown")
            
            # 检查是否为无限授权
            is_unlimited = "UNLIMITED" in str(amount)
            
            # 计算deadline的具体时长
            duration_info = "unknown duration"
            try:
                if deadline != "unknown":
                    import datetime
                    deadline_timestamp = int(deadline)
                    current_time = datetime.datetime.now().timestamp()
                    time_diff = deadline_timestamp - current_time
                    days = int(time_diff / 86400)  # 转换为天数
                    
                    if days > 365:
                        years = days // 365
                        duration_info = f"{years} year{'s' if years > 1 else ''} valid"
                    elif days > 30:
                        months = days // 30
                        duration_info = f"{months} month{'s' if months > 1 else ''} valid"
                    elif days > 0:
                        duration_info = f"{days} day{'s' if days > 1 else ''} valid"
                    else:
                        duration_info = "already expired"
            except:
                duration_info = "unknown duration"
            
            prompt_parts.extend([
                f"Amount authorized: {amount}",
                f"Valid until: {deadline}",
                f"Duration: {duration_info}",
            ])
            
            if is_unlimited:
                prompt_parts.append("⚠️ WARNING: This is an UNLIMITED approval - extremely high risk!")
                prompt_parts.append("Consider: unlimited spending power, duration, spender trustworthiness")
            else:
                prompt_parts.append("Consider: amount size, duration, spender trustworthiness")
            
        elif operation_type == "order":
            prompt_parts.append("Consider: order value, marketplace reputation")
            
        elif operation_type == "vote":
            prompt_parts.append("Consider: governance impact, proposal importance")
            
        elif operation_type == "transfer":
            amount = params.get("amount", "unknown")
            prompt_parts.extend([
                f"Transfer amount: {amount}",
                "Consider: amount size, recipient verification"
            ])
        
        elif "mint" in operation_type or "voucher" in operation_type:
            # NFT mint 操作 - 通常是低风险
            prompt_parts.extend([
                "This is an NFT minting operation",
                "✅ Minting is typically LOW risk - user is creating/claiming NFTs",
                "Consider: minting cost, trusted contract"
            ])
        
        elif "bridge" in operation_type:
            # Bridge/跨链桥 操作 - 特定风险
            amount = params.get("amount", "unknown")
            dest_chain = params.get("destination_chain", "unknown")
            bridge_fee = params.get("bridge_fee", "unknown")
            token = params.get("token", "unknown")
            
            prompt_parts.extend([
                "This is a CROSS-CHAIN BRIDGE operation",
                f"Transferring {amount} to {dest_chain} chain",
                f"Token: {token}",
                f"Bridge fee: {bridge_fee}",
            ])
            
            # Bridge 特定风险分析（简化版）
            prompt_parts.extend([
                "\n⚠️ KEY BRIDGE RISKS:",
                "- Irreversible cross-chain transfer",
                "- Bridge contract trust required",
                "- Verify recipient address for target chain"
            ])
            
            # 评估金额大小
            try:
                amount_num = float(str(amount).replace(" USDC", "").replace(" tokens", "").replace(" units", "").replace(",", ""))
                if amount_num > 10000:  # 大额转账
                    prompt_parts.extend([
                        "\n⚠️ LARGE AMOUNT: Significant cross-chain transfer!",
                        "Risk level: MEDIUM-HIGH"
                    ])
                else:
                    prompt_parts.append("\n⚠️ Risk level: MEDIUM")
            except:
                prompt_parts.append("\n⚠️ Risk level: MEDIUM")
            
            prompt_parts.append("Risk explanation: Use ONLY 2-3 words like 'Cross-chain bridge' or 'Bridge transfer', DO NOT add extra warnings")
        
        elif "intent" in operation_type or "relay" in operation_type or "metatx" in operation_type:
            # Meta Transaction / Relay 操作 - 考虑隐藏风险维度
            has_calldata = params.get("has_calldata", False)
            calldata_length = params.get("calldata_length", 0)
            gas_fee = params.get("gas_fee", "unknown")
            value = params.get("value", "0")
            to_address = params.get("to", "unknown")
            
            prompt_parts.extend([
                "This is a META-TRANSACTION relay operation",
                f"User authorizes third party to submit transaction on their behalf",
                f"Gas fee: {gas_fee}",
                f"Transfer value: {value}",
                f"Target address: {to_address}",
            ])
            
            # 分析隐藏风险维度
            risk_factors = []
            
            if has_calldata and calldata_length > 0:
                # ① 隐式调用风险 (Hidden Call Risk)
                prompt_parts.extend([
                    f"⚠️ CRITICAL: Contains callData ({calldata_length} chars) - ARBITRARY contract execution!",
                    "⚠️ HIDDEN CALL RISK: callData can execute ANY operation:",
                    "  - Token approvals (unlimited spending authorization)",
                    "  - NFT transfers or approvals",
                    "  - Delegate permission settings", 
                    "  - Contract state changes",
                    "⚠️ This is HIGH risk even with value=0!"
                ])
                risk_factors.append("arbitrary execution")
            else:
                # 即使没有 callData，仍需警惕
                prompt_parts.append("⚠️ WARNING: Even with empty callData, value=0 can be misleading")
            
            # ② 恶意地址风险 (Phishing Target)
            is_suspicious_address = False
            if "9999" in to_address or "0000" in to_address or to_address == "unknown":
                prompt_parts.extend([
                    "⚠️ PHISHING RISK: Target address has SUSPICIOUS pattern (0x9999... or similar)",
                    "  - Likely attacker-controlled or test address",
                    "  - NOT a legitimate verified contract"
                ])
                risk_factors.append("suspicious address")
                is_suspicious_address = True
            
            # ③ 签名绑定风险 (Linked Authorization)
            prompt_parts.append("⚠️ LINKED SIGNATURE RISK: This signature may enable follow-up malicious transactions")
            
            # ④ 社会工程风险 (Trust Heuristic)
            is_zero_value_trap = False
            if value == "0" or value == "0 ETH":
                prompt_parts.extend([
                    "⚠️ SOCIAL ENGINEERING: Zero amount creates false sense of security!",
                    "  - Users think 'no money = no risk' but this is WRONG for meta-tx",
                    "  - callData or relay authorization can drain wallet even with value=0"
                ])
                risk_factors.append("zero-value deception")
                is_zero_value_trap = True
            
            # 综合风险评估 - 根据风险因素组合给出精准描述
            if has_calldata and calldata_length > 0:
                prompt_parts.append("\n⚠️ OVERALL: HIGH risk - Multiple hidden dangers, potential asset loss")
                if is_suspicious_address:
                    prompt_parts.append("Risk explanation: 'Hidden call + Suspicious address' or 'Arbitrary execution'")
                else:
                    prompt_parts.append("Risk explanation: 'Hidden contract call' or 'Arbitrary execution'")
            else:
                # 没有 callData 但仍有其他风险因素
                if is_suspicious_address and is_zero_value_trap:
                    prompt_parts.append("\n⚠️ OVERALL: HIGH risk - Suspicious address + Zero-value trap + Relay authorization")
                    prompt_parts.append("Risk explanation: 'Suspicious relay address' or 'Phishing relay risk' or 'Unknown relay + Zero trap'")
                elif is_suspicious_address:
                    prompt_parts.append("\n⚠️ OVERALL: HIGH risk - Suspicious address pattern detected")
                    prompt_parts.append("Risk explanation: 'Suspicious relay address' or 'Unverified relay'")
                elif is_zero_value_trap:
                    prompt_parts.append("\n⚠️ OVERALL: MEDIUM-HIGH risk - Zero-value deception with relay")
                    prompt_parts.append("Risk explanation: 'Zero-value relay trap' or 'Misleading authorization'")
                else:
                    prompt_parts.append("\n⚠️ OVERALL: MEDIUM risk - Standard third-party relay")
                    prompt_parts.append("Risk explanation: 'Third-party relay' or 'Relay authorization'")
        
        prompt_parts.append("Risk level (Low/Medium/High)?")
        return "\n".join(prompt_parts)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """获取成本统计"""
        return {
            "total_requests": self.request_count,
            "total_cost": round(self.total_cost, 6),
            "average_cost_per_request": round(self.total_cost / max(1, self.request_count), 6),
            "estimated_1000_requests": round((self.total_cost / max(1, self.request_count)) * 1000, 2)
        }

# 便捷函数
def create_openai_generator(api_key: str) -> OpenAINLPGenerator:
    """创建OpenAI NLP生成器"""
    return OpenAINLPGenerator(api_key)

# 集成到现有系统的包装函数
def generate_english_with_openai(eip712_data: Dict[str, Any], api_key: str) -> EnglishNLOutput:
    """单次生成英文描述"""
    generator = create_openai_generator(api_key)
    
    # 提取参数
    params = generator.extract_key_parameters(eip712_data)
    
    # 生成缓存键
    params_json = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_json.encode()).hexdigest()
    
    # 生成描述
    return generator.generate_english_description(params_hash, params_json) 