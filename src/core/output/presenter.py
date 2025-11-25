from typing import Dict, Any, List, Optional
from ..input.definitions import IntermediateRepresentation
from ..processing.structure import SemanticStructure
from ..processing.risk import RiskAssessment
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
            "transfer_asset": "Transfer",
            "marketplace_listing": "Listing",
            "vote": "Vote",
            "permit": "Permit"
        }
        action_title = action_map.get(action_type, action_type.replace("_", " ").title())
        
        # Create a short title like "App Name - Action Type Operation"
        short_title = f"{app_name} - {action_title} Operation"
        
        # Standardized clean output
        pipeline_result = {
            "ui": {
                "title": short_title,
                "description": description,
                "risk_level": risk.level,
                "risk_reasons": risk.reasons,
                "risk_mitigation": Presenter._generate_mitigation_suggestions(risk, structure)
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
                "decoded_call": ir.decoded_call
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
                    "risk_explanation": risk.reasons[0] if risk.reasons else "Check details"
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
        
        if risk.level == "high":
            if structure.permission_scope == "unlimited_permanent":
                suggestions.append("建议使用有限额度授权而非无限授权")
                suggestions.append("建议设置授权到期时间")
            if structure.action.raw_value == "approve":
                suggestions.append("建议只授权必要的金额")
                suggestions.append("使用后及时撤销授权")
            if "bridge" in structure.action.raw_value:
                suggestions.append("仔细验证目标链地址")
                suggestions.append("确认桥接合约的官方地址")
        
        elif risk.level == "medium":
            if structure.action.raw_value == "approve":
                suggestions.append("确认授权金额是否合理")
            if structure.contract_role == "Unknown":
                suggestions.append("验证合约地址和来源")
        
        return suggestions
    
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
