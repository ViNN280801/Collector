from __future__ import annotations


class CollectorException(Exception):
    pass


class ValidationError(CollectorException):
    pass


class PathError(CollectorException):
    pass


class FileOperationError(CollectorException):
    pass


class ConfigurationError(CollectorException):
    pass


class SecurityError(CollectorException):
    pass


class FilterError(CollectorException):
    pass


class WorkerPoolError(CollectorException):
    pass


class ProgressTrackingError(CollectorException):
    pass


class ArchiveError(CollectorException):
    pass
