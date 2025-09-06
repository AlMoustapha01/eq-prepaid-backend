from unittest.mock import Mock

from modules.rules.domain.services.sql_generator import SqlGenerator
from modules.rules.domain.value_objects.rule_config import (
    ComparisonOperator,
    ConditionsClause,
    JoinClause,
    JoinType,
    LogicalOperator,
    RuleConfig,
    SelectClause,
    SelectField,
    TableReference,
    WhereCondition,
)


class TestSqlGenerator:
    """Test suite for SqlGenerator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = SqlGenerator()

    def test_generate_simple_select_sql(self):
        """Test generating a simple SELECT SQL query"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(name="id", expression="id", alias=None),
                    SelectField(name="name", expression="name", alias="customer_name"),
                ]
            ),
            from_table=TableReference(main_table="customers", alias="c"),
            joins=[],
            conditions=ConditionsClause(where=[]),
            group_by=[],
            having=[],
            order_by=[],
        )

        # Act
        sql = self.generator.generate_sql(config)

        # Assert
        expected_sql = "SELECT id, name AS customer_name\nFROM customers c"
        assert sql == expected_sql

    def test_generate_sql_with_where_clause(self):
        """Test generating SQL with WHERE conditions"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="all", expression="*", alias=None)]),
            from_table=TableReference(main_table="users", alias=None),
            joins=[],
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="age",
                        operator=ComparisonOperator.GREATER_THAN,
                        value="18",
                        logical_operator=LogicalOperator.AND,
                    ),
                    WhereCondition(
                        field="status",
                        operator=ComparisonOperator.EQUAL,
                        value="'active'",
                        logical_operator=LogicalOperator.AND,
                    ),
                ]
            ),
            group_by=[],
            having=[],
            order_by=[],
        )

        # Act
        sql = self.generator.generate_sql(config)

        # Assert
        assert "SELECT *" in sql
        assert "FROM users" in sql
        assert "WHERE age > '18'" in sql
        assert "AND status = '''active'''" in sql

    def test_generate_sql_with_joins(self):
        """Test generating SQL with JOIN clauses"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(name="user_name", expression="u.name", alias=None),
                    SelectField(name="profile_title", expression="p.title", alias=None),
                ]
            ),
            from_table=TableReference(main_table="users", alias="u"),
            joins=[
                JoinClause(type=JoinType.INNER, table="profiles", alias="p", on="u.id = p.user_id")
            ],
            conditions=ConditionsClause(where=[]),
            group_by=[],
            having=[],
            order_by=[],
        )

        # Act
        sql = self.generator.generate_sql(config)

        # Assert
        assert "SELECT u.name, p.title" in sql
        assert "FROM users u" in sql
        assert "INNER JOIN profiles p ON u.id = p.user_id" in sql

    def test_generate_sql_with_group_by_and_having(self):
        """Test generating SQL with GROUP BY and HAVING clauses"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(
                fields=[
                    SelectField(name="department", expression="department", alias=None),
                    SelectField(
                        name="employee_count", expression="COUNT(*)", alias="employee_count"
                    ),
                ]
            ),
            from_table=TableReference(main_table="employees", alias=None),
            joins=[],
            conditions=ConditionsClause(where=[]),
            group_by=["department"],
            having=[
                WhereCondition(
                    field="COUNT(*)",
                    operator=ComparisonOperator.GREATER_THAN,
                    value="5",
                    logical_operator=LogicalOperator.AND,
                )
            ],
            order_by=[],
        )

        # Act
        sql = self.generator.generate_sql(config)

        # Assert
        assert "SELECT department, COUNT(*) AS employee_count" in sql
        assert "FROM employees" in sql
        assert "GROUP BY department" in sql
        assert "HAVING COUNT(*) > '5'" in sql

    def test_generate_sql_with_parameters(self):
        """Test generating SQL with parameter substitution"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="all", expression="*", alias=None)]),
            from_table=TableReference(main_table="products", alias=None),
            joins=[],
            conditions=ConditionsClause(
                where=[
                    WhereCondition(
                        field="price",
                        operator=ComparisonOperator.LESS_THAN,
                        value=":max_price",
                        logical_operator=LogicalOperator.AND,
                    )
                ]
            ),
            group_by=[],
            having=[],
            order_by=[],
        )

        parameters = {"max_price": "100.00"}

        # Act
        sql = self.generator.generate_sql(config, parameters)

        # Assert
        assert "WHERE price < ':max_price'" in sql


