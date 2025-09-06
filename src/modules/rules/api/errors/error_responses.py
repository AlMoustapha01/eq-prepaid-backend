"""Error response models."""

from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    code: str | None = None
    details: dict[str, Any] | None = None


class ValidationErrorDetail(BaseModel):
    """Validation error detail model."""

    field: str
    message: str
    value: Any | None = None


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""

    error: str = "Validation Error"
    message: str
    code: str = "VALIDATION_ERROR"
    details: list[ValidationErrorDetail]
