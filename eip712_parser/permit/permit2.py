"""
Permit2 parser
"""

from typing import List
from ..types import EIP712Like, PermitMessage, Approval, TransactionLike


class Permit2:
    """Permit2 parser"""
    
    @staticmethod
    def parse(typed_data: EIP712Like) -> PermitMessage:
        """
        Parse Permit2 EIP712 message
        
        Args:
            typed_data: EIP712 format data
            
        Returns:
            Parsed Permit2 message
            
        Raises:
            ValueError: When data format is incorrect
        """
        primary_type = typed_data.get('primaryType', '')
        
        # Check if it's a Permit2-related message format
        if not any(permit_type in primary_type for permit_type in 
                  ['PermitSingle', 'PermitBatch', 'PermitTransferFrom']):
            raise ValueError("Not a valid Permit2 message format")
        
        message = typed_data['message']
        permits = []
        
        if primary_type == 'PermitSingle':
            # Single permit
            details = message['details']
            approval = Approval(
                token=details['token'],
                spender=message['spender'],
                amount=str(details['amount']),
                nonce=str(message['nonce']),
                expiration=str(details['expiration'])
            )
            permits.append(approval)
            
        elif primary_type == 'PermitBatch':
            # Batch permit
            for detail in message['details']:
                approval = Approval(
                    token=detail['token'],
                    spender=message['spender'],
                    amount=str(detail['amount']),
                    nonce=str(message['nonce']),
                    expiration=str(detail['expiration'])
                )
                permits.append(approval)
        
        return PermitMessage(permits=permits)
    
    @staticmethod
    def parse_from_transaction(transaction: TransactionLike) -> List[PermitMessage]:
        """
        Parse Permit2 messages from transaction data
        
        Args:
            transaction: Transaction data
            
        Returns:
            List of parsed Permit2 messages
        """
        # TODO: Implement logic to parse from transaction
        return [] 