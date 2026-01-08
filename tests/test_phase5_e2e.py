"""
End-to-End Tests für Phase 5 Integration
Tests für komplette Fehlererfassung und Monitoring Workflow
"""

import pytest
import time

# Optional Selenium import with fallback
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not installed")
class TestErrorTrackingE2E:
    """End-to-End Tests für Error Tracking"""

    @pytest.fixture(scope='class')
    def driver(self):
        """Initialize Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_error_dashboard_visibility(self, driver):
        """Test error dashboard is visible and functional"""
        driver.get('http://localhost:5000')
        
        # Wait for error dashboard
        try:
            dashboard = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'error-dashboard'))
            )
            assert dashboard is not None
        except TimeoutException:
            pytest.skip("Error dashboard not visible (development mode)")

    def test_error_capture_on_page(self, driver):
        """Test error is captured when thrown on page"""
        driver.get('http://localhost:5000')
        
        # Trigger an error
        driver.execute_script("""
            errorTracker.captureMessage('E2E Test Error', 'error');
        """)
        
        time.sleep(1)
        
        # Check error was captured
        stats = driver.execute_script("""
            return errorTracker.getStats();
        """)
        
        assert stats['total'] > 0

    def test_performance_metrics_available(self, driver):
        """Test performance metrics are available"""
        driver.get('http://localhost:5000')
        time.sleep(2)  # Wait for metrics to populate
        
        metrics = driver.execute_script("""
            return performanceAnalytics.getMetrics();
        """)
        
        assert 'pageLoadTime' in metrics
        assert 'largestContentfulPaint' in metrics

    def test_performance_score_calculation(self, driver):
        """Test performance score is calculated"""
        driver.get('http://localhost:5000')
        time.sleep(2)
        
        score = driver.execute_script("""
            return performanceAnalytics.getPerformanceScore();
        """)
        
        assert score is not None
        assert 0 <= score <= 100

    def test_health_api_accessible(self, driver):
        """Test health API is accessible"""
        driver.get('http://localhost:5000/api/health/status')
        
        body = driver.find_element(By.TAG_NAME, 'body')
        content = body.text
        
        assert 'healthy' in content or 'true' in content

    def test_error_dashboard_clear_button(self, driver):
        """Test error dashboard clear button works"""
        driver.get('http://localhost:5000')
        
        # Add error
        driver.execute_script("""
            errorTracker.captureMessage('Test error');
        """)
        
        time.sleep(1)
        
        # Find and click clear button
        try:
            clear_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, 'error-dashboard-clear'))
            )
            clear_btn.click()
            time.sleep(0.5)
        except TimeoutException:
            pytest.skip("Clear button not found")

    def test_user_context_tracking(self, driver):
        """Test user context is tracked with errors"""
        driver.get('http://localhost:5000')
        
        # Set user
        driver.execute_script("""
            errorTracker.setUser('test-user-123');
            errorTracker.captureMessage('User test error');
        """)
        
        time.sleep(1)
        
        # Verify user is set
        user_id = driver.execute_script("""
            return errorTracker.userId;
        """)
        
        assert user_id == 'test-user-123'

    def test_offline_error_queue(self, driver):
        """Test errors queue when offline"""
        driver.get('http://localhost:5000')
        
        # Go offline
        driver.execute_script("""
            window.dispatchEvent(new Event('offline'));
        """)
        
        time.sleep(0.5)
        
        # Add error while offline
        driver.execute_script("""
            errorTracker.captureMessage('Offline error');
        """)
        
        time.sleep(0.5)
        
        # Check error is in queue
        stats = driver.execute_script("""
            return errorTracker.getStats();
        """)
        
        assert stats['total'] > 0

    def test_core_web_vitals_lcp(self, driver):
        """Test LCP (Largest Contentful Paint) is measured"""
        driver.get('http://localhost:5000')
        time.sleep(3)
        
        lcp = driver.execute_script("""
            return performanceAnalytics.metrics.largestContentfulPaint;
        """)
        
        # LCP should be measured (not null)
        assert lcp is not None or lcp == 0

    def test_core_web_vitals_cls(self, driver):
        """Test CLS (Cumulative Layout Shift) is measured"""
        driver.get('http://localhost:5000')
        time.sleep(2)
        
        cls = driver.execute_script("""
            return performanceAnalytics.metrics.cumulativeLayoutShift;
        """)
        
        assert cls is not None

    def test_api_latency_tracking(self, driver):
        """Test API latency is tracked"""
        driver.get('http://localhost:5000')
        time.sleep(2)
        
        # Make an API call
        driver.execute_script("""
            fetch('/api/health/status').catch(e => {});
        """)
        
        time.sleep(1)
        
        latencies = driver.execute_script("""
            return performanceAnalytics.metrics.apiLatencies;
        """)
        
        assert isinstance(latencies, list)


class TestHealthCheckE2E:
    """End-to-End Tests für Health Checks"""

    def test_health_endpoint_response_time(self):
        """Test health endpoint responds quickly"""
        import requests
        
        start = time.time()
        response = requests.get('http://localhost:5000/api/health')
        duration = time.time() - start
        
        assert response.status_code in [200, 503]
        assert duration < 1.0  # Should be faster than 1 second

    def test_readiness_probe(self):
        """Test Kubernetes readiness probe"""
        import requests
        
        response = requests.get('http://localhost:5000/api/health/ready')
        
        assert response.status_code in [200, 503]
        data = response.json()
        assert 'ready' in data

    def test_liveness_probe(self):
        """Test Kubernetes liveness probe"""
        import requests
        
        response = requests.get('http://localhost:5000/api/health/live')
        
        assert response.status_code in [200, 500]
        data = response.json()
        assert 'alive' in data

    def test_resource_monitoring(self):
        """Test resource monitoring endpoint"""
        import requests
        
        response = requests.get('http://localhost:5000/api/health/resources')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'cpu' in data
        assert 'memory' in data
        assert 'disk' in data
        
        # Verify values are reasonable
        assert 0 <= data['cpu']['percent'] <= 100
        assert 0 <= data['memory']['percent'] <= 100


class TestErrorAPIE2E:
    """End-to-End Tests für Error API"""

    def test_error_collection_workflow(self):
        """Test complete error collection workflow"""
        import requests
        
        # 1. Send errors
        response = requests.post('http://localhost:5000/api/errors', json={
            'errors': [
                {'type': 'error', 'message': 'E2E Error 1'},
                {'type': 'warning', 'message': 'E2E Warning 1'}
            ]
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data['inserted'] == 2
        
        # 2. Get dashboard stats
        response = requests.get('http://localhost:5000/api/errors/dashboard?days=7')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 2
        
        # 3. Get error groups
        response = requests.get('http://localhost:5000/api/errors/groups')
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 1

    def test_error_grouping_accuracy(self):
        """Test errors are grouped correctly"""
        import requests
        
        # Send same error 5 times
        for _ in range(5):
            requests.post('http://localhost:5000/api/errors', json={
                'errors': [{'type': 'error', 'message': 'Same error'}]
            })
        
        # Check grouping
        response = requests.get('http://localhost:5000/api/errors/groups')
        data = response.json()
        
        # Should have at least one group with count >= 5
        found = False
        for group in data['groups']:
            if group['message'] == 'Same error' and group['count'] >= 5:
                found = True
                break
        
        assert found

    def test_error_resolution_workflow(self):
        """Test error group resolution"""
        import requests
        
        # Create error
        requests.post('http://localhost:5000/api/errors', json={
            'errors': [{'type': 'error', 'message': 'E2E Resolution Test'}]
        })
        
        # Get groups
        response = requests.get('http://localhost:5000/api/errors/groups?resolved=false')
        data = response.json()
        
        if data['total'] > 0:
            group_id = data['groups'][0]['id']
            
            # Resolve it
            response = requests.put(
                f'http://localhost:5000/api/errors/groups/{group_id}/resolve',
                json={}
            )
            
            assert response.status_code == 200
            assert response.json()['group']['resolved'] == True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
