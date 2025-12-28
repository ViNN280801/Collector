from __future__ import annotations

import threading
from pathlib import Path
from tkinter import messagebox
from typing import TYPE_CHECKING, Any, Dict

from ...core import (
    CollectionConfigBuilder,
    CollectionService,
    PathError,
    PatternConfig,
    ValidationError,
)
from ...utils.collection_history import CollectionHistory
from ..progress_window import ProgressWindow, create_progress_callback

if TYPE_CHECKING:
    from ..main_window import MainWindow


class CollectionController:
    def __init__(self, main_window: MainWindow) -> None:
        self._main_window = main_window
        self._progress_window: ProgressWindow = ProgressWindow(main_window, main_window.get_locale())
        self._history = CollectionHistory()

        main_window.set_start_callback(self.start_collection)
        main_window.set_settings_callback(self.show_settings)
        main_window.set_history_callback(self.show_history)
        main_window.set_config_manager_callback(self.show_config_manager)
        main_window.set_preview_callback(self.show_preview)

    def start_collection(self) -> None:
        config_data = self._main_window.get_config()

        if not config_data.get("source_paths"):
            messagebox.showerror("Error", "Please add at least one source path")
            return

        if not config_data.get("target_path"):
            messagebox.showerror("Error", "Please specify target path")
            return

        try:
            source_paths = [Path(p) for p in config_data["source_paths"]]
            target_path = Path(config_data["target_path"])

            patterns = []
            if config_data.get("patterns"):
                for pattern in config_data["patterns"]:
                    patterns.append(PatternConfig(pattern=pattern, pattern_type=config_data["pattern_type"]))

            config_builder = (
                CollectionConfigBuilder()
                .with_source_paths(source_paths)
                .with_target_path(target_path)
                .with_patterns(patterns)
                .with_operation_mode(config_data["operation_mode"])
                .with_archive(config_data["create_archive"], config_data["archive_format"])
                .with_system_info(config_data["collect_system_info"])
            )

            config = config_builder.build()

            service = CollectionService(config)

            progress_tracker = service.get_progress_tracker()
            progress_callback = create_progress_callback(self._progress_window)
            progress_tracker.subscribe(progress_callback)

            self._progress_window.show()

            def run_collection() -> None:
                try:
                    results = service.collect()
                    self._main_window.after(0, lambda r=results: self._on_collection_complete(r))  # type: ignore[misc]
                except Exception as error:
                    self._main_window.after(0, lambda err=error: self._on_collection_error(err))  # type: ignore[misc]

            collection_thread = threading.Thread(target=run_collection, daemon=True)
            collection_thread.start()

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except PathError as e:
            messagebox.showerror("Path Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_collection_complete(self, results: Dict[str, Any]) -> None:
        self._progress_window.close()

        config_data = self._main_window.get_config()
        self._history.add_entry(
            source_paths=config_data.get("source_paths", []),
            target_path=config_data.get("target_path", ""),
            results=results,
            config=config_data,
        )

        message = "Collection completed!\n\n"
        message += f"Total files: {results.get('total_files', 0)}\n"
        message += f"Processed: {results.get('processed_files', 0)}\n"
        message += f"Failed: {results.get('failed_files', 0)}\n"
        message += f"Target: {results.get('target_path', 'N/A')}"
        messagebox.showinfo("Success", message)

    def _on_collection_error(self, error: Exception) -> None:
        self._progress_window.close()
        messagebox.showerror("Error", str(error))

    def cancel_collection(self) -> None:
        self._progress_window.close()

    def show_settings(self) -> None:
        from ..config_dialog import ConfigDialog

        current_config = {"port": 8000, "locale": self._main_window.get_locale()}
        dialog = ConfigDialog(self._main_window, current_config, self._main_window.get_locale())
        self._main_window.wait_window(dialog)

        new_config = dialog.get_config()
        if new_config:
            new_locale = new_config.get("locale", self._main_window.get_locale())
            if new_locale:
                self._main_window.set_locale(new_locale)

    def show_history(self) -> None:
        from ..history_window import HistoryWindow

        history_window = HistoryWindow(self._main_window, self._history, self._main_window.get_locale())
        history_window.transient(self._main_window)

    def show_config_manager(self) -> None:
        from ..config_manager_window import ConfigManagerWindow

        current_config = self._main_window.get_config()

        def on_load(config: Dict[str, Any]) -> None:
            self._main_window.load_config(config)

        config_manager_window = ConfigManagerWindow(
            self._main_window,
            current_config,
            self._main_window.get_locale(),
            on_load=on_load,
        )
        config_manager_window.transient(self._main_window)

    def show_preview(self) -> None:
        from ..preview_window import PreviewWindow

        config_data = self._main_window.get_config()
        source_paths = config_data.get("source_paths", [])
        patterns = config_data.get("patterns", [])
        pattern_type = config_data.get("pattern_type", "glob")

        if not source_paths:
            from tkinter import messagebox

            messagebox.showwarning("Warning", "Please add at least one source path")
            return

        preview_window = PreviewWindow(
            self._main_window,
            source_paths,
            patterns,
            pattern_type,
            self._main_window.get_locale(),
        )
        preview_window.transient(self._main_window)
