"""
EIP712 Signature Parser Web UI
Provides user-friendly interface to parse and display EIP712 signature data
"""

import json
import traceback
import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from dynamic_parser import DynamicEIP712Parser
from dynamic_parser.examples.test_data import ALL_TEST_DATA
from dynamic_parser.openai_nlp_generator import create_openai_generator, generate_english_with_openai

# Try to import highlighter from src, fallback to local implementation
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
    from core.output.highlighter import TextHighlighter
except ImportError:
    # Fallback: create a simple highlighter here
    import re
    from typing import List, Dict, Any
    
    class TextHighlighter:
        KEYWORD_PATTERNS = [
            {"pattern": re.compile(r'\b(danger|risk|warning|caution|careful|safe|dangerous|risky)\b|\b(high|medium|low)\s+risk\b', re.IGNORECASE), "className": 'risk-keyword'},
            {"pattern": re.compile(r'\b(authorize|authorization|approval|transfer|transaction|signature|confirm|login|vote|mint|burn|stake|unstake)\b', re.IGNORECASE), "className": 'action-keyword'},
            {"pattern": re.compile(
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.?\d*)\s+(USD|USDT|USDC|ETH)\s+Coin\b|'  # "1,000 USD Coin"
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.?\d*)\s+(USD|USDT|USDC|ETH|Coin|token)\b|'  # "1,000 USD" or "1,000 Coin"
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+\.?\d*)\b|'  # Standalone numbers like "1,000"
                r'\b(USD|USDT|USDC|ETH|Coin|token)\b',  # Standalone tokens
                re.IGNORECASE
            ), "className": 'amount-keyword'},
            {"pattern": re.compile(r'\b(smart\s+contract|contract|address)\b|(0x[a-fA-F0-9]{40})', re.IGNORECASE), "className": 'keyword-highlight'},
            {"pattern": re.compile(r'\b(unlimited|permanent|all|entire|infinite|permit|approve)\b', re.IGNORECASE), "className": 'keyword-highlight'}
        ]
        
        @staticmethod
        def highlight_keywords(text: str) -> str:
            if not text:
                return text
            matches: List[Dict[str, Any]] = []
            for pattern_info in TextHighlighter.KEYWORD_PATTERNS:
                pattern = pattern_info["pattern"]
                className = pattern_info["className"]
                for match in pattern.finditer(text):
                    matches.append({"start": match.start(), "end": match.end(), "text": match.group(0), "className": className})
            matches.sort(key=lambda m: (-(m["end"] - m["start"]), m["start"]))
            filtered_matches: List[Dict[str, Any]] = []
            for current in matches:
                overlap = False
                for existing in filtered_matches:
                    if current["start"] < existing["end"] and current["end"] > existing["start"]:
                        overlap = True
                        break
                if not overlap:
                    filtered_matches.append(current)
            filtered_matches.sort(key=lambda m: -m["start"])
            highlighted_text = text
            for match_info in filtered_matches:
                start, end, match_text, className = match_info["start"], match_info["end"], match_info["text"], match_info["className"]
                highlighted_text = highlighted_text[:start] + f'<span class="{className}">{match_text}</span>' + highlighted_text[end:]
            return highlighted_text

app = Flask(__name__)

