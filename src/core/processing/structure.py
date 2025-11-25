from dataclasses import dataclass, field
from typing import Optional, List, Any
from ..input.definitions import IntermediateRepresentation, SignatureType
from .knowledge_base import KnowledgeBase
from .extractors import ParameterExtractor

@dataclass
class SemanticComponent:
    role: str # e.g., "Actor", "Action", "Object"
    description: str # Human readable text
    raw_value: Any # The technical value
    risk_factor: str = "low" # Hint for risk engine

@dataclass
class SemanticStructure:
    actor: SemanticComponent
    action: SemanticComponent
    target_object: SemanticComponent
    context: List[SemanticComponent]
    # Enhanced fields for semantic interpretation
    contract_role: Optional[str] = None  # e.g., "DEX", "Lending", "NFT Marketplace", "Governance"
    permission_scope: Optional[str] = None  # e.g., "unlimited", "single_use", "time_limited", "specific_amount"
    hidden_implications: List[str] = field(default_factory=list)  # List of potential risks or hidden behaviors

class StructureParser:
    """
    Parses the IR into an Actor-Action-Object semantic structure.
    """

    @staticmethod
    def parse(ir: IntermediateRepresentation) -> SemanticStructure:
        actor = StructureParser._extract_actor(ir)
        action = StructureParser._extract_action(ir)
        target_object = StructureParser._extract_object(ir)
        context = StructureParser._extract_context(ir)

        return SemanticStructure(actor, action, target_object, context)

    @staticmethod
    def _extract_actor(ir: IntermediateRepresentation) -> SemanticComponent:
        # The "Actor" is usually the user signing, but conceptually it could be
        # the contract being empowered.
        # Standard: Actor = User (Sender)
        # Enhanced: Try to identify actor role from context
        
        # For nested EIP-712, try to extract from nested structures
        if ir.signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            # Check for nested actor fields (e.g., message.from.wallet)
            params = ir.params
            actor_value = None
            actor_description = "Current User"
            
            # Try common nested patterns
            if "from.wallet" in params:
                actor_value = params["from.wallet"]
                actor_description = "Sender"
            elif "from" in params and isinstance(params["from"], dict):
                actor_value = params["from"].get("wallet") or params["from"].get("address")
                actor_description = "Sender"
            elif "owner" in params:
                actor_value = params["owner"]
                actor_description = "Owner"
            elif "signer" in params:
                actor_value = params["signer"]
                actor_description = "Signer"
            
            if actor_value:
                return SemanticComponent(
                    role="Actor",
                    description=actor_description,
                    raw_value=actor_value
                )
        
        # Fallback to standard extraction
        actor_description = "Current User"
        actor_value = ir.sender or "User Wallet"
        
        # Try to identify protocol/contract context
        if ir.contract:
            contract_name = KnowledgeBase.get_contract_name(ir.chain_id, ir.contract)
            if contract_name:
                actor_description = f"User interacting with {contract_name}"
        
        # Check domain name for protocol identification
        domain = ir.metadata.get("domain", {})
        domain_name = domain.get("name", "")
        if domain_name:
            protocol_type = KnowledgeBase.identify_protocol_type(domain_name, ir.contract, ir.chain_id)
            if protocol_type:
                actor_description = f"User on {domain_name}"
        
        return SemanticComponent(
            role="Actor",
            description=actor_description,
            raw_value=actor_value
        )

    @staticmethod
    def _extract_action(ir: IntermediateRepresentation) -> SemanticComponent:
        desc = ir.action_type.replace("_", " ").title() if ir.action_type else "Unknown Action"
        
        # Refine description based on type
        if ir.action_type == "approve":
            desc = "Authorize Spender"
        elif ir.action_type == "transfer_asset":
            desc = "Transfer Assets"
        elif ir.action_type == "authentication":
            desc = "Sign In / Authenticate"

        return SemanticComponent(
            role="Action",
            description=desc,
            raw_value=ir.action_type
        )

    @staticmethod
    def _extract_object(ir: IntermediateRepresentation) -> SemanticComponent:
        # The object acted upon (e.g. the Token, the NFT, the dApp)
        
        # Case 1: EIP-712
        if ir.signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            # Try to identify specific object types from nested structures
            params = ir.params
            
            # Check for token address
            token_addr = params.get("token") or params.get("tokenAddress") or params.get("asset")
            if token_addr:
                token_meta = KnowledgeBase.get_token_metadata(token_addr)
                symbol = token_meta.get("symbol", "TOKEN") if token_meta else "TOKEN"
                return SemanticComponent(
                    role="Object",
                    description=f"{symbol} Token",
                    raw_value=token_addr
                )
            
            # Check for NFT contract
            nft_addr = params.get("nft") or params.get("collection") or params.get("contract")
            if nft_addr:
                return SemanticComponent(
                    role="Object",
                    description="NFT Collection",
                    raw_value=nft_addr
                )
            
            # Check for governance contract
            proposal_id = params.get("proposalId") or params.get("proposal")
            if proposal_id:
                return SemanticComponent(
                    role="Object",
                    description=f"Governance Proposal #{proposal_id}",
                    raw_value=str(proposal_id)
                )
            
            # Check for nested structures (e.g., message.to.wallet)
            if "to.wallet" in params:
                return SemanticComponent(
                    role="Object",
                    description="Recipient",
                    raw_value=params["to.wallet"]
                )
            elif "to" in params and isinstance(params["to"], dict):
                to_wallet = params["to"].get("wallet") or params["to"].get("address")
                if to_wallet:
                    return SemanticComponent(
                        role="Object",
                        description="Recipient",
                        raw_value=to_wallet
                    )
            
            # Usually the verifying contract is the context/object
            contract_addr = ir.contract
            name = ir.metadata.get("domain", {}).get("name")
            return SemanticComponent(
                role="Object",
                description=name or "Contract",
                raw_value=contract_addr
            )
            
        # Case 2: Transaction
        if ir.signature_type == SignatureType.ETH_SEND_TRANSACTION:
            # Try to identify token from decoded call
            decoded = ir.decoded_call or {}
            params = decoded.get("parameters", {})
            token_addr = params.get("token") or ir.contract
            
            if token_addr:
                token_meta = KnowledgeBase.get_token_metadata(token_addr)
                if token_meta:
                    symbol = token_meta.get("symbol", "TOKEN")
                    return SemanticComponent(
                        role="Object",
                        description=f"{symbol} Token",
                        raw_value=token_addr
                    )
            
            return SemanticComponent(
                role="Object",
                description="Target Contract",
                raw_value=ir.contract
            )

        # Case 3: Personal Sign
        if ir.signature_type == SignatureType.PERSONAL_SIGN:
            # Try to extract domain from message if available
            msg = ir.params.get("message_cleaned", "")
            extracted = ParameterExtractor.extract(msg)
            if "domain" in extracted:
                 return SemanticComponent(
                    role="Object",
                    description=extracted["domain"],
                    raw_value=extracted["domain"]
                )

        return SemanticComponent(
            role="Object",
            description="Message",
            raw_value="Text Message"
        )

    @staticmethod
    def _extract_context(ir: IntermediateRepresentation) -> List[SemanticComponent]:
        ctx = []
        params = ir.params
        
        # Add Chain Info
        if ir.chain_id:
            chain_name = KnowledgeBase.get_chain_name(ir.chain_id)
            ctx.append(SemanticComponent(
                role="Context",
                description="Network",
                raw_value=f"{chain_name} (Chain ID: {ir.chain_id})"
            ))
            
        # Add Value Info if strictly transferring ETH
        if ir.value and ir.value != "0":
             ctx.append(SemanticComponent(
                role="Context",
                description="Native Value",
                raw_value=ir.value
            ))

        # --- Generalized Parameter Extraction for Risk Analysis ---
        
        # 1. Deadlines / Time
        deadline = params.get("deadline") or params.get("expiry") or params.get("endTime")
        if deadline:
            ctx.append(SemanticComponent(role="Context", description="Deadline", raw_value=deadline))
            
        # 2. Value / Amount (General)
        amount = params.get("value") or params.get("amount")
        if amount and "amount" not in [c.description.lower() for c in ctx]: # Avoid dupe if handled below
             is_inf = KnowledgeBase.is_infinite_allowance(amount)
             desc = "Infinite Amount" if is_inf else "Amount"
             risk = "high" if is_inf else "low"
             ctx.append(SemanticComponent(role="Context", description=desc, raw_value=amount, risk_factor=risk))

        # 3. Cross-chain Indicators
        dest_chain = params.get("destinationChainId") or params.get("targetChain")
        if dest_chain:
            ctx.append(SemanticComponent(role="Context", description="Destination Chain", raw_value=dest_chain, risk_factor="medium"))

        # --- Action Specific Extraction ---

        decoded = ir.decoded_call or ir.metadata.get("decoded_call", {})
        decoded_params = decoded.get("parameters", {}) if decoded else {}

        if ir.action_type == "approve":
            spender = decoded_params.get("spender") or decoded_params.get("param_0") or params.get("spender")
            value = decoded_params.get("amount") or decoded_params.get("param_1") or params.get("value") or params.get("amount")
            if spender:
                # Try to identify spender protocol
                spender_name = KnowledgeBase.get_contract_name(ir.chain_id, spender)
                spender_desc = spender_name if spender_name else "Spender"
                ctx.append(SemanticComponent(role="Context", description=spender_desc, raw_value=spender))
            if value:
                is_inf = KnowledgeBase.is_infinite_allowance(value)
                desc = "Infinite Amount" if is_inf else f"Amount: {value}"
                risk = "high" if is_inf else "low"
                ctx.append(SemanticComponent(role="Context", description=desc, raw_value=value, risk_factor=risk))

        elif ir.action_type == "transfer_asset":
            recipient = decoded_params.get("to") or decoded_params.get("param_0")
            token_amount = decoded_params.get("amount") or decoded_params.get("param_1")
            token_address = decoded_params.get("token") or params.get("token")
            
            if recipient:
                # Try to identify recipient protocol
                recipient_name = KnowledgeBase.get_contract_name(ir.chain_id, recipient)
                recipient_desc = recipient_name if recipient_name else "Recipient"
                ctx.append(SemanticComponent(role="Context", description=recipient_desc, raw_value=recipient))
            
            if token_amount:
                # Try to get token metadata
                token_info = ""
                if token_address:
                    token_meta = KnowledgeBase.get_token_metadata(token_address)
                    if token_meta:
                        token_info = f" ({token_meta.get('symbol', 'TOKEN')})"
                ctx.append(SemanticComponent(role="Context", description=f"Token Amount: {token_amount}{token_info}", raw_value=token_amount))

        elif ir.action_type == "defi_swap":
            amount_in = decoded_params.get("amountIn") or decoded_params.get("param_0")
            amount_out_min = decoded_params.get("amountOutMin") or decoded_params.get("param_1")
            if amount_in:
                ctx.append(SemanticComponent(role="Context", description=f"Input Amount: {amount_in}", raw_value=amount_in))
            if amount_out_min:
                ctx.append(SemanticComponent(role="Context", description=f"Minimum Output: {amount_out_min}", raw_value=amount_out_min, risk_factor="medium"))

        # Attach asset summaries inferred during decoding
        for asset in ir.assets:
            label = "Asset"
            if asset.get("type") == "approval":
                label = "Approval Scope"
            elif asset.get("type") == "native":
                label = "Native Asset"
            desc = f"{label}: {asset.get('symbol', 'TOKEN')} {asset.get('amount_formatted') or asset.get('amount_raw')}"
            risk = "high" if asset.get("direction") == "authorization" else "low"
            ctx.append(SemanticComponent(role="Context", description=desc, raw_value=asset, risk_factor=risk))
        
        # Personal Sign Context Extraction
        if ir.signature_type == SignatureType.PERSONAL_SIGN:
            msg = params.get("message_cleaned", "")
            extracted = ParameterExtractor.extract(msg)
            
            # Add interesting fields to context
            if "nonce" in extracted:
                ctx.append(SemanticComponent(role="Context", description="Nonce", raw_value=extracted["nonce"]))
            if "timestamp" in extracted:
                 ctx.append(SemanticComponent(role="Context", description="Timestamp", raw_value=extracted["timestamp"]))
            if "address" in extracted:
                 ctx.append(SemanticComponent(role="Context", description="Referenced Address", raw_value=extracted["address"]))
            # Add any other custom keys found
            for k, v in extracted.items():
                if k not in ["nonce", "timestamp", "address", "domain"]:
                    ctx.append(SemanticComponent(role="Context", description=k.title(), raw_value=v))
        
        # EIP-712 Nested Context Extraction
        if ir.signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            # Extract all nested fields that weren't already captured
            for key, value in params.items():
                # Skip already processed fields
                if key in ["message", "message_cleaned"]:
                    continue
                
                # Skip if already in context
                if any(c.description == key.title() for c in ctx):
                    continue
                
                # Add nested fields with dot notation
                if "." in key:
                    # This is a nested field, add it
                    desc = key.replace(".", " ").title()
                    ctx.append(SemanticComponent(role="Context", description=desc, raw_value=value))
                elif key not in ["nonce", "deadline", "expiry", "value", "amount", "spender", "to"]:
                    # Add other top-level fields
                    ctx.append(SemanticComponent(role="Context", description=key.title(), raw_value=value))

        return ctx
