import pytest

from modules.rules.domain.value_objects.rule_config import (
    ComparisonOperator,
    ConditionsClause,
    JoinClause,
    JoinType,
    LogicalOperator,
    OrderByClause,
    Parameter,
    ParameterType,
    RuleConfig,
    SelectClause,
    SelectField,
    SortDirection,
    TableReference,
    WhereCondition,
)


class TestRuleConfigToSql:
    """Unit tests for RuleConfig.to_sql method"""

    @pytest.fixture
    def simple_rule_config(self) -> RuleConfig:
        """Creates a simple RuleConfig for testing"""
        return RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(name="id", expression="t.id"),
                    SelectField(name="amount", expression="t.amount", alias="total_amount"),
                ]
            ),
            from_table=TableReference(main_table="transactions", alias="t"),
        )

    @pytest.fixture
    def complex_rule_config(self) -> RuleConfig:
        """Creates a complex RuleConfig for testing"""
        return RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(name="total_amount", expression="SUM(t.amount)", alias="total_ca"),
                    SelectField(name="offer_id", expression="t.offer_id", alias="offer"),
                ]
            ),
            from_table=TableReference(main_table="transactions", alias="t"),
            joins=[
                JoinClause(type=JoinType.INNER, table="offers", alias="o", on="t.offer_id = o.id"),
                JoinClause(
                    type=JoinType.LEFT, table="customers", alias="c", on="t.customer_id = c.id"
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
                        field="t.created_at",
                        operator=ComparisonOperator.GREATER_EQUAL,
                        value="{{start_date}}",
                        logical_operator=None,
                    ),
                ]
            ),
            group_by=["t.offer_id"],
            having=[
                WhereCondition(
                    field="SUM(t.amount)",
                    operator=ComparisonOperator.GREATER_THAN,
                    value=1000,
                )
            ],
            order_by=[
                OrderByClause(field="total_ca", direction=SortDirection.DESC),
                OrderByClause(field="offer", direction=SortDirection.ASC),
            ],
            parameters={
                "start_date": Parameter(
                    type=ParameterType.DATE,
                    required=True,
                    description="Start date for CA calculation",
                )
            },
        )

    def test_simple_to_sql(self, simple_rule_config: RuleConfig):
        """Test to_sql method with simple configuration"""
        # Act
        sql = simple_rule_config.to_sql()

        # Assert
        expected_lines = ["SELECT t.id, t.amount AS total_amount", "FROM transactions t"]

        for line in expected_lines:
            assert line in sql

        # Verify it's valid SQL structure
        assert sql.startswith("SELECT")
        assert "FROM transactions t" in sql

    def test_complex_to_sql_without_parameters(self, complex_rule_config: RuleConfig):
        """Test to_sql method with complex configuration but no parameter substitution"""
        # Act
        sql = complex_rule_config.to_sql()

        # Assert
        expected_components = [
            "SELECT SUM(t.amount) AS total_ca, t.offer_id AS offer",
            "FROM transactions t",
            "INNER JOIN offers o ON t.offer_id = o.id",
            "LEFT JOIN customers c ON t.customer_id = c.id",
            "WHERE t.status = 'COMPLETED'",
            "t.created_at >= {{start_date}}",
            "GROUP BY t.offer_id",
            "HAVING SUM(t.amount) > 1000",
            "ORDER BY total_ca DESC, offer ASC",
        ]

        for component in expected_components:
            assert component in sql

    def test_complex_to_sql_with_parameters(self, complex_rule_config: RuleConfig):
        """Test to_sql method with parameter substitution"""
        # Arrange
        parameters = {"start_date": "2024-01-01"}

        # Act
        sql = complex_rule_config.to_sql(parameters)

        # Assert
        # Parameter should be substituted
        assert "'2024-01-01'" in sql
        assert "{{start_date}}" not in sql

        # Other components should still be present
        expected_components = [
            "SELECT SUM(t.amount) AS total_ca, t.offer_id AS offer",
            "FROM transactions t",
            "WHERE t.status = 'COMPLETED'",
            "t.created_at >= '2024-01-01'",
        ]

        for component in expected_components:
            assert component in sql

    def test_to_sql_with_partial_parameters(self):
        """Test to_sql method with partial parameter substitution"""
        # Arrange - Create config with multiple parameters but only provide some
        config = RuleConfig(
            select=SelectClause(
                fields=[SelectField(name="total", expression="SUM(t.amount)", alias="total_amount")]
            ),
            from_table=TableReference(main_table="transactions", alias="t"),
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="t.created_at",
                        operator=ComparisonOperator.GREATER_EQUAL,
                        value="{{start_date}}",
                        logical_operator=LogicalOperator.AND,
                    ),
                    WhereCondition(
                        field="t.amount",
                        operator=ComparisonOperator.GREATER_THAN,
                        value="{{min_amount}}",
                        logical_operator=None,
                    ),
                ]
            ),
            parameters={
                "start_date": Parameter(
                    type=ParameterType.DATE,
                    required=True,
                    description="Start date for filtering",
                ),
                "min_amount": Parameter(
                    type=ParameterType.FLOAT,
                    required=False,
                    description="Minimum amount threshold",
                ),
            },
        )

        parameters = {"start_date": "2024-01-01"}  # Only provide start_date, not min_amount

        # Act
        sql = config.to_sql(parameters)

        # Assert
        # Provided parameter should be substituted
        assert "'2024-01-01'" in sql
        assert "{{start_date}}" not in sql

        # Non-provided parameter should remain as placeholder
        assert "{{min_amount}}" in sql

    def test_to_sql_with_different_parameter_types(self):
        """Test to_sql method with different parameter types"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="count", expression="COUNT(*)")]),
            from_table=TableReference(main_table="transactions"),
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="amount",
                        operator=ComparisonOperator.GREATER_THAN,
                        value="{{min_amount}}",  # Numeric
                    ),
                    WhereCondition(
                        field="status",
                        operator=ComparisonOperator.EQUAL,
                        value="{{status}}",  # String
                        logical_operator=LogicalOperator.AND,
                    ),
                    WhereCondition(
                        field="is_active",
                        operator=ComparisonOperator.EQUAL,
                        value="{{is_active}}",  # Boolean
                        logical_operator=LogicalOperator.AND,
                    ),
                ]
            ),
            parameters={
                "min_amount": Parameter(
                    type=ParameterType.FLOAT,
                    required=True,
                    description="Minimum amount threshold",
                ),
                "status": Parameter(
                    type=ParameterType.STRING,
                    required=True,
                    description="Transaction status",
                ),
                "is_active": Parameter(
                    type=ParameterType.BOOLEAN,
                    required=True,
                    description="Active status flag",
                ),
            },
        )

        parameters = {
            "min_amount": 100,
            "status": "COMPLETED",
            "is_active": True,
        }

        # Act
        sql = config.to_sql(parameters)

        # Assert
        assert "amount > 100" in sql
        assert "status = 'COMPLETED'" in sql
        assert "is_active = TRUE" in sql

    def test_to_sql_with_null_parameter(self):
        """Test to_sql method with null parameter value"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="count", expression="COUNT(*)")]),
            from_table=TableReference(main_table="transactions"),
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="description",
                        operator=ComparisonOperator.EQUAL,
                        value="{{description}}",
                    )
                ]
            ),
            parameters={
                "description": Parameter(
                    type=ParameterType.STRING,
                    required=False,
                    description="Transaction description",
                ),
            },
        )

        parameters = {"description": None}

        # Act
        sql = config.to_sql(parameters)

        # Assert
        assert "description = NULL" in sql

    def test_to_sql_with_list_parameter_for_in_operator(self):
        """Test to_sql method with list parameter for IN operator"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="count", expression="COUNT(*)")]),
            from_table=TableReference(main_table="transactions"),
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="status",
                        operator=ComparisonOperator.IN,
                        value="{{status_list}}",
                    )
                ]
            ),
            parameters={
                "status_list": Parameter(
                    type=ParameterType.STRING,
                    required=True,
                    description="List of valid statuses",
                ),
            },
        )

        parameters = {"status_list": ["COMPLETED", "PENDING", "FAILED"]}

        # Act
        sql = config.to_sql(parameters)

        # Assert
        # The current implementation treats the list as a string, so we check for that
        assert "status IN" in sql
        assert "COMPLETED" in sql
        assert "PENDING" in sql
        assert "FAILED" in sql

    def test_to_sql_validates_config_first(self):
        """Test that to_sql validates the configuration before generating SQL"""
        # Arrange - Create invalid config (no select fields)
        invalid_config = RuleConfig(
            select=SelectClause(fields=[]),  # Empty fields - invalid
            from_table=TableReference(main_table="transactions"),
        )

        # Act & Assert
        with pytest.raises(ValueError, match="RuleConfig must have at least one select field"):
            invalid_config.to_sql()

    def test_to_sql_returns_string(self, simple_rule_config: RuleConfig):
        """Test that to_sql returns a string"""
        # Act
        result = simple_rule_config.to_sql()

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

    def test_to_sql_with_empty_parameters_dict(self, complex_rule_config: RuleConfig):
        """Test to_sql method with empty parameters dictionary"""
        # Act
        sql = complex_rule_config.to_sql({})

        # Assert
        # Should work the same as no parameters
        assert "{{start_date}}" in sql
        assert "SELECT SUM(t.amount) AS total_ca" in sql

    def test_to_sql_consistency_with_sql_generator(self, complex_rule_config: RuleConfig):
        """Test that to_sql produces the same result as SqlGenerator.generate_sql"""
        # Arrange
        from modules.rules.domain.services.sql_generator import SqlGenerator

        parameters = {"start_date": "2024-01-01"}
        generator = SqlGenerator()

        # Act
        sql_from_config = complex_rule_config.to_sql(parameters)
        sql_from_generator = generator.generate_sql(complex_rule_config, parameters)

        # Assert
        assert sql_from_config == sql_from_generator
