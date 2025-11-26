"""
Test Data for Signature Decoder Demo
Contains various types of EIP712 signature data
"""

# Seaport NFT order data
SEAPORT_ORDER = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "OrderComponents": [
            {"name": "offerer", "type": "address"},
            {"name": "zone", "type": "address"},
            {"name": "offer", "type": "OfferItem[]"},
            {"name": "consideration", "type": "ConsiderationItem[]"},
            {"name": "orderType", "type": "uint8"},
            {"name": "startTime", "type": "uint256"},
            {"name": "endTime", "type": "uint256"},
            {"name": "zoneHash", "type": "bytes32"},
            {"name": "salt", "type": "uint256"},
            {"name": "counter", "type": "uint256"}
        ],
        "OfferItem": [
            {"name": "itemType", "type": "uint8"},
            {"name": "token", "type": "address"},
            {"name": "identifierOrCriteria", "type": "uint256"},
            {"name": "startAmount", "type": "uint256"},
            {"name": "endAmount", "type": "uint256"}
        ],
        "ConsiderationItem": [
            {"name": "itemType", "type": "uint8"},
            {"name": "token", "type": "address"},
            {"name": "identifierOrCriteria", "type": "uint256"},
            {"name": "startAmount", "type": "uint256"},
            {"name": "endAmount", "type": "uint256"},
            {"name": "recipient", "type": "address"}
        ]
    },
    "primaryType": "OrderComponents",
    "domain": {
        "name": "Seaport",
        "version": "1.4",
        "chainId": 1,
        "verifyingContract": "0x00000000006c3852cbEf3e08E8dF289169EdE581"
    },
    "message": {
        "offerer": "0x8ba1f109551bD432803012645Hac136c22C04e2D",
        "zone": "0x0000000000000000000000000000000000000000",
        "offer": [
            {
                "itemType": 2,
                "token": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
                "identifierOrCriteria": "8547",
                "startAmount": "1",
                "endAmount": "1"
            }
        ],
        "consideration": [
            {
                "itemType": 0,
                "token": "0x0000000000000000000000000000000000000000",
                "identifierOrCriteria": "0",
                "startAmount": "975000000000000000",
                "endAmount": "975000000000000000",
                "recipient": "0x8ba1f109551bD432803012645Hac136c22C04e2D"
            },
            {
                "itemType": 0,
                "token": "0x0000000000000000000000000000000000000000",
                "identifierOrCriteria": "0",
                "startAmount": "25000000000000000",
                "endAmount": "25000000000000000",
                "recipient": "0x0000a26b00c1F0DF003000390027140000fAa719"
            }
        ],
        "orderType": 0,
        "startTime": "1699143856",
        "endTime": "1700007856",
        "zoneHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "123456789",
        "counter": "0"
    }
}

# ERC20 Permit authorization data
ERC20_PERMIT = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Permit": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"}
        ]
    },
    "primaryType": "Permit",
    "domain": {
        "name": "USD Coin",
        "version": "2",
        "chainId": 1,
        "verifyingContract": "0xA0b86a33E6411B3036c2F0F1AB5C6F3f22dd20f5"
    },
    "message": {
        "owner": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "spender": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "value": "1000000000000000000000",
        "nonce": 42,
        "deadline": 1699987456
    }
}

# DAO governance vote data
DAO_VOTE = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Ballot": [
            {"name": "proposalId", "type": "uint256"},
            {"name": "voter", "type": "address"},
            {"name": "support", "type": "uint8"},
            {"name": "reason", "type": "string"},
            {"name": "timestamp", "type": "uint256"}
        ]
    },
    "primaryType": "Ballot",
    "domain": {
        "name": "Compound Governor Bravo",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0xc0Da02939E1441F497fd74F78cE7Decb17B66529"
    },
    "message": {
        "proposalId": 123,
        "voter": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "support": 1,
        "reason": "I support this proposal for better governance",
        "timestamp": 1699143856
    }
}

# Custom complex structure data
CUSTOM_TRANSACTION = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Transaction": [
            {"name": "id", "type": "bytes32"},
            {"name": "from", "type": "User"},
            {"name": "to", "type": "User"},
            {"name": "amount", "type": "uint256"},
            {"name": "fee", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "deadline", "type": "uint256"}
        ],
        "User": [
            {"name": "wallet", "type": "address"},
            {"name": "username", "type": "string"},
            {"name": "reputation", "type": "uint256"}
        ]
    },
    "primaryType": "Transaction",
    "domain": {
        "name": "CustomDApp",
        "version": "1.0",
        "chainId": 1,
        "verifyingContract": "0x1234567890123456789012345678901234567890"
    },
    "message": {
        "id": "0xa1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        "from": {
            "wallet": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            "username": "alice",
            "reputation": 850
        },
        "to": {
            "wallet": "0x8ba1f109551bD432803012645Hac136c22C04e2D",
            "username": "bob",
            "reputation": 750
        },
        "amount": "2500000000000000000",
        "fee": "50000000000000000",
        "data": "0x1234abcd",
        "deadline": 1699987456
    }
}

