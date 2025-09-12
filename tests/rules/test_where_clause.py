from datetime import date, datetime

import pytest

from src.modules.rules.domain.value_objects.rule_config.common import (
    NumericAggregation,
    SqlExpression,
)
from src.modules.rules.domain.value_objects.rule_config.where_clause import (
    ComparisonOperator,
    ConditionsClause,
    LogicalOperator,
    WhereClause,
    WhereCondition,
)


class TestWhereCondition:
    """Test cases for WhereCondition class"""

    def test_create_where_condition_equal(self):
        """Test creating WhereCondition with EQUAL operator"""
        condition = WhereCondition(field="user_id", operator=ComparisonOperator.EQUAL, value=123)

        assert condition.field == "user_id"
        assert condition.operator == ComparisonOperator.EQUAL
        assert condition.value == 123
        assert condition.to_sql() == "user_id = 123"

    def test_create_where_condition_string_value(self):
        """Test creating WhereCondition with string value"""
        condition = WhereCondition(
            field="username", operator=ComparisonOperator.EQUAL, value="john_doe"
        )

        assert condition.to_sql() == "username = 'john_doe'"

    def test_create_where_condition_with_quotes_in_string(self):
        """Test string value with quotes gets properly escaped"""
        condition = WhereCondition(
            field="name", operator=ComparisonOperator.EQUAL, value="O'Connor"
        )

        assert condition.to_sql() == "name = 'O''Connor'"

    def test_create_where_condition_not_equal(self):
        """Test NOT_EQUAL operator"""
        condition = WhereCondition(
            field="status", operator=ComparisonOperator.NOT_EQUAL, value="inactive"
        )

        assert condition.to_sql() == "status != 'inactive'"

    def test_create_where_condition_greater_than(self):
        """Test GREATER_THAN operator"""
        condition = WhereCondition(field="age", operator=ComparisonOperator.GREATER_THAN, value=18)

        assert condition.to_sql() == "age > 18"

    def test_create_where_condition_less_equal(self):
        """Test LESS_EQUAL operator"""
        condition = WhereCondition(
            field="price", operator=ComparisonOperator.LESS_EQUAL, value=99.99
        )

        assert condition.to_sql() == "price <= 99.99"

    def test_create_where_condition_like(self):
        """Test LIKE operator"""
        condition = WhereCondition(
            field="email", operator=ComparisonOperator.LIKE, value="%@gmail.com"
        )

        assert condition.to_sql() == "email LIKE '%@gmail.com'"

    def test_create_where_condition_in(self):
        """Test IN operator with list of values"""
        condition = WhereCondition(
            field="category", operator=ComparisonOperator.IN, value=["A", "B", "C"]
        )

        assert condition.to_sql() == "category IN ('A', 'B', 'C')"

    def test_create_where_condition_not_in(self):
        """Test NOT_IN operator"""
        condition = WhereCondition(
            field="status", operator=ComparisonOperator.NOT_IN, value=["deleted", "archived"]
        )

        assert condition.to_sql() == "status NOT IN ('deleted', 'archived')"

    def test_create_where_condition_between(self):
        """Test BETWEEN operator"""
        condition = WhereCondition(field="age", operator=ComparisonOperator.BETWEEN, value=[18, 65])

        assert condition.to_sql() == "age BETWEEN 18 AND 65"

    def test_create_where_condition_is_null(self):
        """Test IS_NULL operator"""
        condition = WhereCondition(
            field="deleted_at", operator=ComparisonOperator.IS_NULL, value=None
        )

        assert condition.to_sql() == "deleted_at IS NULL"

    def test_create_where_condition_is_not_null(self):
        """Test IS_NOT_NULL operator"""
        condition = WhereCondition(
            field="email", operator=ComparisonOperator.IS_NOT_NULL, value=None
        )

        assert condition.to_sql() == "email IS NOT NULL"

    def test_where_condition_with_datetime(self):
        """Test WhereCondition with datetime value"""
        dt = datetime(2023, 12, 25, 10, 30, 0, tzinfo=timezone.utc)
        condition = WhereCondition(
            field="created_at", operator=ComparisonOperator.GREATER_THAN, value=dt
        )

        assert condition.to_sql() == "created_at > '2023-12-25 10:30:00+00:00'"

    def test_where_condition_with_date(self):
        """Test WhereCondition with date value"""
        d = date(2023, 12, 25)
        condition = WhereCondition(field="birth_date", operator=ComparisonOperator.EQUAL, value=d)

        assert condition.to_sql() == "birth_date = '2023-12-25'"

    def test_where_condition_with_boolean(self):
        """Test WhereCondition with boolean value"""
        condition = WhereCondition(field="is_active", operator=ComparisonOperator.EQUAL, value=True)

        assert condition.to_sql() == "is_active = TRUE"

    def test_where_condition_with_sql_expression_field(self):
        """Test WhereCondition with SqlExpression as field"""
        count_expr = SqlExpression(function=NumericAggregation.COUNT, args=["*"])
        condition = WhereCondition(
            field=count_expr, operator=ComparisonOperator.GREATER_THAN, value=10
        )

        assert condition.to_sql() == "COUNT('*') > 10"

    # Validation Tests
    def test_where_condition_validation_invalid_field_name(self):
        """Test validation fails for invalid field name"""
        with pytest.raises(ValueError, match="Invalid field name"):
            WhereCondition(field="123invalid", operator=ComparisonOperator.EQUAL, value="test")

    def test_where_condition_validation_is_null_with_value(self):
        """Test validation fails when IS_NULL has a value"""
        with pytest.raises(ValueError, match="cannot have a value"):
            WhereCondition(field="test", operator=ComparisonOperator.IS_NULL, value="not_null")

    def test_where_condition_validation_in_empty_list(self):
        """Test validation fails for IN with empty list"""
        with pytest.raises(ValueError, match="requires a non-empty list"):
            WhereCondition(field="test", operator=ComparisonOperator.IN, value=[])

    def test_where_condition_validation_between_wrong_count(self):
        """Test validation fails for BETWEEN with wrong number of values"""
        with pytest.raises(ValueError, match="BETWEEN requires exactly 2 values"):
            WhereCondition(field="test", operator=ComparisonOperator.BETWEEN, value=[1, 2, 3])

    def test_where_condition_validation_between_different_types(self):
        """Test validation fails for BETWEEN with different value types"""
        with pytest.raises(ValueError, match="BETWEEN values must have the same type"):
            WhereCondition(field="test", operator=ComparisonOperator.BETWEEN, value=[1, "2"])

    # Serialization Tests
    def test_where_condition_to_dict(self):
        """Test to_dict method"""
        condition = WhereCondition(field="user_id", operator=ComparisonOperator.EQUAL, value=123)
        result = condition.to_dict()

        expected = {"field": "user_id", "operator": "=", "value": 123}
        assert result == expected

    def test_where_condition_from_dict(self):
        """Test from_dict method"""
        data = {"field": "username", "operator": "=", "value": "john"}
        condition = WhereCondition.from_dict(data)

        assert condition.field == "username"
        assert condition.operator == ComparisonOperator.EQUAL
        assert condition.value == "john"


