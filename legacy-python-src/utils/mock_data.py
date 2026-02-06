"""
Signature Decoder Sample Data
=============================

6 representative tasks for evaluation, covering different signature methods and risk levels.

Tasks:
- T1: OpenSea Login (Personal Sign, Low Risk)
- T2: NFT Mint (Transaction, Low Risk)
- T3: DAO Vote (EIP-712, Medium Risk)
- T4: Bridge/Swap (EIP-712, Medium Risk)
- T5: Unlimited Approval (EIP-712, High Risk)
- T6: Phishing Request (EIP-712, High Risk)

Methods:
- PS: Personal Sign (personal_sign)
- TX: Transaction (eth_sendTransaction)
- E712: EIP-712 Typed Data (eth_signTypedData_v4)
"""

# =============================================================================
# T1 - OpenSea Login (Personal Sign, Low Risk)
# =============================================================================
# Method: PS (personal_sign)
# Risk: L (Low)
# Scenario: Standard SIWE login to OpenSea, no asset risk

T1_OPENSEA_LOGIN = {
    "message": "Welcome to OpenSea!\n\nClick to sign in and accept the OpenSea Terms of Service.\n\nThis request will not trigger a blockchain transaction or cost any gas fees.\n\nWallet address:\n0x742d35Cc6634C0532925a3b844Bc454e4438f44e\n\nNonce:\nab8f2d1e-9c3b-4a5f-8d7e-1234567890ab\n\nIssued At:\n2024-01-15T10:30:00.000Z"
}


# =============================================================================
# T2 - NFT Mint (Transaction, Low Risk)
# =============================================================================
# Method: TX (eth_sendTransaction)
# Risk: L (Low)
# Scenario: Mint NFT from a known collection contract
# Contract: Example NFT Contract

T2_NFT_MINT = {
    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "to": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",  # BAYC Contract
    "value": "80000000000000000",  # 0.08 ETH mint price
    "data": "0xa0712d68"  # mint(uint256)
           "0000000000000000000000000000000000000000000000000000000000000001",  # quantity = 1
    "chainId": 1
}


# =============================================================================
# T3 - DAO Vote (EIP-712, Medium Risk)
# =============================================================================
# Method: E712 (eth_signTypedData_v4)
# Risk: M (Medium)
# Scenario: Compound Governor Bravo on-chain vote delegation
# Contract: Compound Governor (0xc0Da02939E1441F497fd74F78cE7Decb17B66529)

T3_DAO_VOTE = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "Ballot": [
            {"name": "proposalId", "type": "uint256"},
            {"name": "support", "type": "uint8"},
            {"name": "voter", "type": "address"},
            {"name": "nonce", "type": "uint256"}
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
        "proposalId": 127,
        "support": 1,  # 0=Against, 1=For, 2=Abstain
        "voter": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "nonce": 0
    }
}


# =============================================================================
# T4 - Bridge / Swap (EIP-712, Medium Risk)
# =============================================================================
# Method: E712 (eth_signTypedData_v4)
# Risk: M (Medium)
# Scenario: Uniswap Permit2 token approval for swap
# Contract: Uniswap Permit2 (0x000000000022D473030F116dDEE9F6B43aC78BA3)

T4_BRIDGE_SWAP = {
    "types": {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"}
        ],
        "PermitSingle": [
            {"name": "details", "type": "PermitDetails"},
            {"name": "spender", "type": "address"},
            {"name": "sigDeadline", "type": "uint256"}
        ],
        "PermitDetails": [
            {"name": "token", "type": "address"},
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"},
            {"name": "nonce", "type": "uint48"}
        ]
    },
    "primaryType": "PermitSingle",
    "domain": {
        "name": "Permit2",
        "chainId": 1,
        "verifyingContract": "0x000000000022D473030F116dDEE9F6B43aC78BA3"
    },
    "message": {
        "details": {
            "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "amount": "1000000000",  # 1000 USDC
            "expiration": 1705399200,  # ~24 hours
            "nonce": 0
        },
        "spender": "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",  # Universal Router
        "sigDeadline": 1705315800
    }
}


# =============================================================================
# T5 - Unlimited Approval (EIP-712, High Risk)
# =============================================================================
# Method: E712 (eth_signTypedData_v4)
# Risk: H (High)
# Scenario: Unlimited token approval to unknown spender
# Contract: USDT (0xdAC17F958D2ee523a2206206994597C13D831ec7)

T5_UNLIMITED_APPROVAL = {
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
        "name": "Tether USD",
        "version": "1",
        "chainId": 1,
        "verifyingContract": "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    },
    "message": {
        "owner": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "spender": "0x1234567890AbcdEF1234567890aBcDeF12345678",  # Unknown address
        "value": "115792089237316195423570985008687907853269984665640564039457584007913129639935",  # uint256.max
        "nonce": 0,
        "deadline": 1893456000  # Year 2030
    }
}


