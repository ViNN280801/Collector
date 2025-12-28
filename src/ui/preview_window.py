from __future__ import annotations

from pathlib import Path
from typing import List

import tkinter as tk
from tkinter import ttk

from ..core import PatternConfig
from ..core.file_filter import FileFilter
from ..utils.translations import get_message


class PreviewWindow(tk.Toplevel):
    def __init__(
        self, parent: tk.Tk, source_paths: List[str], patterns: List[str], pattern_type: str, locale: str = "en"
    ) -> None:
        super().__init__(parent)
        self._locale = locale
        self._source_paths = [Path(p) for p in source_paths]
        self._patterns = patterns
        self._pattern_type = pattern_type

        try:
            title = get_message("gui.preview.title", locale)
        except KeyError:
            title = "File Preview"
        self.title(title)
        self.geometry("800x600")
        self.transient(parent)

        self._create_widgets()
        self._load_preview()

    def _create_widgets(self) -> None:
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        try:
            info_text = get_message("gui.preview.info", self._locale)
        except KeyError:
            info_text = "Files that will be collected:"
        info_label = tk.Label(info_frame, text=info_text, font=("Arial", 10, "bold"))
        info_label.pack(side=tk.LEFT)

        try:
            refresh_text = get_message("gui.preview.refresh", self._locale)
        except KeyError:
            refresh_text = "Refresh"
        refresh_button = tk.Button(info_frame, text=refresh_text, command=self._load_preview)
        refresh_button.pack(side=tk.RIGHT)

        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("file_path", "size")
        self._tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=20)

        try:
            file_path_text = get_message("gui.preview.file_path", self._locale)
        except KeyError:
            file_path_text = "File Path"
        self._tree.heading("#0", text="")
        self._tree.heading("file_path", text=file_path_text)
        try:
            size_text = get_message("gui.preview.size", self._locale)
        except KeyError:
            size_text = "Size"
        self._tree.heading("size", text=size_text)

        self._tree.column("#0", width=0, stretch=tk.NO)
        self._tree.column("file_path", width=600)
        self._tree.column("size", width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self._status_label = tk.Label(status_frame, text="", font=("Arial", 9))
        self._status_label.pack(side=tk.LEFT)

        try:
            close_text = get_message("gui.button.close", self._locale)
        except KeyError:
            close_text = "Close"
        close_button = tk.Button(status_frame, text=close_text, command=self.destroy, width=15)
        close_button.pack(side=tk.RIGHT)

    def _load_preview(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)

        all_files: List[Path] = []
        for source_path in self._source_paths:
            if not source_path.exists():
                continue
            if source_path.is_file():
                all_files.append(source_path)
            elif source_path.is_dir():
                for filepath in source_path.rglob("*"):
                    if filepath.is_file():
                        all_files.append(filepath)

        file_filter = FileFilter()
        pattern_configs = [PatternConfig(pattern=p, pattern_type=self._pattern_type) for p in self._patterns]
        filtered_files = file_filter.filter_files(all_files, pattern_configs)

        total_size = 0
        for filepath in filtered_files:
            try:
                size = filepath.stat().st_size
                total_size += size
                size_str = self._format_size(size)
                self._tree.insert("", tk.END, values=(str(filepath), size_str))
            except OSError:
                continue

        try:
            status_text = get_message("gui.preview.status", self._locale)
        except KeyError:
            status_text = "Total: {} files, {}"
        status = status_text.format(len(filtered_files), self._format_size(total_size))
        self._status_label.config(text=status)

    def _format_size(self, size: int) -> str:
        size_float = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} PB"
