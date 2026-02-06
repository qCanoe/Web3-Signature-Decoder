from typing import Dict, Any, List, Optional
from ..input.definitions import IntermediateRepresentation
from ..processing.structure import SemanticStructure
from ..processing.risk import RiskAssessment, RiskEngine
from ..processing.knowledge_base import KnowledgeBase
from .highlighter import TextHighlighter

class Presenter:
    """
    Formats the pipeline results for the UI.
    """
    
    @staticmethod
    def format(ir: IntermediateRepresentation, structure: SemanticStructure, risk: RiskAssessment, description: str) -> Dict[str, Any]:
        # Generate a concise title based on app name and action type
        domain = ir.metadata.get("domain", {})
        app_name = domain.get("name", "Unknown App")
        
        # Get action type and format it nicely
        action_type = structure.action.raw_value or "operation"
        # Convert action_type like "approve", "authentication" to readable format
        action_map = {
            "approve": "Approval",
            "authentication": "Login",
            "sign_in_with_ethereum": "Login",
            "transfer_asset": "Transfer",
            "marketplace_listing": "Listing",
            "vote": "Vote",
            "permit": "Permit"
        }
        action_title = action_map.get(action_type, action_type.replace("_", " ").title())
        
        # Create a short title like "App Name - Action Type Operation"
        short_title = f"{app_name} - {action_title} Operation"
        
        # Get risk explanation
        risk_explanation = RiskEngine.get_risk_explanation(risk.level)
        
        # Standardized clean output
        risk_signals = risk.details.get("risk_signals", []) if isinstance(risk.details, dict) else []
        risk_policy_version = risk.details.get("risk_policy_version", "v1") if isinstance(risk.details, dict) else "v1"

        pipeline_result = {
            "ui": {
                "title": short_title,
                "description": description,
                "risk_level": risk.level,
                "risk_score": getattr(risk, 'score', 0),
                "risk_reasons": risk.reasons,
                "risk_explanation": risk_explanation,
                "risk_mitigation": Presenter._generate_mitigation_suggestions(risk, structure),
                "risk_policy_version": risk_policy_version,
            },
            "semantic": {
                "actor": {
                    "name": structure.actor.description,
                    "value": structure.actor.raw_value
                },
                "action": {
                    "name": structure.action.description,
                    "type": structure.action.raw_value
                },
                "object": {
                    "name": structure.target_object.description,
                    "value": structure.target_object.raw_value
                },
                "context": [
                    {"label": c.description, "value": str(c.raw_value), "risk": c.risk_factor}
                    for c in structure.context
                ],
                "contract_role": structure.contract_role,
                "permission_scope": structure.permission_scope,
                "hidden_implications": structure.hidden_implications,
                "assets": ir.assets,
                "decoded_call": ir.decoded_call,
                "risk_signals": risk_signals,
            },
            "technical": {
                "type": ir.signature_type,
                "chain_id": ir.chain_id,
                "raw": ir.params,
                "metadata": ir.metadata,
                "original_payload": ir.raw_data,  # Complete original payload
                "decoded_parameters": ir.decoded_call.get("parameters", {}) if ir.decoded_call else {},
                "function_signature": ir.decoded_call.get("signature", "") if ir.decoded_call else "",
                "eip712_types": ir.metadata.get("types", {}),
                "eip712_primary_type": ir.metadata.get("primaryType", ""),
                "contract_verification_url": Presenter._generate_contract_verification_url(ir.chain_id, ir.contract)
            }
        }

        # Compatibility Layer for existing UI (app.js)
        # app.js expects: raw_result.domain_info, raw_result.english_description
        
        domain = ir.metadata.get("domain", {})
        
        compat_result = {
            "success": True,
            "pipeline_result": pipeline_result,
            "raw_result": {
                "domain_info": {
                    "name": domain.get("name", "Unknown App"),
                    "verifyingContract": ir.contract,
                    "chainId": ir.chain_id,
                    "version": domain.get("version", "")
                },
                "english_description": {
                    "title": pipeline_result["ui"]["title"],
                    "summary": TextHighlighter.highlight_keywords(pipeline_result["ui"]["description"]),
                    "risk_level": risk.level,
                    "risk_score": getattr(risk, 'score', 0),
                    "risk_explanation": risk_explanation.get("description", risk.reasons[0] if risk.reasons else "Check details"),
                    "risk_recommendation": risk_explanation.get("recommendation", "Review the details before signing.")
                }
            }
        }
        
        return compat_result
    
    @staticmethod
    def _generate_mitigation_suggestions(risk: RiskAssessment, structure: SemanticStructure) -> List[str]:
        """
        Generate risk mitigation suggestions based on risk level and structure.
        """
        suggestions = []
        
        if risk.level in ["critical", "high"]:
            # Critical/High risk mitigations
            if structure.permission_scope == "unlimited_permanent":
                suggestions.append("Consider using limited amount approval instead of unlimited")
                suggestions.append("Set an expiration time for the approval")
            if structure.action.raw_value == "approve":
                suggestions.append("Only approve the exact amount needed")
                suggestions.append("Revoke approval after use")
            if "bridge" in (structure.action.raw_value or ""):
                suggestions.append("Verify the destination chain address carefully")
                suggestions.append("Confirm the bridge contract is official")
            if structure.action.raw_value in ["batch_operation", "cross_contract_interaction"]:
                suggestions.append("Review each operation in the batch")
                suggestions.append("Verify all contract addresses involved")
            
            # Check for specific risks in reasons
            if any("phishing" in r.lower() for r in risk.reasons):
                suggestions.append("This appears to be a phishing attempt - do not proceed")
                suggestions.append("Verify the request source through official channels")
            if any("unknown contract" in r.lower() for r in risk.reasons):
                suggestions.append("Verify the contract on a block explorer")
                suggestions.append("Check for verified source code")
        
        elif risk.level == "medium":
            if structure.action.raw_value == "approve":
                suggestions.append("Confirm the approval amount is appropriate")
            if structure.contract_role == "Unknown" or structure.contract_role is None:
                suggestions.append("Verify the contract address and source")
            if "transfer" in (structure.action.raw_value or ""):
                suggestions.append("Double-check the recipient address")
        
        elif risk.level == "low":
            if structure.action.raw_value in ["authentication", "sign_in_with_ethereum"]:
                suggestions.append("This is a login signature - generally safe")
        
        # Limit suggestions
        return suggestions[:5] if suggestions else ["Review the transaction details before signing"]
    
    @staticmethod
    def _generate_contract_verification_url(chain_id: Optional[int], contract_address: Optional[str]) -> Optional[str]:
        """
        Generate contract verification URL for popular block explorers.
        """
        if not chain_id or not contract_address:
            return None
        
        # Map chain IDs to explorer URLs
        explorer_map = {
            1: "https://etherscan.io/address/",  # Ethereum Mainnet
            137: "https://polygonscan.com/address/",  # Polygon
            42161: "https://arbiscan.io/address/",  # Arbitrum
            10: "https://optimistic.etherscan.io/address/",  # Optimism
            8453: "https://basescan.org/address/",  # Base
            56: "https://bscscan.com/address/",  # BSC
            43114: "https://snowtrace.io/address/",  # Avalanche
            250: "https://ftmscan.com/address/"  # Fantom
        }
        
        base_url = explorer_map.get(chain_id)
        if base_url:
            return f"{base_url}{contract_address}"
        
        return None
