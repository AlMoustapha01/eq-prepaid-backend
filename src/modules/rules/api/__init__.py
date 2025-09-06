"""Rules API layer."""

from .controllers.rule_controller import RuleController
from .controllers.section_controller import SectionController
from .dependencies import get_rule_repository, get_section_repository
from .routes.rule_routes import rule_router
from .routes.section_routes import section_router

__all__ = [
    "RuleController",
    "SectionController",
    "get_rule_repository",
    "get_section_repository",
    "rule_router",
    "section_router",
]
