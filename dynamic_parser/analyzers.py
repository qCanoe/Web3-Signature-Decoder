"""
Dynamic Parser Value Analyzer
Contains intelligent analysis methods for various field values
"""

from typing import Any, Optional, Tuple
from .field_types import FieldType, FieldSemantic


class ValueAnalyzer:
    """Value analyzer"""
    
    def __init__(self):
        self.analyzers = [
            self.analyze_timestamp_value,
            self.analyze_amount_value,
            self.analyze_address_value,
            self.analyze_percentage_value,
            self.analyze_enum_value,
        ]
    
    def analyze_timestamp_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """Analyze timestamp value"""
        if not isinstance(field_value, (int, str)):
            return None
        
        try:
            timestamp = int(field_value)
            # Check if it's a reasonable timestamp range (2000 - 2100)
            if 946684800 <= timestamp <= 4102444800:
                # Check if it's a deadline
                if any(keyword in field_name.lower() for keyword in ['deadline', 'expiry', 'expires']):
                    return (FieldType.DEADLINE, FieldSemantic.DEADLINE)
                else:
                    return (FieldType.TIMESTAMP, FieldSemantic.TIMESTAMP)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_amount_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """Analyze amount value"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            amount = int(field_value)
            field_name_lower = field_name.lower()
            
            # Check if it's a typical ERC20 amount (18 decimal places)
            if amount > 10**15:  # Greater than 0.001 ETH
                if any(keyword in field_name_lower for keyword in ['amount', 'value', 'quantity']):
                    return (FieldType.AMOUNT, FieldSemantic.AMOUNT)
                elif any(keyword in field_name_lower for keyword in ['price', 'cost']):
                    return (FieldType.AMOUNT, FieldSemantic.PRICE)
                elif any(keyword in field_name_lower for keyword in ['fee', 'commission']):
                    return (FieldType.AMOUNT, FieldSemantic.FEE)
                else:
                    return (FieldType.AMOUNT, FieldSemantic.VALUE)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_address_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """Analyze address value"""
        if field_type != 'address' or not isinstance(field_value, str):
            return None
        
        # Check if it's a valid Ethereum address
        if not (field_value.startswith('0x') and len(field_value) == 42):
            return None
        
        field_name_lower = field_name.lower()
        
        # Infer address type based on field name
        if any(keyword in field_name_lower for keyword in ['token', 'erc20', 'erc721', 'erc1155']):
            return (FieldType.TOKEN_ADDRESS, FieldSemantic.COLLECTION)
        elif any(keyword in field_name_lower for keyword in ['contract', 'verifying']):
            return (FieldType.CONTRACT_ADDRESS, FieldSemantic.TYPE)
        else:
            return (FieldType.USER_ADDRESS, None)
    
    def analyze_percentage_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """Analyze percentage value"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # Check if it's a percentage (range 0-100 or 0-10000)
            if (0 <= value <= 100 and any(keyword in field_name_lower for keyword in ['percent', 'ratio'])) or \
               (0 <= value <= 10000 and 'bps' in field_name_lower):
                return (FieldType.PERCENTAGE, FieldSemantic.RATE)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_enum_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """Analyze enum value"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # Check if it's a small range integer (might be an enum)
            if 0 <= value <= 20:
                if any(keyword in field_name_lower for keyword in ['type', 'kind', 'status', 'state', 'mode']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.TYPE)
                elif any(keyword in field_name_lower for keyword in ['support', 'vote']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.VOTE_TYPE)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """Analyze field value, return inferred type and semantic"""
        for analyzer in self.analyzers:
            result = analyzer(field_name, field_type, field_value)
            if result:
                return result
        return None 