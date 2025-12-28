from __future__ import annotations

import os
import locale
from typing import Dict, Optional

MESSAGES: Dict[str, Dict[str, str]] = {
    "ru": {
        "cli.help.description": "Универсальный коллектор файлов",
        "cli.help.source_paths": "Исходные директории для сбора файлов",
        "cli.help.target_path": "Целевая директория для сохранения файлов",
        "cli.help.patterns": "Паттерны для фильтрации файлов",
        "cli.help.pattern_type": "Тип паттерна (regex или glob)",
        "cli.help.operation_mode": "Режим операции (copy, move, move_remove)",
        "cli.help.create_archive": "Создать архив после сбора",
        "cli.help.archive_format": "Формат архива (zip, tar, 7z)",
        "cli.help.archive_compression": "Компрессия архива (gzip, bzip2, xz) - только для формата tar",
        "cli.help.collect_system_info": "Собрать системную информацию",
        "cli.help.locale": "Язык интерфейса (ru, en)",
        "cli.progress": "Прогресс: {:.1f}% ({}/{})",
        "cli.current_file": "Текущий файл: {}",
        "cli.error.validation": "Ошибка валидации: {}",
        "cli.error.path": "Ошибка пути: {}",
        "cli.error.operation": "Ошибка операции: {}",
        "cli.error.general": "Произошла ошибка: {}",
        "gui.window.title": "Universal Log Collector",
        "gui.source_paths.label": "Исходные пути:",
        "gui.target_path.label": "Целевой путь:",
        "gui.patterns.label": "Паттерны:",
        "gui.operation_mode.label": "Режим операции:",
        "gui.archive.label": "Создать архив",
        "gui.system_info.label": "Собрать системную информацию",
        "gui.language.label": "Язык:",
        "gui.button.start": "Начать сбор",
        "gui.button.settings": "Настройки",
        "gui.button.exit": "Выход",
        "gui.button.add": "Добавить",
        "gui.button.remove": "Удалить",
        "gui.button.browse": "Обзор",
        "gui.button.ok": "OK",
        "gui.button.cancel": "Отмена",
        "gui.progress.title": "Прогресс",
        "gui.progress.status": "{}/{} файлов",
        "gui.progress.percentage": "{:.1f}%",
        "gui.settings.title": "Настройки",
        "gui.settings.port.label": "Порт API:",
        "gui.history.title": "История сборов",
        "gui.history.refresh": "Обновить",
        "gui.history.clear": "Очистить",
        "gui.history.timestamp": "Время",
        "gui.history.source_paths": "Исходные пути",
        "gui.history.target_path": "Целевой путь",
        "gui.history.total_files": "Всего файлов",
        "gui.history.processed_files": "Обработано",
        "gui.history.status": "Статус",
        "gui.history.details": "Детали",
        "gui.button.config_manager": "Конфигурации",
        "gui.button.close": "Закрыть",
        "gui.config_manager.title": "Управление конфигурациями",
        "gui.config_manager.saved_configs": "Сохраненные конфигурации",
        "gui.config_manager.save": "Сохранить текущую",
        "gui.config_manager.load": "Загрузить",
        "gui.config_manager.delete": "Удалить",
        "gui.config_manager.refresh": "Обновить",
        "gui.config_manager.config_name": "Имя конфигурации:",
        "gui.config_manager.error": "Ошибка",
        "gui.config_manager.error_name_required": "Имя конфигурации обязательно",
        "gui.config_manager.success": "Успех",
        "gui.config_manager.config_saved": "Конфигурация успешно сохранена",
        "gui.config_manager.warning": "Предупреждение",
        "gui.config_manager.select_config": "Выберите конфигурацию",
        "gui.config_manager.config_loaded": "Конфигурация успешно загружена",
        "gui.config_manager.confirm": "Подтверждение",
        "gui.config_manager.confirm_delete": "Удалить конфигурацию '{}'?",
        "gui.config_manager.config_deleted": "Конфигурация успешно удалена",
        "gui.button.preview": "Предпросмотр",
        "gui.preview.title": "Предпросмотр файлов",
        "gui.preview.info": "Файлы, которые будут собраны:",
        "gui.preview.refresh": "Обновить",
        "gui.preview.file_path": "Путь к файлу",
        "gui.preview.size": "Размер",
        "gui.preview.status": "Всего: {} файлов, {}",
        "api.error.not_found": "Ресурс не найден",
        "api.error.validation": "Ошибка валидации запроса",
        "api.error.server": "Внутренняя ошибка сервера",
        "api.error.rate_limit": "Превышен лимит запросов",
    },
    "en": {
        "cli.help.description": "Universal file collector",
        "cli.help.source_paths": "Source directories for file collection",
        "cli.help.target_path": "Target directory for saving files",
        "cli.help.patterns": "File filtering patterns",
        "cli.help.pattern_type": "Pattern type (regex or glob)",
        "cli.help.operation_mode": "Operation mode (copy, move, move_remove)",
        "cli.help.create_archive": "Create archive after collection",
        "cli.help.archive_format": "Archive format (zip, tar, 7z)",
        "cli.help.archive_compression": "Archive compression (gzip, bzip2, xz) - only for tar format",
        "cli.help.collect_system_info": "Collect system information",
        "cli.help.locale": "Interface language (ru, en)",
        "cli.progress": "Progress: {:.1f}% ({}/{})",
        "cli.current_file": "Current file: {}",
        "cli.error.validation": "Validation error: {}",
        "cli.error.path": "Path error: {}",
        "cli.error.operation": "Operation error: {}",
        "cli.error.general": "An error occurred: {}",
        "gui.window.title": "Universal Log Collector",
        "gui.source_paths.label": "Source paths:",
        "gui.target_path.label": "Target path:",
        "gui.patterns.label": "Patterns:",
        "gui.operation_mode.label": "Operation mode:",
        "gui.archive.label": "Create archive",
        "gui.system_info.label": "Collect system information",
        "gui.language.label": "Language:",
        "gui.button.start": "Start Collection",
        "gui.button.settings": "Settings",
        "gui.button.exit": "Exit",
        "gui.button.add": "Add",
        "gui.button.remove": "Remove",
        "gui.button.browse": "Browse",
        "gui.button.ok": "OK",
        "gui.button.cancel": "Cancel",
        "gui.button.history": "History",
        "gui.progress.title": "Progress",
        "gui.progress.status": "{}/{} files",
        "gui.progress.percentage": "{:.1f}%",
        "gui.settings.title": "Settings",
        "gui.settings.port.label": "API Port:",
        "gui.history.title": "Collection History",
        "gui.history.refresh": "Refresh",
        "gui.history.clear": "Clear",
        "gui.history.timestamp": "Timestamp",
        "gui.history.source_paths": "Source Paths",
        "gui.history.target_path": "Target Path",
        "gui.history.total_files": "Total Files",
        "gui.history.processed_files": "Processed",
        "gui.history.status": "Status",
        "gui.history.details": "Details",
        "gui.button.config_manager": "Configs",
        "gui.button.close": "Close",
        "gui.config_manager.title": "Config Manager",
        "gui.config_manager.saved_configs": "Saved Configs",
        "gui.config_manager.save": "Save Current",
        "gui.config_manager.load": "Load",
        "gui.config_manager.delete": "Delete",
        "gui.config_manager.refresh": "Refresh",
        "gui.config_manager.config_name": "Config Name:",
        "gui.config_manager.error": "Error",
        "gui.config_manager.error_name_required": "Config name is required",
        "gui.config_manager.success": "Success",
        "gui.config_manager.config_saved": "Config saved successfully",
        "gui.config_manager.warning": "Warning",
        "gui.config_manager.select_config": "Please select a config",
        "gui.config_manager.config_loaded": "Config loaded successfully",
        "gui.config_manager.confirm": "Confirm",
        "gui.config_manager.confirm_delete": "Delete config '{}'?",
        "gui.config_manager.config_deleted": "Config deleted successfully",
        "gui.button.preview": "Preview",
        "gui.preview.title": "File Preview",
        "gui.preview.info": "Files that will be collected:",
        "gui.preview.refresh": "Refresh",
        "gui.preview.file_path": "File Path",
        "gui.preview.size": "Size",
        "gui.preview.status": "Total: {} files, {}",
        "api.error.not_found": "Resource not found",
        "api.error.validation": "Request validation error",
        "api.error.server": "Internal server error",
        "api.error.rate_limit": "Rate limit exceeded",
    },
}


def detect_locale() -> str:
    try:
        # Use getlocale() instead of deprecated getdefaultlocale()
        # getlocale() returns (locale, encoding) or (None, None)
        system_locale_tuple = locale.getlocale()
        if system_locale_tuple and system_locale_tuple[0]:
            system_locale = system_locale_tuple[0]
            lang_code = system_locale.split("_")[0].lower()
            if lang_code in MESSAGES:
                return lang_code
    except Exception:
        pass

    lang_env = os.environ.get("LANG", "")
    if lang_env:
        lang_code = lang_env.split("_")[0].split(".")[0].lower()
        if lang_code in MESSAGES:
            return lang_code

    return "en"


def get_message(key: str, locale: Optional[str] = None) -> str:
    if locale is None:
        locale = detect_locale()

    if locale not in MESSAGES:
        locale = "en"

    if key in MESSAGES[locale]:
        return MESSAGES[locale][key]

    if locale != "en" and key in MESSAGES["en"]:
        return MESSAGES["en"][key]

    return key
