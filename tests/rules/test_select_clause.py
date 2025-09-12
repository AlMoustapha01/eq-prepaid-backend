import pytest

from src.modules.rules.domain.value_objects.rule_config.common import (
    NumericAggregation,
    NumericFunction,
    SqlExpression,
    StringFunction,
)
from src.modules.rules.domain.value_objects.rule_config.select_clause import (
    SelectClause,
    SelectField,
)


class TestSelectField:
    """Test cases for SelectField class"""

    def test_create_select_field_with_string_expression(self):
        """Test creating SelectField with string expression"""
        field = SelectField(expression="user_id", alias="id")

        assert field.expression == "user_id"
        assert field.alias == "id"
        assert field.to_sql() == "user_id AS id"

    def test_create_select_field_without_alias(self):
        """Test creating SelectField without alias"""
        field = SelectField(expression="username")

        assert field.expression == "username"
        assert field.alias is None
        assert field.to_sql() == "username"

    def test_create_select_field_with_sql_expression(self):
        """Test creating SelectField with SqlExpression"""
        sql_expr = SqlExpression(function=NumericAggregation.COUNT, args=["user_id"])
        field = SelectField(expression=sql_expr, alias="total_users")

        assert isinstance(field.expression, SqlExpression)
        assert field.alias == "total_users"
        assert field.to_sql() == "COUNT(user_id) AS total_users"

    def test_create_select_field_with_complex_sql_expression(self):
        """Test creating SelectField with complex nested SqlExpression"""
        inner_expr = SqlExpression(function=StringFunction.UPPER, args=["username"])
        outer_expr = SqlExpression(function=StringFunction.CONCAT, args=[inner_expr, "'_SUFFIX'"])
        field = SelectField(expression=outer_expr, alias="formatted_name")

        expected_sql = "CONCAT(UPPER(username), '''_SUFFIX''') AS formatted_name"
        assert field.to_sql() == expected_sql

    def test_select_field_validation_empty_string_expression(self):
        """Test validation fails for empty string expression"""
        with pytest.raises(ValueError, match="SelectField expression cannot be empty"):
            SelectField(expression="", alias="test")

    def test_select_field_validation_whitespace_expression(self):
        """Test validation fails for whitespace-only expression"""
        with pytest.raises(ValueError, match="SelectField expression cannot be empty"):
            SelectField(expression="   ", alias="test")

    def test_select_field_validation_invalid_alias(self):
        """Test validation fails for invalid alias"""
        with pytest.raises(ValueError, match="Invalid alias"):
            SelectField(expression="user_id", alias="123invalid")

    def test_select_field_validation_alias_with_spaces(self):
        """Test validation fails for alias with spaces"""
        with pytest.raises(ValueError, match="Invalid alias"):
            SelectField(expression="user_id", alias="user id")

    def test_select_field_validation_alias_with_special_chars(self):
        """Test validation fails for alias with special characters"""
        with pytest.raises(ValueError, match="Invalid alias"):
            SelectField(expression="user_id", alias="user-id")

    def test_select_field_valid_aliases(self):
        """Test various valid alias formats"""
        valid_aliases = ["user_id", "userId", "USER_ID", "_private", "field123", "a"]

        for alias in valid_aliases:
            field = SelectField(expression="test_col", alias=alias)
            assert field.alias == alias

    def test_select_field_to_dict_string_expression(self):
        """Test to_dict method with string expression"""
        field = SelectField(expression="user_id", alias="id")
        result = field.to_dict()

        expected = {"expression": "user_id", "alias": "id"}
        assert result == expected

    def test_select_field_to_dict_sql_expression(self):
        """Test to_dict method with SqlExpression"""
        sql_expr = SqlExpression(function=NumericAggregation.SUM, args=["amount"])
        field = SelectField(expression=sql_expr, alias="total")
        result = field.to_dict()

        expected = {"expression": {"function": "SUM", "args": ["amount"]}, "alias": "total"}
        assert result == expected

    def test_select_field_from_dict_string_expression(self):
        """Test from_dict method with string expression"""
        data = {"expression": "user_id", "alias": "id"}
        field = SelectField.from_dict(data)

        assert field.expression == "user_id"
        assert field.alias == "id"

    def test_select_field_from_dict_sql_expression(self):
        """Test from_dict method with SqlExpression"""
        data = {"expression": {"function": "COUNT", "args": ["*"]}, "alias": "total"}
        field = SelectField.from_dict(data)

        assert isinstance(field.expression, SqlExpression)
        assert field.expression.function == "COUNT"
        assert field.expression.args == ["*"]
        assert field.alias == "total"

    def test_select_field_from_dict_no_alias(self):
        """Test from_dict method without alias"""
        data = {"expression": "username", "alias": None}
        field = SelectField.from_dict(data)

        assert field.expression == "username"
        assert field.alias is None


