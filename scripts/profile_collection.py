from __future__ import annotations

import cProfile
import json
import pstats
import sys
import time
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional

from src.core import CollectionConfigBuilder, CollectionService, PatternConfig


def create_test_files(base_dir: Path, count: int) -> None:
    for i in range(count):
        file_path = base_dir / f"file_{i:06d}.log"
        file_path.write_text(f"Test content for file {i}\n" * 100)


def analyze_profile_stats(stats: pstats.Stats) -> Dict[str, Any]:
    """Analyze profile statistics and identify bottlenecks."""
    analysis: Dict[str, Any] = {
        "bottlenecks": [],
        "lock_contention": {},
        "io_operations": {},
        "recommendations": [],
    }

    # Extract function statistics from Stats internal structure
    func_stats: List[Dict[str, Any]] = []

    # Access internal stats dictionary (it's a dict attribute)
    try:
        # pstats.Stats has a 'stats' attribute that contains the statistics
        # This is the internal structure: {(filename, line, func): (cc, nc, tt, ct, callers), ...}
        # Note: This is an internal attribute, but it's the standard way to access detailed stats
        stats_dict = stats.stats  # type: ignore[attr-defined]

        for func_name, stat_tuple in stats_dict.items():
            cc, nc, tt, ct, callers = stat_tuple
            filename, line_num, func = func_name
            func_stats.append(
                {
                    "filename": filename,
                    "line": line_num,
                    "function": func,
                    "total_time": tt,
                    "cumulative_time": ct,
                    "call_count": nc,
                    "primitive_calls": cc,
                }
            )
    except (AttributeError, TypeError, ValueError) as e:
        # If we can't access stats directly, return basic analysis
        analysis["bottlenecks"].append(f"Could not access detailed stats: {e}. Using summary analysis.")
        return analysis

    # Sort by total time to find bottlenecks
    func_stats.sort(key=lambda x: x["total_time"], reverse=True)

    total_time = sum(f["total_time"] for f in func_stats) if func_stats else 1.0

    # Analyze top functions
    top_functions = func_stats[:10]
    for func in top_functions:
        time_percent = (func["total_time"] / total_time) * 100

        # Detect lock contention
        if "lock" in func["function"].lower() or "acquire" in func["function"].lower():
            analysis["lock_contention"][func["function"]] = {
                "time": func["total_time"],
                "percent": time_percent,
                "calls": func["call_count"],
            }
            if time_percent > 50:
                analysis["bottlenecks"].append(
                    f"Severe lock contention: {func['function']} takes {time_percent:.1f}% of total time"
                )

        # Detect I/O operations
        if any(io_op in func["filename"].lower() for io_op in ["pathlib", "os", "shutil", "file", "stat"]):
            if func["filename"] not in analysis["io_operations"]:
                analysis["io_operations"][func["filename"]] = []
            analysis["io_operations"][func["filename"]].append(
                {
                    "function": func["function"],
                    "time": func["total_time"],
                    "percent": time_percent,
                }
            )

    # Generate recommendations
    if analysis["lock_contention"]:
        lock_time = sum(v["time"] for v in analysis["lock_contention"].values())
        lock_percent = (lock_time / total_time) * 100
        if lock_percent > 50:
            analysis["recommendations"].append(
                f"Lock contention is critical ({lock_percent:.1f}% of time). "
                "Consider: 1) Batch progress updates, 2) Use atomic counters, "
                "3) Reduce callback frequency, 4) Use lock-free data structures"
            )

    io_time = sum(sum(f["time"] for f in funcs) for funcs in analysis["io_operations"].values())
    io_percent = (io_time / total_time) * 100
    if io_percent > 30:
        analysis["recommendations"].append(
            f"I/O operations take {io_percent:.1f}% of time. "
            "Consider: 1) Batch file operations, 2) Use async I/O, "
            "3) Optimize path operations, 4) Cache file metadata"
        )

    analysis["top_functions"] = [
        {
            "function": f["function"],
            "filename": f["filename"],
            "time": f["total_time"],
            "percent": (f["total_time"] / total_time) * 100,
            "calls": f["call_count"],
        }
        for f in top_functions
    ]

    return analysis


