from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional

from ..utils.translations import get_message


class ConfigDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, current_config: Dict[str, Any], locale: str = "en") -> None:
        super().__init__(parent)
        self._locale = locale
        self._current_config = current_config
        self._result: Optional[Dict[str, Any]] = None

        self.title(get_message("gui.settings.title", locale))
        self.geometry("400x200")
        self.resizable(False, False)

        self._create_port_widget()
        self._create_language_widget()
        self._create_buttons()

        self.transient(parent)
        self.grab_set()

    def _create_port_widget(self) -> None:
        port_frame = tk.Frame(self)
        port_frame.pack(pady=10, padx=20, fill=tk.X)

        port_label = tk.Label(port_frame, text=get_message("gui.settings.port.label", self._locale))
        port_label.pack(side=tk.LEFT)

        self._port_var = tk.StringVar(value=str(self._current_config.get("port", 8000)))
        self._port_entry = tk.Entry(port_frame, textvariable=self._port_var, width=10)
        self._port_entry.pack(side=tk.LEFT, padx=10)

    def _create_language_widget(self) -> None:
        lang_frame = tk.Frame(self)
        lang_frame.pack(pady=10, padx=20, fill=tk.X)

        lang_label = tk.Label(lang_frame, text=get_message("gui.language.label", self._locale))
        lang_label.pack(side=tk.LEFT)

        self._lang_var = tk.StringVar(value=self._current_config.get("locale", "en"))

        lang_ru = tk.Radiobutton(lang_frame, text="Русский", variable=self._lang_var, value="ru")
        lang_ru.pack(side=tk.LEFT, padx=5)

        lang_en = tk.Radiobutton(lang_frame, text="English", variable=self._lang_var, value="en")
        lang_en.pack(side=tk.LEFT, padx=5)

    def _create_buttons(self) -> None:
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        ok_button = tk.Button(
            button_frame,
            text=get_message("gui.button.ok", self._locale),
            command=self._on_ok,
            width=10,
        )
        ok_button.pack(side=tk.LEFT, padx=5)

        cancel_button = tk.Button(
            button_frame,
            text=get_message("gui.button.cancel", self._locale),
            command=self._on_cancel,
            width=10,
        )
        cancel_button.pack(side=tk.LEFT, padx=5)

    def _on_ok(self) -> None:
        port_str = self._port_var.get()
        try:
            port = int(port_str)
            if port < 1024 or port > 65535:
                messagebox.showerror("Error", "Port must be between 1024 and 65535")
                return
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return

        self._result = {"port": port, "locale": self._lang_var.get()}
        self.destroy()

    def _on_cancel(self) -> None:
        self._result = None
        self.destroy()

    def get_config(self) -> Optional[Dict[str, Any]]:
        return self._result