class TestSelectClause:
    """Test cases for SelectClause class"""

    def test_create_select_clause_single_field(self):
        """Test creating SelectClause with single field"""
        field = SelectField(expression="user_id", alias="id")
        clause = SelectClause(fields=[field])

        assert len(clause.fields) == 1
        assert clause.to_sql() == "SELECT user_id AS id"

    def test_create_select_clause_multiple_fields(self):
        """Test creating SelectClause with multiple fields"""
        fields = [
            SelectField(expression="user_id", alias="id"),
            SelectField(expression="username"),
            SelectField(expression="email", alias="user_email"),
        ]
        clause = SelectClause(fields=fields)

        expected_sql = "SELECT user_id AS id, username, email AS user_email"
        assert clause.to_sql() == expected_sql

    def test_create_select_clause_with_sql_expressions(self):
        """Test creating SelectClause with SqlExpression fields"""
        count_expr = SqlExpression(function=NumericAggregation.COUNT, args=["*"])
        sum_expr = SqlExpression(function=NumericAggregation.SUM, args=["amount"])

        fields = [
            SelectField(expression="category"),
            SelectField(expression=count_expr, alias="total_records"),
            SelectField(expression=sum_expr, alias="total_amount"),
        ]
        clause = SelectClause(fields=fields)

        expected_sql = "SELECT category, COUNT('*') AS total_records, SUM(amount) AS total_amount"
        assert clause.to_sql() == expected_sql

    def test_select_clause_validation_empty_fields(self):
        """Test validation fails for empty fields list"""
        with pytest.raises(ValueError, match="SelectClause must have at least one field"):
            SelectClause(fields=[])

    def test_select_clause_complex_expressions(self):
        """Test SelectClause with complex nested expressions"""
        # UPPER(CONCAT(first_name, ' ', last_name))
        concat_expr = SqlExpression(
            function=StringFunction.CONCAT, args=["first_name", "' '", "last_name"]
        )
        upper_expr = SqlExpression(function=StringFunction.UPPER, args=[concat_expr])

        fields = [
            SelectField(expression="id"),
            SelectField(expression=upper_expr, alias="full_name_upper"),
        ]
        clause = SelectClause(fields=fields)

        expected_sql = "SELECT id, UPPER(CONCAT(first_name, ''' ''', last_name)) AS full_name_upper"
        assert clause.to_sql() == expected_sql

    def test_select_clause_to_dict(self):
        """Test to_dict method for SelectClause"""
        fields = [SelectField(expression="user_id", alias="id"), SelectField(expression="username")]
        clause = SelectClause(fields=fields)
        result = clause.to_dict()

        expected = {
            "fields": [
                {"expression": "user_id", "alias": "id"},
                {"expression": "username", "alias": None},
            ]
        }
        assert result == expected

    def test_select_clause_from_dict(self):
        """Test from_dict method for SelectClause"""
        data = {
            "fields": [
                {"expression": "user_id", "alias": "id"},
                {"expression": "username", "alias": None},
                {"expression": {"function": "COUNT", "args": ["*"]}, "alias": "total"},
            ]
        }
        clause = SelectClause.from_dict(data)

        assert len(clause.fields) == 3
        assert clause.fields[0].expression == "user_id"
        assert clause.fields[0].alias == "id"
        assert clause.fields[1].expression == "username"
        assert clause.fields[1].alias is None
        assert isinstance(clause.fields[2].expression, SqlExpression)
        assert clause.fields[2].alias == "total"

    def test_select_clause_roundtrip_serialization(self):
        """Test that to_dict/from_dict roundtrip works correctly"""
        # Create original clause
        count_expr = SqlExpression(function=NumericAggregation.COUNT, args=["user_id"])
        fields = [
            SelectField(expression="category", alias="cat"),
            SelectField(expression=count_expr, alias="user_count"),
        ]
        original_clause = SelectClause(fields=fields)

        # Serialize and deserialize
        data = original_clause.to_dict()
        restored_clause = SelectClause.from_dict(data)

        # Verify they produce the same SQL
        assert original_clause.to_sql() == restored_clause.to_sql()
        assert len(original_clause.fields) == len(restored_clause.fields)

    def test_select_clause_with_aggregations_and_grouping(self):
        """Test SelectClause suitable for GROUP BY queries"""
        avg_expr = SqlExpression(function=NumericAggregation.AVG, args=["salary"])
        max_expr = SqlExpression(function=NumericAggregation.MAX, args=["hire_date"])

        fields = [
            SelectField(expression="department"),
            SelectField(expression=avg_expr, alias="avg_salary"),
            SelectField(expression=max_expr, alias="latest_hire"),
        ]
        clause = SelectClause(fields=fields)

        expected_sql = "SELECT department, AVG(salary) AS avg_salary, MAX(hire_date) AS latest_hire"
        assert clause.to_sql() == expected_sql

    def test_select_clause_with_string_functions(self):
        """Test SelectClause with string manipulation functions"""
        trim_expr = SqlExpression(function=StringFunction.TRIM, args=["name"])
        length_expr = SqlExpression(function=StringFunction.LENGTH, args=["description"])

        fields = [
            SelectField(expression="id"),
            SelectField(expression=trim_expr, alias="clean_name"),
            SelectField(expression=length_expr, alias="desc_length"),
        ]
        clause = SelectClause(fields=fields)

        expected_sql = "SELECT id, TRIM(name) AS clean_name, LENGTH(description) AS desc_length"
        assert clause.to_sql() == expected_sql