# =============================================================================
# T6 - Phishing Request (EIP-712, High Risk)
# =============================================================================
# Method: E712 (eth_signTypedData_v4)
# Risk: H (High)
# Scenario: Malicious Seaport order that transfers NFT for 0 ETH
# Contract: Seaport 1.5 (0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC)

T6_PHISHING_REQUEST = {
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
            {"name": "conduitKey", "type": "bytes32"},
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
        "version": "1.5",
        "chainId": 1,
        "verifyingContract": "0x00000000000000ADc04C56Bf30aC9d3c0aAF14dC"
    },
    "message": {
        "offerer": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Victim
        "zone": "0x0000000000000000000000000000000000000000",
        "offer": [
            {
                "itemType": 2,  # ERC721
                "token": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",  # BAYC
                "identifierOrCriteria": "8888",
                "startAmount": "1",
                "endAmount": "1"
            }
        ],
        "consideration": [
            {
                "itemType": 0,  # ETH
                "token": "0x0000000000000000000000000000000000000000",
                "identifierOrCriteria": "0",
                "startAmount": "0",  # 0 ETH - Phishing!
                "endAmount": "0",
                "recipient": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
            }
        ],
        "orderType": 0,
        "startTime": "1705312200",
        "endTime": "1737021000",  # 1 year validity
        "zoneHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "12345678901234567890",
        "conduitKey": "0x0000007b02230091a7ed01230072f7006a004d60a8d4e71d599b8104250f0000",
        "counter": "0"
    }
}


# =============================================================================
# T7 - Personal Sign Phishing (Personal Sign, High Risk)
# =============================================================================
# Method: PS (personal_sign)
# Risk: H (High)
# Scenario: Urgent reward message with phishing indicators
#
T7_PERSONAL_SIGN_PHISHING = {
    "message": (
        "URGENT: Verify your wallet immediately to claim your reward.\n"
        "Act now to avoid account suspension.\n"
        "Sign this message to continue."
    )
}


# =============================================================================
# T8 - Multicall Approval (Transaction, Medium Risk)
# =============================================================================
# Method: TX (eth_sendTransaction)
# Risk: M (Medium)
# Scenario: Multicall with a single ERC20 approve call
#
T8_MULTICALL_APPROVE = {
    "from": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
    "to": "0x1111111111111111111111111111111111111111",
    "value": "0",
    "data": (
        "0xac9650d8"
        "0000000000000000000000000000000000000000000000000000000000000020"
        "0000000000000000000000000000000000000000000000000000000000000001"
        "0000000000000000000000000000000000000000000000000000000000000020"
        "0000000000000000000000000000000000000000000000000000000000000044"
        "095ea7b30000000000000000000000001111111111111111111111111111111111111111"
        "0000000000000000000000000000000000000000000000000000000000000001"
        "00000000000000000000000000000000000000000000000000000000"
    ),
    "chainId": 1
}


# =============================================================================
# DATA SUMMARY
# =============================================================================

ALL_TEST_DATA = {
    "t1_opensea_login": T1_OPENSEA_LOGIN,
    "t2_nft_mint": T2_NFT_MINT,
    "t3_dao_vote": T3_DAO_VOTE,
    "t4_bridge_swap": T4_BRIDGE_SWAP,
    "t5_unlimited_approval": T5_UNLIMITED_APPROVAL,
    "t6_phishing_request": T6_PHISHING_REQUEST,
    "t7_personal_sign_phishing": T7_PERSONAL_SIGN_PHISHING,
    "t8_multicall_approve": T8_MULTICALL_APPROVE,
}

# Category index for UI grouping
DATA_CATEGORIES = {
    "low_risk": ["t1_opensea_login", "t2_nft_mint"],
    "medium_risk": ["t3_dao_vote", "t4_bridge_swap", "t8_multicall_approve"],
    "high_risk": ["t5_unlimited_approval", "t6_phishing_request", "t7_personal_sign_phishing"],
}

# Data descriptions for UI display
DATA_DESCRIPTIONS = {
    "t1_opensea_login": "T1: OpenSea Login [PS, Low] - SIWE authentication",
    "t2_nft_mint": "T2: NFT Mint [TX, Low] - Mint from known collection",
    "t3_dao_vote": "T3: DAO Vote [E712, Medium] - Compound governance",
    "t4_bridge_swap": "T4: Bridge/Swap [E712, Medium] - Permit2 token approval",
    "t5_unlimited_approval": "T5: Unlimited Approval [E712, High] - Max uint256 to unknown",
    "t6_phishing_request": "T6: Phishing Request [E712, High] - NFT for 0 ETH",
    "t7_personal_sign_phishing": "T7: Personal Sign Phishing [PS, High] - Urgent reward text",
    "t8_multicall_approve": "T8: Multicall Approve [TX, Medium] - Batch approval call",
}
