from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict

from ..utils.collection_history import CollectionHistory
from ..utils.translations import get_message


class HistoryWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, history: CollectionHistory, locale: str = "en") -> None:
        super().__init__(parent)
        self._locale = locale
        self._history = history
        self._entry_map: Dict[str, Dict[str, Any]] = {}
        try:
            title = get_message("gui.history.title", locale)
        except KeyError:
            title = "Collection History"
        self.title(title)
        self.geometry("800x600")

        self._create_widgets()
        self._refresh_history()

    def _create_widgets(self) -> None:
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar = tk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        try:
            refresh_text = get_message("gui.history.refresh", self._locale)
        except KeyError:
            refresh_text = "Refresh"
        refresh_button = tk.Button(
            toolbar,
            text=refresh_text,
            command=self._refresh_history,
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        try:
            clear_text = get_message("gui.history.clear", self._locale)
        except KeyError:
            clear_text = "Clear"
        clear_button = tk.Button(
            toolbar,
            text=clear_text,
            command=self._clear_history,
        )
        clear_button.pack(side=tk.LEFT, padx=5)

        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("timestamp", "source_paths", "target_path", "total_files", "processed_files", "status")
        self._tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)

        def get_heading(key: str, default: str) -> str:
            try:
                return get_message(f"gui.history.{key}", self._locale)
            except KeyError:
                return default

        self._tree.heading("timestamp", text=get_heading("timestamp", "Timestamp"))
        self._tree.heading("source_paths", text=get_heading("source_paths", "Source Paths"))
        self._tree.heading("target_path", text=get_heading("target_path", "Target Path"))
        self._tree.heading("total_files", text=get_heading("total_files", "Total Files"))
        self._tree.heading("processed_files", text=get_heading("processed_files", "Processed"))
        self._tree.heading("status", text=get_heading("status", "Status"))

        self._tree.column("timestamp", width=150)
        self._tree.column("source_paths", width=200)
        self._tree.column("target_path", width=200)
        self._tree.column("total_files", width=80)
        self._tree.column("processed_files", width=80)
        self._tree.column("status", width=80)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<Double-1>", self._on_item_double_click)

        try:
            details_text = get_message("gui.history.details", self._locale)
        except KeyError:
            details_text = "Details"
        details_frame = tk.LabelFrame(main_frame, text=details_text)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self._details_text = tk.Text(details_frame, height=10, wrap=tk.WORD)
        details_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self._details_text.yview)
        self._details_text.configure(yscrollcommand=details_scrollbar.set)

        self._details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _refresh_history(self) -> None:
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._entry_map.clear()

        history = self._history.get_history()
        for idx, entry in enumerate(history):
            timestamp = entry.get("timestamp", "")
            source_paths = ", ".join(entry.get("source_paths", []))
            target_path = entry.get("target_path", "")
            results = entry.get("results", {})
            total_files = results.get("total_files", 0)
            processed_files = results.get("processed_files", 0)
            failed_files = results.get("failed_files", 0)

            if failed_files == 0:
                status = "Success"
            elif processed_files == 0:
                status = "Failed"
            else:
                status = "Partial"

            entry_id = f"entry_{idx}"
            self._entry_map[entry_id] = entry

            item_id = self._tree.insert(
                "",
                tk.END,
                values=(timestamp, source_paths[:50], target_path[:50], total_files, processed_files, status),
            )
            self._tree.set(item_id, "entry", entry_id)
            self._tree.item(item_id, tags=(entry_id,))

    def _clear_history(self) -> None:
        self._history.clear_history()
        self._refresh_history()

    def _on_item_double_click(self, event: tk.Event) -> None:
        selection = self._tree.selection()
        if selection:
            item_id = selection[0]
            entry_id = self._tree.set(item_id, "entry")
            if entry_id and entry_id in self._entry_map:
                entry = self._entry_map[entry_id]
                self._show_details(entry)

    def _show_details(self, entry: Dict[str, Any]) -> None:
        self._details_text.delete(1.0, tk.END)

        details = {
            "timestamp": entry.get("timestamp", ""),
            "source_paths": entry.get("source_paths", []),
            "target_path": entry.get("target_path", ""),
            "results": entry.get("results", {}),
            "config": entry.get("config", {}),
        }
        self._details_text.insert(1.0, json.dumps(details, indent=2, ensure_ascii=False, default=str))
