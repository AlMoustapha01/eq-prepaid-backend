import re
from dataclasses import dataclass

from slugify import slugify


@dataclass(frozen=True)
class SlugValueObject:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Slug cannot be empty")
        if not self._is_valid_slug(self.value):
            raise ValueError(
                "Invalid slug format. Must contain only lowercase letters, numbers, and hyphens"
            )
        if len(self.value) > 100:
            raise ValueError("Slug cannot exceed 100 characters")

    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        """Validate slug format: lowercase letters, numbers, and hyphens only"""
        return bool(re.match(r"^[a-z0-9-]+$", slug))

    @classmethod
    def from_name(cls, name: str) -> "SlugValueObject":
        """Generate a slug from a name"""
        if not name:
            raise ValueError("Name cannot be empty")

        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = slugify(name)

        if not slug:
            raise ValueError("Cannot generate valid slug from provided name")

        return cls(slug)

    def __str__(self) -> str:
        return self.value
