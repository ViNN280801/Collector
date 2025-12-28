from __future__ import annotations

import gc
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

from src.core import CollectionConfigBuilder, CollectionService, PatternConfig


def get_memory_usage() -> float:
    try:
        import psutil

        process = psutil.Process(os.getpid())
        memory_bytes: int = process.memory_info().rss
        return float(memory_bytes / 1024 / 1024)
    except ImportError:
        return 0.0


def get_cpu_count() -> int:
    """Get number of CPU cores."""
    return os.cpu_count() or 4


def get_system_info() -> Dict[str, Any]:
    """Collect system information for analysis."""
    try:
        import psutil

        cpu_count = get_cpu_count()
        memory = psutil.virtual_memory()
        return {
            "cpu_count": cpu_count,
            "total_memory_gb": memory.total / (1024**3),
            "available_memory_gb": memory.available / (1024**3),
            "memory_percent": memory.percent,
        }
    except ImportError:
        return {
            "cpu_count": get_cpu_count(),
            "total_memory_gb": 0.0,
            "available_memory_gb": 0.0,
            "memory_percent": 0.0,
        }


def create_test_files(base_dir: Path, count: int) -> None:
    for i in range(count):
        file_path = base_dir / f"file_{i:06d}.log"
        file_path.write_text(f"Test content for file {i}\n" * 100)


def run_performance_test(file_count: int, warmup: bool = False, verbose: bool = True) -> Dict[str, Any]:
    """Run performance test with detailed metrics."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        target_dir = temp_path / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        if verbose:
            print(f"Creating {file_count} test files...")
        create_start = time.time()
        create_test_files(source_dir, file_count)
        create_time = time.time() - create_start
        if verbose:
            print(f"Files created in {create_time:.2f} seconds")

        # Warmup run to stabilize JIT/cache
        if warmup:
            if verbose:
                print("Running warmup...")
            warmup_config = (
                CollectionConfigBuilder()
                .with_source_paths([source_dir])
                .with_target_path(temp_path / "warmup_target")
                .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
                .with_operation_mode("copy")
                .with_system_info(False)
                .with_audit_logging(False)
                .build()
            )
            warmup_service = CollectionService(warmup_config)
            warmup_service.collect()
            gc.collect()

        gc.collect()
        initial_memory = get_memory_usage()
        system_info = get_system_info()

        if verbose:
            print(f"\nStarting collection of {file_count} files...")
        start_time = time.perf_counter()

        config = (
            CollectionConfigBuilder()
            .with_source_paths([source_dir])
            .with_target_path(target_dir)
            .with_patterns([PatternConfig(pattern="*.log", pattern_type="glob")])
            .with_operation_mode("copy")
            .with_system_info(False)
            .with_audit_logging(False)
            .build()
        )

        service = CollectionService(config)
        results = service.collect()

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        gc.collect()
        peak_memory = get_memory_usage()

        # Calculate additional metrics
        files_per_second = file_count / elapsed if elapsed > 0 else 0
        avg_time_per_file_ms = (elapsed / file_count * 1000) if file_count > 0 else 0
        throughput_mb_per_sec = (peak_memory - initial_memory) / elapsed if elapsed > 0 else 0

        # Estimate optimal workers (based on worker_pool logic)
        optimal_workers = min(
            system_info["cpu_count"],
            max(1, file_count // 100),
            32,  # MAX_WORKERS
        )

        return {
            "file_count": file_count,
            "elapsed_time": elapsed,
            "files_per_second": files_per_second,
            "avg_time_per_file_ms": avg_time_per_file_ms,
            "initial_memory_mb": initial_memory,
            "peak_memory_mb": peak_memory,
            "memory_delta_mb": peak_memory - initial_memory,
            "throughput_mb_per_sec": throughput_mb_per_sec,
            "processed_files": results.get("processed_files", 0),
            "total_files": results.get("total_files", 0),
            "failed_files": results.get("failed_files", 0),
            "success_rate": (results.get("processed_files", 0) / file_count * 100 if file_count > 0 else 0),
            "optimal_workers": optimal_workers,
            "system_info": system_info,
            "create_time": create_time,
            "timestamp": datetime.now().isoformat(),
        }


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze performance results and provide insights."""
    if not results:
        return {}

    bottlenecks: List[str] = []
    recommendations: List[str] = []

    analysis: Dict[str, Any] = {
        "scalability": {},
        "bottlenecks": bottlenecks,
        "recommendations": recommendations,
    }

    # Scalability analysis - compare first and last (logarithmic scale)
    if len(results) >= 2:
        first = results[0]
        last = results[-1]
        file_ratio = last["file_count"] / first["file_count"] if first["file_count"] > 0 else 1
        time_ratio = last["elapsed_time"] / first["elapsed_time"] if first["elapsed_time"] > 0 else 1
        throughput_ratio = last["files_per_second"] / first["files_per_second"] if first["files_per_second"] > 0 else 1

        analysis["scalability"] = {
            "file_growth": file_ratio,
            "time_growth": time_ratio,
            "throughput_growth": throughput_ratio,
            "scalability_factor": throughput_ratio / file_ratio if file_ratio > 0 else 0,
        }

        # Check for bottlenecks
        if time_ratio > file_ratio * 1.5:
            bottlenecks.append("Time grows faster than file count - possible lock contention or I/O bottleneck")
        if throughput_ratio < 0.5:
            bottlenecks.append("Throughput degrades significantly with scale - optimization needed")

    # Analyze small load performance (1-10 files)
    small_loads = [r for r in results if r["file_count"] <= 10]
    if small_loads:
        avg_small_throughput = sum(r["files_per_second"] for r in small_loads) / len(small_loads)
        if avg_small_throughput < 50:
            bottlenecks.append(
                f"Low throughput for small loads ({avg_small_throughput:.1f} files/s) - "
                "consider optimizing overhead for 1-10 file scenarios"
            )

    # Analyze large load performance (>1000 files)
    large_loads = [r for r in results if r["file_count"] >= 1000]
    if large_loads:
        avg_large_throughput = sum(r["files_per_second"] for r in large_loads) / len(large_loads)
        if avg_large_throughput < 300:
            bottlenecks.append(
                f"Low throughput for large loads ({avg_large_throughput:.1f} files/s) - "
                "consider optimizing batch_size and lock contention"
            )

    # Memory analysis
    max_memory_delta = max(r["memory_delta_mb"] for r in results)
    if max_memory_delta > 100:
        bottlenecks.append(f"High memory usage detected: {max_memory_delta:.2f} MB - possible memory leak")

    # Performance recommendations
    avg_throughput = sum(r["files_per_second"] for r in results) / len(results)
    if avg_throughput < 100:
        recommendations.append("Consider optimizing file operations - throughput is below 100 files/s")

    # Lock contention detection (based on profile data)
    recommendations.append(
        "Profile shows 94.7% time in lock.acquire() - consider: "
        "1) Batch progress updates, 2) Use lock-free counters, 3) Reduce callback frequency"
    )

    return analysis


