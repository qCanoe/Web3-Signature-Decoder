import os
import json
import datetime
from typing import Optional, Dict, Any, List
from ..input.definitions import IntermediateRepresentation, SignatureType
from .structure import SemanticStructure, SemanticComponent
from .knowledge_base import KnowledgeBase
from ..utils.logger import Logger

# Optional: Import OpenAI if available
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = Logger.get_logger(__name__)

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
        except Exception as error:
            logger.debug(f"Failed to load OpenAI API key: {error}")
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
        
        # By default, no deadline implies effectively permanent
        is_permanent = not has_deadline
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
                else:
                    # Expired deadline should not be treated as permanent
                    is_permanent = False
            except Exception as error:
                logger.debug(f"Failed to parse deadline value: {error}")
        
        # Check for single-use patterns (nonce-based)
        has_nonce = any("nonce" in c.description.lower() for c in structure.context)
        if has_nonce and action_type in ["authorization", "permit"]:
            return "single_use"
        
        # Determine granular permission level
        if is_infinite:
            if is_permanent or not has_deadline:
                return "unlimited_permanent"
            return "unlimited_time_limited"
        
        if amount_values:
            if is_permanent or not has_deadline:
                return "specific_amount_permanent"
            return "specific_amount_time_limited"
        
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
                except Exception as error:
                    logger.debug(f"Failed to parse amount value: {error}")
        
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
        
        # Helper to get context value
        def get_ctx(keywords, default=None):
            for c in structure.context:
                desc_lower = c.description.lower()
                if any(kw.lower() in desc_lower for kw in keywords):
                    return c.raw_value
            return default
        
        def format_address(addr):
            if isinstance(addr, str) and len(addr) == 42:
                return f"{addr[:6]}...{addr[-4:]}"
            return str(addr)
        
        # ========== Token Approvals ==========
        if structure.action.raw_value == "approve":
            amount = get_ctx(["Amount", "Infinite"], "tokens")
            spender = get_ctx(["Spender"], "contract")
            if "Infinite" in str(amount) or KnowledgeBase.is_infinite_allowance(amount):
                return f"You are authorizing {format_address(spender)} to spend unlimited {obj} tokens on your behalf."
            return f"You are authorizing {format_address(spender)} to spend {amount} of your {obj}."

        # ========== NFT Approvals ==========
        if structure.action.raw_value in ["nft_approve", "nft_approval"]:
            operator = get_ctx(["Operator", "Spender"], "contract")
            return f"You are granting {format_address(operator)} permission to manage ALL your NFTs in the {obj} collection. This allows transfers without further approval."
        
        # ========== Transfers ==========
        if structure.action.raw_value == "transfer_asset":
            amount = get_ctx(["Amount", "Native", "Token Amount"], "assets")
            recipient = get_ctx(["Recipient", "To"], obj)
            return f"You are transferring {amount} to {format_address(recipient)}. This action is irreversible."
        
        if structure.action.raw_value == "nft_transfer":
            token_id = get_ctx(["TokenId", "Token ID", "Id"], "NFT")
            recipient = get_ctx(["Recipient", "To"], obj)
            return f"You are transferring NFT #{token_id} to {format_address(recipient)}."
            
        # ========== Authentication ==========
        if structure.action.raw_value == "sign_in_with_ethereum":
            statement = get_ctx(["Statement"], None)
            nonce = get_ctx(["Nonce"], None)
            issued_at = get_ctx(["Issued At"], None)
            expiration = get_ctx(["Expiration Time"], None)
            parts = [
                f"You are signing in to {obj} with your wallet. This is a login signature (SIWE) and does not authorize token transfers."
            ]
            details = []
            if nonce:
                details.append(f"nonce {nonce}")
            if issued_at:
                details.append(f"issued {issued_at}")
            if expiration:
                details.append(f"expires {expiration}")
            if details:
                parts.append("Session details: " + ", ".join(details) + ".")
            if statement:
                parts.append(f"Statement: {statement}.")
            return " ".join(parts)

        if structure.action.raw_value == "authentication":
            return f"You are signing into {obj}. This signature proves you own this wallet and does not authorize any token transfers."
        
        if structure.action.raw_value == "sign_message":
            return f"You are signing a message for {obj}. Review the message content carefully."
        
        if structure.action.raw_value == "sign_hash":
            return f"You are signing a raw hash. This is high risk - ensure you trust the source."
        
        # ========== NFT Marketplace ==========
        if structure.action.raw_value == "marketplace_listing":
            price = get_ctx(["Price", "Amount"], "specified price")
            return f"You are listing items for sale on {obj} marketplace at {price}."
        
        if structure.action.raw_value == "nft_trade":
            return f"You are executing an NFT trade through {obj} marketplace."
        
        # ========== Permits (EIP-2612, Permit2) ==========
        if structure.action.raw_value in ["authorization", "permit"]:
            spender = get_ctx(["Spender"], None)
            amount = get_ctx(["Amount", "Value"], None)
            deadline = get_ctx(["Deadline", "Expiry"], None)
            
            parts = ["You are authorizing"]
            
            if spender:
                parts.append(format_address(spender))
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
                    dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                    parts.append(f"until {dt}")
                except:
                    parts.append("with a time limit")
            
            return " ".join(parts) + ". This is an off-chain signature that can be used on-chain."
        
        # ========== Bridge Operations ==========
        if structure.action.raw_value in ["bridge", "bridge_lock"]:
            dest_chain = get_ctx(["Destination Chain", "Target Chain"], None)
            amount = get_ctx(["Amount"], "assets")
            if dest_chain:
                chain_name = KnowledgeBase.get_chain_name(int(dest_chain)) if str(dest_chain).isdigit() else dest_chain
                return f"You are bridging {amount} to {chain_name} via {obj}. Assets will be locked until bridging completes."
            return f"You are locking assets on {obj} bridge for cross-chain transfer."
        
        if structure.action.raw_value in ["bridge_unlock", "bridge_redeem"]:
            amount = get_ctx(["Amount"], "assets")
            return f"You are claiming {amount} from {obj} bridge after cross-chain transfer."
        
        # ========== Governance ==========
        if structure.action.raw_value == "governance_delegation":
            delegatee = get_ctx(["Delegate", "Delegatee"], "delegate")
            return f"You are delegating your voting power to {format_address(delegatee)}. They can vote on your behalf in {obj} governance."
        
        if structure.action.raw_value == "governance":
            proposal_id = get_ctx(["Proposal", "ProposalId"], "")
            vote = get_ctx(["Vote", "Support"], "")
            vote_text = "in favor" if str(vote) == "1" else "against" if str(vote) == "0" else ""
            if proposal_id:
                return f"You are voting {vote_text} on proposal #{proposal_id} in {obj} governance."
            return f"You are participating in {obj} governance."
        
        # ========== DeFi Swaps ==========
        if structure.action.raw_value == "defi_swap":
            amount_in = get_ctx(["Input Amount", "AmountIn"], None)
            amount_out_min = get_ctx(["Minimum Output", "AmountOutMin"], None)
            if amount_in and amount_out_min:
                return f"You are swapping {amount_in} through {obj} for at least {amount_out_min} output."
            elif amount_in:
                return f"You are swapping {amount_in} through {obj}."
            return f"You are performing a token swap through {obj}."
        
        if structure.action.raw_value == "batch_swap":
            batch_summary = get_ctx(["Batch Summary", "Universal Router Summary"], None)
            if batch_summary:
                return f"You are performing a batch of swaps through {obj}. Multiple tokens will be exchanged. {batch_summary}."
            return f"You are performing a batch of swaps through {obj}. Multiple tokens will be exchanged."
        
        # ========== DeFi Lending ==========
        if structure.action.raw_value == "defi_supply":
            amount = get_ctx(["Amount"], "assets")
            return f"You are supplying {amount} to {obj} lending protocol. You will receive interest-bearing tokens in return."
        
        if structure.action.raw_value == "defi_borrow":
            amount = get_ctx(["Amount"], "assets")
            return f"You are borrowing {amount} from {obj} lending protocol. Ensure you have sufficient collateral to avoid liquidation."
        
        if structure.action.raw_value == "defi_repay":
            amount = get_ctx(["Amount"], "assets")
            return f"You are repaying {amount} to {obj} lending protocol to reduce your debt."
        
        if structure.action.raw_value == "defi_withdraw":
            amount = get_ctx(["Amount"], "assets")
            return f"You are withdrawing {amount} from {obj}."
        
        # ========== DeFi Staking ==========
        if structure.action.raw_value == "defi_stake":
            amount = get_ctx(["Amount"], "tokens")
            return f"You are staking {amount} in {obj}. Your tokens will be locked but earn rewards."
        
        if structure.action.raw_value == "defi_unstake":
            amount = get_ctx(["Amount"], "tokens")
            return f"You are unstaking {amount} from {obj}. There may be a cooldown period."
        
        if structure.action.raw_value == "defi_claim":
            return f"You are claiming rewards from {obj}."
        
        # ========== DeFi Liquidity ==========
        if structure.action.raw_value == "defi_liquidity":
            return f"You are managing liquidity position in {obj} pool."
        
        # ========== Batch Operations ==========
        if structure.action.raw_value == "batch_operation":
            batch_summary = get_ctx(["Batch Summary", "Universal Router Summary"], None)
            if batch_summary:
                return f"You are executing a batch of operations through {obj}. Review each action in the batch. {batch_summary}."
            return f"You are executing a batch of operations through {obj}. Review each action in the batch."
        
        if structure.action.raw_value == "batch_approval":
            return f"You are granting multiple token approvals through {obj}. Each approval should be reviewed."
        
        if structure.action.raw_value == "batch_transfer":
            return f"You are performing multiple transfers through {obj}."
        
        if structure.action.raw_value == "cross_contract_interaction":
            return f"You are performing a complex operation through {obj} that interacts with multiple contracts."
        
        # ========== Multisig ==========
        if structure.action.raw_value == "multisig_operation":
            return f"You are signing a transaction for the {obj} multisig wallet. Other signers may need to approve."
        
        # ========== Meta-transactions ==========
        if structure.action.raw_value == "meta_tx":
            return f"You are signing a gasless transaction for {obj}. A relayer will submit it on your behalf."
        
        # ========== Unknown/Fallback ==========
        if structure.action.raw_value == "unknown_operation":
            return f"You are performing an unknown operation on {obj}. Review the raw data carefully."
        
        if structure.action.raw_value == "contract_interaction":
            return f"You are interacting with {obj} contract."
        
        if structure.action.raw_value == "contract_call":
            func_name = structure.action.description if structure.action.description != "Unknown Action" else "a function"
            return f"You are calling {func_name} on {obj} contract."

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
            logger.warning(f"LLM interpretation failed: {e}")
            return f"Perform {structure.action.description} on {structure.target_object.description}."

