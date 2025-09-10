"""Unit tests for SectionEntity domain model."""

from datetime import datetime
from uuid import UUID

import pytest

from modules.rules.domain.events.section_events import (
    SectionActivated,
    SectionCreated,
    SectionDeactivated,
    SectionDescriptionUpdated,
    SectionNameUpdated,
)
from modules.rules.domain.models.section import CreateSectionDto, SectionEntity
from modules.rules.domain.value_objects.enums import SectionStatus
from modules.rules.domain.value_objects.slug import SlugValueObject


class TestSectionEntity:
    """Test cases for SectionEntity domain model."""

    def test_create_section_success(self):
        """Test successful section creation."""
        # Arrange
        dto = CreateSectionDto(name="Test Section", description="A test section for unit testing")

        # Act
        section = SectionEntity.create(dto)

        # Assert
        assert section.id is not None
        assert isinstance(section.id, UUID)
        assert section.name == "Test Section"
        assert section.description == "A test section for unit testing"
        assert section.status == SectionStatus.ACTIVE
        assert section.slug is not None
        assert isinstance(section.slug, SlugValueObject)
        assert section.created_at is not None
        assert section.updated_at is not None

        # Check domain events
        events = section.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], SectionCreated)
        assert events[0].aggregate_id == section.id
        assert events[0].name == "Test Section"
        assert events[0].description == "A test section for unit testing"
        assert events[0].status == SectionStatus.ACTIVE

    def test_create_section_with_special_characters(self):
        """Test section creation with special characters in name."""
        # Arrange
        dto = CreateSectionDto(
            name="Test Section - Spécial Chars & Symbols!",
            description="Section with special characters",
        )

        # Act
        section = SectionEntity.create(dto)

        # Assert
        assert section.name == "Test Section - Spécial Chars & Symbols!"
        assert section.slug is not None
        # Slug should be normalized
        assert " " not in str(section.slug)
        assert "&" not in str(section.slug)

    def test_make_active_from_inactive(self):
        """Test making an inactive section active."""
        # Arrange
        dto = CreateSectionDto(name="Test Section", description="Test")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        section.status = SectionStatus.INACTIVE

        # Act
        section.make_active()

        # Assert
        assert section.status == SectionStatus.ACTIVE
        assert section.updated_at is not None

        # Check domain events
        events = section.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], SectionActivated)
        assert events[0].aggregate_id == section.id

    def test_make_active_when_already_active(self):
        """Test making an already active section active (no change)."""
        # Arrange
        dto = CreateSectionDto(name="Test Section", description="Test")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        original_updated_at = section.updated_at

        # Act
        section.make_active()

        # Assert
        assert section.status == SectionStatus.ACTIVE
        assert section.updated_at == original_updated_at

        # Check no domain events were published
        events = section.get_domain_events()
        assert len(events) == 0

    def test_make_inactive_from_active(self):
        """Test making an active section inactive."""
        # Arrange
        dto = CreateSectionDto(name="Test Section", description="Test")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event

        # Act
        section.make_inactive()

        # Assert
        assert section.status == SectionStatus.INACTIVE
        assert section.updated_at is not None

        # Check domain events
        events = section.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], SectionDeactivated)
        assert events[0].aggregate_id == section.id

    def test_make_inactive_when_already_inactive(self):
        """Test making an already inactive section inactive (no change)."""
        # Arrange
        dto = CreateSectionDto(name="Test Section", description="Test")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        section.status = SectionStatus.INACTIVE
        original_updated_at = section.updated_at

        # Act
        section.make_inactive()

        # Assert
        assert section.status == SectionStatus.INACTIVE
        assert section.updated_at == original_updated_at

        # Check no domain events were published
        events = section.get_domain_events()
        assert len(events) == 0

    def test_update_name_success(self):
        """Test successful name update."""
        # Arrange
        dto = CreateSectionDto(name="Original Name", description="Test")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        old_name = section.name
        old_slug = section.slug

        # Act
        section.update_name("Updated Name")

        # Assert
        assert section.name == "Updated Name"
        assert section.slug != old_slug
        assert section.updated_at is not None

        # Check domain events
        events = section.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], SectionNameUpdated)
        assert events[0].aggregate_id == section.id
        assert events[0].old_name == old_name
        assert events[0].new_name == "Updated Name"
        assert events[0].old_slug == old_slug
        assert events[0].new_slug == section.slug

    def test_update_name_same_name(self):
        """Test updating name with the same name (no change)."""
        # Arrange
        dto = CreateSectionDto(name="Test Name", description="Test")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        original_updated_at = section.updated_at
        original_slug = section.slug

        # Act
        section.update_name("Test Name")

        # Assert
        assert section.name == "Test Name"
        assert section.slug == original_slug
        assert section.updated_at == original_updated_at

        # Check no domain events were published
        events = section.get_domain_events()
        assert len(events) == 0

    def test_update_description_success(self):
        """Test successful description update."""
        # Arrange
        dto = CreateSectionDto(name="Test", description="Original Description")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        old_description = section.description

        # Act
        section.update_description("Updated Description")

        # Assert
        assert section.description == "Updated Description"
        assert section.updated_at is not None

        # Check domain events
        events = section.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], SectionDescriptionUpdated)
        assert events[0].aggregate_id == section.id
        assert events[0].old_description == old_description
        assert events[0].new_description == "Updated Description"

    def test_update_description_same_description(self):
        """Test updating description with the same description (no change)."""
        # Arrange
        dto = CreateSectionDto(name="Test", description="Test Description")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event
        original_updated_at = section.updated_at

        # Act
        section.update_description("Test Description")

        # Assert
        assert section.description == "Test Description"
        assert section.updated_at == original_updated_at

        # Check no domain events were published
        events = section.get_domain_events()
        assert len(events) == 0

    def test_multiple_operations_sequence(self):
        """Test a sequence of multiple operations."""
        # Arrange
        dto = CreateSectionDto(name="Initial Name", description="Initial Description")
        section = SectionEntity.create(dto)
        section.clear_domain_events()  # Clear creation event

        # Act - Perform multiple operations
        section.update_name("New Name")
        section.update_description("New Description")
        section.make_inactive()
        section.make_active()

        # Assert
        assert section.name == "New Name"
        assert section.description == "New Description"
        assert section.status == SectionStatus.ACTIVE
        assert section.updated_at is not None

        # Check all domain events were published
        events = section.get_domain_events()
        assert len(events) == 4
        assert isinstance(events[0], SectionNameUpdated)
        assert isinstance(events[1], SectionDescriptionUpdated)
        assert isinstance(events[2], SectionDeactivated)
        assert isinstance(events[3], SectionActivated)

    def test_validation_called_on_operations(self):
        """Test that validation is called during operations."""
        # Arrange
        dto = CreateSectionDto(name="Test", description="Test")
        section = SectionEntity.create(dto)

        # Act & Assert - These should not raise validation errors
        section.make_inactive()
        section.make_active()
        section.update_name("New Name")
        section.update_description("New Description")

        # All operations completed successfully
        assert section.name == "New Name"
        assert section.description == "New Description"
        assert section.status == SectionStatus.ACTIVE

    def test_create_section_dto_validation(self):
        """Test CreateSectionDto validation."""
        # Valid DTO
        dto = CreateSectionDto(name="Valid Name", description="Valid Description")
        assert dto.name == "Valid Name"
        assert dto.description == "Valid Description"

        # Test with empty strings (should be allowed by Pydantic)
        dto_empty = CreateSectionDto(name="", description="")
        assert dto_empty.name == ""
        assert dto_empty.description == ""

    def test_section_entity_immutable_id(self):
        """Test that section ID doesn't change after creation."""
        # Arrange
        dto = CreateSectionDto(name="Test", description="Test")
        section = SectionEntity.create(dto)
        original_id = section.id

        # Act - Perform various operations
        section.update_name("New Name")
        section.make_inactive()
        section.make_active()
        section.update_description("New Description")

        # Assert - ID should remain the same
        assert section.id == original_id

    def test_domain_events_accumulate(self):
        """Test that domain events accumulate and can be retrieved."""
        # Arrange
        dto = CreateSectionDto(name="Test", description="Test")
        section = SectionEntity.create(dto)

        # Act - Perform operations without clearing events
        section.update_name("New Name")
        section.make_inactive()

        # Assert - All events should be present
        events = section.get_domain_events()
        assert len(events) == 3  # Created, NameUpdated, Deactivated
        assert isinstance(events[0], SectionCreated)
        assert isinstance(events[1], SectionNameUpdated)
        assert isinstance(events[2], SectionDeactivated)

    def test_clear_domain_events(self):
        """Test clearing domain events."""
        # Arrange
        dto = CreateSectionDto(name="Test", description="Test")
        section = SectionEntity.create(dto)

        # Act
        events_before = section.get_domain_events()
        section.clear_domain_events()
        events_after = section.get_domain_events()

        # Assert
        assert len(events_before) == 1
        assert len(events_after) == 0
