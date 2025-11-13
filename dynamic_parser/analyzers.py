"""
动态解析器值分析器
包含各种字段值的智能分析方法
"""

from typing import Any, Optional, Tuple
from .field_types import FieldType, FieldSemantic


class ValueAnalyzer:
    """值分析器"""
    
    def __init__(self):
        self.analyzers = [
            self.analyze_timestamp_value,
            self.analyze_amount_value,
            self.analyze_address_value,
            self.analyze_percentage_value,
            self.analyze_enum_value,
        ]
    
    def analyze_timestamp_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """分析时间戳值"""
        if not isinstance(field_value, (int, str)):
            return None
        
        try:
            timestamp = int(field_value)
            # 检查是否是合理的时间戳范围 (2000年 - 2100年)
            if 946684800 <= timestamp <= 4102444800:
                # 检查是否是截止时间
                if any(keyword in field_name.lower() for keyword in ['deadline', 'expiry', 'expires']):
                    return (FieldType.DEADLINE, FieldSemantic.DEADLINE)
                else:
                    return (FieldType.TIMESTAMP, FieldSemantic.TIMESTAMP)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_amount_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """分析金额值"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            amount = int(field_value)
            field_name_lower = field_name.lower()
            
            # 检查是否是典型的ERC20金额 (18位小数)
            if amount > 10**15:  # 大于 0.001 ETH
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
        """分析地址值"""
        if field_type != 'address' or not isinstance(field_value, str):
            return None
        
        # 检查是否是有效的以太坊地址
        if not (field_value.startswith('0x') and len(field_value) == 42):
            return None
        
        field_name_lower = field_name.lower()
        
        # 根据字段名推断地址类型
        if any(keyword in field_name_lower for keyword in ['token', 'erc20', 'erc721', 'erc1155']):
            return (FieldType.TOKEN_ADDRESS, FieldSemantic.COLLECTION)
        elif any(keyword in field_name_lower for keyword in ['contract', 'verifying']):
            return (FieldType.CONTRACT_ADDRESS, FieldSemantic.TYPE)
        else:
            return (FieldType.USER_ADDRESS, None)
    
    def analyze_percentage_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """分析百分比值"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # 检查是否是百分比（0-100或0-10000的范围）
            if (0 <= value <= 100 and any(keyword in field_name_lower for keyword in ['percent', 'ratio'])) or \
               (0 <= value <= 10000 and 'bps' in field_name_lower):
                return (FieldType.PERCENTAGE, FieldSemantic.RATE)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_enum_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """分析枚举值"""
        if not isinstance(field_value, (int, str)) or not field_type.startswith(('uint', 'int')):
            return None
        
        try:
            value = int(field_value)
            field_name_lower = field_name.lower()
            
            # 检查是否是小范围的整数（可能是枚举）
            if 0 <= value <= 20:
                if any(keyword in field_name_lower for keyword in ['type', 'kind', 'status', 'state', 'mode']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.TYPE)
                elif any(keyword in field_name_lower for keyword in ['support', 'vote']):
                    return (FieldType.ENUM_VALUE, FieldSemantic.VOTE_TYPE)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def analyze_value(self, field_name: str, field_type: str, field_value: Any) -> Optional[Tuple[FieldType, FieldSemantic]]:
        """分析字段值，返回推断的类型和语义"""
        for analyzer in self.analyzers:
            result = analyzer(field_name, field_type, field_value)
            if result:
                return result
        return None 