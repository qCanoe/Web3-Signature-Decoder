import re
import json
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, urlparse
from ..utils.logger import Logger

logger = Logger.get_logger(__name__)

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
        
        # 2b. Try SIWE (Sign-In with Ethereum)
        siwe_data = ParameterExtractor._try_parse_siwe(message)
        if siwe_data:
            params.update(siwe_data)
            
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
        is_siwe = bool(params.get("siwe"))
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    val = parts[1].strip()
                    
                    # Map common keys
                    if key in ['domain', 'site', 'website']: 
                        params["domain"] = val
                    elif key == 'uri':
                        if is_siwe:
                            params["uri"] = val
                        else:
                            params["domain"] = val
                    elif key in ['nonce', 'random', 'token', 'challenge']: params["nonce"] = val
                    elif key in ['timestamp', 'time', 'date']: params["timestamp"] = val
                    elif key in ['address', 'wallet', 'account']: params["address"] = val
                    elif key in ['chain id', 'chainid', 'chain_id']: params["chain_id"] = val
                    elif key in ['issued at', 'issued_at']: params["issued_at"] = val
                    elif key in ['expiration time', 'expiration_time', 'expiry']: params["expiration_time"] = val
                    elif key in ['not before', 'not_before']: params["not_before"] = val
                    elif key in ['request id', 'request_id']: params["request_id"] = val
                    elif key in ['version']: params["version"] = val
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
            except Exception as error:
                logger.debug(f"Failed to decode hex message: {error}")
        return message.strip()

    @staticmethod
    def _try_parse_json(message: str) -> Optional[Dict[str, Any]]:
        try:
            # Try full JSON
            return json.loads(message)
        except Exception as error:
            logger.debug(f"Failed to parse message as JSON: {error}")
            # Try finding JSON block
            match = re.search(r'\{.*\}', message, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception as error:
                    logger.debug(f"Failed to parse JSON block: {error}")
        return None

    @staticmethod
    def _try_parse_query_string(message: str) -> Optional[Dict[str, Any]]:
        if 'http' in message:
            try:
                parsed = urlparse(message)
                if parsed.query:
                    return parse_qs(parsed.query)
            except Exception as error:
                logger.debug(f"Failed to parse URL query string: {error}")
        if '=' in message and '&' in message:
             try:
                 return parse_qs(message)
             except Exception as error:
                 logger.debug(f"Failed to parse query string: {error}")
        return None

    @staticmethod
    def _try_parse_siwe(message: str) -> Optional[Dict[str, Any]]:
        """
        Parse Sign-In with Ethereum (SIWE / EIP-4361) messages.
        """
        lines = [line.rstrip() for line in message.splitlines()]
        if len(lines) < 2:
            return None

        header = lines[0].strip()
        match = re.match(
            r"^(.+?) wants you to sign in with your ethereum account:?\s*$",
            header,
            re.IGNORECASE,
        )
        if not match:
            return None

        address = lines[1].strip()
        if not re.fullmatch(r"0x[a-fA-F0-9]{40}", address):
            return None

        def _is_field_line(line: str) -> bool:
            return re.match(
                r"^(URI|Version|Chain ID|Nonce|Issued At|Expiration Time|Not Before|Request ID|Resources):",
                line,
                re.IGNORECASE,
            ) is not None

        field_index = None
        for i in range(2, len(lines)):
            if _is_field_line(lines[i].strip()):
                field_index = i
                break

        statement_lines = []
        if field_index is not None:
            statement_lines = lines[2:field_index]
        else:
            statement_lines = lines[2:]

        statement = "\n".join([l for l in statement_lines if l.strip()]).strip() or None

        parsed: Dict[str, Any] = {
            "siwe": True,
            "domain": match.group(1).strip(),
            "address": address,
        }
        if statement:
            parsed["statement"] = statement

        resources = []
        i = field_index if field_index is not None else len(lines)
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            if re.match(r"^Resources:\s*$", line, re.IGNORECASE):
                i += 1
                while i < len(lines):
                    res_line = lines[i].strip()
                    if not res_line:
                        i += 1
                        continue
                    if res_line.startswith("-"):
                        resources.append(res_line[1:].strip())
                        i += 1
                        continue
                    if _is_field_line(res_line):
                        break
                    break
                continue

            match_field = re.match(
                r"^(URI|Version|Chain ID|Nonce|Issued At|Expiration Time|Not Before|Request ID):\s*(.*)$",
                line,
                re.IGNORECASE,
            )
            if match_field:
                field = match_field.group(1).lower()
                value = match_field.group(2).strip()
                field_map = {
                    "uri": "uri",
                    "version": "version",
                    "chain id": "chain_id",
                    "nonce": "nonce",
                    "issued at": "issued_at",
                    "expiration time": "expiration_time",
                    "not before": "not_before",
                    "request id": "request_id",
                }
                mapped = field_map.get(field, field.replace(" ", "_"))
                if value:
                    parsed[mapped] = value
            i += 1

        if resources:
            parsed["resources"] = resources

        return parsed

