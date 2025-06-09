"""
User domain package.

Contains all user-related domain logic including exceptions, repository, and service.
"""

from .exceptions import DuplicateUserError, UserError, UserNotFoundError
from .repository import UserRepository
from .service import UserRegistrationInput, UserService, UserServiceFactory

__all__ = [
    "DuplicateUserError",
    "UserError",
    "UserNotFoundError",
    "UserRepository",
    "UserRegistrationInput",
    "UserService",
    "UserServiceFactory",
]
