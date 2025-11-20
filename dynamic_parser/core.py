"""
Dynamic Parser Core Module
Contains main parsing logic, field inference and struct parsing functionality
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
    """Dynamic EIP712 Parser Core Class"""
    
    def __init__(self, enable_nlp: bool = False, nlp_config: Optional[Dict[str, Any]] = None):
        """
        Initialize dynamic EIP712 parser
        
        Args:
            enable_nlp: Whether to enable NLP natural language generation
            nlp_config: NLP configuration dictionary
        """
        self.types: Dict[str, List[Dict[str, str]]] = {}
        self.pattern_matcher = PatternMatcher()
        self.value_analyzer = ValueAnalyzer()
        self.description_formatter = DescriptionFormatter()
        self.result_formatter = ResultFormatter()
        
        # NLP natural language generation functionality
        self.enable_nlp = enable_nlp
        self.nlp_generator = None
        if enable_nlp:
            try:
                self.nlp_generator = create_nlp_generator()
                print("🔤 NLP natural language generator enabled")
            except Exception as e:
                print(f"⚠️ NLP natural language generator initialization failed: {e}")
                self.enable_nlp = False
    
    def parse(self, eip712_data: Dict[str, Any]) -> EIP712ParseResult:
        """
        Parse EIP712 data
        
        Args:
            eip712_data: EIP712 format data
            
        Returns:
            Parsing result
        """
        if not self._validate_eip712_data(eip712_data):
            raise ValueError("Invalid EIP712 data format")
        
        self.types = eip712_data['types']
        
        # Parse domain information
        domain_struct = self._parse_struct("EIP712Domain", eip712_data['domain'])
        
        # Parse primary message
        primary_type = eip712_data['primaryType']
        message_struct = self._parse_struct(primary_type, eip712_data['message'])
        
        return EIP712ParseResult(
            domain=domain_struct,
            primary_type=primary_type,
            message=message_struct,
            raw_data=eip712_data
        )
    
    def _validate_eip712_data(self, data: Dict[str, Any]) -> bool:
        """Validate EIP712 data format"""
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
        Parse struct (enhanced version)
        
        Args:
            struct_name: Struct name
            struct_data: Struct data
            
        Returns:
            Struct information
        """
        if struct_name not in self.types:
            raise ValueError(f"Struct definition not found: {struct_name}")
        
        struct_definition = self.types[struct_name]
        field_names = [field_def['name'] for field_def in struct_definition]
        
        # Detect struct context type
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
        Parse field (enhanced version)
        
        Args:
            field_name: Field name
            field_type: Field type
            field_value: Field value
            struct_context: Struct context
            
        Returns:
            Field information
        """
        # Parse type
        is_array = field_type.endswith('[]')
        array_element_type = None
        base_type = field_type
        
        if is_array:
            base_type = field_type[:-2]
            array_element_type = base_type
        
        # Infer field type
        inferred_type = self._infer_field_type(field_name, base_type, field_value)
        
        # Infer semantic
        semantic = self._infer_semantic(field_name, base_type, field_value, struct_context)
        
        # Handle child structures
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
                            description=f"Array element {i}",
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
        
        # Collect context hints
        context_hints = []
        if struct_context:
            context_hints.append(f"Struct type: {struct_context}")
        
        # Generate description
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
        """Detect struct context type"""
        return self.pattern_matcher.detect_context(struct_name, field_names)
    
    def _infer_field_type(self, field_name: str, field_type: str, field_value: Any) -> FieldType:
        """Infer field type (enhanced version)"""
        field_name_lower = field_name.lower()
        
        # First use value analyzer
        result = self.value_analyzer.analyze_value(field_name, field_type, field_value)
        if result:
            return result[0]
        
        # Use type pattern matching
        inferred_type = self.pattern_matcher.infer_field_type(field_name, field_type)
        if inferred_type != FieldType.UNKNOWN:
            return inferred_type
        
        # Default inference based on field type
        if field_type.startswith('uint') or field_type.startswith('int'):
            # Further infer if it's amount, timestamp, etc.
            if any(keyword in field_name_lower for keyword in ['amount', 'value', 'price', 'fee', 'cost', 'quantity']):
                return FieldType.AMOUNT
            elif any(keyword in field_name_lower for keyword in ['time', 'deadline', 'expiry', 'expires', 'timestamp']):
                return FieldType.TIMESTAMP
            elif 'nonce' in field_name_lower:
                return FieldType.NONCE
            else:
                return FieldType.UINT if field_type.startswith('uint') else FieldType.INT
        
        elif field_type == 'address':
            # Infer address type based on field name
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
            return FieldType.STRING  # Default type
    
    def _infer_semantic(self, field_name: str, field_type: str, field_value: Any, struct_context: Optional[str] = None) -> Optional[FieldSemantic]:
        """Infer field semantic"""
        # First use value analyzer
        result = self.value_analyzer.analyze_value(field_name, field_type, field_value)
        if result and result[1]:
            return result[1]
        
        # Use semantic pattern matching
        semantic = self.pattern_matcher.infer_semantic(field_name)
        if semantic:
            return semantic
        
        return None
    
    def format_result(self, result: EIP712ParseResult) -> str:
        """Format parsing result as readable text"""
        return self.result_formatter.format_result(result)
    
    def analyze_eip712(self, eip712_data: Dict[str, Any]) -> dict:
        """Analyze EIP712 data and return structured result"""
        result = self.parse(eip712_data)
        return self.result_formatter.format_structured_analysis(result)
    
    def parse_and_format(self, eip712_data: Dict[str, Any]) -> str:
        """Parse and format EIP712 data"""
        result = self.parse(eip712_data)
        return self.format_result(result)
    
    def generate_natural_language(self, eip712_data: Dict[str, Any]) -> NaturalLanguageOutput:
        """
        Generate natural language description
        
        Args:
            eip712_data: EIP712 format data
            
        Returns:
            NaturalLanguageOutput: Natural language output result
            
        Raises:
            ValueError: If NLP functionality is not enabled
        """
        if not self.enable_nlp or not self.nlp_generator:
            raise ValueError("NLP natural language generation is not enabled. Please set enable_nlp=True during initialization")
        
        return self.nlp_generator.convert_to_natural_language(eip712_data)
    
    def analyze_with_natural_language(self, eip712_data: Dict[str, Any]) -> dict:
        """
        Complete analysis combining traditional analysis and natural language generation
        
        Args:
            eip712_data: EIP712 format data
            
        Returns:
            dict: Complete analysis including traditional analysis results and natural language description
        """
        # Perform traditional analysis
        traditional_result = self.analyze_eip712(eip712_data)
        
        # If NLP is enabled, add natural language description
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
                print(f"⚠️ Natural language generation failed: {e}")
        
        return {
            "traditional_analysis": traditional_result,
            "natural_language": natural_language_result,
            "has_natural_language": natural_language_result is not None
        } 