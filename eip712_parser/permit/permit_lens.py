"""
PermitLens parser
"""

from typing import List
from ..types import EIP712Like, PermitMessage, Approval, TransactionLike


class PermitLens:
    """PermitLens parser"""
    
    @staticmethod
    def parse(typed_data: EIP712Like) -> PermitMessage:
        """
        Parse PermitLens EIP712 message
        
        Args:
            typed_data: EIP712 format data
            
        Returns:
            Parsed PermitLens message
            
        Raises:
            ValueError: When data format is incorrect
        """
        primary_type = typed_data.get('primaryType', '')
        
        # Check if it's a PermitLens message format
        if 'PermitForAll' not in primary_type:
            raise ValueError("Not a valid PermitLens message format")
        
        message = typed_data['message']
        
        # Parse PermitForAll message
        approval = Approval(
            spender=message['operator'],
            amount="1",  # PermitForAll is usually a boolean value
            nonce=str(message['nonce']),
            expiration=str(message['deadline'])
        )
        
        return PermitMessage(permits=[approval])
    
    @staticmethod
    def parse_from_transaction(transaction: TransactionLike) -> List[PermitMessage]:
        """
        Parse PermitLens messages from transaction data
        
        Args:
            transaction: Transaction data
            
        Returns:
            List of parsed PermitLens messages
        """
        # TODO: Implement logic to parse from transaction
        return [] 