from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, Optional

from ..utils.config_manager import ConfigManager, ConfigManagerError
from ..utils.translations import get_message


class ConfigManagerWindow(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        current_config: Dict[str, Any],
        locale: str = "en",
        on_load: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._locale = locale
        self._current_config = current_config
        self._on_load = on_load
        self._config_manager = ConfigManager()

        try:
            title = get_message("gui.config_manager.title", locale)
        except KeyError:
            title = "Config Manager"
        self.title(title)
        self.geometry("600x500")
        self.transient(parent)

        self._create_widgets()
        self._refresh_configs()

    def _create_widgets(self) -> None:
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        list_frame = tk.LabelFrame(main_frame, text=self._get_text("gui.config_manager.saved_configs", "Saved Configs"))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._config_listbox = tk.Listbox(list_frame, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._config_listbox.yview)
        self._config_listbox.configure(yscrollcommand=scrollbar.set)

        self._config_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        save_button = tk.Button(
            button_frame,
            text=self._get_text("gui.config_manager.save", "Save Current"),
            command=self._save_config,
            width=15,
        )
        save_button.pack(side=tk.LEFT, padx=5)

        load_button = tk.Button(
            button_frame,
            text=self._get_text("gui.config_manager.load", "Load"),
            command=self._load_config,
            width=15,
        )
        load_button.pack(side=tk.LEFT, padx=5)

        delete_button = tk.Button(
            button_frame,
            text=self._get_text("gui.config_manager.delete", "Delete"),
            command=self._delete_config,
            width=15,
        )
        delete_button.pack(side=tk.LEFT, padx=5)

        refresh_button = tk.Button(
            button_frame,
            text=self._get_text("gui.config_manager.refresh", "Refresh"),
            command=self._refresh_configs,
            width=15,
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        name_frame = tk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        name_label = tk.Label(name_frame, text=self._get_text("gui.config_manager.config_name", "Config Name:"))
        name_label.pack(side=tk.LEFT, padx=5)

        self._name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=self._name_var, width=30)
        name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        close_button = tk.Button(
            main_frame,
            text=self._get_text("gui.button.close", "Close"),
            command=self.destroy,
            width=15,
        )
        close_button.pack(pady=10)

    def _get_text(self, key: str, default: str) -> str:
        try:
            return get_message(key, self._locale)
        except KeyError:
            return default

    def _refresh_configs(self) -> None:
        self._config_listbox.delete(0, tk.END)
        configs = self._config_manager.list_configs()
        for config_name in configs:
            self._config_listbox.insert(tk.END, config_name)

    def _save_config(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror(
                self._get_text("gui.config_manager.error", "Error"),
                self._get_text("gui.config_manager.error_name_required", "Config name is required"),
            )
            return

        try:
            self._config_manager.save_config(name, self._current_config)
            messagebox.showinfo(
                self._get_text("gui.config_manager.success", "Success"),
                self._get_text("gui.config_manager.config_saved", "Config saved successfully"),
            )
            self._refresh_configs()
        except ConfigManagerError as e:
            messagebox.showerror(
                self._get_text("gui.config_manager.error", "Error"),
                str(e),
            )

    def _load_config(self) -> None:
        selection = self._config_listbox.curselection()
        if not selection:
            messagebox.showwarning(
                self._get_text("gui.config_manager.warning", "Warning"),
                self._get_text("gui.config_manager.select_config", "Please select a config to load"),
            )
            return

        config_name = self._config_listbox.get(selection[0])

        try:
            config = self._config_manager.load_config(config_name)
            if config and self._on_load:
                self._on_load(config)
                messagebox.showinfo(
                    self._get_text("gui.config_manager.success", "Success"),
                    self._get_text("gui.config_manager.config_loaded", "Config loaded successfully"),
                )
                self.destroy()
        except ConfigManagerError as e:
            messagebox.showerror(
                self._get_text("gui.config_manager.error", "Error"),
                str(e),
            )

    def _delete_config(self) -> None:
        selection = self._config_listbox.curselection()
        if not selection:
            messagebox.showwarning(
                self._get_text("gui.config_manager.warning", "Warning"),
                self._get_text("gui.config_manager.select_config", "Please select a config to delete"),
            )
            return

        config_name = self._config_listbox.get(selection[0])

        result = messagebox.askyesno(
            self._get_text("gui.config_manager.confirm", "Confirm"),
            self._get_text("gui.config_manager.confirm_delete", f"Delete config '{config_name}'?"),
        )

        if result:
            try:
                self._config_manager.delete_config(config_name)
                self._refresh_configs()
                messagebox.showinfo(
                    self._get_text("gui.config_manager.success", "Success"),
                    self._get_text("gui.config_manager.config_deleted", "Config deleted successfully"),
                )
            except ConfigManagerError as e:
                messagebox.showerror(
                    self._get_text("gui.config_manager.error", "Error"),
                    str(e),
                )
