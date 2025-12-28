from pathlib import Path
from typing import NewType

# TypeAlias is available in Python 3.10+, use typing_extensions for Python 3.8-3.9
# Pyright needs ignore comment for Python 3.8 compatibility
try:
    from typing import TypeAlias  # pyright: ignore[reportAttributeAccessIssue]
except ImportError:
    from typing_extensions import TypeAlias

FilePath: TypeAlias = Path
DirectoryPath: TypeAlias = Path
PatternString: TypeAlias = str
JobId = NewType("JobId", str)
UserId = NewType("UserId", str)
