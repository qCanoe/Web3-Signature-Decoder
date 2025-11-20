"""
EIP712 Test Data
Contains various types of EIP712 signature test samples
"""

# Seaport NFT order data
SEAPORT_ORDER_DATA = {
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
                "identifierOrCriteria": 5123,
                "startAmount": 1,
                "endAmount": 1
            }
        ],
        "consideration": [
            {
                "itemType": 0,
                "token": "0x0000000000000000000000000000000000000000",
                "identifierOrCriteria": 0,
                "startAmount": 975000000000000000,
                "endAmount": 975000000000000000,
                "recipient": "0x8ba1f109551bD432803012645Hac136c22C04e2D"
            },
            {
                "itemType": 0,
                "token": "0x0000000000000000000000000000000000000000",
                "identifierOrCriteria": 0,
                "startAmount": 25000000000000000,
                "endAmount": 25000000000000000,
                "recipient": "0x0000a26b00c1F0DF003000390027140000fAa719"
            }
        ],
        "orderType": 0,
        "startTime": 1699123456,
        "endTime": 1699987456,
        "zoneHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "salt": 123456789,
        "counter": 0
    }
}

# ERC20 Permit authorization data
PERMIT_DATA = {
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
        "value": 1000000000000000000000,  # 1000 USDC
        "nonce": 42,
        "deadline": 1699987456
    }
}

# DAO voting data
DAO_VOTING_DATA = {
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
        "support": 1,  # 1 = For, 0 = Against, 2 = Abstain
        "reason": "I support this proposal for better governance",
        "timestamp": 1699123456
    }
}

# Custom complex structure data
CUSTOM_STRUCT_DATA = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "User": [
            {"name": "wallet", "type": "address"},
            {"name": "username", "type": "string"},
            {"name": "reputation", "type": "uint256"}
        ],
        "Transaction": [
            {"name": "id", "type": "bytes32"},
            {"name": "from", "type": "User"},
            {"name": "to", "type": "User"},
            {"name": "amount", "type": "uint256"},
            {"name": "fee", "type": "uint256"},
            {"name": "data", "type": "bytes"},
            {"name": "deadline", "type": "uint256"}
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
        "id": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
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
        "amount": 2500000000000000000,  # 2.5 ETH
        "fee": 50000000000000000,      # 0.05 ETH
        "data": "0x1234abcd",
        "deadline": 1699987456
    }
}

# Simple Permit data for analysis
SIMPLE_PERMIT_DATA = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Permit": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "deadline", "type": "uint256"}
        ]
    },
    "primaryType": "Permit",
    "domain": {
        "name": "USDC",
        "chainId": 1,
        "verifyingContract": "0xA0b86a33E6411B3036c2F0F1AB5C6F3f22dd20f5"
    },
    "message": {
        "owner": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "spender": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        "value": 1000000000,  # 1000 USDC
        "deadline": 1699987456
    }
}

# Test data set
TEST_DATA_SET = {
    "seaport_order": SEAPORT_ORDER_DATA,
    "permit": PERMIT_DATA,
    "dao_voting": DAO_VOTING_DATA,
    "custom_struct": CUSTOM_STRUCT_DATA,
    "simple_permit": SIMPLE_PERMIT_DATA
} 