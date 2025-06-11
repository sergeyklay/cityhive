"""
Inspection domain package.

Contains all inspection-related domain logic including exceptions,
repository, and service.
"""

from .exceptions import (
    DatabaseConflictError,
    HiveNotFoundError,
    InspectionError,
    InvalidScheduleError,
)
from .repository import InspectionRepository
from .service import (
    InspectionCreationInput,
    InspectionService,
    InspectionServiceFactory,
)

__all__ = [
    "InspectionError",
    "InvalidScheduleError",
    "HiveNotFoundError",
    "DatabaseConflictError",
    "InspectionRepository",
    "InspectionCreationInput",
    "InspectionService",
    "InspectionServiceFactory",
]
