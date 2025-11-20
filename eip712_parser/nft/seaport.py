"""
Seaport NFT marketplace parser
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from ..types import (
    EIP712Like, NFTMessage, ParsedDetail, NFTDetail, FTDetail,
    OrderType, NFTProtocolType, BalanceChange, calculate_balance_change,
    TransactionLike
)
import json
import os


@dataclass
class AdditionalRecipient:
    amount: str
    recipient: str


@dataclass
class FulfillmentComponent:
    order_index: int
    item_index: int


@dataclass
class Fulfillment:
    offer_components: List[FulfillmentComponent]
    consideration_components: List[FulfillmentComponent]


@dataclass
class CriteriaResolver:
    order_index: int
    side: int  # 0 | 1 (0 = offer, 1 = consideration)
    index: int
    identifier: str
    criteria_proof: List[str]


@dataclass
class OfferItem:
    item_type: int
    token: str
    identifier_or_criteria: str
    start_amount: str
    end_amount: str


@dataclass
class ConsiderationItem:
    item_type: int
    token: str
    identifier_or_criteria: str
    start_amount: str
    end_amount: str
    recipient: str


@dataclass
class OrderParameters:
    offerer: str
    zone: str
    offer: List[OfferItem]
    consideration: List[ConsiderationItem]
    order_type: int
    start_time: Union[str, int]
    end_time: Union[str, int]
    zone_hash: str
    salt: str
    conduit_key: str
    total_original_consideration_items: Union[str, int]


@dataclass
class OrderComponents:
    offerer: str
    zone: str
    offer: List[OfferItem]
    consideration: List[ConsiderationItem]
    order_type: int
    start_time: Union[str, int]
    end_time: Union[str, int]
    zone_hash: str
    salt: str
    conduit_key: str
    counter: str


@dataclass
class Order:
    parameters: OrderParameters
    signature: str


@dataclass
class AdvancedOrder:
    parameters: OrderParameters
    numerator: Union[str, int]
    denominator: Union[str, int]
    signature: str
    extra_data: str


class Seaport:
    """Seaport NFT marketplace parser"""
    
    # Method signature for matching orders
    MATCH_ORDERS_SIGNATURES = ["0xa8174404"]
    
    @staticmethod
    def parse_order(item: Union[OfferItem, ConsiderationItem]) -> ParsedDetail:
        """
        Parse order item
        
        Args:
            item: Order item to parse
            
        Returns:
            Parsed details
        """
        if item.item_type <= 1:
            # Token type (0: native, 1: erc20)
            return ParsedDetail(
                kind="token",
                detail=FTDetail(
                    type='native' if item.item_type == 0 else 'erc20',
                    currency=item.token,
                    amount=str(item.start_amount)
                )
            )
        else:
            # NFT type (2: erc721, 3: erc1155)
            return ParsedDetail(
                kind="nft",
                detail=NFTDetail(
                    type='erc721' if item.item_type == 2 else 'erc1155',
                    collection=item.token,
                    token_id=str(item.identifier_or_criteria),
                    amount=str(item.start_amount)
                )
            )
    
    @staticmethod
    def _convert_to_offer_items(offer_data: List[Dict[str, Any]]) -> List[OfferItem]:
        """Convert dictionary data to OfferItem objects"""
        offer_items = []
        for item_data in offer_data:
            offer_items.append(OfferItem(
                item_type=int(item_data['itemType']),
                token=item_data['token'],
                identifier_or_criteria=str(item_data['identifierOrCriteria']),
                start_amount=str(item_data['startAmount']),
                end_amount=str(item_data['endAmount'])
            ))
        return offer_items
    
    @staticmethod
    def _convert_to_consideration_items(consideration_data: List[Dict[str, Any]]) -> List[ConsiderationItem]:
        """Convert dictionary data to ConsiderationItem objects"""
        consideration_items = []
        for item_data in consideration_data:
            consideration_items.append(ConsiderationItem(
                item_type=int(item_data['itemType']),
                token=item_data['token'],
                identifier_or_criteria=str(item_data['identifierOrCriteria']),
                start_amount=str(item_data['startAmount']),
                end_amount=str(item_data['endAmount']),
                recipient=item_data['recipient']
            ))
        return consideration_items
    
    @staticmethod
    def parse(typed_data: EIP712Like) -> NFTMessage:
        """
        Parse Seaport EIP712 message
        
        Args:
            typed_data: Data in EIP712 format
            
        Returns:
            Parsed NFT message
            
        Raises:
            ValueError: When data format is incorrect
        """
        message = typed_data['message']
        
        # Check if it's a Seaport message
        if 'offerer' not in message or 'offer' not in message or 'consideration' not in message:
            raise ValueError("Not a valid Seaport message format")
        
        offerer = message['offerer']
        offer_data = message['offer']
        consideration_data = message['consideration']
        
        # Convert data format
        offer_items = Seaport._convert_to_offer_items(offer_data)
        consideration_items = Seaport._convert_to_consideration_items(consideration_data)
        
        # Parse offer items
        parsed_offers = [Seaport.parse_order(item) for item in offer_items]
        
        # Parse consideration items that belong to offerer
        received_consideration = [
            Seaport.parse_order(item) 
            for item in consideration_items 
            if item.recipient.lower() == offerer.lower()
        ]
        
        # Calculate balance changes
        balance_change: BalanceChange = {}
        
        # Calculate items sent by offerer
        for item in parsed_offers:
            calculate_balance_change(balance_change, offerer, item, False)
        
        # Calculate items received by offerer
        for item in received_consideration:
            calculate_balance_change(balance_change, offerer, item, True)
        
        # Calculate balance changes for other recipients
        other_recipients = set()
        for item in consideration_items:
            if item.recipient.lower() != offerer.lower():
                other_recipients.add(item.recipient.lower())
        
        for recipient in other_recipients:
            matched_items = [
                Seaport.parse_order(item)
                for item in consideration_items
                if item.recipient.lower() == recipient
            ]
            for item in matched_items:
                calculate_balance_change(balance_change, recipient, item, True)
        
        # Determine order type
        total_nfts = sum(1 for item in parsed_offers if item.kind == "nft")
        order_type = OrderType.LISTING if total_nfts > 0 else OrderType.OFFER
        
        return NFTMessage(
            offerer=offerer,
            balance_change=balance_change,
            order_type=order_type,
            offer=parsed_offers,
            consideration=received_consideration,
            start_time=message.get('startTime', 0),
            end_time=message.get('endTime', 0),
            type=NFTProtocolType.SEAPORT
        )
    
    @staticmethod
    def parse_from_transaction(transaction: TransactionLike) -> List[NFTMessage]:
        """
        Parse Seaport messages from transaction data
        
        Args:
            transaction: Transaction data
            
        Returns:
            List of parsed NFT messages
        """
        if not transaction.data:
            return []
        
        sign_hash = transaction.data[:10]
        all_orders: List[NFTMessage] = []
        
        if transaction.to and sign_hash in Seaport.MATCH_ORDERS_SIGNATURES:
            # Need to implement ABI decoding functionality here
            # Since there's no complete ABI decoder, return empty list for now
            # In actual use, need to use web3.py's ABI decoding functionality
            pass
        
        return all_orders 