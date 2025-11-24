# Knowledge Base Data Files

This directory contains static data files for the knowledge base, stored in JSON format for easy maintenance and updates.

## File Descriptions

### `function_signatures.json`
Function signature registry, containing mappings from 4-byte selectors to function definitions.
- **Format**: `{ "selector": { "name": "...", "signature": "...", "params": [...], "param_names": [...], "category": "..." } }`
- **Purpose**: Identify and parse smart contract function calls

### `eip712_types.json`
Mapping from EIP-712 primary types to semantic categories.
- **Format**: `{ "PrimaryType": "category" }`
- **Purpose**: Identify semantic types of EIP-712 signatures (e.g., authorization, marketplace_listing, governance, etc.)

### `known_contracts.json`
Mapping of known protocol contract addresses.
- **Format**: `{ "chain_id": { "address": "name" } }`
- **Purpose**: Identify known protocol contracts (DeFi, NFT marketplaces, governance, etc.)

### `token_metadata.json`
Token metadata (symbol, decimals, name).
- **Format**: `{ "address": { "symbol": "...", "decimals": ..., "name": "..." } }`
- **Purpose**: Provide readable token information, supporting multi-chain tokens

### `personal_sign_patterns.json`
Patterns and keywords for Personal Sign messages.
- **Format**: `{ "category": { "keywords": [...], "patterns": [...] } }`
- **Purpose**: Identify intent of Personal Sign messages (authentication, binding, authorization, verification)

### `actor_field_patterns.json`
Actor field name patterns.
- **Format**: `{ "role": ["pattern1", "pattern2", ...] }`
- **Purpose**: Identify Actor roles based on field names (user, spender, protocol, marketplace, etc.)

### `protocol_name_patterns.json`
Protocol name patterns.
- **Format**: `{ "protocol_type": ["pattern1", "pattern2", ...] }`
- **Purpose**: Identify protocol types based on domain names or contract names (nft_marketplace, defi, governance, etc.)

### `chain_names.json`
Mapping from chain ID to chain name.
- **Format**: `{ "chain_id": "Chain Name" }`
- **Purpose**: Convert chain IDs to human-readable chain names

## Updating Data

To update knowledge base data, simply edit the corresponding JSON files. The code will automatically read these files when the module is loaded.

## Notes

1. **JSON Format**: Ensure JSON files are correctly formatted, otherwise loading will fail
2. **Backward Compatibility**: Keys in `known_contracts.json` and `chain_names.json` are string-format chain IDs, which are automatically converted to integers by the code
3. **Encoding**: All JSON files use UTF-8 encoding, supporting multilingual content
4. **Regular Expressions**: The `patterns` field in `personal_sign_patterns.json` contains regular expression strings

## Advantages

- ✅ **Readability**: JSON format is more readable than Python dictionaries
- ✅ **Maintainability**: Update data without modifying Python code
- ✅ **Version Control**: JSON files facilitate version control and collaboration
- ✅ **Tool Support**: Can use JSON editors, validation tools, etc.

