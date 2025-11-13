"""
动态解析器格式化器
包含字段描述生成、结构体描述生成和结果格式化功能
"""

import datetime
from typing import Any, List, Optional
from .field_types import FieldInfo, StructInfo, EIP712ParseResult, FieldType, FieldSemantic


class DescriptionFormatter:
    """描述格式化器"""
    
    def __init__(self):
        self.semantic_descriptions = self._init_semantic_descriptions()
        self.type_descriptions = self._init_type_descriptions()
        self.context_descriptions = self._init_context_descriptions()
    
    def _init_semantic_descriptions(self) -> dict:
        """初始化语义描述映射"""
        return {
            # 身份相关
            FieldSemantic.OWNER: "拥有者地址",
            FieldSemantic.SPENDER: "授权花费者地址", 
            FieldSemantic.RECIPIENT: "接收者地址",
            FieldSemantic.TRADER: "交易者地址",
            FieldSemantic.OFFERER: "报价者地址",
            FieldSemantic.BIDDER: "竞拍者地址",
            FieldSemantic.SELLER: "卖方地址",
            FieldSemantic.BUYER: "买方地址",
            FieldSemantic.VALIDATOR: "验证者地址",
            FieldSemantic.DELEGATE: "委托者地址",
            FieldSemantic.CREATOR: "创建者地址",
            
            # 金额相关
            FieldSemantic.VALUE: "数值",
            FieldSemantic.AMOUNT: "金额",
            FieldSemantic.PRICE: "价格",
            FieldSemantic.FEE: "手续费",
            FieldSemantic.REWARD: "奖励金额",
            FieldSemantic.PENALTY: "惩罚金额",
            FieldSemantic.BALANCE: "余额",
            FieldSemantic.ALLOWANCE: "授权额度",
            FieldSemantic.MINIMUM: "最小值",
            FieldSemantic.MAXIMUM: "最大值",
            FieldSemantic.LIQUIDITY: "流动性",
            FieldSemantic.SLIPPAGE: "滑点",
            FieldSemantic.RATE: "比率",
            FieldSemantic.YIELD: "收益率",
            FieldSemantic.ROYALTY: "版税",
            
            # 时间相关
            FieldSemantic.TIMESTAMP: "时间戳",
            FieldSemantic.DEADLINE: "截止时间",
            FieldSemantic.START_TIME: "开始时间",
            FieldSemantic.END_TIME: "结束时间",
            FieldSemantic.DURATION: "持续时间",
            FieldSemantic.DELAY: "延迟时间",
            FieldSemantic.PERIOD: "周期",
            
            # 标识相关
            FieldSemantic.TOKEN_ID: "代币ID",
            FieldSemantic.NONCE: "随机数",
            FieldSemantic.SALT: "盐值",
            FieldSemantic.INDEX: "索引",
            FieldSemantic.ID: "标识符",
            FieldSemantic.KEY: "键值",
            FieldSemantic.COUNTER: "计数器",
            
            # 数据相关
            FieldSemantic.DATA: "数据",
            FieldSemantic.HASH: "哈希值",
            FieldSemantic.SIGNATURE: "签名",
            FieldSemantic.PROOF: "证明",
            FieldSemantic.MERKLE_ROOT: "默克尔根",
            FieldSemantic.METADATA: "元数据",
            
            # 配置相关
            FieldSemantic.VERSION: "版本号",
            FieldSemantic.CHAIN_ID: "链ID",
            FieldSemantic.TYPE: "类型",
            FieldSemantic.STATUS: "状态",
            FieldSemantic.FLAG: "标志",
            FieldSemantic.OPTION: "选项",
            
            # 治理相关
            FieldSemantic.PROPOSAL_ID: "提案ID",
            FieldSemantic.VOTE_TYPE: "投票类型",
            FieldSemantic.VOTING_POWER: "投票权重",
            
            # NFT相关
            FieldSemantic.COLLECTION: "合集地址",
            FieldSemantic.POOL: "资金池",
        }
    
    def _init_type_descriptions(self) -> dict:
        """初始化类型描述映射"""
        return {
            FieldType.TOKEN_ADDRESS: "代币合约地址",
            FieldType.USER_ADDRESS: "用户地址", 
            FieldType.CONTRACT_ADDRESS: "合约地址",
            FieldType.AMOUNT: "金额数值",
            FieldType.TIMESTAMP: "时间戳",
            FieldType.NONCE: "随机数",
            FieldType.HASH: "哈希值",
            FieldType.SIGNATURE: "签名数据",
        }
    
    def _init_context_descriptions(self) -> dict:
        """初始化上下文描述映射"""
        return {
            "permit": "允许第三方代表用户操作代币",
            "order": "定义交易的报价条件和期望",
            "vote": "记录对提案的投票决策",
            "transfer": "定义资产转移的详细信息",
            "mint": "定义新代币的创建参数",
            "burn": "定义代币销毁的操作",
            "governance": "定义治理提案和执行参数",
            "auction": "定义拍卖的竞价和条件",
            "swap": "定义代币交换的参数",
            "liquidity": "定义流动性操作的参数",
        }
    
    def generate_field_description(self, field_name: str, field_type: FieldType, semantic: Optional[FieldSemantic], field_value: Any) -> str:
        """生成字段描述"""
        base_desc = f"字段 '{field_name}'"
        
        # 添加语义描述
        if semantic:
            semantic_desc = self.semantic_descriptions.get(semantic, semantic.value)
            base_desc += f" ({semantic_desc})"
        
        # 添加类型描述
        type_desc = self.type_descriptions.get(field_type)
        if type_desc:
            base_desc += f" - {type_desc}"
        
        # 添加值描述
        if field_value is not None:
            value_desc = self._format_field_value(field_type, field_value)
            if value_desc:
                base_desc += f" {value_desc}"
        
        return base_desc
    
    def _format_field_value(self, field_type: FieldType, field_value: Any) -> str:
        """格式化字段值"""
        if field_type == FieldType.TIMESTAMP and isinstance(field_value, (int, str)):
            try:
                timestamp = int(field_value)
                if timestamp > 1000000000:  # 看起来像时间戳
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    return f"(时间: {dt.strftime('%Y-%m-%d %H:%M:%S')})"
            except:
                pass
        
        elif field_type in [FieldType.TOKEN_ADDRESS, FieldType.USER_ADDRESS, FieldType.CONTRACT_ADDRESS]:
            return f"({field_value})"
        
        elif field_type == FieldType.AMOUNT and isinstance(field_value, (int, str)):
            try:
                # 尝试转换为 ETH 单位显示
                amount = int(field_value)
                
                # 检测无限授权 (常见的无限授权值)
                # uint256 max: 2^256 - 1
                # 也检测常见的"近似无限"值，如 2^255, 2^128 等
                MAX_UINT256 = 2**256 - 1
                NEAR_MAX_THRESHOLD = MAX_UINT256 - 10**15  # 允许一些浮动
                
                # 常见的"无限授权"模式
                COMMON_UNLIMITED_VALUES = [
                    MAX_UINT256,  # 完整的 uint256 最大值
                    2**255 - 1,   # 一些协议使用的值
                    2**128 - 1,   # 更保守的无限值
                ]
                
                # 检查是否为无限授权
                if amount >= NEAR_MAX_THRESHOLD:
                    return "⚠️ 无限授权 (UNLIMITED)"
                elif amount in COMMON_UNLIMITED_VALUES:
                    return "⚠️ 无限授权 (UNLIMITED)"
                elif amount > 10**50:  # 任何超过 10^50 的值都视为"实质上的无限"
                    return "⚠️ 无限授权 (UNLIMITED - 极大数值)"
                elif amount > 10**15:  # 如果大于 0.001 ETH
                    eth_amount = amount / 10**18
                    return f"({eth_amount:.6f} 代币)"
                else:
                    return f"({amount} 单位)"
            except:
                return f"({field_value})"
        
        elif isinstance(field_value, (str, int)) and len(str(field_value)) < 50:
            return f"= {field_value}"
        
        return ""
    
    def generate_struct_description(self, struct_name: str, fields: List[FieldInfo], struct_context: Optional[str] = None) -> str:
        """生成结构体描述"""
        # 根据结构体名称和字段推断用途
        if struct_name == "EIP712Domain":
            return "EIP712 域信息 - 定义签名的域和验证上下文"
        
        # 使用检测到的上下文
        if struct_context and struct_context in self.context_descriptions:
            context_desc = self.context_descriptions[struct_context]
            return f"{self._get_struct_type_name(struct_context)}结构 '{struct_name}' - {context_desc}"
        
        # 根据字段推断结构体用途（后备方案）
        field_names = [field.name.lower() for field in fields]
        
        if any(name in field_names for name in ['offerer', 'offer', 'consideration']):
            return f"市场订单结构 '{struct_name}' - 包含交易报价和期望条件"
        elif any(name in field_names for name in ['spender', 'value', 'deadline']):
            return f"授权许可结构 '{struct_name}' - 包含代币授权信息"
        elif any(name in field_names for name in ['to', 'value', 'data']):
            return f"交易结构 '{struct_name}' - 包含交易目标和数据"
        elif any(name in field_names for name in ['voter', 'proposal', 'support']):
            return f"治理投票结构 '{struct_name}' - 包含投票决策信息"
        else:
            return f"数据结构 '{struct_name}' - 包含 {len(fields)} 个字段"
    
    def _get_struct_type_name(self, struct_context: str) -> str:
        """获取结构体类型名称"""
        type_names = {
            "permit": "授权许可",
            "order": "市场订单",
            "vote": "治理投票",
            "transfer": "转账",
            "mint": "铸造",
            "burn": "销毁",
            "governance": "治理",
            "auction": "拍卖",
            "swap": "交换",
            "liquidity": "流动性",
        }
        return type_names.get(struct_context, "数据")


