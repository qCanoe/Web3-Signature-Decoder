from typing import Dict, Any
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
                "risk_reasons": risk.reasons
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
                "metadata": ir.metadata
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
