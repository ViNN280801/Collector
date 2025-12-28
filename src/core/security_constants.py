from __future__ import annotations

import platform

MAX_PATH_LENGTH = 4096
MAX_PATTERN_LENGTH = 1000
MAX_SOURCE_PATHS = 1000
MAX_REQUEST_SIZE_MB = 10
MAX_REQUEST_SIZE_BYTES = MAX_REQUEST_SIZE_MB * 1024 * 1024

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

LINUX_MACOS_RESERVED_NAMES = {
    ".",
    "..",
}

WINDOWS_DANGEROUS_CHARS = ["<", ">", '"', "|", "?", "*", "\x00"]

# These characters are valid in Linux/MacOS filenames but are dangerous
# in many contexts (shell commands, command injection, etc.)
# For security, we validate against them cross-platform
LINUX_MACOS_DANGEROUS_CHARS = ["<", ">", '"', "|", "?", "*", "\x00"]

ALL_PLATFORMS_DANGEROUS_CHARS = ["\x00"]


def get_reserved_names() -> set[str]:
    system = platform.system()
    if system == "Windows":
        return WINDOWS_RESERVED_NAMES
    return LINUX_MACOS_RESERVED_NAMES


def get_dangerous_chars() -> list[str]:
    system = platform.system()
    if system == "Windows":
        return WINDOWS_DANGEROUS_CHARS
    return LINUX_MACOS_DANGEROUS_CHARS


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_linux() -> bool:
    return platform.system() == "Linux"


def is_macos() -> bool:
    return platform.system() == "Darwin"
