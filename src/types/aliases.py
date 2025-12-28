from pathlib import Path
from typing import NewType

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

FilePath: TypeAlias = Path
DirectoryPath: TypeAlias = Path
PatternString: TypeAlias = str
JobId = NewType("JobId", str)
UserId = NewType("UserId", str)
