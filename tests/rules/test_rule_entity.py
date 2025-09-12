from uuid import UUID, uuid4

import pytest
from pydantic_core import ValidationError

from modules.rules.domain.events.rule_events import (
    RuleArchived,
    RuleBalanceTypeUpdated,
    RuleConfigurationUpdated,
    RuleCreated,
    RuleDraftStarted,
    RuleNameUpdated,
    RuleProductionStarted,
    RuleProfileTypeUpdated,
    RuleToValidateStarted,
)
from modules.rules.domain.models.rule import CreateRuleDto, RuleEntity
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.domain.value_objects.rule_config.join_clause import JoinClause, JoinType
from modules.rules.domain.value_objects.rule_config.root import RuleConfig, TableReference
from modules.rules.domain.value_objects.rule_config.select_clause import SelectClause, SelectField
from modules.rules.domain.value_objects.rule_config.where_clause import (
    ComparisonOperator,
    ConditionsClause,
    LogicalOperator,
    WhereClause,
    WhereCondition,
)


class TestRuleEntity:
    """Unit tests for RuleEntity"""

    @pytest.fixture
    def valid_rule_config(self) -> RuleConfig:
        """Creates a valid RuleConfig for testing"""
        where_conditions = [
            WhereCondition(field="t.status", operator=ComparisonOperator.EQUAL, value="COMPLETED"),
            WhereCondition(
                field="t.created_at", operator=ComparisonOperator.GREATER_THAN, value="2023-01-01"
            ),
        ]
        where_clause = WhereClause(
            conditions=where_conditions, logical_operator=LogicalOperator.AND
        )

        return RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(expression="SUM(t.amount)", alias="total_ca"),
                    SelectField(expression="t.offer_id", alias="offer"),
                ]
            ),
            from_table=TableReference(name="transactions", alias="t"),
            joins=[
                JoinClause(type=JoinType.INNER, table="offers", alias="o", on="t.offer_id = o.id")
            ],
            conditions=ConditionsClause(where=[where_clause]),
            group_by=["t.offer_id"],
        )

    @pytest.fixture
    def valid_create_rule_dto(self, valid_rule_config: RuleConfig) -> CreateRuleDto:
        """Creates a valid CreateRuleDto for testing"""
        return CreateRuleDto(
            name="CA Calculation Rule",
            profile_type=ProfileType.PREPAID,
            balance_type=BalanceType.MAIN_BALANCE,
            database_table_name=["transactions", "offers"],
            section_id=uuid4(),
            config=valid_rule_config,
        )

    def test_create_rule_success(self, valid_create_rule_dto: CreateRuleDto):
        """Test successful rule creation"""
        # Act
        rule = RuleEntity.create(valid_create_rule_dto)

        # Assert
        assert rule.id is not None
        assert isinstance(rule.id, UUID)
        assert rule.name == valid_create_rule_dto.name
        assert rule.profile_type == valid_create_rule_dto.profile_type
        assert rule.balance_type == valid_create_rule_dto.balance_type
        assert rule.database_table_name == valid_create_rule_dto.database_table_name
        assert rule.section_id == valid_create_rule_dto.section_id
        assert rule.config == valid_create_rule_dto.config
        assert rule.created_at is not None
        assert rule.updated_at is not None
        assert rule.status == RuleStatus.DRAFT

        # Check domain events
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleCreated)
        assert events[0].aggregate_id == rule.id
        assert events[0].name == rule.name

    def test_create_rule_with_empty_name_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with empty name fails"""
        # Act & Assert - Pydantic validation happens at DTO level
        with pytest.raises(ValueError, match="Rule name cannot be empty"):
            CreateRuleDto(
                name="",
                profile_type=ProfileType.PREPAID,
                balance_type=BalanceType.MAIN_BALANCE,
                database_table_name=["transactions"],
                section_id=uuid4(),
                config=valid_create_rule_dto.config,
            )

    def test_create_rule_with_whitespace_name_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with whitespace-only name fails"""
        # Act & Assert - Pydantic validation happens at DTO level
        with pytest.raises(ValueError, match="Rule name cannot be empty"):
            CreateRuleDto(
                name="   ",
                profile_type=ProfileType.PREPAID,
                balance_type=BalanceType.MAIN_BALANCE,
                database_table_name=["transactions"],
                section_id=uuid4(),
                config=valid_create_rule_dto.config,
            )

    def test_create_rule_with_empty_database_tables_fails(
        self, valid_create_rule_dto: CreateRuleDto
    ):
        """Test that creating a rule with no database tables fails"""
        # Act & Assert - Pydantic validation happens at DTO level
        with pytest.raises(ValueError, match="At least one database table is required"):
            CreateRuleDto(
                name="Test Rule",
                profile_type=ProfileType.PREPAID,
                balance_type=BalanceType.MAIN_BALANCE,
                database_table_name=[],
                section_id=uuid4(),
                config=valid_create_rule_dto.config,
            )

    def test_create_rule_with_invalid_section_id_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with invalid section_id fails at DTO level"""
        # Act & Assert - DTO validation happens first
        with pytest.raises(ValidationError) as exc_info:
            CreateRuleDto(
                name="Test Rule",
                profile_type=ProfileType.PREPAID,
                balance_type=BalanceType.MAIN_BALANCE,
                database_table_name=["transactions"],
                section_id=None,
                config=valid_create_rule_dto.config,
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("section_id",) for error in errors)

    def test_create_rule_with_table_mismatch_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with table mismatch between config and database_table_name fails"""
        # Arrange - Remove 'offers' table from database_table_name but keep it in config
        dto = CreateRuleDto(
            name="Test Rule",
            profile_type=ProfileType.PREPAID,
            balance_type=BalanceType.MAIN_BALANCE,
            database_table_name=["transactions"],  # Missing 'offers' table
            section_id=uuid4(),
            config=valid_create_rule_dto.config,  # Config uses 'offers' table
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Tables {'offers'} used in configuration but not listed in database_table_name",
        ):
            RuleEntity.create(dto)

    def test_rule_config_validation_success(self, valid_rule_config: RuleConfig):
        """Test that valid RuleConfig passes validation"""
        # Act & Assert - Should not raise any exception
        # RuleConfig validation happens during construction
        assert valid_rule_config is not None

    def test_rule_config_without_select_fields_fails(self):
        """Test that RuleConfig without select fields fails validation"""
        # Act & Assert - Validation happens during SelectClause construction
        with pytest.raises(ValueError, match="SelectClause must have at least one field"):
            SelectClause(fields=[])  # Empty fields

    def test_rule_config_without_main_table_fails(self):
        """Test that RuleConfig without main table fails validation"""
        # Act & Assert - Validation happens during TableReference construction
        with pytest.raises(ValueError, match="Table name cannot be empty"):
            TableReference(name="")  # Empty main table

    def test_create_rule_with_complex_config(self):
        """Test creating a rule with complex configuration"""
        # Arrange
        complex_config = RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(
                        expression="SUM(CASE WHEN b.balance_type = 'MAIN_BALANCE' THEN t.amount ELSE 0 END)",
                        alias="ca_solde_principal",
                    ),
                    SelectField(
                        expression="SUM(CASE WHEN b.balance_type = 'CRED' THEN t.amount ELSE 0 END)",
                        alias="ca_credit",
                    ),
                ]
            ),
            from_table=TableReference(name="transactions", alias="t"),
            joins=[
                JoinClause(type=JoinType.INNER, table="offers", alias="o", on="t.offer_id = o.id"),
                JoinClause(
                    type=JoinType.INNER,
                    table="balance_operations",
                    alias="b",
                    on="t.id = b.transaction_id",
                ),
            ],
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="t.status", operator=ComparisonOperator.EQUAL, value="COMPLETED"
                    ),
                    WhereCondition(
                        field="o.profile_type",
                        operator=ComparisonOperator.EQUAL,
                        value="{{profile_type}}",
                    ),
                ]
            ),
            group_by=["o.id"],
        )

        dto = CreateRuleDto(
            name="Complex CA Rule",
            profile_type=ProfileType.HYBRID,
            balance_type=BalanceType.CRED,
            database_table_name=["transactions", "offers", "balance_operations"],
            section_id=uuid4(),
            config=complex_config,
        )

        # Act
        rule = RuleEntity.create(dto)

        # Assert
        assert rule is not None
        assert rule.name == "Complex CA Rule"
        assert rule.profile_type == ProfileType.HYBRID
        assert rule.balance_type == BalanceType.CRED
        assert len(rule.config.joins) == 2
        assert len(rule.config.select.fields) == 2

    # ========================================
    # State Machine Transition Tests
    # ========================================

    def test_move_to_validation_from_draft(self, valid_create_rule_dto: CreateRuleDto):
        """Test moving rule from DRAFT to TO_VALIDATE"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()

        # Act
        rule.move_to_validation()

        # Assert
        assert rule.status == RuleStatus.TO_VALIDATE
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleToValidateStarted)

    def test_move_to_production_from_validation(self, valid_create_rule_dto: CreateRuleDto):
        """Test moving rule from TO_VALIDATE to IN_PRODUCTION"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.move_to_validation()
        rule.clear_domain_events()

        # Act
        rule.move_to_production()

        # Assert
        assert rule.status == RuleStatus.IN_PRODUCTION
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleProductionStarted)

    def test_move_to_archived_from_production(self, valid_create_rule_dto: CreateRuleDto):
        """Test moving rule from IN_PRODUCTION to ARCHIVED"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.move_to_validation()
        rule.move_to_production()
        rule.clear_domain_events()

        # Act
        rule.move_to_archived()

        # Assert
        assert rule.status == RuleStatus.ARCHIVED
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleArchived)

    def test_move_to_draft_from_validation(self, valid_create_rule_dto: CreateRuleDto):
        """Test moving rule back from TO_VALIDATE to DRAFT"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.move_to_validation()
        rule.clear_domain_events()

        # Act
        rule.move_to_draft()

        # Assert
        assert rule.status == RuleStatus.DRAFT
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleDraftStarted)

    def test_invalid_transition_draft_to_production_fails(
        self, valid_create_rule_dto: CreateRuleDto
    ):
        """Test that invalid transition from DRAFT to IN_PRODUCTION fails"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)

        # Act & Assert
        with pytest.raises(
            ValueError, match="Invalid transition: RuleStatus.DRAFT → RuleStatus.IN_PRODUCTION"
        ):
            rule.move_to_production()

    def test_invalid_transition_production_to_draft_fails(
        self, valid_create_rule_dto: CreateRuleDto
    ):
        """Test that invalid transition from IN_PRODUCTION to DRAFT fails"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.move_to_validation()
        rule.move_to_production()

        # Act & Assert
        with pytest.raises(
            ValueError, match="Invalid transition: RuleStatus.IN_PRODUCTION → RuleStatus.DRAFT"
        ):
            rule.move_to_draft()

    def test_invalid_transition_archived_to_any_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that no transitions are allowed from ARCHIVED status"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.move_to_validation()
        rule.move_to_production()
        rule.move_to_archived()

        # Act & Assert
        with pytest.raises(
            ValueError, match="Invalid transition: RuleStatus.ARCHIVED → RuleStatus.DRAFT"
        ):
            rule.move_to_draft()

    def test_no_change_when_same_status(self, valid_create_rule_dto: CreateRuleDto):
        """Test that no change occurs when moving to same status"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        original_updated_at = rule.updated_at

        # Act
        rule.move_to_draft()  # Already in DRAFT

        # Assert
        assert rule.status == RuleStatus.DRAFT
        assert rule.updated_at == original_updated_at
        events = rule.get_domain_events()
        assert len(events) == 0

    # ========================================
    # Update Methods Tests
    # ========================================

    def test_update_name_success(self, valid_create_rule_dto: CreateRuleDto):
        """Test successful name update"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        old_name = rule.name

        # Act
        rule.update_name("Updated Rule Name")

        # Assert
        assert rule.name == "Updated Rule Name"
        assert rule.updated_at is not None
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleNameUpdated)
        assert events[0].old_name == old_name
        assert events[0].new_name == "Updated Rule Name"

    def test_update_name_same_name_no_change(self, valid_create_rule_dto: CreateRuleDto):
        """Test that updating to same name causes no change"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        original_name = rule.name
        original_updated_at = rule.updated_at

        # Act
        rule.update_name(original_name)

        # Assert
        assert rule.name == original_name
        assert rule.updated_at == original_updated_at
        events = rule.get_domain_events()
        assert len(events) == 0

    def test_update_profile_type_success(self, valid_create_rule_dto: CreateRuleDto):
        """Test successful profile type update"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        old_profile_type = rule.profile_type

        # Act
        rule.update_profile_type(ProfileType.HYBRID)

        # Assert
        assert rule.profile_type == ProfileType.HYBRID
        assert rule.updated_at is not None
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleProfileTypeUpdated)
        assert events[0].old_profile_type == old_profile_type.value
        assert events[0].new_profile_type == ProfileType.HYBRID.value

    def test_update_profile_type_same_type_no_change(self, valid_create_rule_dto: CreateRuleDto):
        """Test that updating to same profile type causes no change"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        original_profile_type = rule.profile_type
        original_updated_at = rule.updated_at

        # Act
        rule.update_profile_type(original_profile_type)

        # Assert
        assert rule.profile_type == original_profile_type
        assert rule.updated_at == original_updated_at
        events = rule.get_domain_events()
        assert len(events) == 0

    def test_update_balance_type_success(self, valid_create_rule_dto: CreateRuleDto):
        """Test successful balance type update"""
        # Arrange
        valid_create_rule_dto.profile_type = ProfileType.HYBRID  # Allow CRED balance
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        old_balance_type = rule.balance_type

        # Act
        rule.update_balance_type(BalanceType.CRED)

        # Assert
        assert rule.balance_type == BalanceType.CRED
        assert rule.updated_at is not None
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleBalanceTypeUpdated)
        assert events[0].old_balance_type == old_balance_type.value
        assert events[0].new_balance_type == BalanceType.CRED.value

    def test_update_balance_type_same_type_no_change(self, valid_create_rule_dto: CreateRuleDto):
        """Test that updating to same balance type causes no change"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()
        original_balance_type = rule.balance_type
        original_updated_at = rule.updated_at

        # Act
        rule.update_balance_type(original_balance_type)

        # Assert
        assert rule.balance_type == original_balance_type
        assert rule.updated_at == original_updated_at
        events = rule.get_domain_events()
        assert len(events) == 0

    def test_update_configuration_success(self, valid_create_rule_dto: CreateRuleDto):
        """Test successful configuration update"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.clear_domain_events()

        # Create new config
        new_config = RuleConfig(
            select=SelectClause(fields=[SelectField(expression="COUNT(*)", alias="total_count")]),
            from_table=TableReference(name="transactions", alias="t"),
        )

        # Act
        rule.update_configuration(new_config)

        # Assert
        assert rule.config == new_config
        assert rule.updated_at is not None
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], RuleConfigurationUpdated)
        assert events[0].rule_name == rule.name

    # ========================================
    # Validation Tests
    # ========================================

    def test_prepaid_profile_with_cred_balance_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that PREPAID profile with CRED balance fails validation at entity level"""
        # Arrange - Create a valid DTO first
        dto = CreateRuleDto(
            name="Test Rule",
            profile_type=ProfileType.PREPAID,
            balance_type=BalanceType.CRED,
            database_table_name=["transactions"],
            section_id=uuid4(),
            config=valid_create_rule_dto.config,
        )

        # Act & Assert - Entity validation should catch this
        with pytest.raises(ValueError, match="Prepaid profile can only have main balance"):
            RuleEntity.create(dto)

    def test_long_name_fails_validation(self, valid_create_rule_dto: CreateRuleDto):
        """Test that rule name longer than 255 characters fails"""
        # Act & Assert - Pydantic validation happens at DTO level
        with pytest.raises(ValueError, match="Rule name too long"):
            CreateRuleDto(
                name="x" * 256,
                profile_type=ProfileType.PREPAID,
                balance_type=BalanceType.MAIN_BALANCE,
                database_table_name=["transactions"],
                section_id=uuid4(),
                config=valid_create_rule_dto.config,
            )

    # ========================================
    # Domain Events Tests
    # ========================================

    def test_multiple_operations_accumulate_events(self, valid_create_rule_dto: CreateRuleDto):
        """Test that multiple operations accumulate domain events"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)

        # Act - Perform multiple operations without clearing events
        rule.update_name("New Name")
        rule.move_to_validation()
        rule.update_profile_type(ProfileType.HYBRID)

        # Assert
        events = rule.get_domain_events()
        assert len(events) == 4  # Created, NameUpdated, ToValidate, ProfileTypeUpdated
        assert isinstance(events[0], RuleCreated)
        assert isinstance(events[1], RuleNameUpdated)
        assert isinstance(events[2], RuleToValidateStarted)
        assert isinstance(events[3], RuleProfileTypeUpdated)

    def test_clear_domain_events(self, valid_create_rule_dto: CreateRuleDto):
        """Test clearing domain events"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        rule.update_name("New Name")

        # Act
        events_before = rule.get_domain_events()
        rule.clear_domain_events()
        events_after = rule.get_domain_events()

        # Assert
        assert len(events_before) == 2
        assert len(events_after) == 0

    def test_rule_entity_immutable_id(self, valid_create_rule_dto: CreateRuleDto):
        """Test that rule ID doesn't change after operations"""
        # Arrange
        rule = RuleEntity.create(valid_create_rule_dto)
        original_id = rule.id

        # Act - Perform various operations
        rule.update_name("New Name")
        rule.move_to_validation()
        rule.update_profile_type(ProfileType.HYBRID)
        rule.move_to_draft()

        # Assert - ID should remain the same
        assert rule.id == original_id
