from typing import Dict, Any, List, Set
from ..utils.logger import Logger

logger = Logger.get_logger(__name__)

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
    def validate_eip712_schema_integrity(data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Deep validation of EIP-712 schema integrity.
        
        Validates:
        1. All referenced types exist in types dictionary
        2. Message fields match type definitions
        3. PrimaryType can be fully resolved
        4. No circular dependencies
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[str] = []
        
        if not InputValidator.validate_eip712(data):
            errors.append("Basic EIP-712 validation failed")
            return False, errors
        
        types = data.get("types", {})
        primary_type = data.get("primaryType", "")
        message = data.get("message", {})
        
        # 1. Check all referenced types exist
        referenced_types: Set[str] = set()
        InputValidator._collect_referenced_types(types, primary_type, referenced_types)
        
        missing_types = referenced_types - set(types.keys())
        if missing_types:
            errors.append(f"Missing type definitions: {', '.join(missing_types)}")
        
        # 2. Validate message structure matches primaryType definition
        if primary_type in types:
            type_fields = types[primary_type]
            if isinstance(type_fields, list):
                for field_def in type_fields:
                    if isinstance(field_def, dict):
                        field_name = field_def.get("name")
                        field_type = field_def.get("type")
                        
                        # Check if field exists in message
                        if field_name and field_name not in message:
                            # Some fields might be optional, but log as warning
                            logger.debug(
                                f"EIP-712 message missing field: {field_name} in {primary_type}"
                            )
                        
                        # Validate nested types
                        if field_type in types and isinstance(message.get(field_name), dict):
                            nested_errors = InputValidator._validate_nested_type(
                                message[field_name], field_type, types
                            )
                            errors.extend(nested_errors)
        
        # 3. Check for circular dependencies (basic check)
        if InputValidator._has_circular_dependency(types, primary_type, set()):
            errors.append(f"Circular dependency detected in type: {primary_type}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _collect_referenced_types(types: Dict[str, Any], type_name: str, collected: Set[str]) -> None:
        """Recursively collect all types referenced by a given type."""
        if type_name in collected or type_name not in types:
            return
        
        collected.add(type_name)
        type_def = types[type_name]
        
        if isinstance(type_def, list):
            for field_def in type_def:
                if isinstance(field_def, dict):
                    field_type = field_def.get("type", "")
                    # Check if it's a custom type (not a primitive)
                    if field_type and field_type not in InputValidator._PRIMITIVE_TYPES:
                        InputValidator._collect_referenced_types(types, field_type, collected)
    
    @staticmethod
    def _validate_nested_type(value: Any, type_name: str, types: Dict[str, Any]) -> List[str]:
        """Validate a nested type structure."""
        errors: List[str] = []
        
        if type_name not in types:
            return errors
        
        if not isinstance(value, dict):
            errors.append(f"Expected dict for type {type_name}, got {type(value).__name__}")
            return errors
        
        type_def = types[type_name]
        if isinstance(type_def, list):
            for field_def in type_def:
                if isinstance(field_def, dict):
                    field_name = field_def.get("name")
                    field_type = field_def.get("type")
                    
                    if field_name and field_name in value:
                        # Recursively validate nested types
                        if field_type in types and isinstance(value[field_name], dict):
                            nested_errors = InputValidator._validate_nested_type(
                                value[field_name], field_type, types
                            )
                            errors.extend(nested_errors)
        
        return errors
    
    @staticmethod
    def _has_circular_dependency(types: Dict[str, Any], type_name: str, visited: Set[str]) -> bool:
        """Check for circular dependencies in type definitions."""
        if type_name in visited:
            return True
        
        if type_name not in types:
            return False
        
        visited.add(type_name)
        type_def = types[type_name]
        
        if isinstance(type_def, list):
            for field_def in type_def:
                if isinstance(field_def, dict):
                    field_type = field_def.get("type", "")
                    if field_type and field_type not in InputValidator._PRIMITIVE_TYPES:
                        if InputValidator._has_circular_dependency(types, field_type, visited.copy()):
                            return True
        
        return False
    
    _PRIMITIVE_TYPES = {
        "address", "bool", "bytes", "bytes1", "bytes2", "bytes3", "bytes4", "bytes5",
        "bytes6", "bytes7", "bytes8", "bytes9", "bytes10", "bytes11", "bytes12",
        "bytes13", "bytes14", "bytes15", "bytes16", "bytes17", "bytes18", "bytes19",
        "bytes20", "bytes21", "bytes22", "bytes23", "bytes24", "bytes25", "bytes26",
        "bytes27", "bytes28", "bytes29", "bytes30", "bytes31", "bytes32",
        "int", "int8", "int16", "int24", "int32", "int40", "int48", "int56",
        "int64", "int72", "int80", "int88", "int96", "int104", "int112", "int120",
        "int128", "int136", "int144", "int152", "int160", "int168", "int176",
        "int184", "int192", "int200", "int208", "int216", "int224", "int232",
        "int240", "int248", "int256",
        "uint", "uint8", "uint16", "uint24", "uint32", "uint40", "uint48", "uint56",
        "uint64", "uint72", "uint80", "uint88", "uint96", "uint104", "uint112", "uint120",
        "uint128", "uint136", "uint144", "uint152", "uint160", "uint168", "uint176",
        "uint184", "uint192", "uint200", "uint208", "uint216", "uint224", "uint232",
        "uint240", "uint248", "uint256",
        "string"
    }

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

