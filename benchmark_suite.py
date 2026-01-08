"""
Performance & Load Testing Suite
Benchmark-Tests für Production-Readiness
"""

import time
import logging
import statistics
from typing import List, Dict, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Performance Metrics
# ============================================================================

@dataclass
class PerfMetrics:
    """Performance-Metriken"""
    
    name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    min_time: float
    max_time: float
    avg_time: float
    median_time: float
    p95_time: float
    p99_time: float
    requests_per_second: float
    
    def to_dict(self) -> Dict:
        """Konvertiert zu Dict"""
        return {
            'name': self.name,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'response_times': {
                'min_ms': round(self.min_time * 1000, 2),
                'max_ms': round(self.max_time * 1000, 2),
                'avg_ms': round(self.avg_time * 1000, 2),
                'median_ms': round(self.median_time * 1000, 2),
                'p95_ms': round(self.p95_time * 1000, 2),
                'p99_ms': round(self.p99_time * 1000, 2),
            },
            'throughput_rps': round(self.requests_per_second, 2),
            'success_rate': f"{(self.successful_requests/self.total_requests)*100:.1f}%",
        }
    
    def __str__(self) -> str:
        """String-Representation"""
        return f"""
╔══════════════════════════════════════════════════════════╗
║ Performance Results: {self.name:<35}║
╠══════════════════════════════════════════════════════════╣
║ Total Requests:      {self.total_requests:<35}║
║ Successful:          {self.successful_requests:<35}║
║ Failed:              {self.failed_requests:<35}║
├──────────────────────────────────────────────────────────┤
║ Response Times (ms):                                     ║
║   Min:   {round(self.min_time*1000, 2):<34}║
║   Max:   {round(self.max_time*1000, 2):<34}║
║   Avg:   {round(self.avg_time*1000, 2):<34}║
║   P95:   {round(self.p95_time*1000, 2):<34}║
║   P99:   {round(self.p99_time*1000, 2):<34}║
├──────────────────────────────────────────────────────────┤
║ Throughput: {self.requests_per_second:<42}req/sec║
║ Success Rate: {(self.successful_requests/self.total_requests)*100:.1f}%{' '*45}║
╚══════════════════════════════════════════════════════════╝
"""


# ============================================================================
# Benchmark Runner
# ============================================================================

class BenchmarkRunner:
    """Führt Benchmarks aus"""
    
    def __init__(self, name: str):
        self.name = name
        self.response_times: List[float] = []
        self.successful = 0
        self.failed = 0
        self.start_time = None
    
    def run(
        self,
        func: Callable,
        iterations: int = 100,
        workers: int = 1,
    ) -> PerfMetrics:
        """
        Führt Benchmark aus
        
        Args:
            func: Callable zu benchmarken
            iterations: Anzahl Iterationen
            workers: Anzahl parallele Worker
        """
        logger.info(f"🏃 Running benchmark: {self.name}")
        logger.info(f"   Iterations: {iterations}, Workers: {workers}")
        
        self.start_time = time.time()
        self.response_times = []
        self.successful = 0
        self.failed = 0
        
        if workers == 1:
            self._run_sequential(func, iterations)
        else:
            self._run_parallel(func, iterations, workers)
        
        total_time = time.time() - self.start_time
        
        # Calculate metrics
        metrics = self._calculate_metrics(total_time)
        
        logger.info(f"✅ Benchmark complete: {self.name}")
        logger.info(f"\n{metrics}")
        
        return metrics
    
    def _run_sequential(self, func: Callable, iterations: int):
        """Sequenzielle Ausführung"""
        for i in range(iterations):
            try:
                start = time.time()
                func()
                duration = time.time() - start
                self.response_times.append(duration)
                self.successful += 1
            except Exception as e:
                logger.error(f"Error in iteration {i}: {e}")
                self.failed += 1
    
    def _run_parallel(self, func: Callable, iterations: int, workers: int):
        """Parallele Ausführung"""
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self._timed_call, func)
                for _ in range(iterations)
            ]
            
            for future in as_completed(futures):
                try:
                    duration = future.result()
                    if duration is not None:
                        self.response_times.append(duration)
                        self.successful += 1
                except Exception as e:
                    logger.error(f"Error in task: {e}")
                    self.failed += 1
    
    def _timed_call(self, func: Callable) -> float:
        """Misst Zeit für Funktionsaufruf"""
        start = time.time()
        func()
        return time.time() - start
    
    def _calculate_metrics(self, total_time: float) -> PerfMetrics:
        """Berechnet Performance-Metriken"""
        total_requests = self.successful + self.failed
        
        if not self.response_times:
            logger.warning("No successful requests")
            return PerfMetrics(
                name=self.name,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=self.failed,
                min_time=0,
                max_time=0,
                avg_time=0,
                median_time=0,
                p95_time=0,
                p99_time=0,
                requests_per_second=0,
            )
        
        sorted_times = sorted(self.response_times)
        
        return PerfMetrics(
            name=self.name,
            total_requests=total_requests,
            successful_requests=self.successful,
            failed_requests=self.failed,
            min_time=min(self.response_times),
            max_time=max(self.response_times),
            avg_time=statistics.mean(self.response_times),
            median_time=statistics.median(self.response_times),
            p95_time=sorted_times[int(len(sorted_times) * 0.95)],
            p99_time=sorted_times[int(len(sorted_times) * 0.99)],
            requests_per_second=self.successful / total_time,
        )