def export_profile_analysis(analysis: Dict[str, Any], output_file: Optional[str] = None) -> None:
    """Export profile analysis to JSON."""
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"profile_analysis_{timestamp}.json"

    output_path = Path(output_file)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"Profile analysis exported to: {output_path}")


def print_bottleneck_analysis(analysis: Dict[str, Any]) -> None:
    """Print detailed bottleneck analysis."""
    print("\n" + "=" * 80)
    print("Bottleneck Analysis")
    print("=" * 80)

    if analysis.get("bottlenecks"):
        print("\n⚠️  Critical Bottlenecks:")
        for i, bottleneck in enumerate(analysis["bottlenecks"], 1):
            print(f"  {i}. {bottleneck}")

    if analysis.get("lock_contention"):
        print("\n🔒 Lock Contention Analysis:")
        for func, data in analysis["lock_contention"].items():
            print(f"  • {func}: {data['time']:.3f}s ({data['percent']:.1f}%), " f"{data['calls']} calls")

    if analysis.get("io_operations"):
        print("\n📁 I/O Operations Analysis:")
        total_io_time = 0.0
        for filename, funcs in analysis["io_operations"].items():
            file_time = sum(f["time"] for f in funcs)
            total_io_time += file_time
            print(f"  • {Path(filename).name}: {file_time:.3f}s")
            for func in funcs[:3]:  # Top 3 functions per file
                print(f"    - {func['function']}: {func['time']:.3f}s " f"({func['percent']:.1f}%)")

    if analysis.get("recommendations"):
        print("\n💡 Optimization Recommendations:")
        for i, rec in enumerate(analysis["recommendations"], 1):
            print(f"  {i}. {rec}")


def profile_collection(
    file_count: int,
    output_file: str = "profile_stats.prof",
    export_analysis: bool = True,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Profile collection with detailed analysis."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / "source"
        target_dir = temp_path / "target"
        source_dir.mkdir()
        target_dir.mkdir()

        if verbose:
            print(f"Creating {file_count} test files...")
        create_test_files(source_dir, file_count)

        if verbose:
            print(f"Starting collection of {file_count} files...")
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

        profiler = cProfile.Profile()
        profiler.enable()

        service = CollectionService(config)
        results = service.collect()

        profiler.disable()

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        if verbose:
            print(f"\nCollection completed in {elapsed:.2f} seconds")
            print(f"Processed files: {results.get('processed_files', 0)}")
            print(f"Total files: {results.get('total_files', 0)}")

        profiler.dump_stats(output_file)
        if verbose:
            print(f"\nProfile saved to {output_file}")

        stats = pstats.Stats(profiler)

        if verbose:
            stats.sort_stats("cumulative")
            print("\n=== Top 20 functions by cumulative time ===")
            stats.print_stats(20)

            stats.sort_stats("tottime")
            print("\n=== Top 20 functions by total time ===")
            stats.print_stats(20)

        # Detailed analysis
        analysis = analyze_profile_stats(stats)
        analysis["metadata"] = {
            "file_count": file_count,
            "elapsed_time": elapsed,
            "processed_files": results.get("processed_files", 0),
            "total_files": results.get("total_files", 0),
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "platform": sys.platform,
        }

        if verbose:
            print_bottleneck_analysis(analysis)

        if export_analysis:
            export_profile_analysis(analysis)

        return analysis


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Profile collection performance")
    parser.add_argument(
        "file_count",
        type=int,
        nargs="?",
        default=1000,
        help="Number of files to test (default: 1000)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="profile_stats.prof",
        help="Output profile file (default: profile_stats.prof)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Don't export analysis to JSON",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Reduce output verbosity",
    )

    args = parser.parse_args()

    profile_collection(
        args.file_count,
        output_file=args.output,
        export_analysis=not args.no_export,
        verbose=not args.quiet,
    )
