#!/usr/bin/env python3
"""
Load Testing für Phase 5 Error Tracking & Health Monitoring
Tests system performance unter Last
"""

import asyncio
import time
import statistics
import json
from concurrent.futures import ThreadPoolExecutor
import requests
from datetime import datetime


class LoadTester:
    """Load testing tool für OrganisationsAI"""

    def __init__(self, base_url='http://localhost:5000', workers=10):
        self.base_url = base_url
        self.workers = workers
        self.results = {
            'error_collection': [],
            'error_dashboard': [],
            'health_checks': [],
            'api_latency': []
        }

    def test_error_collection_load(self, num_requests=100, errors_per_request=10):
        """Test error collection under load"""
        print(f"\n🔴 Testing Error Collection (Load)")
        print(f"   Requests: {num_requests}, Errors/Request: {errors_per_request}")

        def send_errors():
            errors = [
                {'type': 'error', 'message': f'Load test error {i}'}
                for i in range(errors_per_request)
            ]
            
            start = time.time()
            try:
                response = requests.post(
                    f'{self.base_url}/api/errors',
                    json={'errors': errors},
                    timeout=10
                )
                duration = time.time() - start
                
                if response.status_code == 201:
                    return {
                        'success': True,
                        'duration': duration,
                        'errors_sent': errors_per_request
                    }
                else:
                    return {'success': False, 'duration': duration}
            except Exception as e:
                return {'success': False, 'error': str(e)}

        # Execute requests in parallel
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(executor.map(lambda _: send_errors(), range(num_requests)))

        # Analyze results
        successful = [r for r in results if r.get('success')]
        durations = [r['duration'] for r in successful]

        print(f"   Success Rate: {len(successful)}/{num_requests} ({100*len(successful)/num_requests:.1f}%)")
        print(f"   Avg Response: {statistics.mean(durations)*1000:.1f}ms")
        print(f"   Min Response: {min(durations)*1000:.1f}ms")
        print(f"   Max Response: {max(durations)*1000:.1f}ms")
        print(f"   Std Dev: {statistics.stdev(durations)*1000:.1f}ms" if len(durations) > 1 else "")
        print(f"   Total Errors Sent: {len(successful) * errors_per_request}")

        self.results['error_collection'] = {
            'total': num_requests,
            'successful': len(successful),
            'success_rate': 100*len(successful)/num_requests,
            'avg_response_ms': statistics.mean(durations)*1000,
            'min_response_ms': min(durations)*1000,
            'max_response_ms': max(durations)*1000,
            'total_errors_sent': len(successful) * errors_per_request
        }

    def test_dashboard_load(self, num_requests=50):
        """Test dashboard endpoint under load"""
        print(f"\n📊 Testing Error Dashboard (Load)")
        print(f"   Requests: {num_requests}")

        def get_dashboard():
            start = time.time()
            try:
                response = requests.get(
                    f'{self.base_url}/api/errors/dashboard?days=7',
                    timeout=10
                )
                duration = time.time() - start
                return {
                    'success': response.status_code == 200,
                    'duration': duration
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            results = list(executor.map(lambda _: get_dashboard(), range(num_requests)))

        successful = [r for r in results if r.get('success')]
        durations = [r['duration'] for r in successful]

        print(f"   Success Rate: {len(successful)}/{num_requests} ({100*len(successful)/num_requests:.1f}%)")
        print(f"   Avg Response: {statistics.mean(durations)*1000:.1f}ms")
        print(f"   P95 Response: {sorted(durations)[int(len(durations)*0.95)]*1000:.1f}ms")
        print(f"   P99 Response: {sorted(durations)[int(len(durations)*0.99)]*1000:.1f}ms")

        self.results['error_dashboard'] = {
            'total': num_requests,
            'successful': len(successful),
            'avg_response_ms': statistics.mean(durations)*1000,
            'p95_response_ms': sorted(durations)[int(len(durations)*0.95)]*1000 if durations else 0,
            'p99_response_ms': sorted(durations)[int(len(durations)*0.99)]*1000 if durations else 0
        }

    def test_health_checks_load(self, num_requests=100):
        """Test health check endpoints under load"""
        print(f"\n💚 Testing Health Checks (Load)")
        print(f"   Requests: {num_requests}")

        endpoints = [
            '/api/health',
            '/api/health/status',
            '/api/health/ready',
            '/api/health/live',
            '/api/health/resources'
        ]

        def check_health(endpoint):
            start = time.time()
            try:
                response = requests.get(
                    f'{self.base_url}{endpoint}',
                    timeout=5
                )
                duration = time.time() - start
                return {
                    'endpoint': endpoint,
                    'success': response.status_code in [200, 503],
                    'duration': duration
                }
            except Exception as e:
                return {'endpoint': endpoint, 'success': False, 'error': str(e)}

        # Test each endpoint
        all_results = {}
        for endpoint in endpoints:
            print(f"\n   Testing {endpoint}")
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                results = list(executor.map(
                    lambda _: check_health(endpoint),
                    range(num_requests // len(endpoints))
                ))

            successful = [r for r in results if r.get('success')]
            durations = [r['duration'] for r in successful]

            avg_ms = statistics.mean(durations)*1000 if durations else 0
            print(f"      Avg Response: {avg_ms:.1f}ms")
            print(f"      Success Rate: {len(successful)}/{num_requests//len(endpoints)}")

            all_results[endpoint] = {
                'avg_response_ms': avg_ms,
                'success_rate': 100*len(successful)/(num_requests//len(endpoints))
            }

        self.results['health_checks'] = all_results

    def test_sustained_load(self, duration_seconds=60, requests_per_second=10):
        """Test sustained load over time"""
        print(f"\n🔥 Testing Sustained Load")
        print(f"   Duration: {duration_seconds}s, Rate: {requests_per_second} req/s")

        start_time = time.time()
        request_count = 0
        successful_count = 0
        durations = []

        while time.time() - start_time < duration_seconds:
            # Send batch of requests
            def send_error():
                try:
                    start = time.time()
                    response = requests.post(
                        f'{self.base_url}/api/errors',
                        json={'errors': [{'type': 'error', 'message': 'Sustained load test'}]},
                        timeout=5
                    )
                    duration = time.time() - start
                    if response.status_code == 201:
                        return {'success': True, 'duration': duration}
                except:
                    pass
                return {'success': False}

            with ThreadPoolExecutor(max_workers=requests_per_second) as executor:
                results = list(executor.map(lambda _: send_error(), range(requests_per_second)))

            for result in results:
                request_count += 1
                if result.get('success'):
                    successful_count += 1
                    durations.append(result.get('duration', 0))

            # Regulate rate
            time.sleep(1.0 / requests_per_second)

        elapsed = time.time() - start_time
        print(f"\n   Total Requests: {request_count}")
        print(f"   Successful: {successful_count}")
        print(f"   Success Rate: {100*successful_count/request_count:.1f}%")
        print(f"   Avg Latency: {statistics.mean(durations)*1000:.1f}ms" if durations else "   No successful requests")
        print(f"   Actual RPS: {request_count/elapsed:.1f}")

        self.results['sustained_load'] = {
            'total_requests': request_count,
            'successful': successful_count,
            'duration_seconds': elapsed,
            'avg_latency_ms': statistics.mean(durations)*1000 if durations else 0,
            'actual_rps': request_count/elapsed
        }

    def test_concurrent_users(self, num_users=50, duration_seconds=30):
        """Simulate concurrent users"""
        print(f"\n👥 Testing Concurrent Users")
        print(f"   Users: {num_users}, Duration: {duration_seconds}s")

        def user_session():
            session_start = time.time()
            actions_count = 0
            success_count = 0

            while time.time() - session_start < duration_seconds:
                try:
                    # Simulate user actions
                    response = requests.post(
                        f'{self.base_url}/api/errors',
                        json={'errors': [{'type': 'error', 'message': 'Concurrent user test'}]},
                        timeout=5
                    )
                    actions_count += 1
                    if response.status_code == 201:
                        success_count += 1

                    # Random think time
                    time.sleep(0.1)
                except:
                    actions_count += 1

            return {'actions': actions_count, 'success': success_count}

        with ThreadPoolExecutor(max_workers=num_users) as executor:
            results = list(executor.map(lambda _: user_session(), range(num_users)))

        total_actions = sum(r['actions'] for r in results)
        total_success = sum(r['success'] for r in results)

        print(f"   Total Actions: {total_actions}")
        print(f"   Total Successful: {total_success}")
        print(f"   Success Rate: {100*total_success/total_actions:.1f}%")
        print(f"   Actions/User: {total_actions/num_users:.1f}")

        self.results['concurrent_users'] = {
            'num_users': num_users,
            'total_actions': total_actions,
            'successful_actions': total_success,
            'success_rate': 100*total_success/total_actions if total_actions > 0 else 0
        }

    def generate_report(self):
        """Generate and save load test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': self.results
        }

        filename = f'load_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Report saved to {filename}")

        # Print summary
        print("\n" + "="*50)
        print("LOAD TEST SUMMARY")
        print("="*50)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Base URL: {report['base_url']}")
        
        if self.results['error_collection']:
            print("\nError Collection:")
            print(f"  Success Rate: {self.results['error_collection']['success_rate']:.1f}%")
            print(f"  Avg Response: {self.results['error_collection']['avg_response_ms']:.1f}ms")
        
        if self.results['error_dashboard']:
            print("\nError Dashboard:")
            print(f"  Avg Response: {self.results['error_dashboard']['avg_response_ms']:.1f}ms")
            print(f"  P95: {self.results['error_dashboard']['p95_response_ms']:.1f}ms")


def main():
    """Run load tests"""
    print("="*60)
    print("LOAD TESTING - Phase 5 Error Tracking & Monitoring")
    print("="*60)

    tester = LoadTester(workers=10)

    try:
        # Test error collection
        tester.test_error_collection_load(num_requests=100, errors_per_request=10)

        # Test dashboard
        tester.test_dashboard_load(num_requests=50)

        # Test health checks
        tester.test_health_checks_load(num_requests=100)

        # Test sustained load (shorter for demo)
        tester.test_sustained_load(duration_seconds=30, requests_per_second=10)

        # Test concurrent users
        tester.test_concurrent_users(num_users=20, duration_seconds=20)

    except Exception as e:
        print(f"\n❌ Error during load testing: {e}")
    finally:
        tester.generate_report()


if __name__ == '__main__':
    main()
