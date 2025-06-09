"""
User domain exceptions.

Business-layer exceptions for user operations.
"""


class UserError(Exception):
    """Base exception for user-related errors."""

    pass


class DuplicateUserError(UserError):
    """Raised when attempting to create a user that already exists."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User with email '{email}' already exists")


class UserNotFoundError(UserError):
    """Raised when a requested user cannot be found."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")
