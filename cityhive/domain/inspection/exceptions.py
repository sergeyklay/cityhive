"""
Inspection domain exceptions.

Business-layer exceptions for inspection operations.
"""


class InspectionError(Exception):
    """Base exception for inspection-related errors."""


class InvalidScheduleError(InspectionError):
    """Raised when invalid schedule date is provided."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class HiveNotFoundError(InspectionError):
    """Raised when the specified hive for inspection is not found."""

    def __init__(self, hive_id: int) -> None:
        self.hive_id = hive_id
        super().__init__(f"Hive with ID {hive_id} not found")


class DatabaseConflictError(InspectionError):
    """Raised when database integrity constraints are violated."""

    def __init__(self, message: str, original_error: Exception) -> None:
        self.original_error = original_error
        super().__init__(message)
