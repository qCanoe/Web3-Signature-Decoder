"""
Dynamic ABI and function signature fetcher.
Supports Etherscan API and 4byte.directory for fallback signature lookup.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from functools import lru_cache
from ..config import Config
from ..utils.logger import Logger

logger = Logger.get_logger("ABIFetcher")


class ABIFetcher:
    """
    Fetches contract ABIs and function signatures from external sources.
    """
    
    # Etherscan API endpoints by chain ID
    ETHERSCAN_ENDPOINTS: Dict[int, str] = {
        1: "https://api.etherscan.io/api",
        137: "https://api.polygonscan.com/api",
        42161: "https://api.arbiscan.io/api",
        10: "https://api-optimistic.etherscan.io/api",
        8453: "https://api.basescan.org/api",
        56: "https://api.bscscan.com/api",
        43114: "https://api.snowtrace.io/api",
        250: "https://api.ftmscan.com/api",
        100: "https://api.gnosisscan.io/api",
        324: "https://api-era.zksync.network/api",
        534352: "https://api.scrollscan.com/api",
        59144: "https://api.lineascan.build/api",
        81457: "https://api.blastscan.io/api",
    }
    
    # 4byte.directory API endpoint
    FOURBYTE_API = "https://www.4byte.directory/api/v1/signatures/"
    
    # Cache for fetched ABIs
    _abi_cache: Dict[str, Dict[str, Any]] = {}
    _selector_cache: Dict[str, str] = {}
    
    @staticmethod
    def get_etherscan_api_key() -> Optional[str]:
        """Get Etherscan API key from environment or file."""
        key = os.environ.get("ETHERSCAN_API_KEY")
        if key:
            return key
        
        try:
            api_key_file = Config.BASE_DIR.parent / "api_key.txt"
            if api_key_file.exists():
                with open(api_key_file, "r") as f:
                    for line in f:
                        if line.startswith("ETHERSCAN:"):
                            return line.split(":", 1)[1].strip()
        except Exception as error:
            logger.warning(f"Failed to read Etherscan API key: {error}")
        
        return None
    
    @staticmethod
    @lru_cache(maxsize=500)
    def fetch_contract_abi(chain_id: int, address: str) -> Optional[Dict[str, Any]]:
        """
        Fetch contract ABI from Etherscan-like API.
        
        Args:
            chain_id: Blockchain chain ID
            address: Contract address
            
        Returns:
            ABI dictionary or None if not found
        """
        if chain_id not in ABIFetcher.ETHERSCAN_ENDPOINTS:
            logger.debug(f"No Etherscan endpoint for chain {chain_id}")
            return None
        
        cache_key = f"{chain_id}:{address.lower()}"
        if cache_key in ABIFetcher._abi_cache:
            return ABIFetcher._abi_cache[cache_key]
        
        api_key = ABIFetcher.get_etherscan_api_key()
        endpoint = ABIFetcher.ETHERSCAN_ENDPOINTS[chain_id]
        
        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
        }
        
        if api_key:
            params["apikey"] = api_key
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "1" and data.get("result"):
                abi = json.loads(data["result"])
                result = {"abi": abi, "source": "etherscan"}
                ABIFetcher._abi_cache[cache_key] = result
                logger.info(f"Fetched ABI for {address} on chain {chain_id}")
                return result
            else:
                logger.debug(f"ABI not found for {address}: {data.get('message')}")
                return None
                
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch ABI: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse ABI response: {e}")
            return None
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def fetch_function_signature(selector: str) -> Optional[str]:
        """
        Fetch function signature from 4byte.directory.
        
        Args:
            selector: 4-byte function selector (e.g., "0xa9059cbb")
            
        Returns:
            Function signature string or None if not found
        """
        selector = selector.lower()
        if selector in ABIFetcher._selector_cache:
            return ABIFetcher._selector_cache[selector]
        
        # Remove 0x prefix for API query
        hex_sig = selector[2:] if selector.startswith("0x") else selector
        
        try:
            response = requests.get(
                ABIFetcher.FOURBYTE_API,
                params={"hex_signature": hex_sig},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            results = data.get("results", [])
            if results:
                # Return the most popular (first) result
                signature = results[0].get("text_signature")
                if signature:
                    ABIFetcher._selector_cache[selector] = signature
                    logger.debug(f"Found signature for {selector}: {signature}")
                    return signature
            
            logger.debug(f"No signature found for {selector}")
            return None
            
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch signature from 4byte: {e}")
            return None
    
    @staticmethod
    def parse_function_from_abi(abi: List[Dict[str, Any]], selector: str) -> Optional[Dict[str, Any]]:
        """
        Find and parse function definition from ABI by selector.
        
        Args:
            abi: Contract ABI array
            selector: Function selector to find
            
        Returns:
            Function definition dictionary or None
        """
        from eth_abi import encode
        from eth_utils import keccak
        
        selector = selector.lower()
        
        for item in abi:
            if item.get("type") != "function":
                continue
            
            name = item.get("name", "")
            inputs = item.get("inputs", [])
            
            # Build signature
            input_types = []
            param_names = []
            for inp in inputs:
                input_types.append(ABIFetcher._get_abi_type(inp))
                param_names.append(inp.get("name", ""))
            
            signature = f"{name}({','.join(input_types)})"
            
            # Calculate selector
            try:
                calculated_selector = "0x" + keccak(text=signature).hex()[:8]
                
                if calculated_selector.lower() == selector:
                    return {
                        "name": name,
                        "signature": signature,
                        "params": input_types,
                        "param_names": param_names,
                        "category": ABIFetcher._infer_category(name),
                        "source": "abi"
                    }
            except Exception:
                continue
        
        return None
    
    @staticmethod
    def _get_abi_type(param: Dict[str, Any]) -> str:
        """Convert ABI parameter to type string."""
        base_type = param.get("type", "")
        
        # Handle tuple types
        if base_type == "tuple" or base_type.startswith("tuple"):
            components = param.get("components", [])
            component_types = [ABIFetcher._get_abi_type(c) for c in components]
            tuple_str = f"({','.join(component_types)})"
            
            # Handle tuple arrays
            if base_type.endswith("[]"):
                return tuple_str + "[]"
            return tuple_str
        
        return base_type
    
    @staticmethod
    def _infer_category(function_name: str) -> str:
        """Infer function category from name."""
        name_lower = function_name.lower()
        
        if "transfer" in name_lower:
            if "from" in name_lower:
                return "erc20_transfer_from"
            return "erc20_transfer"
        elif "approve" in name_lower:
            return "erc20_approve"
        elif "permit" in name_lower:
            return "permit"
        elif "swap" in name_lower:
            return "defi_swap"
        elif "stake" in name_lower:
            return "defi_stake"
        elif "unstake" in name_lower or "withdraw" in name_lower:
            return "defi_withdraw"
        elif "deposit" in name_lower or "supply" in name_lower:
            return "defi_deposit"
        elif "borrow" in name_lower:
            return "defi_borrow"
        elif "repay" in name_lower:
            return "defi_repay"
        elif "mint" in name_lower:
            return "nft_mint"
        elif "burn" in name_lower:
            return "nft_burn"
        elif "delegate" in name_lower:
            return "governance_delegation"
        elif "vote" in name_lower or "cast" in name_lower:
            return "governance"
        elif "multicall" in name_lower or "execute" in name_lower:
            return "multicall"
        elif "bridge" in name_lower or "lock" in name_lower or "unlock" in name_lower:
            return "bridge"
        
        return "contract_call"
    
    @staticmethod
    def resolve_unknown_selector(
        selector: str,
        chain_id: Optional[int] = None,
        contract_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Try to resolve an unknown function selector using multiple sources.
        
        Args:
            selector: Function selector
            chain_id: Optional chain ID for ABI lookup
            contract_address: Optional contract address for ABI lookup
            
        Returns:
            Function definition or None
        """
        # 1. Try to fetch from contract ABI if we have the address
        if chain_id and contract_address:
            abi_data = ABIFetcher.fetch_contract_abi(chain_id, contract_address)
            if abi_data and "abi" in abi_data:
                func_def = ABIFetcher.parse_function_from_abi(abi_data["abi"], selector)
                if func_def:
                    return func_def
        
        # 2. Fall back to 4byte.directory
        signature = ABIFetcher.fetch_function_signature(selector)
        if signature:
            # Parse the signature string
            name = signature.split("(")[0]
            params_str = signature.split("(")[1].rstrip(")")
            params = [p.strip() for p in params_str.split(",")] if params_str else []
            
            return {
                "name": name,
                "signature": signature,
                "params": params,
                "param_names": [f"param_{i}" for i in range(len(params))],
                "category": ABIFetcher._infer_category(name),
                "source": "4byte"
            }
        
        return None
    
    @staticmethod
    def clear_cache():
        """Clear all cached data."""
        ABIFetcher._abi_cache.clear()
        ABIFetcher._selector_cache.clear()
        ABIFetcher.fetch_contract_abi.cache_clear()
        ABIFetcher.fetch_function_signature.cache_clear()
        logger.info("ABIFetcher cache cleared")

