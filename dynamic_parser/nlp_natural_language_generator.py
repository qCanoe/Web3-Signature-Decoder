"""
NLP自然语言生成器
使用模板系统将结构化数据转换为流畅的中文描述
"""

import json
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NaturalLanguageOutput:
    """自然语言输出结果"""
    title: str  # 标题描述
    summary: str  # 简要总结
    detailed_description: str  # 详细描述
    field_descriptions: List[str]  # 字段描述列表
    context: str  # 上下文说明
    action_summary: str  # 操作总结


class StructuredDataToNLConverter:
    """结构化数据到自然语言转换器"""
    
    def __init__(self):
        """
        初始化NLP生成器
        """
        # 初始化模板和映射
        self._init_templates()
        self._init_semantic_mappings()
    

    
    def _init_templates(self):
        """初始化自然语言模板"""
        self.action_templates = {
            "permit": "这是一个代币授权操作，{owner}正在授权{spender}可以代表其花费最多{value}个代币，授权有效期至{deadline}。",
            "order": "这是一个市场订单，{offerer}正在出售{offer_items}，期望获得{consideration_items}作为交换。",
            "vote": "这是一个治理投票，{voter}对提案{proposal}投出了{support}票。",
            "transfer": "这是一个转账操作，将{amount}从{from}转移到{to}。",
            "mint": "这是一个铸币操作，为{recipient}铸造{amount}个代币。",
            "burn": "这是一个销毁操作，销毁{amount}个代币。",
            "swap": "这是一个代币交换操作，用{input_amount}个{input_token}兑换{output_amount}个{output_token}。"
        }
        
        self.context_descriptions = {
            "permit": "代币授权许可",
            "order": "市场交易订单", 
            "vote": "治理投票决策",
            "transfer": "资产转移",
            "mint": "代币铸造",
            "burn": "代币销毁",
            "swap": "代币交换",
            "governance": "治理操作",
            "auction": "拍卖竞价",
            "liquidity": "流动性操作"
        }
    
    def _init_semantic_mappings(self):
        """初始化语义映射"""
        self.field_semantic_map = {
            "owner": "代币持有者",
            "spender": "授权支出者", 
            "recipient": "接收者",
            "offerer": "出价者",
            "bidder": "竞拍者",
            "voter": "投票者",
            "value": "数量",
            "amount": "金额",
            "price": "价格",
            "fee": "手续费",
            "deadline": "截止时间",
            "timestamp": "时间戳",
            "startTime": "开始时间",
            "endTime": "结束时间",
            "nonce": "防重放随机数",
            "chainId": "区块链网络ID",
            "verifyingContract": "验证合约地址",
            "token": "代币合约地址",
            "tokenId": "代币ID",
            "salt": "盐值",
            "counter": "计数器"
        }
    
    def convert_to_natural_language(self, eip712_data: Dict[str, Any]) -> NaturalLanguageOutput:
        """
        将EIP712结构化数据转换为自然语言描述
        
        Args:
            eip712_data: EIP712格式的结构化数据
            
        Returns:
            NaturalLanguageOutput: 自然语言输出结果
        """
        # 分析数据结构
        primary_type = eip712_data.get("primaryType", "")
        domain = eip712_data.get("domain", {})
        message = eip712_data.get("message", {})
        types = eip712_data.get("types", {})
        
        # 推断操作类型
        operation_type = self._infer_operation_type(primary_type, message, types)
        
        # 生成各部分描述
        title = self._generate_title(operation_type, primary_type, domain)
        summary = self._generate_summary(operation_type, message, domain)
        detailed_description = self._generate_detailed_description(operation_type, message, types)
        field_descriptions = self._generate_field_descriptions(message, types.get(primary_type, []))
        context = self._generate_context_description(operation_type, domain)
        action_summary = self._generate_action_summary(operation_type, message)
        
        return NaturalLanguageOutput(
            title=title,
            summary=summary,
            detailed_description=detailed_description,
            field_descriptions=field_descriptions,
            context=context,
            action_summary=action_summary
        )
    
    def _infer_operation_type(self, primary_type: str, message: Dict, types: Dict) -> str:
        """推断操作类型"""
        primary_lower = primary_type.lower()
        
        # 基于主类型推断
        if "permit" in primary_lower:
            return "permit"
        elif "order" in primary_lower or "offer" in str(message):
            return "order"
        elif "vote" in primary_lower:
            return "vote"
        elif "transfer" in primary_lower:
            return "transfer"
        elif "mint" in primary_lower:
            return "mint"
        elif "burn" in primary_lower:
            return "burn"
        elif "swap" in primary_lower:
            return "swap"
        
        # 基于字段推断
        message_fields = set(message.keys())
        if {"owner", "spender", "value"}.issubset(message_fields):
            return "permit"
        elif {"offerer", "offer", "consideration"}.intersection(message_fields):
            return "order"
        elif {"voter", "proposal"}.intersection(message_fields):
            return "vote"
        
        return "general"
    
    def _generate_title(self, operation_type: str, primary_type: str, domain: Dict) -> str:
        """生成标题"""
        app_name = domain.get("name", "未知应用")
        context_name = self.context_descriptions.get(operation_type, "数据结构")
        return f"{app_name} - {context_name} ({primary_type})"
    
    def _generate_summary(self, operation_type: str, message: Dict, domain: Dict) -> str:
        """生成摘要"""
        app_name = domain.get("name", "应用")
        
        if operation_type == "permit":
            owner = self._format_address(message.get("owner", ""))
            spender = self._format_address(message.get("spender", ""))
            value = self._format_amount(message.get("value", ""))
            return f"在{app_name}中，地址{owner}授权地址{spender}可以代表其使用最多{value}的代币。"
        
        elif operation_type == "order":
            offerer = self._format_address(message.get("offerer", ""))
            return f"在{app_name}中，地址{offerer}创建了一个市场交易订单。"
        
        elif operation_type == "vote":
            voter = self._format_address(message.get("voter", ""))
            return f"在{app_name}治理系统中，地址{voter}进行了投票操作。"
        
        else:
            return f"在{app_name}中进行的{self.context_descriptions.get(operation_type, '数据')}操作。"
    
    def _generate_detailed_description(self, operation_type: str, message: Dict, types: Dict) -> str:
        """生成详细描述"""
        return self._generate_template_description(operation_type, message)
    
    def _generate_template_description(self, operation_type: str, message: Dict) -> str:
        """基于模板生成描述"""
        if operation_type == "permit":
            owner = self._format_address(message.get("owner"))
            spender = self._format_address(message.get("spender"))
            value = self._format_amount(message.get("value"))
            deadline = self._format_timestamp(message.get("deadline"))
            nonce = message.get("nonce", "未指定")
            
            return f"""这是一个ERC-20代币授权许可操作。具体详情如下：

授权方：{owner}
被授权方：{spender}  
授权金额：{value}
授权截止时间：{deadline}
防重放随机数：{nonce}

该授权允许被授权方在截止时间之前，代表授权方花费指定数量的代币，常用于DeFi协议中的代币交换和流动性操作。"""

        elif operation_type == "order":
            offerer = self._format_address(message.get("offerer"))
            offer = message.get("offer", [])
            consideration = message.get("consideration", [])
            start_time = self._format_timestamp(message.get("startTime"))
            end_time = self._format_timestamp(message.get("endTime"))
            
            offer_desc = self._describe_items(offer, "出售")
            consideration_desc = self._describe_items(consideration, "期望获得")
            
            return f"""这是一个NFT/代币市场交易订单。具体详情如下：

出价者：{offerer}
{offer_desc}
{consideration_desc}
订单生效时间：{start_time}
订单截止时间：{end_time}

该订单定义了一个去中心化市场中的交易意向，任何人都可以在有效期内执行此订单完成交易。"""

        else:
            field_count = len(message)
            return f"这是一个包含{field_count}个字段的区块链数据结构，用于在去中心化应用中执行特定的操作或记录重要信息。"
    

    
    def _generate_field_descriptions(self, message: Dict, type_fields: List[Dict]) -> List[str]:
        """生成字段描述列表"""
        descriptions = []
        
        for field_def in type_fields:
            field_name = field_def["name"]
            field_type = field_def["type"]
            field_value = message.get(field_name)
            
            if field_value is not None:
                semantic_name = self.field_semantic_map.get(field_name, field_name)
                formatted_value = self._format_field_value(field_name, field_value, field_type)
                descriptions.append(f"• {semantic_name}: {formatted_value}")
        
        return descriptions
    
    def _generate_context_description(self, operation_type: str, domain: Dict) -> str:
        """生成上下文描述"""
        app_name = domain.get("name", "未知应用")
        version = domain.get("version", "")
        chain_id = domain.get("chainId", "")
        
        chain_name = self._get_chain_name(chain_id)
        version_text = f"v{version}" if version else ""
        
        return f"此操作发生在{chain_name}网络上的{app_name}{version_text}应用中。"
    
    def _generate_action_summary(self, operation_type: str, message: Dict) -> str:
        """生成操作总结"""
        if operation_type == "permit":
            return f"授权代币使用权限给第三方地址"
        elif operation_type == "order":
            return f"创建去中心化市场交易订单"
        elif operation_type == "vote":
            return f"参与去中心化治理投票"
        elif operation_type == "transfer":
            return f"执行资产转移操作"
        else:
            return f"执行{self.context_descriptions.get(operation_type, '区块链')}操作"
    
    def _format_address(self, address: str) -> str:
        """格式化地址显示"""
        if not address or len(address) < 10:
            return address
        return f"{address[:6]}...{address[-4:]}"
    
    def _format_amount(self, amount: Any) -> str:
        """格式化金额显示"""
        try:
            amount_int = int(amount)
            # 假设是18位小数的代币
            if amount_int > 10**15:  # 大于0.001个代币
                eth_amount = amount_int / 10**18
                return f"{eth_amount:.6f} 代币"
            else:
                return f"{amount_int} 单位"
        except:
            return str(amount)
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """格式化时间戳"""
        try:
            ts = int(timestamp)
            if ts > 1000000000:  # Unix时间戳
                dt = datetime.datetime.fromtimestamp(ts)
                return dt.strftime("%Y年%m月%d日 %H:%M:%S")
        except:
            pass
        return str(timestamp)
    
    def _format_field_value(self, field_name: str, value: Any, field_type: str) -> str:
        """格式化字段值"""
        if "address" in field_type.lower() or field_name.lower().endswith(("er", "to", "from")):
            return self._format_address(str(value))
        elif field_name.lower() in ["deadline", "timestamp", "starttime", "endtime"]:
            return self._format_timestamp(value)
        elif field_name.lower() in ["value", "amount", "price"] and isinstance(value, (int, str)):
            return self._format_amount(value)
        elif isinstance(value, list):
            return f"包含{len(value)}个项目的数组"
        elif isinstance(value, dict):
            return f"包含{len(value)}个字段的对象"
        else:
            return str(value)
    
    def _describe_items(self, items: List[Dict], action: str) -> str:
        """描述物品列表"""
        if not items:
            return f"{action}：无"
        
        descriptions = []
        for i, item in enumerate(items):
            item_type = item.get("itemType", 0)
            token = item.get("token", "")
            amount = item.get("startAmount", item.get("amount", "1"))
            
            if item_type == 0:  # ETH
                eth_amount = int(amount) / 10**18 if amount else 0
                descriptions.append(f"  {i+1}. {eth_amount:.6f} ETH")
            elif item_type == 1:  # ERC20
                token_addr = self._format_address(token)
                formatted_amount = self._format_amount(amount)
                descriptions.append(f"  {i+1}. {formatted_amount} (代币: {token_addr})")
            elif item_type == 2:  # ERC721
                token_id = item.get("identifierOrCriteria", "")
                token_addr = self._format_address(token)
                descriptions.append(f"  {i+1}. NFT #{token_id} (合约: {token_addr})")
            else:
                descriptions.append(f"  {i+1}. 其他类型物品")
        
        return f"{action}：\n" + "\n".join(descriptions)
    
    def _get_chain_name(self, chain_id: Any) -> str:
        """获取链名称"""
        chain_names = {
            1: "以太坊主网",
            5: "Goerli测试网", 
            11155111: "Sepolia测试网",
            137: "Polygon主网",
            56: "BSC主网"
        }
        try:
            return chain_names.get(int(chain_id), f"链ID {chain_id}")
        except:
            return "未知网络"


def create_nlp_generator() -> StructuredDataToNLConverter:
    """
    创建NLP自然语言生成器实例
    
    Returns:
        StructuredDataToNLConverter: 生成器实例
    """
    return StructuredDataToNLConverter() 