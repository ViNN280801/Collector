from pathlib import Path
from typing import NewType

# TypeAlias is available in Python 3.10+ in typing module
# For compatibility with mypy on Python 3.8, use typing_extensions directly
# typing_extensions provides TypeAlias for Python 3.8-3.9, and is compatible with 3.10+
from typing_extensions import TypeAlias

FilePath: TypeAlias = Path
DirectoryPath: TypeAlias = Path
PatternString: TypeAlias = str
JobId = NewType("JobId", str)
UserId = NewType("UserId", str)
