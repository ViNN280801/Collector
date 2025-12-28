from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any, Callable, Dict, List, Optional

from ..utils.translations import detect_locale, get_message


class MainWindow(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self._locale = detect_locale()
        self.title(get_message("gui.window.title", self._locale))
        self.geometry("700x600")

        self._source_paths: List[str] = []
        self._patterns: List[str] = []

        self._create_source_paths_widget()
        self._create_target_path_widget()
        self._create_patterns_widget()
        self._create_operation_mode_widget()
        self._create_archive_widget()
        self._create_system_info_widget()
        self._create_language_widget()
        self._create_buttons()

        self._start_callback: Optional[Callable[[], None]] = None
        self._settings_callback: Optional[Callable[[], None]] = None
        self._history_callback: Optional[Callable[[], None]] = None
        self._config_manager_callback: Optional[Callable[[], None]] = None
        self._preview_callback: Optional[Callable[[], None]] = None

    def _create_source_paths_widget(self) -> None:
        frame = tk.LabelFrame(self, text=get_message("gui.source_paths.label", self._locale), padx=10, pady=10)
        frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self._source_listbox = tk.Listbox(frame, height=5)
        self._source_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(frame, command=self._source_listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self._source_listbox.config(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(frame)
        button_frame.pack(side=tk.LEFT, padx=5)

        add_button = tk.Button(
            button_frame,
            text=get_message("gui.button.add", self._locale),
            command=self._add_source_path,
        )
        add_button.pack(pady=2)

        remove_button = tk.Button(
            button_frame,
            text=get_message("gui.button.remove", self._locale),
            command=self._remove_source_path,
        )
        remove_button.pack(pady=2)

    def _create_target_path_widget(self) -> None:
        frame = tk.LabelFrame(self, text=get_message("gui.target_path.label", self._locale), padx=10, pady=10)
        frame.pack(pady=10, padx=10, fill=tk.X)

        self._target_var = tk.StringVar()
        target_entry = tk.Entry(frame, textvariable=self._target_var, width=50)
        target_entry.pack(side=tk.LEFT, padx=5)

        browse_button = tk.Button(
            frame,
            text=get_message("gui.button.browse", self._locale),
            command=self._browse_target_path,
        )
        browse_button.pack(side=tk.LEFT)

    def _create_patterns_widget(self) -> None:
        frame = tk.LabelFrame(self, text=get_message("gui.patterns.label", self._locale), padx=10, pady=10)
        frame.pack(pady=10, padx=10, fill=tk.X)

        self._pattern_var = tk.StringVar()
        pattern_entry = tk.Entry(frame, textvariable=self._pattern_var, width=30)
        pattern_entry.pack(side=tk.LEFT, padx=5)

        self._pattern_type_var = tk.StringVar(value="glob")
        radio_glob = tk.Radiobutton(frame, text="Glob", variable=self._pattern_type_var, value="glob")
        radio_glob.pack(side=tk.LEFT, padx=5)

        radio_regex = tk.Radiobutton(frame, text="Regex", variable=self._pattern_type_var, value="regex")
        radio_regex.pack(side=tk.LEFT, padx=5)

    def _create_operation_mode_widget(self) -> None:
        frame = tk.LabelFrame(
            self,
            text=get_message("gui.operation_mode.label", self._locale),
            padx=10,
            pady=10,
        )
        frame.pack(pady=10, padx=10, fill=tk.X)

        self._operation_mode_var = tk.StringVar(value="copy")

        modes = [("Copy", "copy"), ("Move", "move"), ("Move & Remove", "move_remove")]
        for text, value in modes:
            radio = tk.Radiobutton(frame, text=text, variable=self._operation_mode_var, value=value)
            radio.pack(side=tk.LEFT, padx=10)

    def _create_archive_widget(self) -> None:
        frame = tk.Frame(self)
        frame.pack(pady=5, padx=10, fill=tk.X)

        self._archive_var = tk.BooleanVar(value=False)
        archive_check = tk.Checkbutton(
            frame,
            text=get_message("gui.archive.label", self._locale),
            variable=self._archive_var,
        )
        archive_check.pack(side=tk.LEFT)

        self._archive_format_var = tk.StringVar(value="zip")
        archive_combo = ttk.Combobox(
            frame,
            textvariable=self._archive_format_var,
            values=["zip", "tar", "7z"],
            width=10,
            state="readonly",
        )
        archive_combo.pack(side=tk.LEFT, padx=10)

    def _create_system_info_widget(self) -> None:
        frame = tk.Frame(self)
        frame.pack(pady=5, padx=10, fill=tk.X)

        self._system_info_var = tk.BooleanVar(value=True)
        system_info_check = tk.Checkbutton(
            frame,
            text=get_message("gui.system_info.label", self._locale),
            variable=self._system_info_var,
        )
        system_info_check.pack(side=tk.LEFT)

    def _create_language_widget(self) -> None:
        frame = tk.Frame(self)
        frame.pack(pady=5, padx=10, fill=tk.X)

        label = tk.Label(frame, text=get_message("gui.language.label", self._locale))
        label.pack(side=tk.LEFT)

        self._locale_var = tk.StringVar(value=self._locale)

        radio_ru = tk.Radiobutton(
            frame, text="Русский", variable=self._locale_var, value="ru", command=self._update_language
        )
        radio_ru.pack(side=tk.LEFT, padx=5)

        radio_en = tk.Radiobutton(
            frame, text="English", variable=self._locale_var, value="en", command=self._update_language
        )
        radio_en.pack(side=tk.LEFT, padx=5)

    def _create_buttons(self) -> None:
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        try:
            preview_text = get_message("gui.button.preview", self._locale)
        except KeyError:
            preview_text = "Preview"
        preview_button = tk.Button(
            button_frame,
            text=preview_text,
            command=self._on_preview,
            width=15,
        )
        preview_button.pack(side=tk.LEFT, padx=5)

        start_button = tk.Button(
            button_frame,
            text=get_message("gui.button.start", self._locale),
            command=self._on_start_collection,
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        start_button.pack(side=tk.LEFT, padx=5)

        settings_button = tk.Button(
            button_frame,
            text=get_message("gui.button.settings", self._locale),
            command=self._on_settings,
            width=15,
        )
        settings_button.pack(side=tk.LEFT, padx=5)

        try:
            history_text = get_message("gui.button.history", self._locale)
        except KeyError:
            history_text = "History"
        history_button = tk.Button(
            button_frame,
            text=history_text,
            command=self._on_history,
            width=15,
        )
        history_button.pack(side=tk.LEFT, padx=5)

        try:
            config_mgr_text = get_message("gui.button.config_manager", self._locale)
        except KeyError:
            config_mgr_text = "Configs"
        config_manager_button = tk.Button(
            button_frame,
            text=config_mgr_text,
            command=self._on_config_manager,
            width=15,
        )
        config_manager_button.pack(side=tk.LEFT, padx=5)

        exit_button = tk.Button(
            button_frame,
            text=get_message("gui.button.exit", self._locale),
            command=self.quit,
            width=15,
        )
        exit_button.pack(side=tk.LEFT, padx=5)

    def _add_source_path(self) -> None:
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self._source_paths.append(path)
            self._source_listbox.insert(tk.END, path)

    def _remove_source_path(self) -> None:
        selection = self._source_listbox.curselection()
        if selection:
            index = selection[0]
            self._source_listbox.delete(index)
            del self._source_paths[index]

    def _browse_target_path(self) -> None:
        path = filedialog.askdirectory(title="Select Target Directory")
        if path:
            self._target_var.set(path)

    def _on_start_collection(self) -> None:
        if self._start_callback:
            self._start_callback()

    def _on_settings(self) -> None:
        if self._settings_callback:
            self._settings_callback()

    def _on_history(self) -> None:
        if self._history_callback:
            self._history_callback()

    def _on_config_manager(self) -> None:
        if self._config_manager_callback:
            self._config_manager_callback()

    def _on_preview(self) -> None:
        if self._preview_callback is not None:
            self._preview_callback()

    def _update_language(self) -> None:
        new_locale = self._locale_var.get()
        if new_locale != self._locale:
            self._locale = new_locale

    def set_start_callback(self, callback: Callable[[], None]) -> None:
        self._start_callback = callback

    def set_settings_callback(self, callback: Callable[[], None]) -> None:
        self._settings_callback = callback

    def set_history_callback(self, callback: Callable[[], None]) -> None:
        self._history_callback = callback

    def set_config_manager_callback(self, callback: Callable[[], None]) -> None:
        self._config_manager_callback = callback

    def set_preview_callback(self, callback: Callable[[], None]) -> None:
        self._preview_callback = callback

    def set_locale(self, locale: str) -> None:
        self._locale = locale

    def load_config(self, config: Dict[str, Any]) -> None:
        if "source_paths" in config:
            self._source_paths = config["source_paths"]
            self._source_listbox.delete(0, tk.END)
            for path in self._source_paths:
                self._source_listbox.insert(tk.END, path)

        if "target_path" in config:
            self._target_var.set(config["target_path"])

        if "patterns" in config:
            self._patterns = config["patterns"]
            pattern_text = ", ".join(self._patterns) if self._patterns else ""
            self._pattern_var.set(pattern_text)

        if "pattern_type" in config:
            self._pattern_type_var.set(config["pattern_type"])

        if "operation_mode" in config:
            self._operation_mode_var.set(config["operation_mode"])

        if "create_archive" in config:
            self._archive_var.set(config["create_archive"])

        if "archive_format" in config:
            self._archive_format_var.set(config["archive_format"])

        if "collect_system_info" in config:
            self._system_info_var.set(config["collect_system_info"])

        if "locale" in config:
            self._locale_var.set(config["locale"])
            self._update_language()

    def get_config(self) -> Dict[str, Any]:
        pattern = self._pattern_var.get().strip()
        patterns = [pattern] if pattern else []

        return {
            "source_paths": self._source_paths,
            "target_path": self._target_var.get(),
            "patterns": patterns,
            "pattern_type": self._pattern_type_var.get(),
            "operation_mode": self._operation_mode_var.get(),
            "create_archive": self._archive_var.get(),
            "archive_format": self._archive_format_var.get(),
            "collect_system_info": self._system_info_var.get(),
            "locale": self._locale_var.get(),
        }

    def get_locale(self) -> str:
        return self._locale
