from uuid import UUID, uuid4

import pytest

from modules.rules.domain.models.rule import CreateRuleDto, RuleEntity
from modules.rules.domain.value_objects.enums import BalanceType, ProfileType
from modules.rules.domain.value_objects.rule_config import (
    ComparisonOperator,
    ConditionsClause,
    JoinClause,
    JoinType,
    LogicalOperator,
    Parameter,
    ParameterType,
    RuleConfig,
    SelectClause,
    SelectField,
    TableReference,
    WhereCondition,
)


class TestRuleEntity:
    """Unit tests for RuleEntity"""

    @pytest.fixture
    def valid_rule_config(self) -> RuleConfig:
        """Creates a valid RuleConfig for testing"""
        return RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(name="total_amount", expression="SUM(t.amount)", alias="total_ca"),
                    SelectField(name="offer_id", expression="t.offer_id", alias="offer"),
                ]
            ),
            from_table=TableReference(main_table="transactions", alias="t"),
            joins=[
                JoinClause(type=JoinType.INNER, table="offers", alias="o", on="t.offer_id = o.id")
            ],
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="t.status",
                        operator=ComparisonOperator.EQUAL,
                        value="COMPLETED",
                        logical_operator=LogicalOperator.AND,
                    ),
                    WhereCondition(
                        field="t.created_at",
                        operator=ComparisonOperator.GREATER_EQUAL,
                        value="{{start_date}}",
                        logical_operator=None,
                    ),
                ]
            ),
            group_by=["t.offer_id"],
            parameters={
                "start_date": Parameter(
                    type=ParameterType.DATE,
                    required=True,
                    description="Start date for CA calculation",
                )
            },
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

    def test_create_rule_with_empty_name_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with empty name fails"""
        # Arrange
        valid_create_rule_dto.name = ""

        # Act & Assert
        with pytest.raises(ValueError, match="A rule must have a name"):
            RuleEntity.create(valid_create_rule_dto)

    def test_create_rule_with_whitespace_name_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with whitespace-only name fails"""
        # Arrange
        valid_create_rule_dto.name = "   "

        # Act & Assert
        with pytest.raises(ValueError, match="A rule must have a name"):
            RuleEntity.create(valid_create_rule_dto)

    def test_create_rule_with_empty_database_tables_fails(
        self, valid_create_rule_dto: CreateRuleDto
    ):
        """Test that creating a rule with no database tables fails"""
        # Arrange
        valid_create_rule_dto.database_table_name = []

        # Act & Assert
        with pytest.raises(ValueError, match="A rule must specify at least one database table"):
            RuleEntity.create(valid_create_rule_dto)

    def test_create_rule_with_invalid_section_id_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with invalid section_id fails"""
        # Arrange
        valid_create_rule_dto.section_id = None

        # Act & Assert
        with pytest.raises(ValueError, match="A rule must be associated with a section"):
            RuleEntity.create(valid_create_rule_dto)

    def test_create_rule_with_table_mismatch_fails(self, valid_create_rule_dto: CreateRuleDto):
        """Test that creating a rule with table mismatch between config and database_table_name fails"""
        # Arrange - Remove 'offers' table from database_table_name but keep it in config
        valid_create_rule_dto.database_table_name = ["transactions"]

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Table 'offers' used in configuration but not listed in database_table_name",
        ):
            RuleEntity.create(valid_create_rule_dto)

    def test_rule_config_validation_success(self, valid_rule_config: RuleConfig):
        """Test that valid RuleConfig passes validation"""
        # Act & Assert - Should not raise any exception
        valid_rule_config.validate()

    def test_rule_config_without_select_fields_fails(self):
        """Test that RuleConfig without select fields fails validation"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[]),  # Empty fields
            from_table=TableReference(main_table="transactions"),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="RuleConfig must have at least one select field"):
            config.validate()

    def test_rule_config_without_main_table_fails(self):
        """Test that RuleConfig without main table fails validation"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="test", expression="COUNT(*)")]),
            from_table=TableReference(main_table=""),  # Empty main table
        )

        # Act & Assert
        with pytest.raises(ValueError, match="RuleConfig must specify a main table"):
            config.validate()

    def test_rule_config_with_undefined_parameter_fails(self):
        """Test that RuleConfig with undefined parameter reference fails validation"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="test", expression="COUNT(*)")]),
            from_table=TableReference(main_table="transactions"),
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="created_at",
                        operator=ComparisonOperator.GREATER_EQUAL,
                        value="{{undefined_param}}",  # Parameter not defined
                    )
                ]
            ),
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Parameter 'undefined_param' is referenced but not defined"
        ):
            config.validate()

    def test_get_required_parameters(self, valid_rule_config: RuleConfig):
        """Test getting required parameters from RuleConfig"""
        # Act
        required_params = valid_rule_config.get_required_parameters()

        # Assert
        assert "start_date" in required_params
        assert len(required_params) == 1

    def test_get_table_names(self, valid_rule_config: RuleConfig):
        """Test getting all table names from RuleConfig"""
        # Act
        table_names = valid_rule_config.get_table_names()

        # Assert
        assert "transactions" in table_names
        assert "offers" in table_names
        assert len(table_names) == 2

    def test_create_rule_with_complex_config(self):
        """Test creating a rule with complex configuration"""
        # Arrange
        complex_config = RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(
                        name="ca_main_balance",
                        expression="SUM(CASE WHEN b.balance_type = 'MAIN_BALANCE' THEN t.amount ELSE 0 END)",
                        alias="ca_solde_principal",
                    ),
                    SelectField(
                        name="ca_credit",
                        expression="SUM(CASE WHEN b.balance_type = 'CRED' THEN t.amount ELSE 0 END)",
                        alias="ca_credit",
                    ),
                ]
            ),
            from_table=TableReference(main_table="transactions", alias="t"),
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
                        field="t.status",
                        operator=ComparisonOperator.EQUAL,
                        value="COMPLETED",
                        logical_operator=LogicalOperator.AND,
                    ),
                    WhereCondition(
                        field="o.profile_type",
                        operator=ComparisonOperator.EQUAL,
                        value="{{profile_type}}",
                        logical_operator=None,
                    ),
                ]
            ),
            group_by=["o.id"],
            parameters={
                "profile_type": Parameter(
                    type=ParameterType.ENUM,
                    values=["PREPAID", "HYBRID"],
                    required=True,
                    description="Customer profile type",
                )
            },
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