# LazyNFT Mint data
LAZY_NFT_MINT = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "LazyNFTVoucher": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "minPrice", "type": "uint256"},
            {"name": "uri", "type": "string"},
            {"name": "creator", "type": "address"},
            {"name": "royalty", "type": "uint256"},
            {"name": "deadline", "type": "uint256"}
        ]
    },
    "primaryType": "LazyNFTVoucher",
    "domain": {
        "name": "LazyNFT",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0x7f268357A8c2552623316e2562D90e642bB538E5"
    },
    "message": {
        "tokenId": 42,
        "minPrice": "100000000000000000",
        "uri": "https://example.com/metadata/42",
        "creator": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "royalty": 250,
        "deadline": 1699987456
    }
}

# Snapshot vote data
SNAPSHOT_VOTE = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"}
        ],
        "Vote": [
            {"name": "from", "type": "address"},
            {"name": "space", "type": "string"},
            {"name": "timestamp", "type": "uint64"},
            {"name": "proposal", "type": "bytes32"},
            {"name": "choice", "type": "uint32"},
            {"name": "reason", "type": "string"},
            {"name": "app", "type": "string"},
            {"name": "metadata", "type": "string"}
        ]
    },
    "primaryType": "Vote",
    "domain": {
        "name": "snapshot",
        "version": "0.1.4"
    },
    "message": {
        "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "space": "uniswap.eth",
        "timestamp": 1699143856,
        "proposal": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "choice": 1,
        "reason": "This proposal will improve the protocol",
        "app": "snapshot",
        "metadata": "{\"plugins\":{},\"network\":1}"
    }
}

# --- New Transaction Data ---

# ETH Transfer (Native)
ETH_TRANSFER = {
    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "to": "0x8ba1f109551bD432803012645Hac136c22C04e2D",
    "value": "1000000000000000000", # 1 ETH
    "data": "0x",
    "chainId": 1
}

# Uniswap Swap (ETH -> Token)
# Function: swapExactETHForTokens(uint256 amountOutMin, address[] path, address to, uint256 deadline)
# Selector: 0x7ff36ab5
TX_UNISWAP_SWAP = {
    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "to": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", # Uniswap V2 Router
    "value": "1000000000000000000", # 1 ETH input
    "data": "0x7ff36ab500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000742d35cc6634c0532925a3b844bc454e4438f44e00000000000000000000000000000000000000000000000000000000655360500000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc20000000000000000000000006b175474e89094c44da98b954eedeac495271d0f",
    "chainId": 1
}

# Bridge Deposit (ETH to L2)
# Function: deposit(address token, uint256 amount)
# Selector: 0x44cee73c
# NOTE: Bridge contracts often differ, this is a generic example matching one in knowledge_base
TX_BRIDGE_DEPOSIT = {
    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "to": "0x406eD831689A3151C74007C4B28d56650C7D0d55", # Arbitrum Bridge L1
    "value": "0",
    "data": "0x44cee73c0000000000000000000000006b175474e89094c44da98b954eedeac495271d0f0000000000000000000000000000000000000000000000000de0b6b3a7640000", # Token + 1000 units
    "chainId": 1
}

# --- Personal Sign Data ---

# Standard Login Message
MSG_LOGIN = {
    "message": "Sign in to OpenSea\nNonce: 123456"
}

# Phishing Message
MSG_PHISHING = {
    "message": "URGENT: Your account is compromised. Sign to verify ownership immediately."
}


# All test data
ALL_TEST_DATA = {
    "seaport_order": SEAPORT_ORDER,
    "erc20_permit": ERC20_PERMIT,
    "dao_vote": DAO_VOTE,
    "custom_transaction": CUSTOM_TRANSACTION,
    "lazy_nft_mint": LAZY_NFT_MINT,
    "snapshot_vote": SNAPSHOT_VOTE,
    # New Data
    "eth_transfer": ETH_TRANSFER,
    "uniswap_swap": TX_UNISWAP_SWAP,
    "bridge_deposit": TX_BRIDGE_DEPOSIT,
    "msg_login": MSG_LOGIN,
    "msg_phishing": MSG_PHISHING
}