# ============================================================================
# Email Processing Benchmarks
# ============================================================================

class EmailProcessingBenchmark:
    """Email-Processing Benchmarks"""
    
    @staticmethod
    def benchmark_metadata_extraction():
        """Benchmark: Metadata-Extraktion"""
        from app.email_parser import EmailMetadataExtractor
        from unittest.mock import Mock
        
        extractor = EmailMetadataExtractor()
        
        def extract():
            mock_email = Mock()
            mock_email.get.return_value = "test@example.com"
            extractor.extract_metadata(mock_email)
        
        runner = BenchmarkRunner("Email Metadata Extraction")
        return runner.run(extract, iterations=1000, workers=4)
    
    @staticmethod
    def benchmark_email_validation():
        """Benchmark: Email-Validierung"""
        from app.email_parser import EmailValidator
        from unittest.mock import Mock
        
        validator = EmailValidator()
        
        def validate():
            mock_email = Mock()
            mock_email.is_multipart.return_value = True
            validator.validate_email(mock_email)
        
        runner = BenchmarkRunner("Email Validation")
        return runner.run(validate, iterations=1000, workers=4)


# ============================================================================
# Text Processing Benchmarks
# ============================================================================

class TextProcessingBenchmark:
    """Text-Processing Benchmarks"""
    
    @staticmethod
    def benchmark_layout_detection():
        """Benchmark: Layout-Erkennung"""
        from app.advanced_text_processor import LayoutDetector
        
        detector = LayoutDetector()
        sample_text = "Header\n\nParagraph\n\n- List item\n\nFooter"
        
        def detect():
            detector.detect_layout(sample_text)
        
        runner = BenchmarkRunner("Layout Detection")
        return runner.run(detect, iterations=1000, workers=4)
    
    @staticmethod
    def benchmark_quality_analysis():
        """Benchmark: Qualitäts-Analyse"""
        from app.advanced_text_processor import TextQualityAnalyzer
        
        analyzer = TextQualityAnalyzer()
        sample_text = "This is a sample text for quality analysis."
        
        def analyze():
            analyzer.analyze_quality(sample_text, ocr_confidence=0.95)
        
        runner = BenchmarkRunner("Quality Analysis")
        return runner.run(analyze, iterations=1000, workers=4)


# ============================================================================
# File Upload Benchmarks
# ============================================================================

class FileUploadBenchmark:
    """File-Upload Benchmarks"""
    
    @staticmethod
    def benchmark_file_validation():
        """Benchmark: Datei-Validierung"""
        from app.advanced_upload_handler import AdvancedUploadHandler
        
        handler = AdvancedUploadHandler()
        
        def validate():
            handler._validate_extension('test.pdf')
        
        runner = BenchmarkRunner("File Validation")
        return runner.run(validate, iterations=10000, workers=4)
    
    @staticmethod
    def benchmark_hash_calculation():
        """Benchmark: Hash-Berechnung"""
        from app.advanced_upload_handler import AdvancedUploadHandler
        
        handler = AdvancedUploadHandler()
        test_content = b"x" * 1000000  # 1MB
        
        def calculate():
            handler._calculate_file_hash(test_content)
        
        runner = BenchmarkRunner("Hash Calculation (1MB)")
        return runner.run(calculate, iterations=100, workers=2)


# ============================================================================
# Rate Limiter Benchmarks
# ============================================================================

class RateLimiterBenchmark:
    """Rate Limiter Benchmarks"""
    
    @staticmethod
    def benchmark_token_bucket():
        """Benchmark: Token Bucket"""
        from app.rate_limiter import TokenBucket
        
        bucket = TokenBucket(capacity=1000, refill_rate=100)
        
        def consume():
            bucket.consume(1)
        
        runner = BenchmarkRunner("Token Bucket Consumption")
        return runner.run(consume, iterations=10000, workers=8)


