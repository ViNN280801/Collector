from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..utils.translations import get_message


class ProgressWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, locale: str = "en") -> None:
        super().__init__(parent)
        self._locale = locale
        self.title(get_message("gui.progress.title", locale))
        self.geometry("500x200")
        self.resizable(False, False)

        self._create_progress_bar()
        self._create_percentage_label()
        self._create_status_label()
        self._create_file_label()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.withdraw()

    def _create_progress_bar(self) -> None:
        self._progress_bar = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=450, mode="determinate", maximum=100)
        self._progress_bar.pack(pady=20, padx=25)

    def _create_percentage_label(self) -> None:
        self._percentage_label = tk.Label(self, text="0.0%", font=("Arial", 14, "bold"))
        self._percentage_label.pack(pady=5)

    def _create_status_label(self) -> None:
        status_text = get_message("gui.progress.status", self._locale).format(0, 0)
        self._status_label = tk.Label(self, text=status_text, font=("Arial", 10))
        self._status_label.pack(pady=5)

    def _create_file_label(self) -> None:
        self._file_label = tk.Label(self, text="", font=("Arial", 8), wraplength=450, justify=tk.LEFT)
        self._file_label.pack(pady=5, padx=25)

    def update_progress(
        self,
        percentage: float,
        current: int,
        total: int,
        current_file: Optional[str] = None,
    ) -> None:
        self._progress_bar["value"] = percentage

        percentage_text = get_message("gui.progress.percentage", self._locale).format(percentage)
        self._percentage_label.config(text=percentage_text)

        status_text = get_message("gui.progress.status", self._locale).format(current, total)
        self._status_label.config(text=status_text)

        if current_file:
            self._file_label.config(text=current_file)

        self.update_idletasks()

    def _on_close(self) -> None:
        pass

    def show(self) -> None:
        self.deiconify()

    def close(self) -> None:
        self.withdraw()


def create_progress_callback(progress_window: ProgressWindow):
    def callback(
        percentage: float,
        current: int,
        total: int,
        current_file: Optional[str] = None,
    ) -> None:
        progress_window.update_progress(percentage, current, total, current_file)

    return callback
