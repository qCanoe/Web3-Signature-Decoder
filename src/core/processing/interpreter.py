import os
import json
import datetime
from typing import Optional, Dict, Any, List
from ..input.definitions import IntermediateRepresentation, SignatureType
from .structure import SemanticStructure, SemanticComponent
from .knowledge_base import KnowledgeBase

# Optional: Import OpenAI if available
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

class Interpreter:
    """
    Interprets the Semantic Structure into human-readable text.
    Uses a hybrid approach: Templates -> LLM (optional).
    """
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.client = None
        if self.api_key and HAS_OPENAI:
            self.client = openai.OpenAI(api_key=self.api_key)

    def _load_api_key(self) -> Optional[str]:
        # Try environment variable first
        key = os.environ.get("OPENAI_API_KEY")
        if key: return key
        
        # Try file
        try:
            if os.path.exists("api_key.txt"):
                with open("api_key.txt", "r") as f:
                    content = f.read().strip()
                    if ":" in content:
                        return content.split(":", 1)[1].strip()
                    return content
        except Exception:
            pass
        return None

    def interpret(self, structure: SemanticStructure, ir: Optional[IntermediateRepresentation] = None) -> str:
        """
        Interprets the semantic structure and enriches it with additional semantic information.
        This corresponds to interpret_frame() in the framework.
        
        Args:
            structure: Semantic structure to interpret
            ir: Optional IntermediateRepresentation for additional context
            
        Returns:
            Natural language summary string
        """
        # Enrich structure with semantic information
        self._enrich_structure(structure, ir)
        
        # 1. Try Template
        summary = self._template_interpret(structure)
        if summary:
            return summary
            
        # 2. Try LLM
        if self.client:
            return self._llm_interpret(structure)

        # 3. Fallback
        action_desc = structure.action.description
        if action_desc == "Unknown Action" and structure.action.raw_value:
             action_desc = structure.action.raw_value.replace("_", " ").title()
        elif action_desc == "Unknown Action":
             action_desc = "an operation"
            
        return f"You are performing {action_desc} on {structure.target_object.description}."
    
    def _enrich_structure(self, structure: SemanticStructure, ir: Optional[IntermediateRepresentation] = None):
        """
        Enrich semantic structure with contract_role, permission_scope, and hidden_implications.
        This implements the interpret_frame() functionality from the framework.
        """
        if not ir:
            return
        
        # 1. Identify contract_role
        structure.contract_role = self._lookup_contract_role(structure, ir)
        
        # 2. Infer permission_scope
        structure.permission_scope = self._infer_permission_level(structure, ir)
        
        # 3. Detect hidden_implications
        structure.hidden_implications = self._detect_risk_patterns(structure, ir)
    
    def _lookup_contract_role(self, structure: SemanticStructure, ir: IntermediateRepresentation) -> Optional[str]:
        """
        Identify the role of the contract (DEX, Lending, NFT Marketplace, etc.)
        Corresponds to lookup_contract_role() in the framework.
        """
        contract_address = ir.contract
        chain_id = ir.chain_id
        
        if contract_address and chain_id:
            # Check known contracts
            contract_name = KnowledgeBase.get_contract_name(chain_id, contract_address)
            if contract_name:
                contract_lower = contract_name.lower()
                if any(x in contract_lower for x in ["router", "swap", "dex", "uniswap", "sushiswap", "1inch"]):
                    return "DEX"
                elif any(x in contract_lower for x in ["aave", "compound", "lending", "pool"]):
                    return "Lending"
                elif any(x in contract_lower for x in ["seaport", "opensea", "blur", "marketplace", "nft"]):
                    return "NFT Marketplace"
                elif any(x in contract_lower for x in ["governance", "vote", "dao"]):
                    return "Governance"
                elif any(x in contract_lower for x in ["bridge", "wormhole", "multichain"]):
                    return "Bridge"
                elif "permit" in contract_lower or "permit2" in contract_lower:
                    return "Authorization"
        
        # Check domain name for protocol type
        domain = ir.metadata.get("domain", {})
        domain_name = domain.get("name", "")
        if domain_name:
            protocol_type = KnowledgeBase.identify_protocol_type(domain_name, contract_address, chain_id)
            if protocol_type:
                type_map = {
                    "nft_marketplace": "NFT Marketplace",
                    "defi": "DeFi Protocol",
                    "governance": "Governance",
                    "bridge": "Bridge",
                    "lending": "Lending",
                    "staking": "Staking",
                }
                return type_map.get(protocol_type, protocol_type.replace("_", " ").title())
        
        # Check action type for hints
        action_type = structure.action.raw_value
        if action_type:
            if "swap" in action_type or "trade" in action_type:
                return "DEX"
            elif "approve" in action_type or "permit" in action_type:
                return "Authorization"
            elif "vote" in action_type or "governance" in action_type:
                return "Governance"
            elif "marketplace" in action_type or "listing" in action_type:
                return "NFT Marketplace"
        
        return None
    
    def _infer_permission_level(self, structure: SemanticStructure, ir: IntermediateRepresentation) -> Optional[str]:
        """
        Infer the scope of permissions being granted.
        Corresponds to infer_permission_level() in the framework.
        Returns more granular permission levels.
        """
        action_type = structure.action.raw_value
        
        # Check for infinite approval
        is_infinite = False
        for ctx in structure.context:
            if "Infinite" in ctx.description or ctx.risk_factor == "high":
                amount = ctx.raw_value
                if KnowledgeBase.is_infinite_allowance(amount):
                    is_infinite = True
                    break
        
        # Check amount values
        amount_values = [c.raw_value for c in structure.context if "Amount" in c.description or "value" in c.description.lower()]
        for amount in amount_values:
            if KnowledgeBase.is_infinite_allowance(amount):
                is_infinite = True
                break
        
        # Check for time-limited permissions
        has_deadline = False
        deadline_value = None
        for ctx in structure.context:
            if "deadline" in ctx.description.lower() or "expiry" in ctx.description.lower():
                has_deadline = True
                deadline_value = ctx.raw_value
                break
        
        # Check if deadline is far in the future or permanent
        is_permanent = True
        if has_deadline and deadline_value:
            try:
                deadline_int = int(deadline_value)
                import time
                current_time = int(time.time())
                # If deadline is more than 1 year away, consider it effectively permanent
                if deadline_int > current_time + 31536000:  # 1 year
                    is_permanent = True
                elif deadline_int > current_time:
                    is_permanent = False
            except:
                pass
        
        # Check for single-use patterns (nonce-based)
        has_nonce = any("nonce" in c.description.lower() for c in structure.context)
        if has_nonce and action_type in ["authorization", "permit"]:
            return "single_use"
        
        # Determine granular permission level
        if is_infinite:
            if is_permanent or not has_deadline:
                return "unlimited_permanent"
            else:
                return "unlimited_time_limited"
        else:
            if is_permanent or not has_deadline:
                return "specific_amount_permanent"
            else:
                return "specific_amount_time_limited"
        
        # Check for specific amount
        if amount_values:
            return "specific_amount"
        
        # Default based on action type
        if action_type == "approve":
            return "specific_amount"  # Default to specific unless proven otherwise
        elif action_type == "authentication":
            return "session_based"
        elif action_type == "authorization":
            return "time_limited" if has_deadline else "specific_amount_permanent"
        
        return None
    
    def _detect_risk_patterns(self, structure: SemanticStructure, ir: IntermediateRepresentation) -> List[str]:
        """
        Detect hidden implications and risk patterns.
        Corresponds to detect_risk_patterns() in the framework.
        Enhanced with more sophisticated pattern detection.
        """
        implications = []
        
        # 1. Check for infinite approval
        for ctx in structure.context:
            if "Infinite" in ctx.description:
                implications.append("Unlimited spending permission - contract can spend all tokens without further approval")
                break
        
        # 2. Check for high-value transfers
        for ctx in structure.context:
            if "Amount" in ctx.description:
                try:
                    amount_val = float(ctx.raw_value)
                    if amount_val > 1e18:  # Roughly 1 ETH or equivalent
                        implications.append(f"High value operation: {amount_val / 1e18:.2f} ETH equivalent")
                except:
                    pass
        
        # 3. Check for irreversible actions
        if structure.action.raw_value == "transfer_asset":
            implications.append("Irreversible transfer - assets will be moved permanently")
        
        # 4. Check for cross-chain operations
        for ctx in structure.context:
            if "Destination Chain" in ctx.description or "targetChain" in ctx.description.lower():
                implications.append("Cross-chain operation - assets will move to different network")
        
        # 5. Check for delegation patterns
        if "delegate" in structure.action.raw_value.lower() or "delegation" in structure.action.raw_value.lower():
            implications.append("Voting power delegation - delegate can vote on your behalf")
        
        # 6. Check for implicit delegation (through permit)
        if structure.action.raw_value == "authorization" and structure.permission_scope == "unlimited_permanent":
            implications.append("Implicit delegation - permit grants unlimited permanent access, can be used for on-chain actions")
        
        # 7. Check for cross-contract operations
        if structure.action.raw_value == "cross_contract_interaction":
            implications.append("Cross-contract operation - involves multiple contracts, verify all interactions")
        
        # 8. Check for long-term permissions
        if structure.permission_scope in ["unlimited_permanent", "specific_amount_permanent"]:
            implications.append("Permanent permission - no expiration date, requires manual revocation")
        
        # 9. Check for unknown contracts
        if ir.contract and not KnowledgeBase.get_contract_name(ir.chain_id, ir.contract):
            implications.append("Unknown contract - verify contract address before proceeding")
        
        # 10. Check for eth_sign (blind signing)
        if ir.signature_type == SignatureType.ETH_SIGN:
            implications.append("Blind signing - signing raw hash without seeing content")
        
        # 11. Check for suspicious patterns in personal sign messages
        if ir.signature_type == SignatureType.PERSONAL_SIGN:
            message = str(ir.params.get("message", "")).lower()
            suspicious_keywords = ["urgent", "immediately", "verify", "claim", "reward"]
            if any(kw in message for kw in suspicious_keywords):
                implications.append("Suspicious message content - may be phishing attempt")
        
        # 12. Check for bridge operations (cross-chain risk)
        if structure.action.raw_value in ["bridge", "bridge_lock", "bridge_unlock", "bridge_redeem"]:
            implications.append("Bridge operation - assets will be locked/unlocked on different chains")
        
        # 13. Check for router/aggregator patterns (indirect operations)
        contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract or "")
        if contract_name and ("router" in contract_name.lower() or "aggregator" in contract_name.lower()):
            if structure.action.raw_value == "defi_swap":
                implications.append("Router contract - may execute multiple operations across different contracts")
        
        return implications

    def _template_interpret(self, structure: SemanticStructure) -> Optional[str]:
        actor = structure.actor.description
        action = structure.action.description
        obj = structure.target_object.description
        
        # Extract context values for cleaner templates
        ctx_map = {c.description: c.raw_value for c in structure.context}
        
        if structure.action.raw_value == "approve":
            amount = next((c.raw_value for c in structure.context if "Amount" in c.description or "Infinite" in c.description), "tokens")
            spender = next((c.raw_value for c in structure.context if c.role == "Spender" or c.description == "Spender"), "contract")
            if "Infinite" in str(amount) or KnowledgeBase.is_infinite_allowance(amount):
                return f"You are authorizing {spender} to spend unlimited {obj} tokens on your behalf."
            return f"You are authorizing {spender} to spend {amount} of your {obj}."

        if structure.action.raw_value == "transfer_asset":
            amount = next((c.raw_value for c in structure.context if "Amount" in c.description or "Native" in c.description), "assets")
            return f"You are transferring {amount} to {obj}."
            
        if structure.action.raw_value == "authentication":
            return f"You are signing into {obj}. This does not move funds."
            
        if structure.action.raw_value == "marketplace_listing":
            return f"You are listing items for sale on {obj}."
        
        if structure.action.raw_value in ["authorization", "permit"]:
            spender = next((c.raw_value for c in structure.context if c.role == "Spender" or c.description == "Spender"), None)
            amount = next((c.raw_value for c in structure.context if "Amount" in c.description or "value" in c.description.lower()), None)
            deadline = next((c.raw_value for c in structure.context if "Deadline" in c.description or "Expiry" in c.description), None)
            
            parts = []
            parts.append("You are authorizing")
            
            if spender:
                spender_ctx = next((c for c in structure.context if c.role == "Spender" or c.description == "Spender"), None)
                if spender_ctx and spender_ctx.description and spender_ctx.description != "Spender":
                    parts.append(f"{spender_ctx.description}")
                else:
                    parts.append(f"contract {str(spender)[:6]}...{str(spender)[-4:]}")
            else:
                parts.append("a contract")
                
            if amount:
                if KnowledgeBase.is_infinite_allowance(amount) or "Infinite" in str(amount):
                    parts.append(f"to spend unlimited {obj}")
                else:
                    parts.append(f"to spend {amount} {obj}")
            else:
                parts.append(f"to access your {obj}")
            
            if deadline:
                try:
                    ts = int(deadline)
                    dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                    parts.append(f"until {dt}")
                except:
                    parts.append("with a specific deadline")
            
            return " ".join(parts) + "."
        
        if structure.action.raw_value in ["bridge", "bridge_lock"]:
            dest_chain = next((c.raw_value for c in structure.context if "Destination Chain" in c.description or "targetChain" in c.description.lower()), None)
            if dest_chain:
                return f"You are locking assets on {obj} to bridge to chain {dest_chain}."
            return f"You are locking assets on {obj} bridge."
        
        if structure.action.raw_value in ["bridge_unlock", "bridge_redeem"]:
            return f"You are unlocking/redeeming assets from {obj} bridge."
        
        if structure.action.raw_value == "governance_delegation":
            delegatee = next((c.raw_value for c in structure.context if "delegate" in c.description.lower() or "delegatee" in c.description.lower()), "delegate")
            return f"You are delegating voting power to {delegatee} for {obj}."
        
        if structure.action.raw_value == "cross_contract_interaction":
            return f"You are performing a complex operation through {obj} that may involve multiple contracts."
        
        if structure.action.raw_value == "defi_swap":
            amount_in = next((c.raw_value for c in structure.context if "Input Amount" in c.description or "amountIn" in c.description.lower()), None)
            if amount_in:
                return f"You are swapping {amount_in} through {obj}."
            return f"You are performing a swap through {obj}."

        return None

    def _llm_interpret(self, structure: SemanticStructure) -> str:
        if not self.client:
            return "LLM unavailable."

        # Build prompt context
        context_str = "\n".join([f"- {c.description}: {c.raw_value}" for c in structure.context])
        prompt = f"""
        Explain this blockchain transaction to a non-technical user in 1-2 simple sentences.
        
        Actor: {structure.actor.description} ({structure.actor.raw_value})
        Action: {structure.action.description}
        Target: {structure.target_object.description} ({structure.target_object.raw_value})
        Context:
        {context_str}
        
        Focus on the consequences (e.g., "You are giving X access to Y").
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini", # or appropriate model
                messages=[
                    {"role": "system", "content": "You are a helpful security assistant explaining crypto transactions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"Perform {structure.action.description} on {structure.target_object.description}."

