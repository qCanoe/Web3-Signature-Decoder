"""
OpenAI GPT-4.1-mini integrated NLP generator
English natural language generation based on parameter extraction
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
    """English natural language output result"""
    title: str
    summary: str
    detailed_description: str
    technical_details: str
    context: str
    risk_level: str
    risk_explanation: str

class OpenAINLPGenerator:
    """English NLP generator based on OpenAI GPT-4.1-mini"""
    
    def __init__(self, api_key: str):
        """Initialize OpenAI client"""
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4-1106-preview"  # GPT-4.1-mini
        
        # Cost tracking
        self.total_cost = 0.0
        self.request_count = 0
    
    def extract_key_parameters(self, eip712_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key parameters from EIP712 data"""
        primary_type = eip712_data.get("primaryType", "")
        domain = eip712_data.get("domain", {})
        message = eip712_data.get("message", {})
        
        # Extract core information
        extracted = {
            "operation_type": primary_type.lower(),
            "app_name": domain.get("name", "Unknown App"),
            "version": domain.get("version", ""),
            "chain_id": domain.get("chainId", ""),
            "contract": domain.get("verifyingContract", "")[:10] + "..." if domain.get("verifyingContract") else "",
        }
        
        # Extract specific fields based on operation type
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
            # NFT mint operation
            extracted.update({
                "recipient": self._format_address(message.get("to", message.get("recipient", message.get("redeemer", "")))),
                "token_id": message.get("tokenId", message.get("minPrice", "")),
                "amount": message.get("amount", "1")
            })
        elif "bridge" in primary_type.lower() or "destinationchainid" in str(message).lower():
            # Bridge/Cross-chain bridge operation
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
            # Meta Transaction / Relay operation
            extracted.update({
                "from": self._format_address(message.get("from", "")),
                "to": self._format_address(message.get("to", "")),
                "value": self._format_amount(message.get("value", 0)),
                "has_calldata": bool(message.get("callData") or message.get("data")),
                "calldata_length": len(str(message.get("callData", message.get("data", "0x")))) - 2,  # Remove 0x prefix
                "gas_fee": self._format_amount(message.get("gasFee", message.get("fee", 0))),
                "deadline": self._format_timestamp(message.get("deadline", 0)),
                "note": message.get("note", "")[:50] + "..." if len(message.get("note", "")) > 50 else message.get("note", "")
            })
        
        return extracted
    
    @lru_cache(maxsize=50)
    def generate_english_description(self, params_hash: str, params_json: str) -> EnglishNLOutput:
        """Generate English description (with cache)"""
        params = json.loads(params_json)
        
        # Build concise prompt
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
                max_tokens=100,  # Increased to 100 to avoid truncation
                timeout=15
            )
            
            # Calculate cost
            usage = response.usage
            cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)
            self.total_cost += cost
            self.request_count += 1
            
            response_time = time.time() - start_time
            print(f"✅ OpenAI API call completed in {response_time:.2f}s, Cost: {cost:.6f}")
            
            # Parse response
            return self._parse_response(response.choices[0].message.content, params)
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            # Fallback to template generation
            return self._fallback_template_generation(params)
    
    def _build_prompt(self, params: Dict[str, Any]) -> str:
        """Build optimized prompt"""
        operation_type = params.get("operation_type", "operation")
        app_name = params.get("app_name", "Unknown")
        
        # Build concise core information
        if operation_type == "permit":
            amount = params.get("amount", "tokens")
            deadline = params.get("deadline", "")
            
            # Format deadline information
            deadline_text = ""
            if deadline:
                try:
                    import datetime
                    deadline_timestamp = int(deadline)
                    deadline_date = datetime.datetime.fromtimestamp(deadline_timestamp)
                    deadline_text = f" until {deadline_date.strftime('%Y-%m-%d')}"
                except:
                    deadline_text = f" until deadline {deadline}"
            
            # Special handling for unlimited approval
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
            
            # Detect suspicious address
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
        """Parse GPT response into structured output"""
        operation_type = params.get("operation_type", "operation")
        app_name = params.get("app_name", "Unknown App")
        
        # Generate title
        title = f"{app_name} - {operation_type.title()} Operation"
        
        # Use GPT response as main description
        description = response_text.strip()
        
        # Generate technical details
        tech_details = self._generate_technical_details(params)
        
        # Generate context
        context = self._generate_context(params)
        
        # Assess risk level and explanation
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
        """Template generation when API fails"""
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
        """Calculate API call cost"""
        # GPT-4.1-mini pricing: $0.40/1M input, $1.60/1M output
        input_cost = (input_tokens / 1_000_000) * 0.40
        output_cost = (output_tokens / 1_000_000) * 1.60
        return input_cost + output_cost
    
    def _get_token_symbol(self, token_address: str) -> str:
        """Identify common token by contract address"""
        if not token_address or not isinstance(token_address, str):
            return "tokens"
        
        # Common token addresses (Ethereum mainnet)
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
        """Format amount by token type"""
        try:
            amount_int = int(amount)
            
            # Use different decimal places based on token type
            if token_symbol in ["USDC", "USDT"]:
                # 6 decimal places
                token_amount = amount_int / 10**6
                if token_amount >= 1:
                    return f"{token_amount:,.2f} {token_symbol}"
                else:
                    return f"{token_amount:.6f} {token_symbol}"
            elif token_symbol in ["WBTC"]:
                # 8 decimal places
                token_amount = amount_int / 10**8
                return f"{token_amount:.8f} {token_symbol}".rstrip('0').rstrip('.')
            elif token_symbol in ["DAI", "WETH", "LINK", "UNI"]:
                # 18 decimal places
                token_amount = amount_int / 10**18
                if token_amount >= 1:
                    return f"{token_amount:,.4f} {token_symbol}"
                else:
                    return f"{token_amount:.6f} {token_symbol}"
            else:
                # Default display as units (unable to determine decimal places)
                if amount_int >= 1000:
                    return f"{amount_int:,} units"
                else:
                    return f"{amount_int} units"
        except:
            return str(amount)
    
    def _format_address(self, address: str) -> str:
        """Format address"""
        if not address or len(address) < 10:
            return address
        return f"{address[:6]}...{address[-4:]}"
    
    def _format_amount(self, amount: Any) -> str:
        """Format amount, detect unlimited approval"""
        try:
            amount_int = int(amount)
            
            # Detect unlimited approval (common unlimited approval values)
            # uint256 max: 2^256 - 1
            # Also detect common "near infinite" values like 2^255, 2^128, etc.
            MAX_UINT256 = 2**256 - 1
            NEAR_MAX_THRESHOLD = MAX_UINT256 - 10**15  # Allow some floating
            
            # Common "unlimited approval" patterns
            COMMON_UNLIMITED_VALUES = [
                MAX_UINT256,  # Full uint256 maximum value
                2**255 - 1,   # Values used by some protocols
                2**128 - 1,   # More conservative infinite value
            ]
            
            # Check if unlimited approval
            # 1. Check if close to uint256 maximum
            if amount_int >= NEAR_MAX_THRESHOLD:
                return "UNLIMITED (infinite approval)"
            # 2. Check if common unlimited approval value
            elif amount_int in COMMON_UNLIMITED_VALUES:
                return "UNLIMITED (infinite approval)"
            # 3. Any value over 10^50 is considered "effectively infinite" (larger than all possible token supplies)
            elif amount_int > 10**50:
                return "UNLIMITED (infinite approval)"
            # 4. Normal token amount
            elif amount_int >= 10**18:  # 18 decimal places (ETH, DAI, etc.)
                eth_amount = amount_int / 10**18
                return f"{eth_amount:,.6f} tokens".rstrip('0').rstrip('.')
            elif amount_int >= 10**6:  # 6 decimal places (USDC, USDT)
                token_amount = amount_int / 10**6
                if token_amount >= 1:
                    return f"{token_amount:,.2f} tokens"
                else:
                    return f"{token_amount:.6f} tokens"
            elif amount_int >= 1000:  # Large numbers, add thousand separators
                return f"{amount_int:,} units"
            else:
                return f"{amount_int} units"
        except:
            return str(amount)
    
    def _get_chain_name(self, chain_id: Any) -> str:
        """Get chain name"""
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
        """Format timestamp"""
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
        """Generate technical details"""
        details = []
        for key, value in params.items():
            if value and key != "operation_type":
                details.append(f"{key.replace('_', ' ').title()}: {value}")
        return " | ".join(details[:5])  # Limit length
    
    def _generate_context(self, params: Dict[str, Any]) -> str:
        """Generate execution context"""
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
        """Assess risk level and explanation using GPT"""
        try:
            # Build risk assessment prompt
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
            
            # Parse risk level and explanation
            if "Risk:" in risk_response and "-" in risk_response:
                parts = risk_response.split("Risk:", 1)[1].split("-", 1)
                if len(parts) == 2:
                    risk_level = parts[0].strip()
                    risk_explanation = parts[1].strip()
                    
                    # Validate risk level
                    if risk_level in ["Low", "Medium", "High"]:
                        return risk_level, risk_explanation
            
            # Parsing failed, use default values
            return "High", "Unlimited approval"
                
        except Exception as e:
            print(f"Risk assessment failed: {e}")
            return "Medium", "Check needed"
    
    def _build_risk_assessment_prompt(self, params: Dict[str, Any]) -> str:
        """Build risk assessment prompt"""
        operation_type = params.get("operation_type", "unknown")
        app_name = params.get("app_name", "Unknown")
        
        prompt_parts = [f"Operation: {operation_type} in {app_name}"]
        
        # Add specific risk considerations based on operation type
        if operation_type == "permit":
            amount = params.get("amount", "unknown")
            deadline = params.get("deadline", "unknown")
            
            # Check if unlimited approval
            is_unlimited = "UNLIMITED" in str(amount)
            
            # Calculate specific duration of deadline
            duration_info = "unknown duration"
            try:
                if deadline != "unknown":
                    import datetime
                    deadline_timestamp = int(deadline)
                    current_time = datetime.datetime.now().timestamp()
                    time_diff = deadline_timestamp - current_time
                    days = int(time_diff / 86400)  # Convert to days
                    
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
            # NFT mint operation - usually low risk
            prompt_parts.extend([
                "This is an NFT minting operation",
                "✅ Minting is typically LOW risk - user is creating/claiming NFTs",
                "Consider: minting cost, trusted contract"
            ])
        
        elif "bridge" in operation_type:
            # Bridge/Cross-chain bridge operation - specific risks
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
            
            # Bridge-specific risk analysis (simplified)
            prompt_parts.extend([
                "\n⚠️ KEY BRIDGE RISKS:",
                "- Irreversible cross-chain transfer",
                "- Bridge contract trust required",
                "- Verify recipient address for target chain"
            ])
            
            # Evaluate amount size
            try:
                amount_num = float(str(amount).replace(" USDC", "").replace(" tokens", "").replace(" units", "").replace(",", ""))
                if amount_num > 10000:  # Large transfer
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
            # Meta Transaction / Relay operation - consider hidden risk dimensions
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
            
            # Analyze hidden risk dimensions
            risk_factors = []
            
            if has_calldata and calldata_length > 0:
                # ① Hidden Call Risk
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
                # Even without callData, still be vigilant
                prompt_parts.append("⚠️ WARNING: Even with empty callData, value=0 can be misleading")
            
            # ② Phishing Target Risk
            is_suspicious_address = False
            if "9999" in to_address or "0000" in to_address or to_address == "unknown":
                prompt_parts.extend([
                    "⚠️ PHISHING RISK: Target address has SUSPICIOUS pattern (0x9999... or similar)",
                    "  - Likely attacker-controlled or test address",
                    "  - NOT a legitimate verified contract"
                ])
                risk_factors.append("suspicious address")
                is_suspicious_address = True
            
            # ③ Linked Authorization Risk
            prompt_parts.append("⚠️ LINKED SIGNATURE RISK: This signature may enable follow-up malicious transactions")
            
            # ④ Social Engineering Risk (Trust Heuristic)
            is_zero_value_trap = False
            if value == "0" or value == "0 ETH":
                prompt_parts.extend([
                    "⚠️ SOCIAL ENGINEERING: Zero amount creates false sense of security!",
                    "  - Users think 'no money = no risk' but this is WRONG for meta-tx",
                    "  - callData or relay authorization can drain wallet even with value=0"
                ])
                risk_factors.append("zero-value deception")
                is_zero_value_trap = True
            
            # Comprehensive risk assessment - provide precise description based on risk factor combination
            if has_calldata and calldata_length > 0:
                prompt_parts.append("\n⚠️ OVERALL: HIGH risk - Multiple hidden dangers, potential asset loss")
                if is_suspicious_address:
                    prompt_parts.append("Risk explanation: 'Hidden call + Suspicious address' or 'Arbitrary execution'")
                else:
                    prompt_parts.append("Risk explanation: 'Hidden contract call' or 'Arbitrary execution'")
            else:
                # No callData but still has other risk factors
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
        """Get cost statistics"""
        return {
            "total_requests": self.request_count,
            "total_cost": round(self.total_cost, 6),
            "average_cost_per_request": round(self.total_cost / max(1, self.request_count), 6),
            "estimated_1000_requests": round((self.total_cost / max(1, self.request_count)) * 1000, 2)
        }

# Convenience functions
def create_openai_generator(api_key: str) -> OpenAINLPGenerator:
    """Create OpenAI NLP generator"""
    return OpenAINLPGenerator(api_key)

# Wrapper function for integration into existing system
def generate_english_with_openai(eip712_data: Dict[str, Any], api_key: str) -> EnglishNLOutput:
    """Generate English description in one call"""
    generator = create_openai_generator(api_key)
    
    # Extract parameters
    params = generator.extract_key_parameters(eip712_data)
    
    # Generate cache key
    params_json = json.dumps(params, sort_keys=True)
    params_hash = hashlib.md5(params_json.encode()).hexdigest()
    
    # Generate description
    return generator.generate_english_description(params_hash, params_json) 