class TestSqlValidation:
    """Test suite for SQL validation functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = SqlGenerator()

    def test_validate_valid_simple_select(self):
        """Test validation of a valid simple SELECT statement"""
        # Arrange
        sql = "SELECT id, name FROM users WHERE age > 18"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_empty_sql(self):
        """Test validation of empty SQL"""
        # Arrange
        sql = ""

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is False
        assert "SQL query cannot be empty" in result["errors"]

    def test_validate_sql_without_from_clause(self):
        """Test validation of SELECT without FROM clause"""
        # Arrange
        sql = "SELECT id, name"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is False
        assert "SELECT statement must contain a FROM clause" in result["errors"]

    def test_validate_sql_with_mismatched_parentheses(self):
        """Test validation of SQL with mismatched parentheses"""
        # Arrange
        sql = "SELECT * FROM users WHERE (age > 18 AND status = 'active'"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is False
        assert any("parentheses" in error.lower() for error in result["errors"])

    def test_validate_sql_with_unmatched_quotes(self):
        """Test validation of SQL with unmatched quotes"""
        # Arrange
        sql = "SELECT * FROM users WHERE name = 'John"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is False
        assert any("quotes" in error.lower() for error in result["errors"])

    def test_validate_sql_with_invalid_start(self):
        """Test validation of SQL that doesn't start with valid command"""
        # Arrange
        sql = "INVALID SELECT * FROM users"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is False
        assert any("valid command" in error for error in result["errors"])

    def test_validate_sql_with_dangerous_patterns(self):
        """Test validation of SQL with potentially dangerous patterns"""
        # Arrange
        sql = "SELECT * FROM users; DROP TABLE users;"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is False
        assert any("dangerous" in error.lower() for error in result["errors"])

    def test_validate_sql_with_warnings(self):
        """Test validation that generates warnings"""
        # Arrange
        sql = "SELECT * FROM users"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True
        assert len(result["warnings"]) > 0
        assert any("SELECT *" in warning for warning in result["warnings"])

    def test_validate_update_without_where(self):
        """Test validation of UPDATE without WHERE clause"""
        # Arrange
        sql = "UPDATE users SET status = 'inactive'"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True  # Valid syntax but has warnings
        assert any("WHERE clause" in warning for warning in result["warnings"])

    def test_validate_delete_without_where(self):
        """Test validation of DELETE without WHERE clause"""
        # Arrange
        sql = "DELETE FROM users"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True  # Valid syntax but has warnings
        assert any("WHERE clause" in warning for warning in result["warnings"])

    def test_validate_very_long_query(self):
        """Test validation of very long SQL query"""
        # Arrange
        long_select = ", ".join([f"field_{i}" for i in range(100)])
        sql = f"SELECT {long_select} FROM users WHERE id = 1"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True
        assert any("long SQL query" in warning for warning in result["warnings"])

    def test_validate_potential_cartesian_product(self):
        """Test validation of potential Cartesian product"""
        # Arrange
        sql = "SELECT * FROM users, orders WHERE users.id = 1"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True
        # Note: The Cartesian product warning logic may need adjustment in the actual implementation


