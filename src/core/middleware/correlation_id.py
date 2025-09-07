"""Correlation ID middleware for request tracing."""

import logging
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


def is_valid_uuid4(uuid_string: str) -> bool:
    """Validate if string is a valid UUID4."""
    try:
        uuid_obj = uuid.UUID(uuid_string, version=4)
        return str(uuid_obj) == uuid_string
    except ValueError:
        return False


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to requests for tracing."""

    def __init__(
        self,
        app,
        header_name: str = "X-Request-ID",
        generator: Callable | None = None,
        validator: Callable | None = None,
    ):
        super().__init__(app)
        self.header_name = header_name
        self.generator = generator or (lambda: str(uuid.uuid4()))
        self.validator = validator or is_valid_uuid4

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add correlation ID.

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint to call

        Returns:
            Response with correlation ID header

        """
        # Get correlation ID from request header or generate new one
        correlation_id = request.headers.get(self.header_name)

        # Validate existing correlation ID or generate new one
        if not correlation_id or not self.validator(correlation_id):
            correlation_id = self.generator()

        # Add correlation ID to request state for use in handlers
        request.state.correlation_id = correlation_id

        # Log request with correlation ID
        logger.info(
            "Request started - Method: %s, URL: %s, %s: %s",
            request.method,
            request.url,
            self.header_name,
            correlation_id,
        )

        # Process request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id

        # Log response with correlation ID
        logger.info(
            "Request completed - Status: %s, %s: %s",
            response.status_code,
            self.header_name,
            correlation_id,
        )

        return response