class TestSelectClauseEdgeCases:
    """Test edge cases and error conditions"""

    def test_select_field_with_column_containing_dots(self):
        """Test SelectField with table.column notation"""
        field = SelectField(expression="users.user_id", alias="id")
        assert field.to_sql() == "users.user_id AS id"

    def test_select_field_with_schema_table_column(self):
        """Test SelectField with schema.table.column notation"""
        field = SelectField(expression="public.users.user_id", alias="id")
        assert field.to_sql() == "public.users.user_id AS id"

    def test_select_clause_preserves_field_order(self):
        """Test that SelectClause preserves field order"""
        fields = [
            SelectField(expression="z_field"),
            SelectField(expression="a_field"),
            SelectField(expression="m_field"),
        ]
        clause = SelectClause(fields=fields)

        expected_sql = "SELECT z_field, a_field, m_field"
        assert clause.to_sql() == expected_sql

    def test_select_field_sql_expression_with_mixed_args(self):
        """Test SqlExpression with mixed argument types"""
        # ROUND(price * 1.1, 2)
        multiply_expr = SqlExpression(
            function="*",  # Custom operator as function
            args=["price", 1.1],
        )
        round_expr = SqlExpression(function=NumericFunction.ROUND, args=[multiply_expr, 2])

        field = SelectField(expression=round_expr, alias="adjusted_price")
        # Note: This tests the structure, actual SQL generation depends on SqlExpression implementation
        assert field.alias == "adjusted_price"
        assert isinstance(field.expression, SqlExpression)
