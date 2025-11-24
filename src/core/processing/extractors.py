import re
import json
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, urlparse

class ParameterExtractor:
    """
    Extracts structured parameters from unstructured text messages.
    """
    
    # Regex Patterns
    PATTERNS = {
        "ETH_ADDRESS": re.compile(r'0x[a-fA-F0-9]{40}'),
        "DOMAIN": re.compile(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}'),
        "TIMESTAMP": re.compile(r'\b\d{10,13}\b'),
        "UUID": re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE),
        "URL": re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    }

    @staticmethod
    def extract(message: str) -> Dict[str, Any]:
        params = {}
        
        # 1. Cleanup
        message = ParameterExtractor._clean_message(message)
        
        # 2. Try JSON
        json_data = ParameterExtractor._try_parse_json(message)
        if json_data:
            params.update(json_data)
            return params # If fully JSON, return directly
            
        # 3. Try Query String
        query_params = ParameterExtractor._try_parse_query_string(message)
        if query_params:
            # Flatten list values
            flat_query = {k: v[0] if isinstance(v, list) and v else v for k, v in query_params.items()}
            params.update(flat_query)
        
        # 4. Regex Extraction
        if "address" not in params:
            addrs = ParameterExtractor.PATTERNS["ETH_ADDRESS"].findall(message)
            if addrs: params["address"] = addrs[0]
            
        if "domain" not in params:
            domains = ParameterExtractor.PATTERNS["DOMAIN"].findall(message)
            if domains: params["domain"] = domains[0]
            
        if "timestamp" not in params:
            ts = ParameterExtractor.PATTERNS["TIMESTAMP"].findall(message)
            if ts: params["timestamp"] = ts[0]
            
        if "nonce" not in params:
            uuids = ParameterExtractor.PATTERNS["UUID"].findall(message)
            if uuids: params["nonce"] = uuids[0]

        # 5. Key-Value Pairs (Line by Line)
        lines = message.split('\n')
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    val = parts[1].strip()
                    
                    # Map common keys
                    if key in ['domain', 'site', 'website', 'uri']: params["domain"] = val
                    elif key in ['nonce', 'random', 'token', 'challenge']: params["nonce"] = val
                    elif key in ['timestamp', 'time', 'date']: params["timestamp"] = val
                    elif key in ['address', 'wallet', 'account']: params["address"] = val
                    else:
                        # Add other keys if valid identifier (simple heuristic)
                        if ' ' not in key:
                            params[key] = val
                            
        return params

    @staticmethod
    def _clean_message(message: str) -> str:
        if message.startswith('0x'):
            try:
                # Try decoding hex
                decoded = bytes.fromhex(message[2:]).decode('utf-8', errors='ignore')
                if any(c.isalnum() for c in decoded): # Check if meaningful content
                    return decoded
            except:
                pass
        return message.strip()

    @staticmethod
    def _try_parse_json(message: str) -> Optional[Dict[str, Any]]:
        try:
            # Try full JSON
            return json.loads(message)
        except:
            # Try finding JSON block
            match = re.search(r'\{.*\}', message, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        return None

    @staticmethod
    def _try_parse_query_string(message: str) -> Optional[Dict[str, Any]]:
        if 'http' in message:
            try:
                parsed = urlparse(message)
                if parsed.query:
                    return parse_qs(parsed.query)
            except:
                pass
        if '=' in message and '&' in message:
             try:
                 return parse_qs(message)
             except:
                 pass
        return None

