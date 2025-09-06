"""API routes."""

from .rule_routes import rule_router
from .section_routes import section_router

__all__ = [
    "rule_router",
    "section_router",
]
