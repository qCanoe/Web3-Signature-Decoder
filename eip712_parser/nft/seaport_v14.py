"""
Seaport v1.4 NFT 市场解析器
"""

from typing import List
from ..types import EIP712Like, NFTMessage, TransactionLike
from .seaport import Seaport


class SeaportV14(Seaport):
    """Seaport v1.4 NFT 市场解析器"""
    
    @staticmethod
    def parse(typed_data: EIP712Like) -> NFTMessage:
        """
        解析 Seaport v1.4 EIP712 消息
        
        Args:
            typed_data: EIP712 格式的数据
            
        Returns:
            解析后的 NFT 消息
            
        Raises:
            ValueError: 当数据格式不正确时
        """
        # 检查版本
        domain = typed_data.get('domain', {})
        version = domain.get('version', '')
        
        if version != '1.4':
            raise ValueError("不是 Seaport v1.4 消息格式")
        
        # 使用父类的解析逻辑，但可以根据需要进行版本特定的修改
        return super().parse(typed_data) 