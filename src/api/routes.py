"""
API Routes for Spec Compliance Checker Service
"""
import os
import logging
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime

from src.core.checker import ComplianceChecker
from src.utils.validators import validate_check_request

api_blueprint = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

# Store for compliance checks (in-memory for simplicity, use DB in production)
checks_store = {}
checker = ComplianceChecker()

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        expected_key = os.getenv('API_KEY')
        
        if not expected_key:
            # API key must be configured for security
            logger.error("API_KEY not configured - authentication required")
            return jsonify({
                'error': {
                    'code': 'CONFIGURATION_ERROR',
                    'message': 'API key authentication is not configured. Set API_KEY environment variable.'
                }
            }), 500
        
        if api_key != expected_key:
            return jsonify({
                'error': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Invalid or missing API key'
                }
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Ollama connectivity
        ollama_status = checker.check_ollama_health()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'ollama_status': ollama_status.get('status', 'unknown'),
            'ollama_model': os.getenv('OLLAMA_MODEL', 'codellama:7b-instruct')
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'error': str(e)
        }), 503

@api_blueprint.route('/compliance/check', methods=['POST'])
@require_api_key
def trigger_compliance_check():
    """Trigger a new compliance check"""
    try:
        data = request.get_json()
        
        # Validate request
        validation_error = validate_check_request(data)
        if validation_error:
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': validation_error
                }
            }), 400
        
        # Start compliance check
        result = checker.start_check(
            repository_url=data['repository_url'],
            branch=data.get('branch', 'main'),
            spec_files=data.get('spec_files'),
            target_paths=data.get('target_paths'),
            options=data.get('options', {})
        )
        
        # Store check in memory
        checks_store[result['check_id']] = result
        
        return jsonify(result), 202
        
    except Exception as e:
        logger.error(f"Failed to start compliance check: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to start compliance check',
                'details': str(e)
            }
        }), 500

@api_blueprint.route('/compliance/check/<check_id>', methods=['GET'])
@require_api_key
def get_check_status(check_id):
    """Get status of a compliance check"""
    try:
        # Get from store
        check = checks_store.get(check_id)
        
        if not check:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Check {check_id} not found'
                }
            }), 404
        
        # Update status from checker
        status = checker.get_check_status(check_id)
        if status:
            checks_store[check_id].update(status)
        
        return jsonify(checks_store[check_id]), 200
        
    except Exception as e:
        logger.error(f"Failed to get check status: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve check status',
                'details': str(e)
            }
        }), 500

@api_blueprint.route('/compliance/checks', methods=['GET'])
@require_api_key
def list_compliance_checks():
    """List all compliance checks"""
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        repo_filter = request.args.get('repository')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        # Filter checks
        filtered_checks = list(checks_store.values())
        
        if status_filter:
            filtered_checks = [c for c in filtered_checks if c.get('status') == status_filter]
        
        if repo_filter:
            filtered_checks = [c for c in filtered_checks if repo_filter in c.get('repository', '')]
        
        # Sort by started_at (newest first)
        filtered_checks.sort(key=lambda x: x.get('started_at', ''), reverse=True)
        
        # Paginate
        total = len(filtered_checks)
        paginated_checks = filtered_checks[offset:offset + limit]
        
        return jsonify({
            'total': total,
            'limit': limit,
            'offset': offset,
            'checks': paginated_checks
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list checks: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to list checks',
                'details': str(e)
            }
        }), 500

@api_blueprint.route('/compliance/check/<check_id>/todo', methods=['GET'])
@require_api_key
def get_todo_report(check_id):
    """Get TODO.md report for a completed check"""
    try:
        check = checks_store.get(check_id)
        
        if not check:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Check {check_id} not found'
                }
            }), 404
        
        if check.get('status') != 'completed':
            return jsonify({
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Check has not completed yet'
                }
            }), 400
        
        # Get TODO content
        todo_content = checker.get_todo_content(check_id)
        
        return todo_content, 200, {'Content-Type': 'text/markdown'}
        
    except Exception as e:
        logger.error(f"Failed to get TODO report: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to retrieve TODO report',
                'details': str(e)
            }
        }), 500

@api_blueprint.route('/compliance/check/<check_id>', methods=['DELETE'])
@require_api_key
def delete_check(check_id):
    """Delete a compliance check"""
    try:
        if check_id not in checks_store:
            return jsonify({
                'error': {
                    'code': 'NOT_FOUND',
                    'message': f'Check {check_id} not found'
                }
            }), 404
        
        # Delete from store
        del checks_store[check_id]
        
        # Clean up from checker
        checker.delete_check(check_id)
        
        return jsonify({
            'message': 'Check deleted successfully',
            'check_id': check_id
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to delete check: {e}")
        return jsonify({
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete check',
                'details': str(e)
            }
        }), 500
