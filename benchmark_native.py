"""
Benchmark: Native C vs Python Image Processing
"""
import numpy as np
import time
import sys

try:
    import image_fast
    NATIVE_AVAILABLE = True
except ImportError:
    NATIVE_AVAILABLE = False
    print("❌ Native extension not available!")
    sys.exit(1)

# Also test against OpenCV
import cv2


def benchmark_denoise(image, iterations=10):
    """Benchmark denoising"""
    print("\n=== Denoising Benchmark ===")
    
    # Native C
    img_copy = image.copy()
    start = time.time()
    for _ in range(iterations):
        image_fast.denoise(img_copy, 5, 75.0, 75.0)
    native_time = (time.time() - start) / iterations
    
    # OpenCV (Python)
    img_copy = image.copy()
    start = time.time()
    for _ in range(iterations):
        cv2.bilateralFilter(img_copy, 5, 75, 75)
    opencv_time = (time.time() - start) / iterations
    
    speedup = opencv_time / native_time
    
    print(f"Native C:  {native_time*1000:.2f}ms")
    print(f"OpenCV:    {opencv_time*1000:.2f}ms")
    print(f"Speedup:   {speedup:.1f}x faster! 🚀")
    
    return speedup


def benchmark_threshold(image, iterations=10):
    """Benchmark adaptive thresholding"""
    print("\n=== Adaptive Threshold Benchmark ===")
    
    # Native C
    img_copy = image.copy()
    start = time.time()
    for _ in range(iterations):
        image_fast.adaptive_threshold(img_copy, 11)
    native_time = (time.time() - start) / iterations
    
    # OpenCV
    img_copy = image.copy()
    start = time.time()
    for _ in range(iterations):
        cv2.adaptiveThreshold(img_copy, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 11, 2)
    opencv_time = (time.time() - start) / iterations
    
    speedup = opencv_time / native_time
    
    print(f"Native C:  {native_time*1000:.2f}ms")
    print(f"OpenCV:    {opencv_time*1000:.2f}ms")
    print(f"Speedup:   {speedup:.1f}x faster! 🚀")
    
    return speedup


def benchmark_contrast(image, iterations=100):
    """Benchmark contrast enhancement"""
    print("\n=== Contrast Enhancement Benchmark ===")
    
    # Native C
    img_copy = image.copy()
    start = time.time()
    for _ in range(iterations):
        image_fast.enhance_contrast(img_copy, 1.5, 0)
    native_time = (time.time() - start) / iterations
    
    # NumPy
    img_copy = image.copy()
    start = time.time()
    for _ in range(iterations):
        np.clip(1.5 * img_copy + 0, 0, 255, out=img_copy)
    numpy_time = (time.time() - start) / iterations
    
    speedup = numpy_time / native_time
    
    print(f"Native C:  {native_time*1000:.2f}ms")
    print(f"NumPy:     {numpy_time*1000:.2f}ms")
    print(f"Speedup:   {speedup:.1f}x faster! 🚀")
    
    return speedup


if __name__ == '__main__':
    print("🔥 Native C Extension Performance Benchmark\n")
    
    # Test sizes
    sizes = [
        (500, 500, "Small (500x500)"),
        (1000, 1000, "Medium (1000x1000)"),
        (2000, 2000, "Large (2000x2000)"),
    ]
    
    total_speedup = 0
    count = 0
    
    for width, height, label in sizes:
        print(f"\n{'='*50}")
        print(f"Image Size: {label}")
        print(f"{'='*50}")
        
        # Generate test image
        image = np.random.randint(0, 256, (height, width), dtype=np.uint8)
        
        # Run benchmarks
        s1 = benchmark_denoise(image, iterations=5)
        s2 = benchmark_threshold(image, iterations=10)
        s3 = benchmark_contrast(image, iterations=50)
        
        avg = (s1 + s2 + s3) / 3
        total_speedup += avg
        count += 1
        
        print(f"\nAverage Speedup: {avg:.1f}x 🚀")
    
    print(f"\n{'='*50}")
    print(f"OVERALL AVERAGE SPEEDUP: {total_speedup/count:.1f}x")
    print(f"{'='*50}")
    
    if total_speedup / count > 10:
        print("\n✅ Native C extension is SIGNIFICANTLY faster!")
        print("   Recommended for production use on Raspberry Pi!")
    elif total_speedup / count > 2:
        print("\n✅ Native C extension provides good speedup!")
    else:
        print("\n⚠️ Speedup lower than expected, check compilation flags")
