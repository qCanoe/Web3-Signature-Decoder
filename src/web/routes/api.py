from flask import Blueprint, request, jsonify
import json
import re
import traceback
from typing import Any, Dict, List
from ...core.pipeline import SemanticPipeline
from ...utils.mock_data import ALL_TEST_DATA, DATA_CATEGORIES, DATA_DESCRIPTIONS

api_bp = Blueprint('api', __name__, url_prefix='/api')
snap_bp = Blueprint('snap', __name__)
pipeline = SemanticPipeline()

@api_bp.route('/parse', methods=['POST'])
def parse_signature():
    """Parse API using the new Semantic Pipeline"""
    try:
        data = request.json
        # Support multiple field names for backward compatibility
        raw_data = data.get('data') or data.get('signature_data') or data.get('eip712_data')
        origin = data.get('origin') or data.get('dapp_url')  # DApp origin URL
        
        if not raw_data:
            return jsonify({'error': 'Please provide signature data'}), 400
            
        # Run the pipeline with origin support
        # The pipeline returns a result dict formatted for the UI
        result = pipeline.process(raw_data, origin=origin)
        
        return jsonify(result)
        
    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return jsonify({
            'success': False,
            'error': error_msg,
            'traceback': traceback_str
        }), 500

@api_bp.route('/test_data')
def get_test_data():
    """Get test data API with categories and descriptions"""
    try:
        test_data = {}
        for name, data in ALL_TEST_DATA.items():
            risk_level = 'medium'
            for level, items in DATA_CATEGORIES.items():
                if name in items:
                    risk_level = level
                    break
            
            test_data[name] = {
                'name': name,
                'data': data,
                'description': DATA_DESCRIPTIONS.get(name, f"{name} example data"),
                'risk_level': risk_level
            }
        
        return jsonify({
            'success': True,
            'test_data': test_data,
            'categories': DATA_CATEGORIES
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@snap_bp.route('/health', methods=['GET'])
def snap_health():
    """Health check for Snap backend."""
    return jsonify({'status': 'ok'})

@snap_bp.route('/snap/analyze', methods=['POST'])
def snap_analyze():
    """
    Snap analysis endpoint compatible with MetaMask Snap requests.
    Expects: { type, data, origin?, chainId?, signatureMethod? }
    """
    try:
        payload = request.json or {}
        req_type = payload.get('type')
        origin = payload.get('origin')
        data = payload.get('data')
        chain_id = payload.get('chainId')
        signature_method = payload.get('signatureMethod')

        if req_type == 'signature':
            raw_data = _extract_signature_payload(data, signature_method)
            if raw_data is None:
                return jsonify({'error': 'Invalid signature payload'}), 400
            result = pipeline.process(raw_data, origin=origin)
            return jsonify(_to_snap_result(result))

        if req_type == 'transaction':
            if not isinstance(data, dict):
                return jsonify({'error': 'Invalid transaction payload'}), 400
            tx_data = dict(data)
            if chain_id and 'chainId' not in tx_data:
                tx_data['chainId'] = chain_id
            result = pipeline.process(tx_data, origin=origin)
            return jsonify(_to_snap_result(result))

        return jsonify({'error': 'Invalid request type'}), 400

    except Exception as e:
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return jsonify({
            'success': False,
            'error': error_msg,
            'traceback': traceback_str
        }), 500


def _extract_signature_payload(data: Any, signature_method: Any) -> Any:
    """
    Normalize Snap signature payload to raw data accepted by the pipeline.
    """
    if isinstance(data, dict):
        # Snap signature objects usually include { data, signatureMethod, from }
        if 'data' in data:
            return data.get('data')
        return data
    if isinstance(data, str):
        return data
    if signature_method and isinstance(signature_method, str):
        # Fallback: allow passing the whole object if needed
        return data
    return None


def _to_snap_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert pipeline output to Snap AnalysisResult shape.
    """
    pipeline_result = result.get('pipeline_result')
    if not isinstance(pipeline_result, dict):
        pipeline_result = result if isinstance(result, dict) else {}
    ui = pipeline_result.get('ui', {}) if isinstance(pipeline_result, dict) else {}
    semantic = pipeline_result.get('semantic', {}) if isinstance(pipeline_result, dict) else {}

    action = ui.get('title') or _safe_get(semantic, ['action', 'name']) or 'Unknown Operation'
    description = ui.get('description') or ''

    risk_level = ui.get('risk_level') or 'medium'
    risk_score = ui.get('risk_score') or 0
    risk_reasons = ui.get('risk_reasons') or []

    highlights = _build_highlights(semantic.get('context', []))
    actors = _build_actors(semantic)

    return {
        'action': action,
        'description': description,
        'risk': {
            'level': risk_level,
            'score': risk_score,
            'reasons': risk_reasons,
        },
        'highlights': highlights,
        'actors': actors,
    }


def _build_highlights(context: Any) -> List[Dict[str, str]]:
    if not isinstance(context, list):
        return []

    highlights = []
    for item in context:
        if not isinstance(item, dict):
            continue
        label = str(item.get('label') or item.get('description') or 'Context')
        value = _stringify(item.get('value') or item.get('raw_value'))
        highlight_type = _infer_highlight_type(label, value)
        highlights.append({
            'label': label,
            'value': value,
            'type': highlight_type,
        })
    return highlights


def _build_actors(semantic: Dict[str, Any]) -> List[Dict[str, str]]:
    actors = []
    actor = semantic.get('actor', {}) if isinstance(semantic, dict) else {}
    obj = semantic.get('object', {}) if isinstance(semantic, dict) else {}

    actor_value = actor.get('value')
    if _is_hex_address(actor_value):
        actors.append({
            'role': actor.get('name') or 'Actor',
            'address': actor_value,
        })

    object_value = obj.get('value')
    if _is_hex_address(object_value):
        actors.append({
            'role': obj.get('name') or 'Object',
            'address': object_value,
        })

    return actors


def _infer_highlight_type(label: str, value: str) -> str:
    if _is_hex_address(value):
        return 'address'
    lowered = (label or '').lower()
    if 'amount' in lowered or 'value' in lowered:
        return 'amount'
    return 'text'


def _stringify(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value)
        except Exception:
            return str(value)
    return str(value)


def _is_hex_address(value: Any) -> bool:
    return isinstance(value, str) and re.match(r'^0x[a-fA-F0-9]{40}$', value) is not None


def _safe_get(data: Any, path: List[str]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
