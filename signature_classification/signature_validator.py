"""
签名验证器 - 验证签名数据格式和有效性
"""

import re
from typing import Dict, Any, Union, List, Optional
from dataclasses import dataclass

from .signature_types import SignatureType


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class SignatureValidator:
    """签名验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self._init_validation_rules()
    
    def _init_validation_rules(self):
        """初始化验证规则"""
        
        # 地址验证正则
        self.address_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        
        # 哈希验证正则
        self.hash_pattern = re.compile(r'^0x[a-fA-F0-9]{64}$')
        
        # 十六进制数据验证
        self.hex_pattern = re.compile(r'^0x[a-fA-F0-9]*$')
        
        # EIP-712 必需字段
        self.eip712_required_fields = {"types", "domain", "primaryType", "message"}
        
        # 交易必需字段
        self.transaction_required_fields = {"to"}
        self.transaction_optional_fields = {"from", "value", "data", "gas", "gasPrice", "nonce"}
    
    def validate(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType) -> ValidationResult:
        """
        验证签名数据
        
        Args:
            data: 签名数据
            signature_type: 签名类型
            
        Returns:
            验证结果
        """
        errors = []
        warnings = []
        metadata = {}
        
        # 基础数据验证
        base_errors = self._validate_base_data(data)
        errors.extend(base_errors)
        
        # 根据签名类型进行专门验证
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            type_errors, type_warnings, type_metadata = self._validate_eip712(data)
        elif signature_type == SignatureType.ETH_SEND_TRANSACTION:
            type_errors, type_warnings, type_metadata = self._validate_transaction(data)
        elif signature_type == SignatureType.PERSONAL_SIGN:
            type_errors, type_warnings, type_metadata = self._validate_personal_sign(data)
        elif signature_type == SignatureType.ETH_SIGN:
            type_errors, type_warnings, type_metadata = self._validate_eth_sign(data)
        else:
            type_errors, type_warnings, type_metadata = [], [], {}
        
        errors.extend(type_errors)
        warnings.extend(type_warnings)
        metadata.update(type_metadata)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def _validate_base_data(self, data: Union[str, Dict[str, Any]]) -> List[str]:
        """基础数据验证"""
        errors = []
        
        if data is None:
            errors.append("数据不能为空")
            return errors
        
        if isinstance(data, str):
            if not data.strip():
                errors.append("字符串数据不能为空")
        elif isinstance(data, dict):
            if not data:
                errors.append("字典数据不能为空")
        
        return errors
    
    def _validate_eip712(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """验证EIP-712数据"""
        errors = []
        warnings = []
        metadata = {}
        
        if not isinstance(data, dict):
            errors.append("EIP-712数据必须是字典格式")
            return errors, warnings, metadata
        
        # 检查必需字段
        missing_fields = self.eip712_required_fields - set(data.keys())
        if missing_fields:
            errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        # 验证types字段
        if "types" in data:
            types_errors = self._validate_eip712_types(data["types"])
            errors.extend(types_errors)
        
        # 验证domain字段
        if "domain" in data:
            domain_errors, domain_metadata = self._validate_eip712_domain(data["domain"])
            errors.extend(domain_errors)
            metadata.update(domain_metadata)
        
        # 验证primaryType字段
        if "primaryType" in data and "types" in data:
            primary_type = data["primaryType"]
            if not isinstance(primary_type, str):
                errors.append("primaryType必须是字符串")
            elif primary_type not in data["types"]:
                errors.append(f"primaryType '{primary_type}' 不在types定义中")
        
        # 验证message字段
        if "message" in data:
            if not isinstance(data["message"], dict):
                errors.append("message字段必须是字典")
        
        return errors, warnings, metadata
    
    def _validate_eip712_types(self, types: Any) -> List[str]:
        """验证EIP-712 types字段"""
        errors = []
        
        if not isinstance(types, dict):
            errors.append("types字段必须是字典")
            return errors
        
        # 检查EIP712Domain类型
        if "EIP712Domain" not in types:
            errors.append("types中必须包含EIP712Domain定义")
        
        # 验证类型定义格式
        for type_name, type_def in types.items():
            if not isinstance(type_def, list):
                errors.append(f"类型定义 '{type_name}' 必须是数组")
                continue
            
            for field in type_def:
                if not isinstance(field, dict):
                    errors.append(f"类型 '{type_name}' 的字段定义必须是字典")
                    continue
                
                if "name" not in field or "type" not in field:
                    errors.append(f"类型 '{type_name}' 的字段必须包含name和type")
        
        return errors
    
    def _validate_eip712_domain(self, domain: Any) -> tuple[List[str], Dict[str, Any]]:
        """验证EIP-712 domain字段"""
        errors = []
        metadata = {}
        
        if not isinstance(domain, dict):
            errors.append("domain字段必须是字典")
            return errors, metadata
        
        # 验证常见域字段
        if "name" in domain:
            metadata["protocol_name"] = domain["name"]
        
        if "version" in domain:
            metadata["protocol_version"] = domain["version"]
        
        if "chainId" in domain:
            chain_id = domain["chainId"]
            if isinstance(chain_id, str) and chain_id.isdigit():
                metadata["chain_id"] = int(chain_id)
            elif isinstance(chain_id, int):
                metadata["chain_id"] = chain_id
        
        if "verifyingContract" in domain:
            contract = domain["verifyingContract"]
            if isinstance(contract, str):
                if not self.address_pattern.match(contract):
                    errors.append("verifyingContract必须是有效的以太坊地址")
                else:
                    metadata["contract_address"] = contract
        
        return errors, metadata
    
    def _validate_transaction(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """验证交易数据"""
        errors = []
        warnings = []
        metadata = {}
        
        if not isinstance(data, dict):
            errors.append("交易数据必须是字典格式")
            return errors, warnings, metadata
        
        # 检查必需字段
        if "to" not in data:
            errors.append("交易必须包含'to'字段")
        else:
            to_address = data["to"]
            if to_address is not None and not self.address_pattern.match(str(to_address)):
                errors.append("'to'字段必须是有效的以太坊地址或null")
        
        # 验证可选字段
        if "from" in data:
            from_address = data["from"]
            if not self.address_pattern.match(str(from_address)):
                errors.append("'from'字段必须是有效的以太坊地址")
        
        if "value" in data:
            value = data["value"]
            if isinstance(value, str):
                if not (value.startswith("0x") and self.hex_pattern.match(value)):
                    if not value.isdigit():
                        errors.append("'value'字段必须是十六进制字符串或数字")
        
        if "data" in data:
            tx_data = data["data"]
            if isinstance(tx_data, str) and tx_data != "0x":
                if not self.hex_pattern.match(tx_data):
                    errors.append("'data'字段必须是有效的十六进制数据")
        
        # 验证Gas相关字段
        gas_fields = ["gas", "gasLimit", "gasPrice", "maxFeePerGas", "maxPriorityFeePerGas"]
        for field in gas_fields:
            if field in data:
                gas_value = data[field]
                if isinstance(gas_value, str):
                    if not (gas_value.startswith("0x") and self.hex_pattern.match(gas_value)):
                        if not gas_value.isdigit():
                            errors.append(f"'{field}'字段必须是十六进制字符串或数字")
        
        return errors, warnings, metadata
    
    def _validate_personal_sign(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """验证个人签名数据"""
        errors = []
        warnings = []
        metadata = {}
        
        if isinstance(data, str):
            # 验证字符串消息
            if len(data) > 10000:  # 10KB limit
                warnings.append("消息长度过长，可能影响用户体验")
            
            # 检查是否包含十六进制数据
            if data.startswith("0x"):
                if not self.hex_pattern.match(data):
                    errors.append("十六进制数据格式无效")
                else:
                    metadata["data_type"] = "hex"
                    metadata["hex_length"] = len(data) - 2
            else:
                metadata["data_type"] = "text"
                metadata["text_length"] = len(data)
        
        elif isinstance(data, dict):
            # 验证字典格式的个人消息
            if "message" not in data:
                warnings.append("字典格式的个人消息通常应包含'message'字段")
        
        return errors, warnings, metadata
    
    def _validate_eth_sign(self, data: Union[str, Dict[str, Any]]) -> tuple[List[str], List[str], Dict[str, Any]]:
        """验证eth_sign数据"""
        errors = []
        warnings = ["eth_sign方法存在安全风险，建议避免使用"]
        metadata = {}
        
        if isinstance(data, str):
            if not data.startswith("0x"):
                errors.append("eth_sign数据必须是十六进制格式")
            elif not self.hex_pattern.match(data):
                errors.append("十六进制数据格式无效")
            else:
                hex_length = len(data) - 2
                metadata["hex_length"] = hex_length
                
                # 根据长度判断数据类型
                if hex_length == 64:  # 32 bytes hash
                    metadata["data_type"] = "hash"
                elif hex_length == 130:  # 65 bytes signature
                    metadata["data_type"] = "signature"
                else:
                    metadata["data_type"] = "raw_data"
        
        return errors, warnings, metadata
    
    def validate_address(self, address: str) -> bool:
        """验证以太坊地址格式"""
        if not isinstance(address, str):
            return False
        return bool(self.address_pattern.match(address))
    
    def validate_hash(self, hash_value: str) -> bool:
        """验证哈希格式"""
        if not isinstance(hash_value, str):
            return False
        return bool(self.hash_pattern.match(hash_value))
    
    def validate_hex_data(self, hex_data: str) -> bool:
        """验证十六进制数据格式"""
        if not isinstance(hex_data, str):
            return False
        return bool(self.hex_pattern.match(hex_data)) 