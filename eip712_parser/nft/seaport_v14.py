"""
Seaport v1.4 NFT marketplace parser
"""

from typing import List
from ..types import EIP712Like, NFTMessage, TransactionLike
from .seaport import Seaport


class SeaportV14(Seaport):
    """Seaport v1.4 NFT marketplace parser"""
    
    @staticmethod
    def parse(typed_data: EIP712Like) -> NFTMessage:
        """
        Parse Seaport v1.4 EIP712 message
        
        Args:
            typed_data: EIP712 format data
            
        Returns:
            Parsed NFT message
            
        Raises:
            ValueError: When data format is incorrect
        """
        # Check version
        domain = typed_data.get('domain', {})
        version = domain.get('version', '')
        
        if version != '1.4':
            raise ValueError("Not a Seaport v1.4 message format")
        
        # Use parent class parsing logic, but can make version-specific modifications as needed
        return super().parse(typed_data) 