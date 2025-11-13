"""
ETH Transaction 测试数据
"""

# ETH转账交易
ETH_TRANSFER_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "value": "0x16345785d8a0000",  # 0.1 ETH
    "gas": "0x5208",  # 21000
    "gasPrice": "0x3b9aca00",  # 1 gwei
    "nonce": "0x1",
    "data": "0x"
}

# ERC20 代币转账
ERC20_TRANSFER_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT合约
    "value": "0x0",
    "gas": "0xc350",  # 50000
    "gasPrice": "0x77359400",  # 2 gwei
    "nonce": "0x2",
    "data": "0xa9059cbb000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa96045000000000000000000000000000000000000000000000000000000000098968000"  # transfer(address,uint256)
}

# ERC20 代币授权
ERC20_APPROVE_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT合约
    "value": "0x0",
    "gas": "0xb71b",  # 46875
    "gasPrice": "0x77359400",  # 2 gwei
    "nonce": "0x3",
    "data": "0x095ea7b30000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488dffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"  # approve(address,uint256) - 无限授权
}

# Uniswap V2 代币交换
UNISWAP_SWAP_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2 Router
    "value": "0x16345785d8a0000",  # 0.1 ETH
    "gas": "0x30d40",  # 200000
    "gasPrice": "0xba43b7400",  # 5 gwei
    "nonce": "0x4",
    "data": "0x7ff36ab50000000000000000000000000000000000000000000000000000000000989680000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b000000000000000000000000000000000000000000000000000000006553c9f00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7"  # swapExactETHForTokens
}

# NFT转移
NFT_TRANSFER_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",  # BAYC合约
    "value": "0x0",
    "gas": "0x15f90",  # 90000
    "gasPrice": "0x3b9aca00",  # 1 gwei
    "nonce": "0x5",
    "data": "0x23b872dd000000000000000000000000742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa960450000000000000000000000000000000000000000000000000000000000001234"  # transferFrom(address,address,uint256)
}

# NFT授权所有
NFT_APPROVE_ALL_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",  # BAYC合约
    "value": "0x0",
    "gas": "0xc350",  # 50000
    "gasPrice": "0x77359400",  # 2 gwei
    "nonce": "0x6",
    "data": "0xa22cb465000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001"  # setApprovalForAll(address,bool)
}

# 合约部署
CONTRACT_DEPLOY_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": None,  # 合约部署没有to地址
    "value": "0x0",
    "gas": "0x186a0",  # 100000
    "gasPrice": "0x4a817c800",  # 20 gwei
    "nonce": "0x7",
    "data": "0x608060405234801561001057600080fd5b506040518060400160405280600781526020017f4d79546f6b656e000000000000000000000000000000000000000000000000008152506040518060400160405280600381526020017f4d544b000000000000000000000000000000000000000000000000000000000081525081600390805190602001906100959291906100d5565b5080600490805190602001906100ac9291906100d5565b50505034801561001057600080fd5b506040518060200160405280600"  # 合约字节码
}

# EIP-1559 交易
EIP1559_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "value": "0x2386f26fc10000",  # 0.01 ETH
    "gas": "0x5208",  # 21000
    "maxFeePerGas": "0x77359400",  # 2 gwei
    "maxPriorityFeePerGas": "0x3b9aca00",  # 1 gwei
    "nonce": "0x8",
    "data": "0x"
}

# 大额ETH转账 (高风险)
HIGH_VALUE_ETH_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "value": "0x21e19e0c9bab2400000",  # 100 ETH
    "gas": "0x5208",  # 21000
    "gasPrice": "0x4a817c800",  # 20 gwei
    "nonce": "0x9",
    "data": "0x"
}

# 未知合约调用
UNKNOWN_CONTRACT_TX = {
    "from": "0x742d35cc6670c13f11d1d3b0b99a6de5f8a5e17b",
    "to": "0x1234567890123456789012345678901234567890",  # 未知合约
    "value": "0x0",
    "gas": "0x7530",  # 30000
    "gasPrice": "0x77359400",  # 2 gwei
    "nonce": "0xa",
    "data": "0x12345678000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa960450000000000000000000000000000000000000000000000000de0b6b3a7640000"  # 未知函数调用
}

# 测试用例集合
TEST_TRANSACTIONS = {
    "eth_transfer": ETH_TRANSFER_TX,
    "erc20_transfer": ERC20_TRANSFER_TX,
    "erc20_approve": ERC20_APPROVE_TX,
    "uniswap_swap": UNISWAP_SWAP_TX,
    "nft_transfer": NFT_TRANSFER_TX,
    "nft_approve_all": NFT_APPROVE_ALL_TX,
    "contract_deploy": CONTRACT_DEPLOY_TX,
    "eip1559": EIP1559_TX,
    "high_value_eth": HIGH_VALUE_ETH_TX,
    "unknown_contract": UNKNOWN_CONTRACT_TX
}

# 预期的分析结果
EXPECTED_RESULTS = {
    "eth_transfer": {
        "type": "eth_transfer",
        "risk_level": "low",
        "description_contains": ["转账", "ETH"]
    },
    "erc20_transfer": {
        "type": "token_transfer",
        "risk_level": "low",
        "description_contains": ["转账", "USDT"]
    },
    "erc20_approve": {
        "type": "token_approval",
        "risk_level": "high",
        "description_contains": ["无限授权", "USDT"],
        "risk_factors": ["疑似无限代币授权"]
    },
    "uniswap_swap": {
        "type": "defi_swap",
        "risk_level": "low",
        "description_contains": ["交换", "Uniswap"]
    },
    "nft_transfer": {
        "type": "nft_transfer", 
        "risk_level": "low",
        "description_contains": ["NFT"]
    },
    "nft_approve_all": {
        "type": "nft_approval",
        "risk_level": "medium",
        "description_contains": ["授权", "NFT"],
        "risk_factors": ["NFT全部授权"]
    },
    "contract_deploy": {
        "type": "contract_deploy",
        "risk_level": "low",
        "description_contains": ["部署", "合约"]
    },
    "high_value_eth": {
        "type": "eth_transfer",
        "risk_level": "medium",
        "description_contains": ["转账", "ETH"],
        "risk_factors": ["大额ETH转账"]
    },
    "unknown_contract": {
        "type": "contract_call",
        "risk_level": "medium",
        "description_contains": ["未知合约"],
        "risk_factors": ["未知合约调用"]
    }
} 