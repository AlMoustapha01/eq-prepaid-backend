"""Exception manager for handling domain exceptions in controllers."""

import logging
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from modules.rules.domain.exceptions import (
    RuleAlreadyExistsError,
    RuleConfigurationError,
    RuleException,
    RuleNotFoundError,
    RuleSqlGenerationError,
    RuleValidationError,
    SectionAlreadyExistsError,
    SectionException,
    SectionNotFoundError,
    SectionValidationError,
)

from .error_responses import ErrorResponse

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class ExceptionManager:
    """Manages domain exception to HTTP exception conversion."""

    def __init__(self):
        self._exception_handlers: dict[type[Exception], Callable] = {
            # Rule exceptions
            RuleNotFoundError: self._handle_not_found_error,
            RuleAlreadyExistsError: self._handle_already_exists_error,
            RuleValidationError: self._handle_validation_error,
            RuleConfigurationError: self._handle_configuration_error,
            RuleSqlGenerationError: self._handle_sql_generation_error,
            # Section exceptions
            SectionNotFoundError: self._handle_not_found_error,
            SectionAlreadyExistsError: self._handle_already_exists_error,
            SectionValidationError: self._handle_validation_error,
            # Base exceptions
            RuleException: self._handle_generic_rule_error,
            SectionException: self._handle_generic_section_error,
        }

    def handle_exception(self, exception: Exception) -> HTTPException:
        """
        Convert domain exception to HTTP exception.

        Args:
            exception: Domain exception to convert

        Returns:
            HTTPException with appropriate status code and message

        """
        exception_type = type(exception)

        # Find the most specific handler
        for exc_type, handler in self._exception_handlers.items():
            if isinstance(exception, exc_type):
                logger.warning(f"Handling {exception_type.__name__}: {exception}")
                return handler(exception)

        # Fallback for unhandled exceptions
        logger.error(f"Unhandled exception: {exception}")
        return self._handle_generic_error(exception)

    def _handle_not_found_error(self, exception: Exception) -> HTTPException:
        """Handle not found errors."""
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                error="Not Found",
                message=str(exception),
                code=getattr(exception, "code", "NOT_FOUND"),
            ).dict(),
        )

    def _handle_already_exists_error(self, exception: Exception) -> HTTPException:
        """Handle already exists errors."""
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error="Conflict",
                message=str(exception),
                code=getattr(exception, "code", "ALREADY_EXISTS"),
            ).dict(),
        )

    def _handle_validation_error(self, exception: Exception) -> HTTPException:
        """Handle validation errors."""
        details = {}
        if hasattr(exception, "field") and exception.field:
            details["field"] = exception.field

        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Validation Error",
                message=str(exception),
                code=getattr(exception, "code", "VALIDATION_ERROR"),
                details=details if details else None,
            ).dict(),
        )

    def _handle_configuration_error(self, exception: Exception) -> HTTPException:
        """Handle configuration errors."""
        details = {}
        if hasattr(exception, "config_field") and exception.config_field:
            details["config_field"] = exception.config_field

        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Configuration Error",
                message=str(exception),
                code=getattr(exception, "code", "CONFIGURATION_ERROR"),
                details=details if details else None,
            ).dict(),
        )

    def _handle_sql_generation_error(self, exception: Exception) -> HTTPException:
        """Handle SQL generation errors."""
        details = {}
        if hasattr(exception, "rule_id") and exception.rule_id:
            details["rule_id"] = str(exception.rule_id)

        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponse(
                error="SQL Generation Error",
                message=str(exception),
                code=getattr(exception, "code", "SQL_GENERATION_ERROR"),
                details=details if details else None,
            ).dict(),
        )

    def _handle_generic_rule_error(self, exception: Exception) -> HTTPException:
        """Handle generic rule errors."""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Rule Error",
                message=str(exception),
                code=getattr(exception, "code", "RULE_ERROR"),
            ).dict(),
        )

    def _handle_generic_section_error(self, exception: Exception) -> HTTPException:
        """Handle generic section errors."""
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                error="Section Error",
                message=str(exception),
                code=getattr(exception, "code", "SECTION_ERROR"),
            ).dict(),
        )

    def _handle_generic_error(self, exception: Exception) -> HTTPException:
        """Handle generic unhandled errors."""
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Internal Server Error",
                message="An unexpected error occurred",
                code="INTERNAL_SERVER_ERROR",
            ).dict(),
        )


# Global exception manager instance
exception_manager = ExceptionManager()