class TestWhereClause:
    """Test cases for WhereClause class"""

    def test_create_where_clause_single_condition(self):
        """Test WhereClause with single condition"""
        condition = WhereCondition(field="user_id", operator=ComparisonOperator.EQUAL, value=123)
        clause = WhereClause(conditions=[condition])

        assert clause.to_sql() == "user_id = 123"

    def test_create_where_clause_multiple_conditions_and(self):
        """Test WhereClause with multiple conditions using AND"""
        conditions = [
            WhereCondition(field="age", operator=ComparisonOperator.GREATER_THAN, value=18),
            WhereCondition(field="status", operator=ComparisonOperator.EQUAL, value="active"),
        ]
        clause = WhereClause(conditions=conditions, logical_operator=LogicalOperator.AND)

        expected_sql = "age > 18 AND status = 'active'"
        assert clause.to_sql() == expected_sql

    def test_create_where_clause_multiple_conditions_or(self):
        """Test WhereClause with multiple conditions using OR"""
        conditions = [
            WhereCondition(field="role", operator=ComparisonOperator.EQUAL, value="admin"),
            WhereCondition(field="role", operator=ComparisonOperator.EQUAL, value="moderator"),
        ]
        clause = WhereClause(conditions=conditions, logical_operator=LogicalOperator.OR)

        expected_sql = "role = 'admin' OR role = 'moderator'"
        assert clause.to_sql() == expected_sql

    def test_where_clause_validation_empty_conditions(self):
        """Test validation fails for empty conditions"""
        with pytest.raises(ValueError, match="WhereClause must have at least one condition"):
            WhereClause(conditions=[])

    def test_where_clause_nested(self):
        """Test nested WhereClause"""
        inner_conditions = [
            WhereCondition(field="age", operator=ComparisonOperator.GREATER_THAN, value=18),
            WhereCondition(field="age", operator=ComparisonOperator.LESS_THAN, value=65),
        ]
        inner_clause = WhereClause(
            conditions=inner_conditions, logical_operator=LogicalOperator.AND
        )

        outer_conditions = [
            WhereCondition(field="status", operator=ComparisonOperator.EQUAL, value="active"),
            inner_clause,
        ]
        outer_clause = WhereClause(
            conditions=outer_conditions, logical_operator=LogicalOperator.AND
        )

        expected_sql = "status = 'active' AND (age > 18 AND age < 65)"
        assert outer_clause.to_sql() == expected_sql