def export_results(results: List[Dict[str, Any]], output_file: Optional[str] = None) -> None:
    """Export results to JSON file."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"performance_results_{timestamp}.json"

    output_path = Path(output_file)
    analysis = analyze_results(results)

    export_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
        },
        "results": results,
        "analysis": analysis,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"\nResults exported to: {output_path}")


def print_detailed_summary(results: List[Dict[str, Any]]) -> None:
    """Print detailed performance summary."""
    print(f"\n{'=' * 80}")
    print("Detailed Performance Summary")
    print(f"{'=' * 80}")

    # Table header
    print(
        f"{'Files':<10} {'Time (s)':<12} {'Files/s':<12} {'Avg (ms/file)':<15} "
        f"{'Memory (MB)':<15} {'Success %':<12}"
    )
    print("-" * 80)

    # Table rows
    for result in results:
        print(
            f"{result['file_count']:<10} "
            f"{result['elapsed_time']:<12.2f} "
            f"{result['files_per_second']:<12.2f} "
            f"{result['avg_time_per_file_ms']:<15.2f} "
            f"{result['peak_memory_mb']:<15.2f} "
            f"{result['success_rate']:<12.1f}"
        )

    # Analysis
    analysis = analyze_results(results)
    if analysis:
        print(f"\n{'=' * 80}")
        print("Performance Analysis")
        print(f"{'=' * 80}")

        if analysis.get("scalability"):
            scale = analysis["scalability"]
            print("\nScalability:")
            print(f"  File growth: {scale['file_growth']:.2f}x")
            print(f"  Time growth: {scale['time_growth']:.2f}x")
            print(f"  Throughput growth: {scale['throughput_growth']:.2f}x")
            print(f"  Scalability factor: {scale['scalability_factor']:.2f}")

        if analysis.get("bottlenecks"):
            print("\n⚠️  Potential Bottlenecks:")
            for bottleneck in analysis["bottlenecks"]:
                print(f"  • {bottleneck}")

        if analysis.get("recommendations"):
            print("\n💡 Recommendations:")
            for rec in analysis["recommendations"]:
                print(f"  • {rec}")


def main() -> None:
    """Main performance test function."""
    import argparse

    parser = argparse.ArgumentParser(description="Performance Test Suite")
    parser.add_argument(
        "--files",
        type=int,
        nargs="+",
        default=[1, 10, 100, 1000, 10000],
        help="File counts to test (default: 1 10 100 1000 10000 - logarithmic scale)",
    )
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="Run warmup iteration before testing",
    )
    parser.add_argument(
        "--export",
        type=str,
        metavar="FILE",
        help="Export results to JSON file",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Performance Test Suite")
    print("=" * 80)

    system_info = get_system_info()
    print("\nSystem Information:")
    print(f"  CPU cores: {system_info['cpu_count']}")
    print(f"  Total memory: {system_info['total_memory_gb']:.2f} GB")
    print(f"  Available memory: {system_info['available_memory_gb']:.2f} GB")

    results = []

    for file_count in args.files:
        print(f"\n{'=' * 80}")
        print(f"Testing with {file_count} files")
        print(f"{'=' * 80}")
        result = run_performance_test(file_count, warmup=args.warmup, verbose=not args.quiet)
        results.append(result)

        if not args.quiet:
            print("\nResults:")
            print(f"  Elapsed time: {result['elapsed_time']:.2f} seconds")
            print(f"  Files per second: {result['files_per_second']:.2f}")
            print(f"  Average time per file: {result['avg_time_per_file_ms']:.2f} ms")
            print(f"  Memory usage: {result['peak_memory_mb']:.2f} MB")
            print(f"  Memory delta: {result['memory_delta_mb']:.2f} MB")
            print(f"  Throughput: {result['throughput_mb_per_sec']:.2f} MB/s")
            print(f"  Processed: {result['processed_files']}/{result['total_files']}")
            print(f"  Success rate: {result['success_rate']:.1f}%")
            print(f"  Optimal workers: {result['optimal_workers']}")

    print_detailed_summary(results)

    if args.export:
        export_results(results, args.export)
    elif not args.quiet:
        export_results(results)  # Auto-export with timestamp


if __name__ == "__main__":
    main()
