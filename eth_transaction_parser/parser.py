"""
ETH Transaction 主解析器
"""

import json
import logging
from typing import Dict, Any, Optional, Union
from .models import EthTransaction, TransactionAnalysis, TransactionType, RiskLevel
from .parameter_extractor import TransactionParameterExtractor
from .transaction_analyzer import TransactionAnalyzer


class EthTransactionParser:
    """ETH交易解析器"""
    
    def __init__(self, enable_logging: bool = False):
        """
        初始化解析器
        
        Args:
            enable_logging: 是否启用日志
        """
        self.logger = logging.getLogger(__name__)
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
        
        self.parameter_extractor = TransactionParameterExtractor()
        self.transaction_analyzer = TransactionAnalyzer()
    
    def parse(self, transaction_data: Union[str, Dict[str, Any]]) -> TransactionAnalysis:
        """
        解析交易数据
        
        Args:
            transaction_data: 交易数据 (JSON字符串或字典)
            
        Returns:
            TransactionAnalysis: 解析和分析结果
        """
        try:
            # 解析输入数据
            if isinstance(transaction_data, str):
                tx_dict = json.loads(transaction_data)
            else:
                tx_dict = transaction_data
            
            # 提取交易参数
            transaction = self._extract_transaction_params(tx_dict)
            
            # 分析交易
            analysis = self.transaction_analyzer.analyze(transaction)
            
            self.logger.info(f"解析完成: {analysis.transaction_type.value}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"解析失败: {str(e)}")
            # 返回基本的错误分析
            return TransactionAnalysis(
                transaction=EthTransaction(),
                transaction_type=TransactionType.UNKNOWN,
                confidence=0.0,
                risk_level=RiskLevel.HIGH,
                security_warnings=[f"解析错误: {str(e)}"],
                description="交易解析失败",
                summary="无法解析的交易"
            )
    
    def _extract_transaction_params(self, tx_dict: Dict[str, Any]) -> EthTransaction:
        """
        提取交易参数
        
        Args:
            tx_dict: 交易字典
            
        Returns:
            EthTransaction: 交易对象
        """
        return EthTransaction(
            from_address=tx_dict.get('from'),
            to_address=tx_dict.get('to'),
            value=tx_dict.get('value', '0x0'),
            gas=tx_dict.get('gas'),
            gas_price=tx_dict.get('gasPrice'),
            max_fee_per_gas=tx_dict.get('maxFeePerGas'),
            max_priority_fee_per_gas=tx_dict.get('maxPriorityFeePerGas'),
            nonce=tx_dict.get('nonce'),
            data=tx_dict.get('data', '0x')
        )
    
    def parse_batch(self, transactions: list) -> list:
        """
        批量解析交易
        
        Args:
            transactions: 交易列表
            
        Returns:
            list: 解析结果列表
        """
        results = []
        for tx in transactions:
            try:
                result = self.parse(tx)
                results.append(result)
            except Exception as e:
                self.logger.error(f"批量解析中的单个交易失败: {str(e)}")
                results.append(None)
        
        return results
    
    def get_transaction_summary(self, analysis: TransactionAnalysis) -> str:
        """
        获取交易摘要
        
        Args:
            analysis: 交易分析结果
            
        Returns:
            str: 交易摘要
        """
        tx = analysis.transaction
        
        # 基本信息
        summary_parts = [
            f"交易类型: {analysis.transaction_type.value}",
            f"发送方: {tx.from_address or '未知'}",
            f"接收方: {tx.to_address or '未知'}",
        ]
        
        # 价值转移
        if tx.value_eth and tx.value_eth > 0:
            summary_parts.append(f"ETH数量: {tx.value_eth:.6f} ETH")
        
        # 合约调用
        if analysis.contract_call:
            if analysis.contract_call.function_name:
                summary_parts.append(f"调用函数: {analysis.contract_call.function_name}")
        
        # 代币信息
        if analysis.token_info:
            if analysis.token_info.amount_formatted:
                symbol = analysis.token_info.symbol or "代币"
                summary_parts.append(f"代币数量: {analysis.token_info.amount_formatted} {symbol}")
        
        # 风险信息
        if analysis.risk_level != RiskLevel.LOW:
            summary_parts.append(f"风险级别: {analysis.risk_level.value}")
        
        return " | ".join(summary_parts)
    
    def export_analysis(self, analysis: TransactionAnalysis, format: str = "json") -> str:
        """
        导出分析结果
        
        Args:
            analysis: 分析结果
            format: 导出格式 ('json', 'yaml', 'text')
            
        Returns:
            str: 导出的内容
        """
        if format.lower() == "json":
            return self._export_json(analysis)
        elif format.lower() == "yaml":
            return self._export_yaml(analysis)
        elif format.lower() == "text":
            return self._export_text(analysis)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_json(self, analysis: TransactionAnalysis) -> str:
        """导出为JSON格式"""
        data = {
            "transaction_type": analysis.transaction_type.value,
            "confidence": analysis.confidence,
            "risk_level": analysis.risk_level.value,
            "description": analysis.description,
            "summary": analysis.summary,
            "transaction": {
                "from": analysis.transaction.from_address,
                "to": analysis.transaction.to_address,
                "value_eth": analysis.transaction.value_eth,
                "is_contract_call": analysis.transaction.is_contract_call,
            }
        }
        
        if analysis.contract_call:
            data["contract_call"] = {
                "function_name": analysis.contract_call.function_name,
                "function_selector": analysis.contract_call.function_selector,
                "parameters": analysis.contract_call.parameters,
            }
        
        if analysis.token_info:
            data["token_info"] = {
                "symbol": analysis.token_info.symbol,
                "amount_formatted": analysis.token_info.amount_formatted,
                "address": analysis.token_info.address,
            }
        
        if analysis.risk_factors:
            data["risk_factors"] = analysis.risk_factors
        
        if analysis.security_warnings:
            data["security_warnings"] = analysis.security_warnings
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_yaml(self, analysis: TransactionAnalysis) -> str:
        """导出为YAML格式"""
        return "YAML 格式导出已禁用，请使用 JSON 或 TEXT 格式"
    
    def _export_text(self, analysis: TransactionAnalysis) -> str:
        """导出为文本格式"""
        lines = [
            "=== ETH 交易分析报告 ===",
            "",
            f"交易类型: {analysis.transaction_type.value}",
            f"置信度: {analysis.confidence:.2f}",
            f"风险级别: {analysis.risk_level.value}",
            "",
            "交易信息:",
            f"  发送方: {analysis.transaction.from_address or '未知'}",
            f"  接收方: {analysis.transaction.to_address or '未知'}",
        ]
        
        if analysis.transaction.value_eth:
            lines.append(f"  ETH数量: {analysis.transaction.value_eth:.6f} ETH")
        
        if analysis.contract_call:
            lines.extend([
                "",
                "合约调用:",
                f"  函数: {analysis.contract_call.function_name or '未知'}",
                f"  选择器: {analysis.contract_call.function_selector or '未知'}",
            ])
        
        if analysis.token_info:
            lines.extend([
                "",
                "代币信息:",
                f"  符号: {analysis.token_info.symbol or '未知'}",
                f"  数量: {analysis.token_info.amount_formatted or '未知'}",
            ])
        
        if analysis.risk_factors:
            lines.extend([
                "",
                "风险因素:",
            ])
            for factor in analysis.risk_factors:
                lines.append(f"  - {factor}")
        
        if analysis.security_warnings:
            lines.extend([
                "",
                "安全警告:",
            ])
            for warning in analysis.security_warnings:
                lines.append(f"  - {warning}")
        
        lines.extend([
            "",
            f"描述: {analysis.description}",
            f"摘要: {analysis.summary}",
        ])
        
        return "\n".join(lines) 