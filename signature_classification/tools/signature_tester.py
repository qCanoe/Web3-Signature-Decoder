#!/usr/bin/env python3
"""
以太坊签名分类器测试工具

使用方法:
  python signature_tester.py         # 批量测试所有样本
  python signature_tester.py 2       # 测试第2个样本
  python signature_tester.py 1       # 测试第1个样本

功能:
- 自动加载 test_samples.json 中的测试数据
- 支持批量测试(默认)和单独测试(通过索引)
- 验证数据完整性和签名类型分类
"""

import json
import sys
import os
from typing import Dict, Any, Union, Optional

# 添加父目录到路径以导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from signature_classification import (
    SignatureClassifier, 
    SignatureValidator,
    RiskAnalyzer
)


class SignatureTester:
    """签名测试器"""
    
    def __init__(self):
        """初始化测试器"""
        self.classifier = SignatureClassifier()
        self.validator = SignatureValidator()
        self.risk_analyzer = RiskAnalyzer()
        self.test_samples_path = os.path.join(os.path.dirname(__file__), "test_samples.json")
        
        # 检查命令行参数
        import sys
        self.single_test_index = None
        if len(sys.argv) > 1:
            try:
                self.single_test_index = int(sys.argv[1]) - 1  # 转换为0基索引
            except ValueError:
                print("❌ 无效的样本索引，将进行批量测试")
    
    
    def load_test_samples(self) -> Dict[str, Any]:
        """加载测试样本数据"""
        try:
            with open(self.test_samples_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ 测试样本文件不存在: {self.test_samples_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            return None
    
    def analyze_signature(self, data: Union[str, Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析签名数据"""
        try:
            # 1. 签名分类
            classification = self.classifier.classify(data)
            
            # 2. 数据验证  
            validation = self.validator.validate(data, classification.signature_type)
            
            # 3. 风险评估
            risk_assessment = self.risk_analyzer.analyze_risk(
                classification.signature_type, 
                data, 
                context=context
            )
            
            return {
                "classification": classification,
                "validation": validation,
                "risk_assessment": risk_assessment,
                "success": True
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }
    
    def format_output(self, analysis_result: Dict[str, Any], data: Union[str, Dict[str, Any]]):
        """格式化输出分析结果"""
        
        if not analysis_result["success"]:
            print(f"❌ 分析失败: {analysis_result['error']}")
            return
        
        classification = analysis_result["classification"]
        validation = analysis_result["validation"]
        risk_assessment = analysis_result["risk_assessment"]
        
        # 对于 eth_sign 类型，显示简化的高风险警告
        if classification.signature_type == "eth_sign":
            print("🔴" + "="*50 + "🔴")
            print("⚠️              ETH_SIGN 高风险警告              ⚠️")
            print("🔴" + "="*50 + "🔴")
            print()
            print("🚫 签名类型: eth_sign")
            print("🔴 风险级别: 极高风险")
            print("⚠️ 状态: 禁止使用")
            print()
            print("💡 安全建议:")
            print("   • eth_sign 方法存在严重安全漏洞")
            print("   • 已被多数钱包禁用")
            print("   • 强烈建议拒绝此类签名请求")
            print()
            print("🔴" + "="*50 + "🔴")
            return
        
        # 分类结果
        print("分类结果:")
        print(f"   签名类型: {classification.signature_type}")
        print(f"   功能分类: {classification.category}")
        
        # 数据验证
        print(f"\n✅ 数据验证:")
        validation_status = "✅ 通过" if validation.is_valid else "❌ 失败"
        print(f"   状态: {validation_status}")
        
        # 显示验证错误（如果有）
        if validation.errors:
            print(f"   ❌ 错误:")
            for error in validation.errors:
                print(f"      • {error}")
        
        # 显示重要警告（如果有）
        if validation.warnings:
            print(f"   ⚠️ 警告:")
            for warning in validation.warnings:
                print(f"      • {warning}")
        
        print()
    
    def extract_raw_data(self, sample: dict, method: str):
        """从样本中提取原始数据用于分析"""
        if method == "personal_sign":
            return sample.get("message", "")
        elif method == "eth_signTypedData_v4":
            return sample.get("message", {})
        elif method == "eth_sendTransaction":
            return sample.get("message", {})
        elif method == "eth_sign":
            return sample.get("message", "")
        else:
            return sample.get("raw", sample.get("message", ""))
    
    def list_samples(self, samples: list):
        """列出所有样本"""
        for i, sample in enumerate(samples):
            method = sample.get("method", "unknown")
            description = self.get_sample_description(sample)
            print(f"   {i+1}. {method} - {description}")
    
    def get_sample_description(self, sample: dict) -> str:
        """获取样本描述"""
        method = sample.get("method", "unknown")
        
        if method == "personal_sign":
            message = sample.get("message", "")
            if len(message) > 50:
                return f"{message[:50]}..."
            return message
        
        elif method == "eth_signTypedData_v4":
            domain_name = sample.get("message", {}).get("domain", {}).get("name", "Unknown")
            primary_type = sample.get("message", {}).get("primaryType", "Unknown")
            return f"{domain_name} - {primary_type}"
        
        elif method == "eth_sendTransaction":
            to_address = sample.get("message", {}).get("to", "")
            value = sample.get("message", {}).get("value", "0x0")
            return f"发送到 {to_address[:10]}... (值: {value})"
        
        elif method == "eth_sign":
            return "原始签名数据"
        
        else:
            return "未知类型"
    
    def batch_test_samples(self, samples: list):
        """批量测试所有样本"""
        for i, sample in enumerate(samples):
            method = sample.get("method", "unknown")
            description = self.get_sample_description(sample)
            
            print(f"测试样本 {i + 1}/{len(samples)}: {method}")
            print(f"描述: {description}")
            print()
            
            # 提取 raw 数据用于分析
            raw_data = self.extract_raw_data(sample, method)
            result = self.analyze_signature(raw_data)
            self.format_output(result, raw_data)
            
            print("-" * 60)
            print()

    def run(self):
        """运行测试器"""
        
        test_data = self.load_test_samples()
        
        if test_data is None:
            print("❌ 无法加载测试样本，程序退出")
            return
        
        print(f"✅ 成功加载测试样本: {self.test_samples_path}")
        
        # 检查数据格式
        if isinstance(test_data, list):
            # 数组格式 - 根据参数决定测试模式
            if self.single_test_index is not None:
                # 单独测试指定样本
                self.test_single_sample_by_index(test_data, self.single_test_index)
            else:
                # 默认批量测试所有样本
                print(f" 发现 {len(test_data)} 个测试样本，开始批量测试...")
                print()
                self.batch_test_samples(test_data)
        else:
            # 单个对象格式 - 直接测试
            print()
            result = self.analyze_signature(test_data)
            self.format_output(result, test_data)
        
    
    def test_single_sample_by_index(self, samples: list, index: int):
        """通过索引测试单个样本"""
        if index < 0 or index >= len(samples):
            print(f"❌ 样本索引超出范围 (1-{len(samples)})")
            print("💡 可用的样本:")
            self.list_samples(samples)
            return
        
        selected_sample = samples[index]
        method = selected_sample.get("method", "unknown")
        description = self.get_sample_description(selected_sample)
        
        print(f" 测试样本 {index + 1}: {method}")
        print(f" 描述: {description}")
        print()
        
        # 提取 raw 数据用于分析
        raw_data = self.extract_raw_data(selected_sample, method)
        result = self.analyze_signature(raw_data)
        self.format_output(result, raw_data)


if __name__ == "__main__":
    tester = SignatureTester()
    tester.run() 