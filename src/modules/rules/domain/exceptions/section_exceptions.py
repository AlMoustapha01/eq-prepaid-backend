"""Section domain exceptions."""

from uuid import UUID


class BaseSectionExceptionError(Exception):
    """Base exception for section domain errors."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class SectionNotFoundError(BaseSectionExceptionError):
    """Exception raised when a section is not found."""

    def __init__(
        self,
        section_id: UUID | None = None,
        section_name: str | None = None,
        slug: str | None = None,
    ):
        if section_id:
            message = f"Section with ID '{section_id}' not found"
        elif section_name:
            message = f"Section with name '{section_name}' not found"
        elif slug:
            message = f"Section with slug '{slug}' not found"
        else:
            message = "Section not found"
        super().__init__(message, "SECTION_NOT_FOUND")
        self.section_id = section_id
        self.section_name = section_name
        self.slug = slug


class SectionAlreadyExistsError(BaseSectionExceptionError):
    """Exception raised when trying to create a section that already exists."""

    def __init__(self, section_name: str | None = None, slug: str | None = None):
        if section_name:
            message = f"Section with name '{section_name}' already exists"
        elif slug:
            message = f"Section with slug '{slug}' already exists"
        else:
            message = "Section already exists"
        super().__init__(message, "SECTION_ALREADY_EXISTS")
        self.section_name = section_name
        self.slug = slug


class SectionValidationError(BaseSectionExceptionError):
    """Exception raised when section validation fails."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, "SECTION_VALIDATION_ERROR")
        self.field = field