# Automatically load OpenAI API Key
def load_openai_api_key():
    """Automatically load OpenAI API Key"""
    try:
        # Try to read from api_key.txt file in root directory
        api_key_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_key.txt')
        if os.path.exists(api_key_path):
            with open(api_key_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Parse format like "OpenAI: sk-xxx"
                if ':' in content:
                    return content.split(':', 1)[1].strip()
                return content
    except Exception as e:
        print(f"Failed to load API key: {e}")
    return None

# Globally load API Key
OPENAI_API_KEY = load_openai_api_key()


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/parse', methods=['POST'])
def parse_signature():
    """Parse EIP712 signature API"""
    try:
        data = request.json
        # Support multiple field names for backward compatibility
        signature_data = data.get('data') or data.get('signature_data') or data.get('eip712_data')
        
        if not signature_data:
            return jsonify({'error': 'Please provide signature data'}), 400
        
        # If it's a string, try to parse as JSON
        if isinstance(signature_data, str):
            try:
                signature_data = json.loads(signature_data)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON format'}), 400
        
        # Create parser and parse
        parser = DynamicEIP712Parser()
        result = parser.parse(signature_data)
        
        # Format result
        formatted_result = parser.format_result(result)
        
        # OpenAI English description generation (enabled by default)
        english_description = None
        if OPENAI_API_KEY:
            try:
                english_output = generate_english_with_openai(signature_data, OPENAI_API_KEY)
                # Convert EnglishNLOutput to dict and apply highlighting
                english_description = {
                    'title': english_output.title,
                    'summary': TextHighlighter.highlight_keywords(english_output.summary),
                    'detailed_description': english_output.detailed_description,
                    'technical_details': english_output.technical_details,
                    'context': english_output.context,
                    'risk_level': english_output.risk_level,
                    'risk_explanation': english_output.risk_explanation
                }
            except Exception as e:
                print(f"OpenAI generation failed: {e}")
                english_description = {
                    'error': f"OpenAI generation failed: {str(e)}"
                }
        else:
            english_description = {
                'error': "OpenAI API Key not configured"
            }
        
        # Convert to JSON serializable format
        serialized_result = {
            'success': True,
            'formatted_result': formatted_result,
            'raw_result': {
                'domain_info': {
                    'name': next((f.value for f in result.domain.fields if f.name == 'name'), 'Unknown'),
                    'version': next((f.value for f in result.domain.fields if f.name == 'version'), 'Unknown'),
                    'chainId': next((f.value for f in result.domain.fields if f.name == 'chainId'), 'Unknown'), 
                    'verifyingContract': next((f.value for f in result.domain.fields if f.name == 'verifyingContract'), 'Unknown'),
                    'fields': [
                        {
                            'name': field.name,
                            'type': field.field_type.value,
                            'semantic': field.semantic.value if field.semantic else None,
                            'description': field.description,
                            'value': field.value
                        } for field in result.domain.fields
                    ]
                },
                'primary_struct': {
                    'name': result.message.name,
                    'fields': [
                        {
                            'name': field.name,
                            'type': field.field_type.value,
                            'semantic': field.semantic.value if field.semantic else None,
                            'description': field.description,
                            'value': field.value
                        } for field in result.message.fields
                    ]
                },
                'all_structs': {
                    'EIP712Domain': {
                        'name': 'EIP712Domain',
                        'fields': [
                            {
                                'name': field.name,
                                'type': field.field_type.value,
                                'semantic': field.semantic.value if field.semantic else None,
                                'description': field.description,
                                'value': field.value
                            } for field in result.domain.fields
                        ]
                    },
                    result.message.name: {
                        'name': result.message.name,
                        'fields': [
                            {
                                'name': field.name,
                                'type': field.field_type.value,
                                'semantic': field.semantic.value if field.semantic else None,
                                'description': field.description,
                                'value': field.value
                            } for field in result.message.fields
                        ]
                    }
                },
                'risk_level': getattr(result, 'risk_level', 'unknown'),
                'english_description': english_description if english_description else None
            }
        }
        
        return jsonify(serialized_result)
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        return jsonify({
            'success': False,
            'error': error_msg,
            'traceback': traceback_str
        }), 500


@app.route('/api/test_data')
def get_test_data():
    """Get test data API"""
    try:
        # Convert test data to JSON format
        test_data = {}
        for name, data in ALL_TEST_DATA.items():
            test_data[name] = {
                'name': name,
                'data': data,
                'description': f"{name} example data"
            }
        
        return jsonify({
            'success': True,
            'test_data': test_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 