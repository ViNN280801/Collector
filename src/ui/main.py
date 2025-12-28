from __future__ import annotations

import sys

from .controllers.collection_controller import CollectionController
from .main_window import MainWindow


def main() -> int:
    try:
        root = MainWindow()
        CollectionController(root)
        root.mainloop()
        return 0
    except Exception as e:
        print(f"GUI Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
