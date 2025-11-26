from flask import Blueprint, request, jsonify
import traceback
from ...core.pipeline import SemanticPipeline
from ...utils.mock_data import ALL_TEST_DATA

api_bp = Blueprint('api', __name__, url_prefix='/api')
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
    """Get test data API"""
    try:
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

