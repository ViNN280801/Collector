from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core import (
    CollectionConfigBuilder,
    CollectionService,
    FileOperationError,
    PathError,
    PatternConfig,
    ValidationError,
)
from ..utils.translations import detect_locale, get_message


def create_argument_parser(locale: str = "en") -> ArgumentParser:
    parser = ArgumentParser(description=get_message("cli.help.description", locale))

    parser.add_argument(
        "--source-paths",
        nargs="+",
        required=True,
        help=get_message("cli.help.source_paths", locale),
    )

    parser.add_argument("--target-path", required=True, help=get_message("cli.help.target_path", locale))

    parser.add_argument("--patterns", nargs="+", help=get_message("cli.help.patterns", locale))

    parser.add_argument(
        "--pattern-type",
        choices=["regex", "glob"],
        default="glob",
        help=get_message("cli.help.pattern_type", locale),
    )

    parser.add_argument(
        "--operation-mode",
        choices=["copy", "move", "move_remove"],
        default="copy",
        help=get_message("cli.help.operation_mode", locale),
    )

    parser.add_argument(
        "--create-archive",
        action="store_true",
        help=get_message("cli.help.create_archive", locale),
    )

    parser.add_argument(
        "--archive-format",
        default="zip",
        choices=["zip", "tar", "7z"],
        help=get_message("cli.help.archive_format", locale),
    )

    parser.add_argument(
        "--archive-compression",
        choices=["gzip", "bzip2", "xz"],
        help=get_message("cli.help.archive_compression", locale),
    )

    parser.add_argument(
        "--collect-system-info",
        action="store_true",
        default=True,
        dest="collect_system_info",
        help=get_message("cli.help.collect_system_info", locale),
    )

    parser.add_argument(
        "--no-collect-system-info",
        action="store_false",
        dest="collect_system_info",
    )

    parser.add_argument("--locale", choices=["ru", "en"], help=get_message("cli.help.locale", locale))

    return parser


def progress_callback_cli(
    percentage: float,
    current: int,
    total: int,
    current_file: Optional[str] = None,
) -> None:
    progress_msg = f"Progress: {percentage:.1f}% ({current}/{total})"
    if current_file:
        file_msg = f" - Current file: {current_file}"
        print(f"\r{progress_msg}{file_msg}", end="", flush=True)
    else:
        print(f"\r{progress_msg}", end="", flush=True)


def format_results(results: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("\n")
    lines.append("=" * 60)
    lines.append("Collection Results:")
    lines.append("=" * 60)
    lines.append(f"Total files: {results.get('total_files', 0)}")
    lines.append(f"Processed files: {results.get('processed_files', 0)}")
    lines.append(f"Failed files: {results.get('failed_files', 0)}")
    lines.append(f"Target path: {results.get('target_path', 'N/A')}")
    if results.get("pc_info_collected"):
        lines.append(f"PC Info collected: {results.get('pc_info_path', 'N/A')}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main() -> int:
    initial_locale = detect_locale()
    parser = create_argument_parser(initial_locale)
    args = parser.parse_args()

    locale = args.locale if args.locale else initial_locale

    try:
        source_paths = [Path(p) for p in args.source_paths]
        target_path = Path(args.target_path)

        patterns = []
        if args.patterns:
            for pattern in args.patterns:
                patterns.append(PatternConfig(pattern=pattern, pattern_type=args.pattern_type))

        config_builder = (
            CollectionConfigBuilder()
            .with_source_paths(source_paths)
            .with_target_path(target_path)
            .with_patterns(patterns)
            .with_operation_mode(args.operation_mode)
            .with_archive(args.create_archive, args.archive_format, getattr(args, "archive_compression", None))
            .with_system_info(args.collect_system_info)
        )

        config = config_builder.build()

        service = CollectionService(config)

        progress_tracker = service.get_progress_tracker()
        progress_tracker.subscribe(progress_callback_cli)

        results = service.collect()

        print()
        print(format_results(results))

        return 0

    except ValidationError as e:
        print(get_message("cli.error.validation", locale).format(e), file=sys.stderr)
        return 1
    except PathError as e:
        print(get_message("cli.error.path", locale).format(e), file=sys.stderr)
        return 1
    except FileOperationError as e:
        print(get_message("cli.error.operation", locale).format(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(get_message("cli.error.general", locale).format(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
