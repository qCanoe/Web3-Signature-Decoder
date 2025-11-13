"""
签名分类器 - 核心签名识别引擎
"""

import json
import re
from typing import Dict, Any, Union, Optional, List, Tuple
from dataclasses import dataclass

from .signature_types import SignatureType, SignatureCategory, SecurityLevel, get_signature_metadata


@dataclass
class ClassificationResult:
    """分类结果"""
    signature_type: SignatureType
    category: SignatureCategory
    security_level: SecurityLevel
    confidence: float  # 置信度 0-1
    metadata: Dict[str, Any]
    warnings: List[str]
    detected_patterns: List[str]


class SignatureClassifier:
    """签名分类器 - 识别和分类以太坊签名类型"""
    
    def __init__(self):
        """初始化分类器"""
        self._init_patterns()
    
    def _init_patterns(self):
        """初始化检测模式"""
        
        # EIP-712 检测模式
        self.eip712_required_fields = {"types", "domain", "primaryType", "message"}
        self.eip712_domain_fields = {"name", "version", "chainId", "verifyingContract"}
        
        # 交易数据检测模式
        self.transaction_fields = {
            "required": {"to"},
            "optional": {"from", "value", "data", "gas", "gasPrice", "gasLimit", "nonce", "maxFeePerGas", "maxPriorityFeePerGas"}
        }
        
        # 十六进制模式
        self.hex_patterns = {
            "address": re.compile(r'^0x[a-fA-F0-9]{40}$'),
            "hash": re.compile(r'^0x[a-fA-F0-9]{64}$'),
            "signature": re.compile(r'^0x[a-fA-F0-9]{130}$'),
            "hex_data": re.compile(r'^0x[a-fA-F0-9]+$')
        }
        
        # 危险关键词检测
        self.risk_keywords = {
            "high": ["transfer", "approve", "withdraw", "claim", "execute"],
            "medium": ["sign", "auth", "verify", "permit", "delegate"],
            "phishing": ["urgent", "limited time", "expires", "act now", "verify immediately"]
        }
    
    def classify(self, data: Union[str, Dict[str, Any]]) -> ClassificationResult:
        """
        分类签名数据
        
        Args:
            data: 输入的签名数据
            
        Returns:
            分类结果
        """
        # 数据预处理
        processed_data, data_format = self._preprocess_data(data)
        
        # 执行分类
        signature_type = self._detect_signature_type(processed_data, data_format)
        
        # 获取元数据
        metadata = get_signature_metadata(signature_type)
        
        # 计算置信度
        confidence = self._calculate_confidence(processed_data, signature_type, data_format)
        
        # 检测警告和模式
        warnings = self._detect_warnings(processed_data, signature_type)
        patterns = self._detect_patterns(processed_data, signature_type)
        
        # 构建结果
        return ClassificationResult(
            signature_type=signature_type,
            category=metadata.category,
            security_level=metadata.security_level,
            confidence=confidence,
            metadata={
                "data_format": data_format,
                "description": metadata.description,
                "common_use_cases": metadata.common_use_cases,
                "risk_factors": metadata.risk_factors,
                "wallet_support": metadata.wallet_support,
                "raw_data_type": type(data).__name__
            },
            warnings=warnings,
            detected_patterns=patterns
        )
    
    def _preprocess_data(self, data: Union[str, Dict[str, Any]]) -> Tuple[Union[str, Dict[str, Any]], str]:
        """预处理输入数据"""
        
        if isinstance(data, dict):
            return data, "dict"
        
        if isinstance(data, str):
            # 去除空白字符
            data = data.strip()
            
            # 尝试解析JSON
            if data.startswith('{'):
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, dict):
                        return parsed, "json_string"
                except (json.JSONDecodeError, ValueError):
                    pass
            
            return data, "string"
        
        return str(data), "other"
    
    def _detect_signature_type(self, data: Union[str, Dict[str, Any]], data_format: str) -> SignatureType:
        """检测签名类型"""
        
        if data_format in ["dict", "json_string"]:
            return self._classify_dict_data(data)
        else:
            return self._classify_string_data(data)
    
    def _classify_dict_data(self, data: Dict[str, Any]) -> SignatureType:
        """分类字典格式数据"""
        
        # 检查 EIP-712 结构
        if self._is_eip712_structure(data):
            return SignatureType.ETH_SIGN_TYPED_DATA_V4
        
        # 检查交易结构
        if self._is_transaction_structure(data):
            return SignatureType.ETH_SEND_TRANSACTION
        
        # 检查个人消息结构
        if self._is_personal_message_structure(data):
            return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    def _classify_string_data(self, data: str) -> SignatureType:
        """分类字符串格式数据"""
        
        if not data:
            return SignatureType.UNKNOWN
        
        # 检查十六进制数据
        if data.startswith("0x"):
            return self._classify_hex_data(data)
        
        # 检查纯文本消息
        if self._is_readable_text(data):
            return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    def _is_eip712_structure(self, data: Dict[str, Any]) -> bool:
        """检查是否为EIP-712结构"""
        
        # 检查必需字段
        if not self.eip712_required_fields.issubset(data.keys()):
            return False
        
        # 验证类型字段
        types = data.get("types")
        if not isinstance(types, dict) or "EIP712Domain" not in types:
            return False
        
        # 验证域字段
        domain = data.get("domain")
        if not isinstance(domain, dict):
            return False
        
        # 验证主类型
        primary_type = data.get("primaryType")
        if not isinstance(primary_type, str) or primary_type not in types:
            return False
        
        # 验证消息
        message = data.get("message")
        if not isinstance(message, dict):
            return False
        
        return True
    
    def _is_transaction_structure(self, data: Dict[str, Any]) -> bool:
        """检查是否为交易结构"""
        
        # 必须包含 'to' 字段，这是交易的基本要求
        if "to" not in data:
            return False
        
        # 检查交易相关字段的数量
        transaction_field_count = 0
        all_transaction_fields = self.transaction_fields["required"] | self.transaction_fields["optional"]
        
        for field in all_transaction_fields:
            if field in data:
                transaction_field_count += 1
        
        # 如果包含足够多的交易字段，认为是交易
        return transaction_field_count >= 2
    
    def _is_personal_message_structure(self, data: Dict[str, Any]) -> bool:
        """检查是否为个人消息结构"""
        
        # 检查消息字段
        if "message" in data and isinstance(data["message"], str):
            return True
        
        # 检查其他可能的消息字段
        message_fields = ["text", "content", "msg", "data"]
        for field in message_fields:
            if field in data and isinstance(data[field], str):
                return True
        
        return False
    
    def _classify_hex_data(self, data: str) -> SignatureType:
        """分类十六进制数据"""
        
        # 检查地址格式
        if self.hex_patterns["address"].match(data):
            return SignatureType.PERSONAL_SIGN
        
        # 检查哈希格式
        if self.hex_patterns["hash"].match(data):
            return SignatureType.ETH_SIGN
        
        # 检查签名格式
        if self.hex_patterns["signature"].match(data):
            return SignatureType.ETH_SIGN
        
        # 其他十六进制数据
        if self.hex_patterns["hex_data"].match(data):
            hex_length = len(data) - 2  # 减去 '0x'
            if hex_length > 128:  # 长数据可能是原始签名
                return SignatureType.ETH_SIGN
            else:
                return SignatureType.PERSONAL_SIGN
        
        return SignatureType.UNKNOWN
    
    def _is_readable_text(self, text: str) -> bool:
        """检查是否为可读文本"""
        
        try:
            # 检查UTF-8编码
            text.encode('utf-8')
            
            # 检查是否包含过多控制字符
            control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r')
            control_ratio = control_chars / len(text) if text else 0
            
            # 如果控制字符比例过高，认为不是可读文本
            return control_ratio < 0.1
            
        except UnicodeEncodeError:
            return False
    
    def _calculate_confidence(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType, data_format: str) -> float:
        """计算分类置信度"""
        
        confidence = 0.5  # 基础置信度
        
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
            if isinstance(data, dict) and self._is_eip712_structure(data):
                confidence = 0.95
        
        elif signature_type == SignatureType.ETH_SEND_TRANSACTION:
            if isinstance(data, dict) and self._is_transaction_structure(data):
                field_count = len(set(data.keys()) & (self.transaction_fields["required"] | self.transaction_fields["optional"]))
                confidence = min(0.9, 0.6 + field_count * 0.1)
        
        elif signature_type == SignatureType.PERSONAL_SIGN:
            if isinstance(data, str):
                if self._is_readable_text(data):
                    confidence = 0.8
                elif data.startswith("0x") and self.hex_patterns["address"].match(data):
                    confidence = 0.7
        
        elif signature_type == SignatureType.ETH_SIGN:
            if isinstance(data, str) and data.startswith("0x"):
                if self.hex_patterns["signature"].match(data) or self.hex_patterns["hash"].match(data):
                    confidence = 0.9
        
        return confidence
    
    def _detect_warnings(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType) -> List[str]:
        """检测警告信息"""
        
        warnings = []
        
        # 高风险签名类型警告
        if signature_type == SignatureType.ETH_SIGN:
            warnings.append("⚠️ eth_sign 方法存在极高安全风险，已被多数钱包禁用")
        
        # 检查数据中的风险关键词
        data_text = str(data).lower()
        
        for keyword in self.risk_keywords["phishing"]:
            if keyword in data_text:
                warnings.append(f"⚠️ 检测到钓鱼相关关键词: '{keyword}'")
        
        # EIP-712特定警告
        if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4 and isinstance(data, dict):
            # 检查过期时间
            message = data.get("message", {})
            if isinstance(message, dict):
                # 检查常见的时间字段
                time_fields = ["endTime", "deadline", "expiry", "validUntil"]
                for field in time_fields:
                    if field in message:
                        warnings.append(f"⚠️ 签名包含时效性限制，请注意 {field} 字段")
        
        return warnings
    
    def _detect_patterns(self, data: Union[str, Dict[str, Any]], signature_type: SignatureType) -> List[str]:
        """检测数据模式"""
        
        patterns = []
        
        if isinstance(data, dict):
            patterns.append(f"结构化数据，包含 {len(data)} 个字段")
            
            if signature_type == SignatureType.ETH_SIGN_TYPED_DATA_V4:
                primary_type = data.get("primaryType")
                if primary_type:
                    patterns.append(f"EIP-712 主类型: {primary_type}")
                
                domain = data.get("domain", {})
                if isinstance(domain, dict) and "name" in domain:
                    patterns.append(f"协议名称: {domain['name']}")
        
        elif isinstance(data, str):
            if data.startswith("0x"):
                hex_length = len(data) - 2
                patterns.append(f"十六进制数据，长度: {hex_length} 字符")
            else:
                patterns.append(f"文本消息，长度: {len(data)} 字符")
        
        return patterns
    
    def get_supported_types(self) -> List[SignatureType]:
        """获取支持的签名类型列表"""
        return [
            SignatureType.ETH_SEND_TRANSACTION,
            SignatureType.PERSONAL_SIGN,
            SignatureType.ETH_SIGN_TYPED_DATA_V4,
            SignatureType.ETH_SIGN
        ]
    
    def batch_classify(self, data_list: List[Union[str, Dict[str, Any]]]) -> List[ClassificationResult]:
        """批量分类签名数据"""
        return [self.classify(data) for data in data_list] 