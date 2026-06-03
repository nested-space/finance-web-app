"""Typed boundary errors.

These are the only error types services raise across the boundary. The web layer
maps them to HTTP status codes; nothing surfaces a stack trace to the user
(``docs/ARCHITECTURE.md`` -> "Repository protocol shape", ``docs/DEVELOPMENT.md``
-> "Security baseline").
"""

from __future__ import annotations


class NotFoundError(Exception):
    """Raised when a row addressed by id does not exist."""

    def __init__(self, resource: str, identifier: int) -> None:
        super().__init__(f"{resource} {identifier} not found")
        self.resource = resource
        self.identifier = identifier


class ValidationError(Exception):
    """Raised when a use-case rule rejects otherwise well-typed input."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"{field}: {reason}")
        self.field = field
        self.reason = reason


class RepositoryError(Exception):
    """Wraps an unexpected persistence failure so services never catch ``sqlite3.Error``."""

    def __init__(self, operation: str, cause: Exception) -> None:
        super().__init__(f"{operation} failed: {cause}")
        self.operation = operation
        self.cause = cause
