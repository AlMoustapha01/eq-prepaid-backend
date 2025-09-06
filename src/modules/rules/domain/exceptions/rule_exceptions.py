"""Rule domain exceptions."""

from uuid import UUID


class RuleException(Exception):
    """Base exception for rule domain errors."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class RuleNotFoundError(RuleException):
    """Exception raised when a rule is not found."""

    def __init__(self, rule_id: UUID | None = None, rule_name: str | None = None):
        if rule_id:
            message = f"Rule with ID '{rule_id}' not found"
        elif rule_name:
            message = f"Rule with name '{rule_name}' not found"
        else:
            message = "Rule not found"
        super().__init__(message, "RULE_NOT_FOUND")
        self.rule_id = rule_id
        self.rule_name = rule_name


class RuleAlreadyExistsError(RuleException):
    """Exception raised when trying to create a rule that already exists."""

    def __init__(self, rule_name: str):
        message = f"Rule with name '{rule_name}' already exists"
        super().__init__(message, "RULE_ALREADY_EXISTS")
        self.rule_name = rule_name


class RuleValidationError(RuleException):
    """Exception raised when rule validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "RULE_VALIDATION_ERROR")
        self.field = field


class RuleConfigurationError(RuleException):
    """Exception raised when rule configuration is invalid."""

    def __init__(self, message: str, config_field: str | None = None):
        super().__init__(message, "RULE_CONFIGURATION_ERROR")
        self.config_field = config_field


class RuleSqlGenerationError(RuleException):
    """Exception raised when SQL generation fails."""

    def __init__(self, message: str, rule_id: UUID | None = None):
        super().__init__(message, "RULE_SQL_GENERATION_ERROR")
        self.rule_id = rule_id
