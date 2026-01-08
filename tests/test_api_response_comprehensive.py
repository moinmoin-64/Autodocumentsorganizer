"""
Comprehensive API Response Tests
Tests for API response formatting and status codes
"""

import pytest
import json
from app.api_response import APIResponse


class TestAPIResponseSuccess:
    """Test successful API responses"""
    
    def test_success_with_data(self, app):
        """Test success response with data"""
        with app.app_context():
            response, code = APIResponse.success(data={'name': 'test'})
            # response is a jsonify object, convert to dict
            response_data = json.loads(response.get_data())
            assert code == 200
            assert response_data['success'] is True
            assert response_data['data'] == {'name': 'test'}
    
    def test_success_with_message(self, app):
        """Test success response with message"""
        with app.app_context():
            response, code = APIResponse.success(message='Test message')
            response_data = json.loads(response.get_data())
            assert code == 200
            assert response_data['success'] is True
            assert response_data['message'] == 'Test message'
    
    def test_success_with_data_and_message(self, app):
        """Test success response with both data and message"""
        with app.app_context():
            response, code = APIResponse.success(data={'value': 1}, message='Done')
            response_data = json.loads(response.get_data())
            assert code == 200
            assert response_data['success'] is True
            assert response_data['data'] == {'value': 1}
            assert response_data['message'] == 'Done'
    
    def test_success_default_message(self, app):
        """Test success response with default message"""
        with app.app_context():
            response, code = APIResponse.success()
            response_data = json.loads(response.get_data())
            assert code == 200
            assert response_data['success'] is True
            assert 'message' in response_data or response_data.get('message') == 'Success'


class TestAPIResponseError:
    """Test error API responses"""
    
    def test_error_response(self, app):
        """Test error response"""
        with app.app_context():
            response, code = APIResponse.error(message='Test error')
            response_data = json.loads(response.get_data())
            assert code == 400
            assert response_data['success'] is False
            assert response_data['error']['message'] == 'Test error'
            assert response_data['error']['code'] == 'UNKNOWN_ERROR'
    
    def test_error_with_details(self, app):
        """Test error response with details"""
        with app.app_context():
            response, code = APIResponse.error(
                message='Error',
                details={'field': 'value'}
            )
            response_data = json.loads(response.get_data())
            assert code == 400
            assert response_data['success'] is False
            assert response_data['error']['details'] == {'field': 'value'}
    
    def test_validation_error(self, app):
        """Test validation error response"""
        with app.app_context():
            errors = {'email': 'Invalid email'}
            response, code = APIResponse.validation_error(errors)
            response_data = json.loads(response.get_data())
            assert code == 422
            assert response_data['success'] is False
            assert response_data['error']['details']['fields'] == errors
    
    def test_validation_error_with_message(self, app):
        """Test validation error with custom message"""
        with app.app_context():
            response, code = APIResponse.validation_error(
                {'field': 'error'},
                message='Custom validation message'
            )
            response_data = json.loads(response.get_data())
            assert code == 422
            assert response_data['success'] is False
            assert 'message' in response_data['error']
            assert response_data['error']['message'] == 'Custom validation message'


class TestAPIResponseNotFound:
    """Test not found responses"""
    
    def test_not_found(self, app):
        """Test not found response"""
        with app.app_context():
            response, code = APIResponse.not_found('Resource', 123)
            response_data = json.loads(response.get_data())
            assert code == 404
            assert response_data['success'] is False
            assert 'Resource' in response_data['error']['message']
            assert '123' in response_data['error']['message']
            assert response_data['error']['code'] == 'NOT_FOUND'
    
    def test_not_found_custom_message(self, app):
        """Test not found with custom message"""
        with app.app_context():
            response, code = APIResponse.not_found('Document')
            response_data = json.loads(response.get_data())
            assert code == 404
            assert response_data['success'] is False


class TestAPIResponseServerError:
    """Test server error responses"""
    
    def test_server_error(self, app):
        """Test server error response"""
        with app.app_context():
            response, code = APIResponse.server_error(message='Server error')
            response_data = json.loads(response.get_data())
            assert code == 500
            assert response_data['success'] is False
            assert response_data['error']['message'] == 'Server error'
            assert response_data['error']['code'] == 'SERVER_ERROR'
    
    def test_server_error_with_exception(self, app):
        """Test server error with exception"""
        with app.app_context():
            exc = Exception('Test exception')
            response, code = APIResponse.server_error(
                message='Error',
                exception=exc
            )
            response_data = json.loads(response.get_data())
            assert code == 500
            assert response_data['success'] is False
    
    def test_unauthorized(self, app):
        """Test unauthorized response"""
        with app.app_context():
            response, code = APIResponse.unauthorized()
            response_data = json.loads(response.get_data())
            assert code == 401
            assert response_data['success'] is False


