"""
动态解析器核心模块
包含主要的解析逻辑、字段推断和结构体解析功能
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from .field_types import (
    FieldInfo, StructInfo, EIP712ParseResult, 
    FieldType, FieldSemantic
)
from .patterns import PatternMatcher
from .analyzers import ValueAnalyzer
from .formatters import DescriptionFormatter, ResultFormatter
from .nlp_natural_language_generator import create_nlp_generator, NaturalLanguageOutput


class DynamicEIP712Parser:
    """动态 EIP712 解析器核心类"""
    
    def __init__(self, enable_nlp: bool = False, nlp_config: Optional[Dict[str, Any]] = None):
        """
        初始化动态EIP712解析器
        
        Args:
            enable_nlp: 是否启用NLP自然语言生成功能
            nlp_config: NLP配置字典
        """
        self.types: Dict[str, List[Dict[str, str]]] = {}
        self.pattern_matcher = PatternMatcher()
        self.value_analyzer = ValueAnalyzer()
        self.description_formatter = DescriptionFormatter()
        self.result_formatter = ResultFormatter()
        
        # NLP自然语言生成功能
        self.enable_nlp = enable_nlp
        self.nlp_generator = None
        if enable_nlp:
            try:
                self.nlp_generator = create_nlp_generator()
                print("🔤 NLP自然语言生成器已启用")
            except Exception as e:
                print(f"⚠️ NLP自然语言生成器初始化失败: {e}")
                self.enable_nlp = False
    
    def parse(self, eip712_data: Dict[str, Any]) -> EIP712ParseResult:
        """
        解析 EIP712 数据
        
        Args:
            eip712_data: EIP712 格式的数据
            
        Returns:
            解析结果
        """
        if not self._validate_eip712_data(eip712_data):
            raise ValueError("无效的 EIP712 数据格式")
        
        self.types = eip712_data['types']
        
        # 解析域信息
        domain_struct = self._parse_struct("EIP712Domain", eip712_data['domain'])
        
        # 解析主要消息
        primary_type = eip712_data['primaryType']
        message_struct = self._parse_struct(primary_type, eip712_data['message'])
        
        return EIP712ParseResult(
            domain=domain_struct,
            primary_type=primary_type,
            message=message_struct,
            raw_data=eip712_data
        )
    
    def _validate_eip712_data(self, data: Dict[str, Any]) -> bool:
        """验证 EIP712 数据格式"""
        required_fields = ['types', 'domain', 'primaryType', 'message']
        
        for field in required_fields:
            if field not in data:
                return False
        
        if 'EIP712Domain' not in data['types']:
            return False
        
        if data['primaryType'] not in data['types']:
            return False
        
        return True
    
    def _parse_struct(self, struct_name: str, struct_data: Dict[str, Any]) -> StructInfo:
        """
        解析结构体（增强版）
        
        Args:
            struct_name: 结构体名称
            struct_data: 结构体数据
            
        Returns:
            结构体信息
        """
        if struct_name not in self.types:
            raise ValueError(f"未找到结构体定义: {struct_name}")
        
        struct_definition = self.types[struct_name]
        field_names = [field_def['name'] for field_def in struct_definition]
        
        # 检测结构体上下文类型
        struct_context = self._detect_struct_context(struct_name, field_names)
        
        fields = []
        for field_def in struct_definition:
            field_name = field_def['name']
            field_type = field_def['type']
            field_value = struct_data.get(field_name)
            
            field_info = self._parse_field(field_name, field_type, field_value, struct_context)
            fields.append(field_info)
        
        description = self.description_formatter.generate_struct_description(
            struct_name, fields, struct_context
        )
        
        return StructInfo(
            name=struct_name,
            fields=fields,
            description=description,
            struct_type=struct_context
        )
    
    def _parse_field(self, field_name: str, field_type: str, field_value: Any, struct_context: Optional[str] = None) -> FieldInfo:
        """
        解析字段（增强版）
        
        Args:
            field_name: 字段名
            field_type: 字段类型
            field_value: 字段值
            struct_context: 结构体上下文
            
        Returns:
            字段信息
        """
        # 解析类型
        is_array = field_type.endswith('[]')
        array_element_type = None
        base_type = field_type
        
        if is_array:
            base_type = field_type[:-2]
            array_element_type = base_type
        
        # 推断字段类型
        inferred_type = self._infer_field_type(field_name, base_type, field_value)
        
        # 推断语义
        semantic = self._infer_semantic(field_name, base_type, field_value, struct_context)
        
        # 处理子结构
        children = []
        if base_type in self.types and field_value is not None:
            if is_array and isinstance(field_value, list):
                for i, item in enumerate(field_value):
                    if isinstance(item, dict):
                        child_struct = self._parse_struct(base_type, item)
                        child_field = FieldInfo(
                            name=f"[{i}]",
                            type_name=base_type,
                            field_type=FieldType.STRUCT,
                            semantic=None,
                            value=item,
                            description=f"数组元素 {i}",
                            children=[FieldInfo(
                                name=child.name,
                                type_name=child.type_name,
                                field_type=child.field_type,
                                semantic=child.semantic,
                                value=child.value,
                                description=child.description
                            ) for child in child_struct.fields]
                        )
                        children.append(child_field)
            elif isinstance(field_value, dict):
                child_struct = self._parse_struct(base_type, field_value)
                children = [FieldInfo(
                    name=child.name,
                    type_name=child.type_name,
                    field_type=child.field_type,
                    semantic=child.semantic,
                    value=child.value,
                    description=child.description
                ) for child in child_struct.fields]
        
        # 收集上下文提示
        context_hints = []
        if struct_context:
            context_hints.append(f"结构体类型: {struct_context}")
        
        # 生成描述
        description = self.description_formatter.generate_field_description(
            field_name, inferred_type, semantic, field_value
        )
        
        return FieldInfo(
            name=field_name,
            type_name=field_type,
            field_type=inferred_type,
            semantic=semantic,
            value=field_value,
            description=description,
            is_array=is_array,
            array_element_type=array_element_type,
            children=children,
            context_hints=context_hints
        )
    
    def _detect_struct_context(self, struct_name: str, field_names: List[str]) -> Optional[str]:
        """检测结构体上下文类型"""
        return self.pattern_matcher.detect_context(struct_name, field_names)
    
    def _infer_field_type(self, field_name: str, field_type: str, field_value: Any) -> FieldType:
        """推断字段类型（增强版）"""
        field_name_lower = field_name.lower()
        
        # 首先使用值分析器
        result = self.value_analyzer.analyze_value(field_name, field_type, field_value)
        if result:
            return result[0]
        
        # 使用类型模式匹配
        inferred_type = self.pattern_matcher.infer_field_type(field_name, field_type)
        if inferred_type != FieldType.UNKNOWN:
            return inferred_type
        
        # 基于字段类型的默认推断
        if field_type.startswith('uint') or field_type.startswith('int'):
            # 进一步推断是否为金额、时间戳等
            if any(keyword in field_name_lower for keyword in ['amount', 'value', 'price', 'fee', 'cost', 'quantity']):
                return FieldType.AMOUNT
            elif any(keyword in field_name_lower for keyword in ['time', 'deadline', 'expiry', 'expires', 'timestamp']):
                return FieldType.TIMESTAMP
            elif 'nonce' in field_name_lower:
                return FieldType.NONCE
            else:
                return FieldType.UINT if field_type.startswith('uint') else FieldType.INT
        
        elif field_type == 'address':
            # 根据字段名推断地址类型
            if any(keyword in field_name_lower for keyword in ['token', 'erc20', 'erc721', 'erc1155']):
                return FieldType.TOKEN_ADDRESS
            elif any(keyword in field_name_lower for keyword in ['contract', 'verifying']):
                return FieldType.CONTRACT_ADDRESS
            else:
                return FieldType.USER_ADDRESS
        
        elif field_type == 'string':
            return FieldType.STRING
        
        elif field_type == 'bool':
            return FieldType.BOOL
        
        elif field_type.startswith('bytes'):
            if 'hash' in field_name_lower:
                return FieldType.HASH
            elif 'signature' in field_name_lower:
                return FieldType.SIGNATURE
            else:
                return FieldType.BYTES
        
        elif field_type in self.types:
            return FieldType.STRUCT
        
        elif field_type.endswith('[]'):
            return FieldType.ARRAY
        
        else:
            return FieldType.STRING  # 默认类型
    
    def _infer_semantic(self, field_name: str, field_type: str, field_value: Any, struct_context: Optional[str] = None) -> Optional[FieldSemantic]:
        """推断字段语义"""
        # 首先使用值分析器
        result = self.value_analyzer.analyze_value(field_name, field_type, field_value)
        if result and result[1]:
            return result[1]
        
        # 使用语义模式匹配
        semantic = self.pattern_matcher.infer_semantic(field_name)
        if semantic:
            return semantic
        
        return None
    
    def format_result(self, result: EIP712ParseResult) -> str:
        """格式化解析结果为可读文本"""
        return self.result_formatter.format_result(result)
    
    def analyze_eip712(self, eip712_data: Dict[str, Any]) -> dict:
        """分析EIP712数据并返回结构化结果"""
        result = self.parse(eip712_data)
        return self.result_formatter.format_structured_analysis(result)
    
    def parse_and_format(self, eip712_data: Dict[str, Any]) -> str:
        """解析并格式化EIP712数据"""
        result = self.parse(eip712_data)
        return self.format_result(result)
    
    def generate_natural_language(self, eip712_data: Dict[str, Any]) -> NaturalLanguageOutput:
        """
        生成自然语言描述
        
        Args:
            eip712_data: EIP712格式数据
            
        Returns:
            NaturalLanguageOutput: 自然语言输出结果
            
        Raises:
            ValueError: 如果NLP功能未启用
        """
        if not self.enable_nlp or not self.nlp_generator:
            raise ValueError("NLP自然语言生成功能未启用。请在初始化时设置 enable_nlp=True")
        
        return self.nlp_generator.convert_to_natural_language(eip712_data)
    
    def analyze_with_natural_language(self, eip712_data: Dict[str, Any]) -> dict:
        """
        结合传统分析和自然语言生成的完整分析
        
        Args:
            eip712_data: EIP712格式数据
            
        Returns:
            dict: 包含传统分析结果和自然语言描述的完整分析
        """
        # 进行传统分析
        traditional_result = self.analyze_eip712(eip712_data)
        
        # 如果启用了NLP功能，添加自然语言描述
        natural_language_result = None
        if self.enable_nlp and self.nlp_generator:
            try:
                nl_output = self.generate_natural_language(eip712_data)
                natural_language_result = {
                    "title": nl_output.title,
                    "summary": nl_output.summary,
                    "detailed_description": nl_output.detailed_description,
                    "field_descriptions": nl_output.field_descriptions,
                    "context": nl_output.context,
                    "action_summary": nl_output.action_summary
                }
            except Exception as e:
                print(f"⚠️ 自然语言生成失败: {e}")
        
        return {
            "traditional_analysis": traditional_result,
            "natural_language": natural_language_result,
            "has_natural_language": natural_language_result is not None
        } 