"""Domain exceptions for rules module."""

from .rule_exceptions import (
    RuleAlreadyExistsError,
    RuleConfigurationError,
    RuleException,
    RuleNotFoundError,
    RuleSqlGenerationError,
    RuleValidationError,
)
from .section_exceptions import (
    SectionAlreadyExistsError,
    SectionException,
    SectionNotFoundError,
    SectionValidationError,
)

__all__ = [
    "RuleAlreadyExistsError",
    "RuleConfigurationError",
    # Rule exceptions
    "RuleException",
    "RuleNotFoundError",
    "RuleSqlGenerationError",
    "RuleValidationError",
    "SectionAlreadyExistsError",
    # Section exceptions
    "SectionException",
    "SectionNotFoundError",
    "SectionValidationError",
]