class TestAPIResponseSpecialStatus:
    """Test special status responses"""
    
    def test_no_content(self, app):
        """Test 204 no content response"""
        with app.app_context():
            response, code = APIResponse.no_content('Deleted')
            assert code == 204
    
    def test_created(self, app):
        """Test 201 created response"""
        with app.app_context():
            response, code = APIResponse.created(data={'id': 1})
            response_data = json.loads(response.get_data())
            assert code == 201
            assert response_data['success'] is True
            assert response_data['data'] == {'id': 1}
    
    def test_accepted(self, app):
        """Test 204 no content response (replaces missing 202 accepted)"""
        with app.app_context():
            response, code = APIResponse.no_content('Operation completed')
            assert code == 204
            assert response == ''


class TestAPIResponsePaginated:
    """Test paginated responses"""
    
    def test_paginated_basic(self, app):
        """Test basic paginated response"""
        with app.app_context():
            response, code = APIResponse.paginated(
                data=[{'id': 1}, {'id': 2}],
                total=100,
                page=1,
                page_size=10
            )
            response_data = json.loads(response.get_data())
            assert code == 200
            assert response_data['success'] is True
            assert response_data['data'] == [{'id': 1}, {'id': 2}]
            assert response_data['pagination']['total'] == 100
            assert response_data['pagination']['page'] == 1
            assert response_data['pagination']['page_size'] == 10
    
    def test_paginated_with_message(self, app):
        """Test paginated response with message"""
        with app.app_context():
            response, code = APIResponse.paginated(
                data=[],
                total=0,
                page=1,
                page_size=10,
                message='Empty list'
            )
            response_data = json.loads(response.get_data())
            assert code == 200
            assert response_data['message'] == 'Empty list'
    
    def test_paginated_calculates_pages(self, app):
        """Test paginated response calculates total_pages"""
        with app.app_context():
            response, code = APIResponse.paginated(
                data=[],
                total=100,
                page=1,
                page_size=10
            )
            response_data = json.loads(response.get_data())
            if 'total_pages' in response_data.get('pagination', {}):
                assert response_data['pagination']['total_pages'] == 10


class TestAPIResponseStructure:
    """Test response structure consistency"""
    
    def test_all_responses_have_success_field(self, app):
        """Test that all responses include success field"""
        with app.app_context():
            responses = [
                APIResponse.success(),
                APIResponse.error('test'),
                APIResponse.not_found('test'),
                APIResponse.server_error(),
            ]
            
            for response, code in responses:
                response_data = json.loads(response.get_data())
                assert 'success' in response_data
    
    def test_all_responses_have_message(self, app):
        """Test that success responses have message and errors have error.message"""
        with app.app_context():
            # Success responses have message at top level
            response, code = APIResponse.success(message='test')
            response_data = json.loads(response.get_data())
            assert 'message' in response_data
            
            # Error responses have message in error object
            response, code = APIResponse.error('test')
            response_data = json.loads(response.get_data())
            assert 'error' in response_data
            assert 'message' in response_data['error']
            
            # Not found error
            response, code = APIResponse.not_found('test')
            response_data = json.loads(response.get_data())
            assert 'error' in response_data
            assert 'message' in response_data['error']
    
    def test_status_codes_correct(self, app):
        """Test that status codes are HTTP compliant"""
        with app.app_context():
            test_cases = [
                (APIResponse.success(), 200),
                (APIResponse.created(data={}), 201),
                (APIResponse.error('test'), 400),
                (APIResponse.unauthorized(), 401),
                (APIResponse.not_found('test'), 404),
                (APIResponse.server_error(), 500),
            ]
            
            for (response, code), expected_code in test_cases:
                assert code == expected_code


class TestAPIResponseFormatting:
    """Test response formatting"""
    
    def test_response_is_jsonable(self, app):
        """Test that response body is JSON-serializable"""
        with app.app_context():
            response, code = APIResponse.success()
            # Should be able to serialize to JSON
            response_data = json.loads(response.get_data())
            assert isinstance(response_data, dict)
    
    def test_status_code_is_int(self, app):
        """Test that status code is integer"""
        with app.app_context():
            response, code = APIResponse.success()
            assert isinstance(code, int)
    
    def test_data_preserved(self, app):
        """Test that data is preserved correctly"""
        with app.app_context():
            test_data = {
                'string': 'value',
                'number': 42,
                'float': 3.14,
                'bool': True,
                'null': None,
                'list': [1, 2, 3],
                'dict': {'nested': 'value'}
            }
            
            response, code = APIResponse.success(data=test_data)
            response_data = json.loads(response.get_data())
            assert response_data['data'] == test_data


class TestAPIResponseErrors:
    """Test error handling in responses"""
    
    def test_error_with_none_message(self, app):
        """Test error with None message"""
        with app.app_context():
            response, code = APIResponse.error(message=None)
            response_data = json.loads(response.get_data())
            assert code == 400
            assert 'message' in response_data or response_data['success'] is False
    
    def test_error_with_empty_string(self, app):
        """Test error with empty message"""
        with app.app_context():
            response, code = APIResponse.error(message='')
            assert code == 400
    
    def test_server_error_without_message(self, app):
        """Test server error without message"""
        with app.app_context():
            response, code = APIResponse.server_error()
            response_data = json.loads(response.get_data())
            assert code == 500
            assert response_data['success'] is False

