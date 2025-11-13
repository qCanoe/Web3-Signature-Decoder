"""
Seaport NFT 市场解析器
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
    side: int  # 0 | 1
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
    """Seaport NFT 市场解析器"""
    
    # 匹配订单的方法签名
    MATCH_ORDERS_SIGNATURES = ["0xa8174404"]
    
    @staticmethod
    def parse_order(item: Union[OfferItem, ConsiderationItem]) -> ParsedDetail:
        """
        解析订单项
        
        Args:
            item: 要解析的订单项
            
        Returns:
            解析后的详情
        """
        if item.item_type <= 1:
            # 代币类型 (0: native, 1: erc20)
            return ParsedDetail(
                kind="token",
                detail=FTDetail(
                    type='native' if item.item_type == 0 else 'erc20',
                    currency=item.token,
                    amount=str(item.start_amount)
                )
            )
        else:
            # NFT类型 (2: erc721, 3: erc1155)
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
        """将字典数据转换为OfferItem对象"""
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
        """将字典数据转换为ConsiderationItem对象"""
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
        解析 Seaport EIP712 消息
        
        Args:
            typed_data: EIP712 格式的数据
            
        Returns:
            解析后的 NFT 消息
            
        Raises:
            ValueError: 当数据格式不正确时
        """
        message = typed_data['message']
        
        # 检查是否为 Seaport 消息
        if 'offerer' not in message or 'offer' not in message or 'consideration' not in message:
            raise ValueError("不是有效的 Seaport 消息格式")
        
        offerer = message['offerer']
        offer_data = message['offer']
        consideration_data = message['consideration']
        
        # 转换数据格式
        offer_items = Seaport._convert_to_offer_items(offer_data)
        consideration_items = Seaport._convert_to_consideration_items(consideration_data)
        
        # 解析 offer 项目
        parsed_offers = [Seaport.parse_order(item) for item in offer_items]
        
        # 解析 consideration 项目中属于 offerer 的部分
        received_consideration = [
            Seaport.parse_order(item) 
            for item in consideration_items 
            if item.recipient.lower() == offerer.lower()
        ]
        
        # 计算余额变化
        balance_change: BalanceChange = {}
        
        # 计算 offerer 发出的项目
        for item in parsed_offers:
            calculate_balance_change(balance_change, offerer, item, False)
        
        # 计算 offerer 收到的项目
        for item in received_consideration:
            calculate_balance_change(balance_change, offerer, item, True)
        
        # 计算其他接收者的余额变化
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
        
        # 确定订单类型
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
        从交易数据中解析 Seaport 消息
        
        Args:
            transaction: 交易数据
            
        Returns:
            解析后的 NFT 消息列表
        """
        if not transaction.data:
            return []
        
        sign_hash = transaction.data[:10]
        all_orders: List[NFTMessage] = []
        
        if transaction.to and sign_hash in Seaport.MATCH_ORDERS_SIGNATURES:
            # 这里需要实现 ABI 解码功能
            # 由于没有完整的 ABI 解码器，这里先返回空列表
            # 在实际使用中需要使用 web3.py 的 ABI 解码功能
            pass
        
        return all_orders 