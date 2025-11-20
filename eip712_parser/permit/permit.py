"""
Basic Permit parser
"""

from typing import List, Optional
from ..types import EIP712Like, PermitMessage, Approval, TransactionLike


class Permit:
    """Basic Permit parser"""
    
    @staticmethod
    def parse(typed_data: EIP712Like) -> PermitMessage:
        """
        Parse basic Permit EIP712 message
        
        Args:
            typed_data: EIP712 format data
            
        Returns:
            Parsed Permit message
            
        Raises:
            ValueError: When data format is incorrect
        """
        primary_type = typed_data.get('primaryType', '')
        
        # Check if it's a Permit message format
        if primary_type != 'Permit':
            raise ValueError("Not a valid Permit message format")
        
        message = typed_data['message']
        
        # Parse Permit message
        approval = Approval(
            owner=message.get('owner'),
            spender=message['spender'],
            amount=str(message['value']),
            nonce=str(message['nonce']),
            expiration=str(message['deadline'])
        )
        
        return PermitMessage(permits=[approval])
    
    @staticmethod
    def parse_from_transaction(transaction: TransactionLike) -> List[PermitMessage]:
        """
        Parse Permit messages from transaction data
        
        Args:
            transaction: Transaction data
            
        Returns:
            List of parsed Permit messages
        """
        # TODO: Implement logic to parse from transaction
        return [] 