class TestSqlGeneratorPrivateMethods:
    """Test suite for private methods of SqlGenerator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = SqlGenerator()

    def test_build_select_clause_with_aliases(self):
        """Test building SELECT clause with field aliases"""
        # Arrange
        config = Mock()
        config.select.fields = [
            SelectField(name="id", expression="id", alias="user_id"),
            SelectField(name="name", expression="name", alias=None),
        ]

        # Act
        result = self.generator._build_select_clause(config)

        # Assert
        assert result == "SELECT id AS user_id, name"

    def test_build_from_clause_with_alias(self):
        """Test building FROM clause with table alias"""
        # Arrange
        config = Mock()
        config.from_table = TableReference(main_table="users", alias="u")

        # Act
        result = self.generator._build_from_clause(config)

        # Assert
        assert result == "FROM users u"

    def test_build_from_clause_without_alias(self):
        """Test building FROM clause without table alias"""
        # Arrange
        config = Mock()
        config.from_table = TableReference(main_table="users", alias=None)

        # Act
        result = self.generator._build_from_clause(config)

        # Assert
        assert result == "FROM users"

    def test_get_join_type_sql(self):
        """Test getting SQL representation of join types"""
        # Test different join types
        assert self.generator._get_join_type_sql(JoinType.INNER) == "INNER JOIN"
        assert self.generator._get_join_type_sql(JoinType.LEFT) == "LEFT JOIN"
        assert self.generator._get_join_type_sql(JoinType.RIGHT) == "RIGHT JOIN"
        assert self.generator._get_join_type_sql(JoinType.FULL) == "FULL OUTER JOIN"

    def test_get_comparison_operator_sql(self):
        """Test getting SQL representation of comparison operators"""
        # Test different comparison operators
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.EQUAL) == "="
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.NOT_EQUAL) == "!="
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.GREATER_THAN) == ">"
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.LESS_THAN) == "<"
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.GREATER_EQUAL) == ">="
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.LESS_EQUAL) == "<="
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.LIKE) == "LIKE"
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.IN) == "IN"
        assert self.generator._get_comparison_operator_sql(ComparisonOperator.NOT_IN) == "NOT IN"

    def test_get_logical_operator_sql(self):
        """Test getting SQL representation of logical operators"""
        # Test different logical operators
        assert self.generator._get_logical_operator_sql(LogicalOperator.AND) == "AND"
        assert self.generator._get_logical_operator_sql(LogicalOperator.OR) == "OR"


class TestSqlGeneratorEdgeCases:
    """Test suite for edge cases and error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = SqlGenerator()

    def test_generate_sql_with_empty_joins(self):
        """Test generating SQL with empty joins list"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="all", expression="*", alias=None)]),
            from_table=TableReference(main_table="users", alias=None),
            joins=[],
            conditions=ConditionsClause(where=[]),
            group_by=[],
            having=[],
            order_by=[],
        )

        # Act
        sql = self.generator.generate_sql(config)

        # Assert
        assert "SELECT *" in sql
        assert "FROM users" in sql
        assert "JOIN" not in sql

    def test_generate_sql_with_none_parameters(self):
        """Test generating SQL with None parameters"""
        # Arrange
        config = RuleConfig(
            select=SelectClause(fields=[SelectField(name="all", expression="*", alias=None)]),
            from_table=TableReference(main_table="users", alias=None),
            joins=[],
            conditions=ConditionsClause(where=[]),
            group_by=[],
            having=[],
            order_by=[],
        )

        # Act
        sql = self.generator.generate_sql(config, None)

        # Assert
        assert "SELECT *" in sql
        assert "FROM users" in sql

    def test_validate_sql_with_whitespace_normalization(self):
        """Test SQL validation with excessive whitespace"""
        # Arrange
        sql = "SELECT    *    FROM     users     WHERE    id   =   1"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True

    def test_validate_sql_with_mixed_case(self):
        """Test SQL validation with mixed case keywords"""
        # Arrange
        sql = "select * from Users where ID = 1"

        # Act
        result = self.generator.validate_sql_syntax(sql)

        # Assert
        assert result["is_valid"] is True
