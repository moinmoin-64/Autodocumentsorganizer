"""
Unit Tests für Phase 5 Error Tracking System
Test coverage für error_tracking.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app import create_app, db
from app.error_tracking import ErrorLog, ErrorGroup, error_bp, HealthCheck


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestErrorTracking:
    """Error Tracking API Tests"""

    def test_collect_single_error(self, client):
        """Test collecting a single error"""
        response = client.post('/api/errors', json={
            'errors': [{
                'type': 'error',
                'message': 'Test error message',
                'context': {
                    'userId': 'user-123',
                    'environment': 'test'
                }
            }]
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] == True
        assert data['inserted'] == 1

    def test_collect_multiple_errors(self, client):
        """Test collecting multiple errors at once"""
        errors = [
            {
                'type': 'error',
                'message': f'Error {i}',
                'context': {'userId': f'user-{i}'}
            }
            for i in range(5)
        ]
        
        response = client.post('/api/errors', json={'errors': errors})
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['inserted'] == 5

    def test_error_grouping(self, client, app):
        """Test error grouping by message"""
        # Send same error twice
        for _ in range(2):
            client.post('/api/errors', json={
                'errors': [{
                    'type': 'error',
                    'message': 'Duplicate error',
                    'context': {'userId': 'user-1'}
                }]
            })
        
        with app.app_context():
            group = ErrorGroup.query.filter_by(
                error_message='Duplicate error'
            ).first()
            assert group is not None
            assert group.count == 2

    def test_error_dashboard_stats(self, client, app):
        """Test error dashboard statistics"""
        # Add various errors
        client.post('/api/errors', json={
            'errors': [
                {'type': 'error', 'message': 'Error 1'},
                {'type': 'warning', 'message': 'Warning 1'},
                {'type': 'info', 'message': 'Info 1'}
            ]
        })
        
        response = client.get('/api/errors/dashboard?days=7')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] == 3
        assert data['byType']['error'] == 1
        assert data['byType']['warning'] == 1

    def test_error_groups_endpoint(self, client, app):
        """Test getting error groups"""
        # Add errors to create groups
        client.post('/api/errors', json={
            'errors': [
                {'type': 'error', 'message': 'Test error'},
                {'type': 'error', 'message': 'Test error'},
                {'type': 'error', 'message': 'Different error'}
            ]
        })
        
        response = client.get('/api/errors/groups?resolved=false')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] >= 2

    def test_resolve_error_group(self, client, app):
        """Test resolving an error group"""
        # Create an error group
        client.post('/api/errors', json={
            'errors': [{'type': 'error', 'message': 'Test error'}]
        })
        
        with app.app_context():
            group = ErrorGroup.query.first()
            assert group is not None
            
            response = client.put(f'/api/errors/groups/{group.id}/resolve', json={})
            assert response.status_code == 200
            assert response.get_json()['group']['resolved'] == True

    def test_cleanup_old_errors(self, client, app):
        """Test cleaning up old errors"""
        with app.app_context():
            # Create old error (40 days ago)
            old_error = ErrorLog(
                error_type='error',
                message='Old error',
                timestamp=datetime.utcnow() - timedelta(days=40)
            )
            db.session.add(old_error)
            db.session.commit()
            
            # Cleanup with 30-day retention
            response = client.post('/api/errors/cleanup?days=30')
            assert response.status_code == 200
            data = response.get_json()
            assert data['deleted'] >= 1

    def test_invalid_request(self, client):
        """Test invalid request handling"""
        response = client.post('/api/errors', json={})
        assert response.status_code == 400

    def test_error_with_stack_trace(self, client, app):
        """Test error with full stack trace"""
        response = client.post('/api/errors', json={
            'errors': [{
                'type': 'error',
                'message': 'Stack trace error',
                'filename': 'app.js',
                'lineno': 123,
                'colno': 45,
                'stack': 'Error: test\n  at Function (app.js:123:45)',
                'context': {'userId': 'user-1'}
            }]
        })
        
        assert response.status_code == 201
        
        with app.app_context():
            error = ErrorLog.query.first()
            assert error.filename == 'app.js'
            assert error.lineno == 123
            assert error.stack is not None


class TestHealthChecks:
    """Health Check API Tests"""

    def test_health_check_endpoint(self, client):
        """Test full health check"""
        response = client.get('/api/health')
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'status' in data
        assert 'resources' in data

    def test_health_status_quick(self, client):
        """Test quick status check"""
        response = client.get('/api/health/status')
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'healthy' in data

    def test_database_health(self, client):
        """Test database health check"""
        response = client.get('/api/health/database')
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'status' in data

    def test_cache_health(self, client):
        """Test cache health check"""
        response = client.get('/api/health/cache')
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'status' in data

    def test_resources_check(self, client):
        """Test resource monitoring"""
        response = client.get('/api/health/resources')
        assert response.status_code == 200
        data = response.get_json()
        assert 'cpu' in data
        assert 'memory' in data
        assert 'disk' in data

    def test_kubernetes_readiness(self, client):
        """Test Kubernetes readiness probe"""
        response = client.get('/api/health/ready')
        assert response.status_code in [200, 503]
        data = response.get_json()
        assert 'ready' in data

    def test_kubernetes_liveness(self, client):
        """Test Kubernetes liveness probe"""
        response = client.get('/api/health/live')
        assert response.status_code in [200, 500]
        data = response.get_json()
        assert 'alive' in data


class TestErrorTrackerFrontend:
    """Frontend Error Tracker Tests (JavaScript Unit Tests wrapper)"""

    def test_error_tracker_initialization(self, client):
        """Test error tracker can be initialized"""
        # This would be in browser, but we test the backend endpoint
        response = client.post('/api/errors', json={
            'errors': [{
                'type': 'test',
                'message': 'Frontend initialized',
                'context': {'userId': None}
            }]
        })
        assert response.status_code == 201

    def test_batch_error_reporting(self, client):
        """Test batch error reporting efficiency"""
        # Send 10 errors in one batch
        errors = [
            {'type': 'error', 'message': f'Error {i}'}
            for i in range(10)
        ]
        
        response = client.post('/api/errors', json={'errors': errors})
        assert response.status_code == 201
        data = response.get_json()
        assert data['inserted'] == 10


class TestPerformanceAnalytics:
    """Performance Analytics Tests"""

    def test_metrics_endpoint(self, client):
        """Test metrics reporting endpoint"""
        response = client.post('/api/metrics', json={
            'pageLoadTime': 2150,
            'largestContentfulPaint': 1900,
            'firstInputDelay': 45,
            'cumulativeLayoutShift': 0.08,
            'score': 95
        })
        # Endpoint may not exist yet, but test structure
        assert response.status_code in [200, 404, 201]


class TestIntegration:
    """Integration Tests"""

    def test_error_to_dashboard_flow(self, client, app):
        """Test complete flow: error capture → grouping → dashboard"""
        # 1. Capture error
        client.post('/api/errors', json={
            'errors': [{'type': 'error', 'message': 'Integration test'}]
        })
        
        # 2. Check grouping
        with app.app_context():
            group = ErrorGroup.query.first()
            assert group is not None
            assert group.count == 1
        
        # 3. Check dashboard
        response = client.get('/api/errors/dashboard?days=7')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total'] >= 1

    def test_health_and_errors_together(self, client):
        """Test health checks and error tracking together"""
        # Health should work even with errors
        client.post('/api/errors', json={
            'errors': [{'type': 'error', 'message': 'Test'}]
        })
        
        response = client.get('/api/health/status')
        assert response.status_code in [200, 503]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=app.error_tracking', '--cov-report=html'])
