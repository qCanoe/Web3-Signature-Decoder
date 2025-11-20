#!/usr/bin/env python3
"""
Parameter extraction method tests
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personal_sign_parser.parameter_extractor import ParameterExtractor


def test_extraction_methods():
    """Test different parameter extraction methods"""
    extractor = ParameterExtractor()
    
    # Test messages
    messages = [
        "Sign in to example.com\nNonce: abc123",
        '{"domain":"app.com","nonce":"xyz789"}', 
        "domain=site.com&nonce=token123",
        "Visit https://myapp.com and use nonce abc123"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"📝 Test {i}: {message[:40]}...")
        
        # Detailed extraction process
        cleaned = extractor._clean_message(message)
        print(f"  After cleaning: {cleaned}")
        
        # JSON parsing
        json_data = extractor._try_parse_json(cleaned)
        if json_data:
            print(f"  JSON parsing: {json_data}")
        
        # Query string parsing
        query_data = extractor._try_parse_query_string(cleaned)
        if query_data:
            print(f"  Query string: {query_data}")
        
        # Final extraction result
        params = extractor.extract(message)
        print(f"  Final result:")
        print(f"    Domain: {params.domain}")
        print(f"    Nonce: {params.nonce}")
        print(f"    Custom fields: {params.custom_fields}")
        print()


if __name__ == "__main__":
    test_extraction_methods() 