class TestConditionsClause:
    """Test cases for ConditionsClause class"""

    def test_conditions_clause_empty(self):
        """Test empty ConditionsClause"""
        clause = ConditionsClause()

        assert clause.to_sql() == ""

    def test_conditions_clause_single_condition(self):
        """Test ConditionsClause with single condition"""
        condition = WhereCondition(field="user_id", operator=ComparisonOperator.EQUAL, value=123)
        clause = ConditionsClause(where=[condition])

        assert clause.to_sql() == "WHERE user_id = 123"

    def test_conditions_clause_multiple_conditions(self):
        """Test ConditionsClause with multiple conditions"""
        conditions = [
            WhereCondition(field="age", operator=ComparisonOperator.GREATER_THAN, value=18),
            WhereCondition(field="status", operator=ComparisonOperator.EQUAL, value="active"),
        ]
        clause = ConditionsClause(where=conditions)

        expected_sql = "WHERE age > 18 AND status = 'active'"
        assert clause.to_sql() == expected_sql

    def test_conditions_clause_with_where_clause(self):
        """Test ConditionsClause with WhereClause object"""
        conditions = [
            WhereCondition(field="role", operator=ComparisonOperator.EQUAL, value="admin"),
            WhereCondition(field="role", operator=ComparisonOperator.EQUAL, value="moderator"),
        ]
        where_clause = WhereClause(conditions=conditions, logical_operator=LogicalOperator.OR)

        clause = ConditionsClause(where=[where_clause])

        expected_sql = "WHERE role = 'admin' OR role = 'moderator'"
        assert clause.to_sql() == expected_sql

    def test_conditions_clause_serialization_roundtrip(self):
        """Test serialization roundtrip for ConditionsClause"""
        conditions = [
            WhereCondition(field="user_id", operator=ComparisonOperator.EQUAL, value=123),
            WhereCondition(
                field="status", operator=ComparisonOperator.IN, value=["active", "pending"]
            ),
        ]
        original_clause = ConditionsClause(where=conditions)

        # Serialize and deserialize
        data = original_clause.to_dict()
        restored_clause = ConditionsClause.from_dict(data)

        # Verify they produce the same SQL
        assert original_clause.to_sql() == restored_clause.to_sql()


class TestWhereClauseEdgeCases:
    """Test edge cases and complex scenarios"""

    def test_complex_nested_where_clauses(self):
        """Test deeply nested WHERE clauses"""
        # (age > 18 AND age < 65) OR (role = 'admin')
        age_conditions = [
            WhereCondition(field="age", operator=ComparisonOperator.GREATER_THAN, value=18),
            WhereCondition(field="age", operator=ComparisonOperator.LESS_THAN, value=65),
        ]
        age_clause = WhereClause(conditions=age_conditions, logical_operator=LogicalOperator.AND)

        role_condition = WhereCondition(
            field="role", operator=ComparisonOperator.EQUAL, value="admin"
        )

        main_clause = WhereClause(
            conditions=[age_clause, role_condition], logical_operator=LogicalOperator.OR
        )

        expected_sql = "(age > 18 AND age < 65) OR role = 'admin'"
        assert main_clause.to_sql() == expected_sql

    def test_where_condition_with_table_prefix(self):
        """Test WhereCondition with table.column notation"""
        condition = WhereCondition(
            field="users.user_id", operator=ComparisonOperator.EQUAL, value=123
        )

        assert condition.to_sql() == "users.user_id = 123"

    def test_mixed_value_types_in_conditions(self):
        """Test conditions with various value types"""
        conditions = [
            WhereCondition(field="id", operator=ComparisonOperator.EQUAL, value=123),
            WhereCondition(field="name", operator=ComparisonOperator.LIKE, value="%john%"),
            WhereCondition(field="is_active", operator=ComparisonOperator.EQUAL, value=True),
            WhereCondition(
                field="created_at",
                operator=ComparisonOperator.GREATER_THAN,
                value=datetime(2023, 1, 1, tzinfo=timezone.utc),
            ),
            WhereCondition(field="deleted_at", operator=ComparisonOperator.IS_NULL, value=None),
        ]

        clause = ConditionsClause(where=conditions)
        sql = clause.to_sql()

        assert "WHERE" in sql
        assert "id = 123" in sql
        assert "name LIKE '%john%'" in sql
        assert "is_active = TRUE" in sql
        assert "created_at > '2023-01-01 00:00:00'" in sql
        assert "deleted_at IS NULL" in sql
