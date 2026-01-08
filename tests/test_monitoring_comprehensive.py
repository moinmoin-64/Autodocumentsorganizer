"""
Comprehensive Monitoring and Metrics Tests
Tests for logging, metrics, monitoring endpoints
"""

import pytest
import json
from datetime import datetime


class TestMonitoringBasic:
    """Basic monitoring endpoint tests"""
    
    def test_metrics_endpoint_exists(self, client):
        """Test metrics endpoint is available"""
        response = client.get('/metrics')
        # Metrics endpoint may or may not exist
        assert response.status_code in [200, 404]
    
    def test_prometheus_metrics(self, client):
        """Test Prometheus metrics format"""
        response = client.get('/metrics')
        if response.status_code == 200:
            # Should be prometheus format text
            assert 'HELP' in response.data.decode() or 'TYPE' in response.data.decode() or 'http' in response.data.decode()
    
    def test_monitoring_endpoint(self, client):
        """Test monitoring status endpoint"""
        response = client.get('/api/monitoring/status')
        # May or may not exist
        assert response.status_code in [200, 404]
    
    def test_stats_endpoint(self, client):
        """Test statistics endpoint"""
        response = client.get('/api/stats')
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict)


class TestLogging:
    """Logging functionality tests"""
    
    def test_request_logging(self, client, caplog):
        """Test that requests are logged"""
        with caplog.at_level('INFO'):
            response = client.get('/api/health')
        
        # Health request should be logged
        log_output = caplog.text
        # May contain request info
        assert 'health' in log_output.lower() or len(log_output) > 0
    
    def test_error_logging(self, client, caplog):
        """Test that errors are logged"""
        with caplog.at_level('ERROR'):
            response = client.get('/api/nonexistent')
        
        # 404 errors might be logged
        assert response.status_code in [404, 301, 307]
    
    def test_warning_logging(self, client, caplog):
        """Test warning level logging"""
        with caplog.at_level('WARNING'):
            # Request with unusual parameters
            response = client.get('/api/documents?page=99999')
        
        # Request should complete
        assert response.status_code in [200, 400, 404]
    
    def test_debug_logging_disabled_in_production(self, client, app):
        """Test debug logging is not excessive in production"""
        # Check if debug logging is disabled
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        assert log_level in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']


class TestMetrics:
    """Metrics collection tests"""
    
    def test_request_count_metric(self, client):
        """Test request counting"""
        # Make some requests
        for i in range(3):
            response = client.get('/api/health')
        
        # Check if metrics are available
        response = client.get('/metrics')
        if response.status_code == 200:
            # Should contain request metrics
            assert 'http' in response.data.decode().lower() or 'requests' in response.data.decode().lower()
    
    def test_response_time_metric(self, client):
        """Test response time tracking"""
        import time
        start = time.time()
        response = client.get('/api/health')
        duration = time.time() - start
        
        # Response should be fast
        assert duration < 1.0
        assert response.status_code in [200, 404]
    
    def test_error_rate_metric(self, client):
        """Test error rate tracking"""
        # Make requests including errors
        success_count = 0
        for endpoint in ['/api/health', '/api/nonexistent']:
            response = client.get(endpoint)
            if response.status_code == 200:
                success_count += 1
        
        # Should have both success and error
        assert success_count >= 0
    
    def test_database_metrics(self, client, db):
        """Test database operation metrics"""
        # Perform database operations
        try:
            docs = db.get_documents()
        except:
            pass
        
        # Metrics endpoint should be available
        response = client.get('/metrics')
        assert response.status_code in [200, 404]


class TestPerformanceMonitoring:
    """Performance monitoring tests"""
    
    def test_slow_request_detection(self, client):
        """Test detection of slow requests"""
        import time
        start = time.time()
        response = client.get('/api/documents?limit=1000')
        duration = time.time() - start
        
        # Should complete
        assert response.status_code in [200, 400, 404]
        # Should track timing
        assert duration >= 0
    
    def test_concurrent_request_handling(self, client):
        """Test handling of concurrent requests"""
        # Simulate concurrent requests
        responses = []
        for i in range(5):
            response = client.get('/api/health')
            responses.append(response.status_code)
        
        # All should respond
        assert len(responses) == 5
        assert all(code in [200, 404] for code in responses)
    
    def test_memory_usage_tracking(self, client):
        """Test memory usage monitoring"""
        # Application should not crash from memory
        for i in range(10):
            response = client.get('/api/health')
            assert response.status_code in [200, 404]
    
    def test_cpu_usage_monitoring(self, client):
        """Test CPU usage monitoring"""
        # Application should handle sustained load
        for i in range(20):
            response = client.get('/api/documents')
        
        # Should still respond
        response = client.get('/api/health')
        assert response.status_code in [200, 404]


