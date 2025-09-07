"""Domain exceptions for rules module."""

from .rule_exceptions import (
    BaseRuleExceptionError,
    RuleAlreadyExistsError,
    RuleConfigurationError,
    RuleNotFoundError,
    RuleSqlGenerationError,
    RuleValidationError,
)
from .section_exceptions import (
    BaseSectionExceptionError,
    SectionAlreadyExistsError,
    SectionNotFoundError,
    SectionValidationError,
)

__all__ = [
    "BaseRuleExceptionError",
    "BaseSectionExceptionError",
    "RuleAlreadyExistsError",
    "RuleConfigurationError",
    "RuleNotFoundError",
    "RuleSqlGenerationError",
    "RuleValidationError",
    "SectionAlreadyExistsError",
    "SectionNotFoundError",
    "SectionValidationError",
]