class ResultFormatter:
    """结果格式化器"""
    
    def format_result(self, result: EIP712ParseResult) -> str:
        """格式化解析结果为可读文本"""
        lines = []
        
        lines.append("=" * 60)
        lines.append("EIP712 签名结构解析结果")
        lines.append("=" * 60)
        
        # 域信息
        lines.append(f"\n域信息 ({result.domain.name}):")
        lines.append(f"   描述: {result.domain.description}")
        for field in result.domain.fields:
            lines.append(f"   • {field.description}")
        
        # 主要消息
        lines.append(f"\n主要消息 ({result.primary_type}):")
        lines.append(f"   描述: {result.message.description}")
        lines.append(f"   字段数量: {len(result.message.fields)}")
        
        lines.append(f"\n消息结构树:")
        self._format_struct_tree(result.message, lines, indent="   ")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)
    
    def _format_struct_tree(self, struct: StructInfo, lines: List[str], indent: str = ""):
        """格式化结构体树"""
        for i, field in enumerate(struct.fields):
            is_last = i == len(struct.fields) - 1
            tree_char = "└── " if is_last else "├── "
            next_indent = indent + ("    " if is_last else "│   ")
            
            lines.append(f"{indent}{tree_char}{field.description}")
            
            # 递归显示子字段
            if field.children:
                for j, child in enumerate(field.children):
                    child_is_last = j == len(field.children) - 1
                    child_tree_char = "└── " if child_is_last else "├── "
                    lines.append(f"{next_indent}{child_tree_char}{child.description}")
    
    def format_structured_analysis(self, result: EIP712ParseResult) -> dict:
        """格式化为结构化分析结果"""
        return {
            "primary_type": result.primary_type,
            "message_description": result.message.description,
            "field_count": len(result.message.fields),
            "fields": [
                {
                    "name": field.name,
                    "type": field.type_name,
                    "semantic": field.semantic.value if field.semantic else None,
                    "value": field.value,
                    "description": field.description,
                    "context_hints": field.context_hints
                }
                for field in result.message.fields
            ],
            "domain": {
                "name": result.domain.name,
                "description": result.domain.description,
                "fields": [
                    {
                        "name": field.name,
                        "value": field.value,
                        "description": field.description
                    }
                    for field in result.domain.fields
                ]
            }
        } 