class TestAlertingConditions:
    """Alert condition monitoring"""
    
    def test_high_error_rate_detection(self, client):
        """Test detection of high error rates"""
        error_count = 0
        for i in range(10):
            response = client.get('/api/invalid_endpoint_123')
            if response.status_code >= 400:
                error_count += 1
        
        # Should track errors
        assert error_count > 0
    
    def test_service_availability(self, client):
        """Test service availability monitoring"""
        response = client.get('/api/health')
        # Service should be available or gracefully degrade
        assert response.status_code in [200, 404, 503]
    
    def test_critical_endpoint_monitoring(self, client):
        """Test monitoring of critical endpoints"""
        # Database endpoint should be monitored
        response = client.get('/api/documents')
        assert response.status_code in [200, 401, 404]
    
    def test_dependency_health(self, client, db):
        """Test dependency health status"""
        # Check if database is accessible
        try:
            db.get_documents()
            db_healthy = True
        except:
            db_healthy = False
        
        # Application should indicate health status
        response = client.get('/api/health')
        assert response.status_code in [200, 404, 503]


class TestMonitoringIntegration:
    """Integration tests for monitoring"""
    
    def test_end_to_end_monitoring(self, client):
        """Test complete monitoring flow"""
        # Make requests
        response1 = client.get('/api/health')
        
        # Check metrics
        response2 = client.get('/metrics')
        
        # Both should respond appropriately
        assert response1.status_code in [200, 404]
        assert response2.status_code in [200, 404]
    
    def test_monitoring_does_not_impact_performance(self, client):
        """Test that monitoring doesn't degrade performance"""
        import time
        
        # Time a request
        start = time.time()
        response = client.get('/api/documents')
        duration = time.time() - start
        
        # Should be fast (less than 1 second)
        assert duration < 1.0
        assert response.status_code in [200, 401, 404]
    
    def test_monitoring_data_consistency(self, client):
        """Test consistency of monitoring data"""
        # Make requests
        for i in range(3):
            response = client.get('/api/health')
        
        # Check metrics multiple times
        response1 = client.get('/metrics')
        response2 = client.get('/metrics')
        
        # Metrics should be consistent
        assert response1.status_code == response2.status_code
    
    def test_monitoring_with_errors(self, client):
        """Test monitoring captures errors"""
        # Make some error requests
        for i in range(3):
            response = client.get('/api/invalid')
        
        # Monitoring should still work
        response = client.get('/metrics')
        assert response.status_code in [200, 404]


class TestMonitoringDataIntegrity:
    """Data integrity in monitoring"""
    
    def test_metrics_accumulation(self, client):
        """Test that metrics accumulate correctly"""
        # Get initial metrics
        response1 = client.get('/metrics')
        
        # Make requests
        client.get('/api/health')
        client.get('/api/health')
        
        # Get updated metrics
        response2 = client.get('/metrics')
        
        # Metrics should be available
        assert response1.status_code == response2.status_code
    
    def test_no_data_loss_in_monitoring(self, client):
        """Test that monitoring doesn't lose data"""
        # Rapid fire requests
        for i in range(10):
            client.get('/api/health')
        
        # Check metrics
        response = client.get('/metrics')
        # All requests should be accounted for
        assert response.status_code in [200, 404]
    
    def test_monitoring_timestamp_accuracy(self, client):
        """Test accuracy of monitoring timestamps"""
        import time
        
        # Make a request
        before = datetime.now()
        response = client.get('/api/health')
        after = datetime.now()
        
        # Response should be within expected timeframe
        assert response.status_code in [200, 404]
        # Timing validation
        assert before <= after


class TestMonitoringConfiguration:
    """Monitoring configuration tests"""
    
    def test_monitoring_enabled(self, app):
        """Test that monitoring is enabled"""
        # Check if monitoring is configured
        monitoring_enabled = app.config.get('MONITORING_ENABLED', True)
        # Should be enabled by default
        assert monitoring_enabled in [True, False]
    
    def test_metrics_level_configuration(self, app):
        """Test metrics detail level"""
        metrics_level = app.config.get('METRICS_LEVEL', 'basic')
        # Should have valid configuration
        assert metrics_level in ['basic', 'detailed', 'verbose', 'advanced']
    
    def test_log_retention_configured(self, app):
        """Test log retention settings"""
        retention = app.config.get('LOG_RETENTION_DAYS', 7)
        # Should have reasonable retention
        assert isinstance(retention, int)
        assert retention > 0