# ============================================================================
# Load Testing
# ============================================================================

class LoadTest:
    """Last-Test"""
    
    @staticmethod
    def concurrent_requests(url: str, concurrent: int = 100, duration: int = 60):
        """
        Simuliert gleichzeitige Requests
        
        Args:
            url: Target URL
            concurrent: Anzahl gleichzeitige Requests
            duration: Testdauer in Sekunden
        """
        import requests
        
        logger.info(f"🔥 Load test: {concurrent} concurrent requests to {url}")
        
        response_times = []
        errors = []
        start_time = time.time()
        request_count = 0
        
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = []
            
            while time.time() - start_time < duration:
                future = executor.submit(
                    LoadTest._make_request,
                    url,
                    response_times,
                    errors
                )
                futures.append(future)
                request_count += 1
                
                # Limit submissions per second
                if request_count % 100 == 0:
                    time.sleep(0.1)
            
            # Wait for remaining tasks
            for future in as_completed(futures, timeout=30):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Task error: {e}")
        
        total_time = time.time() - start_time
        
        logger.info(f"📊 Load test results:")
        logger.info(f"   Total requests: {request_count}")
        logger.info(f"   Successful: {request_count - len(errors)}")
        logger.info(f"   Errors: {len(errors)}")
        logger.info(f"   Duration: {total_time:.1f}s")
        logger.info(f"   Throughput: {request_count/total_time:.1f} req/sec")
        
        if response_times:
            logger.info(f"   Avg response: {statistics.mean(response_times)*1000:.1f}ms")
            logger.info(f"   P95 response: {sorted(response_times)[int(len(response_times)*0.95)]*1000:.1f}ms")
    
    @staticmethod
    def _make_request(url: str, response_times: list, errors: list):
        """Macht einzelnen Request"""
        try:
            import requests
            
            start = time.time()
            response = requests.get(url, timeout=10)
            duration = time.time() - start
            
            response_times.append(duration)
            
            if response.status_code != 200:
                errors.append(f"HTTP {response.status_code}")
        
        except Exception as e:
            errors.append(str(e))


# ============================================================================
# Report Generation
# ============================================================================

class BenchmarkReport:
    """Generiert Benchmark-Report"""
    
    def __init__(self):
        self.results: List[PerfMetrics] = []
    
    def add_result(self, metrics: PerfMetrics):
        """Fügt Ergebnis hinzu"""
        self.results.append(metrics)
    
    def save_json(self, filename: str):
        """Speichert als JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': [r.to_dict() for r in self.results],
            'summary': self._generate_summary(),
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report saved: {filename}")
    
    def _generate_summary(self) -> Dict:
        """Generiert Zusammenfassung"""
        if not self.results:
            return {}
        
        return {
            'total_benchmarks': len(self.results),
            'total_requests': sum(r.total_requests for r in self.results),
            'total_successful': sum(r.successful_requests for r in self.results),
            'overall_avg_response_ms': round(
                sum(r.avg_time for r in self.results) / len(self.results) * 1000, 2
            ),
            'total_throughput_rps': round(
                sum(r.requests_per_second for r in self.results), 2
            ),
        }


# ============================================================================
# Main Benchmark Suite
# ============================================================================

def run_full_benchmark_suite():
    """Führt komplette Benchmark-Suite aus"""
    logger.info("🏃 Starting full benchmark suite...")
    
    report = BenchmarkReport()
    
    # Email Processing
    logger.info("\n📧 Email Processing Benchmarks")
    report.add_result(EmailProcessingBenchmark.benchmark_metadata_extraction())
    report.add_result(EmailProcessingBenchmark.benchmark_email_validation())
    
    # Text Processing
    logger.info("\n📝 Text Processing Benchmarks")
    report.add_result(TextProcessingBenchmark.benchmark_layout_detection())
    report.add_result(TextProcessingBenchmark.benchmark_quality_analysis())
    
    # File Upload
    logger.info("\n📤 File Upload Benchmarks")
    report.add_result(FileUploadBenchmark.benchmark_file_validation())
    report.add_result(FileUploadBenchmark.benchmark_hash_calculation())
    
    # Rate Limiting
    logger.info("\n🚦 Rate Limiter Benchmarks")
    report.add_result(RateLimiterBenchmark.benchmark_token_bucket())
    
    # Save report
    report.save_json('benchmark_results.json')
    
    logger.info("✅ Benchmark suite complete!")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_full_benchmark_suite()
