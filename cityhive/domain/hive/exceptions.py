"""
Hive domain exceptions.

Business-layer exceptions for hive operations.
"""


class HiveError(Exception):
    """Base exception for hive-related errors."""

    pass


class InvalidLocationError(HiveError):
    """Raised when invalid location coordinates are provided."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UserNotFoundError(HiveError):
    """Raised when the specified user for hive creation is not found."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")
