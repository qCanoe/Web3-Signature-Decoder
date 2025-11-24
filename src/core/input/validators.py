from typing import Dict, Any, List

class InputValidator:
    @staticmethod
    def validate_eip712(data: Dict[str, Any]) -> bool:
        required_fields = ["types", "domain", "primaryType", "message"]
        for field in required_fields:
            if field not in data:
                return False
        
        if not isinstance(data["types"], dict):
            return False
            
        if "EIP712Domain" not in data["types"]:
            return False
            
        if data["primaryType"] not in data["types"]:
            return False
            
        return True

    @staticmethod
    def validate_transaction(data: Dict[str, Any]) -> bool:
        # Minimal validation for transaction
        # Must have at least 'to' or 'data' (contract creation)
        if "to" not in data and "data" not in data:
            return False
        return True

    @staticmethod
    def validate_personal_sign(data: Any) -> bool:
        # Can be string or dict with 'message'
        if isinstance(data, str) and data:
            return True
        if isinstance(data, dict) and "message" in data:
            return True
        return False

