import pytest

from src.modules.rules.domain.value_objects.rule_config.common import (
    ConditionalFunction,
    DateTimeFunction,
    NumericAggregation,
    SqlExpression,
    StringFunction,
)
from src.modules.rules.domain.value_objects.rule_config.join_clause import JoinClause, JoinType
from src.modules.rules.domain.value_objects.rule_config.root import RuleConfig, TableReference
from src.modules.rules.domain.value_objects.rule_config.select_clause import (
    SelectClause,
    SelectField,
)
from src.modules.rules.domain.value_objects.rule_config.where_clause import (
    ComparisonOperator,
    ConditionsClause,
    LogicalOperator,
    WhereClause,
    WhereCondition,
)


class TestTableReference:
    """Test cases for TableReference class"""

    def test_create_table_reference_with_alias(self):
        """Test creating TableReference with alias"""
        table_ref = TableReference(name="users", alias="u")

        assert table_ref.name == "users"
        assert table_ref.alias == "u"
        assert table_ref.to_sql() == "users u"

    def test_create_table_reference_without_alias(self):
        """Test creating TableReference without alias"""
        table_ref = TableReference(name="transactions")

        assert table_ref.name == "transactions"
        assert table_ref.alias is None
        assert table_ref.to_sql() == "transactions"

    def test_table_reference_with_schema(self):
        """Test TableReference with schema-qualified name"""
        table_ref = TableReference(name="public.users", alias="u")

        assert table_ref.to_sql() == "public.users u"

    # Validation Tests
    def test_table_reference_validation_empty_name(self):
        """Test validation fails for empty table name"""
        with pytest.raises(ValueError, match="Table name cannot be empty"):
            TableReference(name="")

    def test_table_reference_validation_whitespace_name(self):
        """Test validation fails for whitespace-only name"""
        with pytest.raises(ValueError, match="Table name cannot be empty"):
            TableReference(name="   ")

    def test_table_reference_validation_invalid_alias(self):
        """Test validation fails for invalid alias"""
        with pytest.raises(ValueError, match="Invalid alias"):
            TableReference(name="users", alias="123invalid")

    def test_table_reference_validation_alias_with_spaces(self):
        """Test validation fails for alias with spaces"""
        with pytest.raises(ValueError, match="Invalid alias"):
            TableReference(name="users", alias="user alias")

    def test_table_reference_valid_aliases(self):
        """Test various valid alias formats"""
        valid_aliases = ["u", "user_table", "USER_TABLE", "_private", "table123"]

        for alias in valid_aliases:
            table_ref = TableReference(name="users", alias=alias)
            assert table_ref.alias == alias

    # Serialization Tests
    def test_table_reference_to_dict_with_alias(self):
        """Test to_dict method with alias"""
        table_ref = TableReference(name="users", alias="u")
        result = table_ref.to_dict()

        expected = {"name": "users", "alias": "u"}
        assert result == expected

    def test_table_reference_to_dict_without_alias(self):
        """Test to_dict method without alias"""
        table_ref = TableReference(name="transactions")
        result = table_ref.to_dict()

        expected = {"name": "transactions", "alias": None}
        assert result == expected

    def test_table_reference_from_dict_with_alias(self):
        """Test from_dict method with alias"""
        data = {"name": "orders", "alias": "o"}
        table_ref = TableReference.from_dict(data)

        assert table_ref.name == "orders"
        assert table_ref.alias == "o"

    def test_table_reference_from_dict_without_alias(self):
        """Test from_dict method without alias"""
        data = {"name": "products"}
        table_ref = TableReference.from_dict(data)

        assert table_ref.name == "products"
        assert table_ref.alias is None


class TestRuleConfig:
    """Test cases for RuleConfig class"""

    def test_create_minimal_rule_config(self):
        """Test creating RuleConfig with minimal required fields"""
        select_clause = SelectClause(
            fields=[SelectField(expression="id"), SelectField(expression="name")]
        )
        from_table = TableReference(name="users")

        config = RuleConfig(select=select_clause, from_table=from_table)

        assert isinstance(config.select, SelectClause)
        assert isinstance(config.from_table, TableReference)
        assert config.joins == []
        assert isinstance(config.conditions, ConditionsClause)
        assert config.group_by == []
        assert config.having == []
        assert config.order_by == []

    def test_create_complex_rule_config(self):
        """Test creating RuleConfig with all components"""
        # SELECT
        select_clause = SelectClause(
            fields=[
                SelectField(expression="u.id", alias="user_id"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["o.id"]),
                    alias="order_count",
                ),
            ]
        )

        # FROM
        from_table = TableReference(name="users", alias="u")

        # JOIN
        joins = [JoinClause(type=JoinType.LEFT, table="orders", alias="o", on="o.user_id = u.id")]

        # WHERE
        conditions = ConditionsClause(
            where=[
                WhereCondition(field="u.status", operator=ComparisonOperator.EQUAL, value="active")
            ]
        )

        # HAVING
        having = [
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.COUNT, args=["o.id"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=5,
            )
        ]

        config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=joins,
            conditions=conditions,
            group_by=["u.id"],
            having=having,
            order_by=["user_id DESC"],
        )

        assert len(config.joins) == 1
        assert len(config.conditions.where) == 1
        assert config.group_by == ["u.id"]
        assert len(config.having) == 1
        assert config.order_by == ["user_id DESC"]

    # Validation Tests
    def test_rule_config_validation_invalid_select(self):
        """Test validation fails for invalid select clause"""
        from_table = TableReference(name="users")

        with pytest.raises(ValueError, match="RuleConfig.select must be a SelectClause"):
            RuleConfig(select="invalid", from_table=from_table)

    def test_rule_config_validation_invalid_from_table(self):
        """Test validation fails for invalid from_table"""
        select_clause = SelectClause(fields=[SelectField(expression="id")])

        with pytest.raises(ValueError, match="RuleConfig.from_table must be a TableReference"):
            RuleConfig(select=select_clause, from_table="invalid")

    # Serialization Tests
    def test_rule_config_to_dict_minimal(self):
        """Test to_dict method with minimal configuration"""
        select_clause = SelectClause(fields=[SelectField(expression="id")])
        from_table = TableReference(name="users")

        config = RuleConfig(select=select_clause, from_table=from_table)
        result = config.to_dict()

        expected_keys = [
            "select",
            "from_table",
            "joins",
            "conditions",
            "group_by",
            "having",
            "order_by",
        ]
        assert all(key in result for key in expected_keys)
        assert result["joins"] == []
        assert result["group_by"] == []
        assert result["having"] == []
        assert result["order_by"] == []

    def test_rule_config_to_dict_complex(self):
        """Test to_dict method with complex configuration"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="u.id", alias="user_id"),
                SelectField(expression="u.name", alias="username"),
            ]
        )
        from_table = TableReference(name="users", alias="u")
        joins = [
            JoinClause(type=JoinType.INNER, table="profiles", alias="p", on="p.user_id = u.id")
        ]
        conditions = ConditionsClause(
            where=[
                WhereCondition(field="u.status", operator=ComparisonOperator.EQUAL, value="active")
            ]
        )

        config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=joins,
            conditions=conditions,
            group_by=["u.id"],
            order_by=["username ASC"],
        )

        result = config.to_dict()

        assert "select" in result
        assert "from_table" in result
        assert len(result["joins"]) == 1
        assert "conditions" in result
        assert result["group_by"] == ["u.id"]
        assert result["order_by"] == ["username ASC"]

    def test_rule_config_from_dict_minimal(self):
        """Test from_dict method with minimal data"""
        data = {
            "select": {"fields": [{"expression": "id", "alias": None}]},
            "from_table": {"name": "users", "alias": None},
        }

        config = RuleConfig.from_dict(data)

        assert isinstance(config.select, SelectClause)
        assert isinstance(config.from_table, TableReference)
        assert config.from_table.name == "users"
        assert len(config.joins) == 0

    def test_rule_config_from_dict_complex(self):
        """Test from_dict method with complex data"""
        data = {
            "select": {
                "fields": [
                    {"expression": "u.id", "alias": "user_id"},
                    {"expression": "u.name", "alias": "username"},
                ]
            },
            "from_table": {"name": "users", "alias": "u"},
            "joins": [
                {
                    "type": "LEFT",
                    "table": "orders",
                    "alias": "o",
                    "on": "o.user_id = u.id",
                    "use_as": True,
                }
            ],
            "conditions": {"where": [{"field": "u.status", "operator": "=", "value": "active"}]},
            "group_by": ["u.id"],
            "having": [],
            "order_by": ["username ASC"],
        }

        config = RuleConfig.from_dict(data)

        assert len(config.select.fields) == 2
        assert config.from_table.alias == "u"
        assert len(config.joins) == 1
        assert config.joins[0].type == JoinType.LEFT
        assert len(config.conditions.where) == 1
        assert config.group_by == ["u.id"]
        assert config.order_by == ["username ASC"]

    def test_rule_config_serialization_roundtrip(self):
        """Test that to_dict/from_dict roundtrip works correctly"""
        # Create original config
        select_clause = SelectClause(
            fields=[
                SelectField(expression="u.id", alias="user_id"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.SUM, args=["o.amount"]),
                    alias="total",
                ),
            ]
        )
        from_table = TableReference(name="users", alias="u")
        joins = [JoinClause(type=JoinType.LEFT, table="orders", alias="o", on="o.user_id = u.id")]
        conditions = ConditionsClause(
            where=[
                WhereCondition(field="u.status", operator=ComparisonOperator.EQUAL, value="active")
            ]
        )

        original_config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=joins,
            conditions=conditions,
            group_by=["u.id"],
            order_by=["total DESC"],
        )

        # Serialize and deserialize
        data = original_config.to_dict()
        restored_config = RuleConfig.from_dict(data)

        # Verify key properties match
        assert len(original_config.select.fields) == len(restored_config.select.fields)
        assert original_config.from_table.name == restored_config.from_table.name
        assert original_config.from_table.alias == restored_config.from_table.alias
        assert len(original_config.joins) == len(restored_config.joins)
        assert original_config.group_by == restored_config.group_by
        assert original_config.order_by == restored_config.order_by


class TestRuleConfigSqlGeneration:
    """Test cases for RuleConfig.to_sql() method"""

    def test_minimal_sql_generation(self):
        """Test SQL generation with minimal configuration"""
        select_clause = SelectClause(fields=[SelectField(expression="id")])
        from_table = TableReference(name="users")

        config = RuleConfig(select=select_clause, from_table=from_table)
        sql = config.to_sql()

        expected = "SELECT id FROM users"
        assert sql == expected

    def test_sql_generation_with_alias(self):
        """Test SQL generation with table alias"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="u.id", alias="user_id"),
                SelectField(expression="u.name"),
            ]
        )
        from_table = TableReference(name="users", alias="u")

        config = RuleConfig(select=select_clause, from_table=from_table)
        sql = config.to_sql()

        expected = "SELECT u.id AS user_id, u.name FROM users u"
        assert sql == expected

    def test_sql_generation_with_joins(self):
        """Test SQL generation with JOIN clauses"""
        select_clause = SelectClause(
            fields=[SelectField(expression="u.name"), SelectField(expression="p.bio")]
        )
        from_table = TableReference(name="users", alias="u")
        joins = [
            JoinClause(type=JoinType.INNER, table="profiles", alias="p", on="p.user_id = u.id"),
            JoinClause(type=JoinType.LEFT, table="orders", alias="o", on="o.user_id = u.id"),
        ]

        config = RuleConfig(select=select_clause, from_table=from_table, joins=joins)
        sql = config.to_sql()

        expected = "SELECT u.name, p.bio FROM users u INNER JOIN profiles AS p ON p.user_id = u.id LEFT JOIN orders AS o ON o.user_id = u.id"
        assert sql == expected

    def test_sql_generation_with_where(self):
        """Test SQL generation with WHERE conditions"""
        select_clause = SelectClause(fields=[SelectField(expression="*")])
        from_table = TableReference(name="users")
        conditions = ConditionsClause(
            where=[
                WhereCondition(field="status", operator=ComparisonOperator.EQUAL, value="active"),
                WhereCondition(field="age", operator=ComparisonOperator.GREATER_THAN, value=18),
            ]
        )

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)
        sql = config.to_sql()

        expected = "SELECT * FROM users WHERE status = 'active' AND age > 18"
        assert sql == expected

    def test_sql_generation_with_group_by(self):
        """Test SQL generation with GROUP BY"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="category"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                    alias="count",
                ),
            ]
        )
        from_table = TableReference(name="products")

        config = RuleConfig(select=select_clause, from_table=from_table, group_by=["category"])
        sql = config.to_sql()

        expected = "SELECT category, COUNT('*') AS count FROM products GROUP BY category"
        assert sql == expected

    def test_sql_generation_with_having(self):
        """Test SQL generation with HAVING conditions"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="category"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                    alias="count",
                ),
            ]
        )
        from_table = TableReference(name="products")
        having = [
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=5,
            )
        ]

        config = RuleConfig(
            select=select_clause, from_table=from_table, group_by=["category"], having=having
        )
        sql = config.to_sql()

        expected = "SELECT category, COUNT('*') AS count FROM products GROUP BY category HAVING COUNT('*') > 5"
        assert sql == expected

    def test_sql_generation_with_order_by(self):
        """Test SQL generation with ORDER BY"""
        select_clause = SelectClause(
            fields=[SelectField(expression="name"), SelectField(expression="created_at")]
        )
        from_table = TableReference(name="users")

        config = RuleConfig(
            select=select_clause, from_table=from_table, order_by=["name ASC", "created_at DESC"]
        )
        sql = config.to_sql()

        expected = "SELECT name, created_at FROM users ORDER BY name ASC, created_at DESC"
        assert sql == expected

    def test_complete_sql_generation(self):
        """Test SQL generation with all components"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="u.id", alias="user_id"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["o.id"]),
                    alias="order_count",
                ),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.SUM, args=["o.amount"]),
                    alias="total_amount",
                ),
            ]
        )
        from_table = TableReference(name="users", alias="u")
        joins = [JoinClause(type=JoinType.LEFT, table="orders", alias="o", on="o.user_id = u.id")]
        conditions = ConditionsClause(
            where=[
                WhereCondition(field="u.status", operator=ComparisonOperator.EQUAL, value="active")
            ]
        )
        having = [
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.COUNT, args=["o.id"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=0,
            )
        ]

        config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=joins,
            conditions=conditions,
            group_by=["u.id"],
            having=having,
            order_by=["total_amount DESC"],
        )
        sql = config.to_sql()

        expected_parts = [
            "SELECT u.id AS user_id, COUNT(o.id) AS order_count, SUM(o.amount) AS total_amount",
            "FROM users u",
            "LEFT JOIN orders AS o ON o.user_id = u.id",
            "WHERE u.status = 'active'",
            "GROUP BY u.id",
            "HAVING COUNT(o.id) > 0",
            "ORDER BY total_amount DESC",
        ]
        expected = " ".join(expected_parts)
        assert sql == expected

    def test_sql_generation_with_multiple_having_conditions(self):
        """Test SQL generation with multiple HAVING conditions"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="category"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                    alias="count",
                ),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.AVG, args=["price"]),
                    alias="avg_price",
                ),
            ]
        )
        from_table = TableReference(name="products")
        having = [
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=10,
            ),
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.AVG, args=["price"]),
                operator=ComparisonOperator.LESS_THAN,
                value=100.0,
            ),
        ]

        config = RuleConfig(
            select=select_clause, from_table=from_table, group_by=["category"], having=having
        )
        sql = config.to_sql()

        expected = "SELECT category, COUNT('*') AS count, AVG(price) AS avg_price FROM products GROUP BY category HAVING COUNT('*') > 10 AND AVG(price) < 100.0"
        assert sql == expected

    def test_sql_generation_empty_where_conditions(self):
        """Test SQL generation with empty WHERE conditions"""
        select_clause = SelectClause(fields=[SelectField(expression="*")])
        from_table = TableReference(name="users")
        conditions = ConditionsClause(where=[])  # Empty WHERE

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)
        sql = config.to_sql()

        expected = "SELECT * FROM users"
        assert sql == expected

    def test_sql_generation_with_complex_where_clause(self):
        """Test SQL generation with complex nested WHERE clause"""
        select_clause = SelectClause(fields=[SelectField(expression="*")])
        from_table = TableReference(name="users")

        # Create nested WHERE: (age > 18 AND age < 65) OR role = 'admin'
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
        conditions = ConditionsClause(where=[main_clause])

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)
        sql = config.to_sql()

        expected = "SELECT * FROM users WHERE (age > 18 AND age < 65) OR role = 'admin'"
        assert sql == expected


class TestRuleConfigEdgeCases:
    """Test edge cases and complex scenarios"""

    def test_rule_config_with_nested_where_clauses(self):
        """Test RuleConfig with nested WHERE clauses"""
        select_clause = SelectClause(fields=[SelectField(expression="*")])
        from_table = TableReference(name="users")

        # Create nested WHERE: (age > 18 AND age < 65) OR role = 'admin'
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
        conditions = ConditionsClause(where=[main_clause])

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)

        # Verify the structure is preserved
        assert len(config.conditions.where) == 1
        assert isinstance(config.conditions.where[0], WhereClause)

    def test_rule_config_with_multiple_joins(self):
        """Test RuleConfig with multiple JOIN clauses"""
        select_clause = SelectClause(fields=[SelectField(expression="u.name")])
        from_table = TableReference(name="users", alias="u")

        joins = [
            JoinClause(type=JoinType.INNER, table="profiles", alias="p", on="p.user_id = u.id"),
            JoinClause(type=JoinType.LEFT, table="orders", alias="o", on="o.user_id = u.id"),
            JoinClause(
                type=JoinType.RIGHT, table="payments", alias="pay", on="pay.order_id = o.id"
            ),
        ]

        config = RuleConfig(select=select_clause, from_table=from_table, joins=joins)

        assert len(config.joins) == 3
        assert config.joins[0].type == JoinType.INNER
        assert config.joins[1].type == JoinType.LEFT
        assert config.joins[2].type == JoinType.RIGHT

    def test_rule_config_with_complex_having_conditions(self):
        """Test RuleConfig with complex HAVING conditions"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="category"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                    alias="count",
                ),
            ]
        )
        from_table = TableReference(name="products")

        having = [
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.COUNT, args=["*"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=10,
            ),
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.AVG, args=["price"]),
                operator=ComparisonOperator.LESS_THAN,
                value=100.0,
            ),
        ]

        config = RuleConfig(
            select=select_clause, from_table=from_table, group_by=["category"], having=having
        )

        assert len(config.having) == 2
        assert isinstance(config.having[0].field, SqlExpression)
        assert isinstance(config.having[1].field, SqlExpression)

    def test_rule_config_empty_optional_lists(self):
        """Test RuleConfig with explicitly empty optional lists"""
        select_clause = SelectClause(fields=[SelectField(expression="id")])
        from_table = TableReference(name="users")

        config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=[],
            group_by=[],
            having=[],
            order_by=[],
        )

        assert config.joins == []
        assert config.group_by == []
        assert config.having == []
        assert config.order_by == []


class TestRuleConfigComprehensiveSQL:
    """Test SQL generation with all possible components"""

    def test_full_sql_with_all_components(self):
        """Test SQL generation with SELECT, FROM, JOIN, WHERE, GROUP BY, HAVING, ORDER BY"""
        # Complex SELECT with functions and aliases
        select_clause = SelectClause(
            fields=[
                SelectField(expression="u.id"),
                SelectField(expression="u.name"),
                SelectField(expression="u.email"),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.COUNT, args=["o.id"]),
                    alias="total_orders",
                ),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.SUM, args=["o.amount"]),
                    alias="total_spent",
                ),
                SelectField(
                    expression=SqlExpression(function=NumericAggregation.AVG, args=["o.amount"]),
                    alias="avg_order_value",
                ),
                SelectField(
                    expression=SqlExpression(function=StringFunction.UPPER, args=["p.title"]),
                    alias="profile_title",
                ),
            ]
        )

        from_table = TableReference(name="users", alias="u")

        # Multiple JOINs
        joins = [
            JoinClause(type=JoinType.INNER, table="profiles", alias="p", on="p.user_id = u.id"),
            JoinClause(type=JoinType.LEFT, table="orders", alias="o", on="o.user_id = u.id"),
            JoinClause(
                type=JoinType.LEFT, table="order_items", alias="oi", on="oi.order_id = o.id"
            ),
            JoinClause(
                type=JoinType.INNER, table="products", alias="prod", on="prod.id = oi.product_id"
            ),
        ]

        # Complex WHERE conditions with nested logic
        active_condition = WhereCondition(
            field="u.active", operator=ComparisonOperator.EQUAL, value=True
        )
        date_condition = WhereCondition(
            field="u.created_at", operator=ComparisonOperator.GREATER_THAN, value="2023-01-01"
        )

        price_conditions = [
            WhereCondition(field="o.amount", operator=ComparisonOperator.GREATER_THAN, value=50),
            WhereCondition(field="o.amount", operator=ComparisonOperator.LESS_THAN, value=1000),
        ]
        price_clause = WhereClause(
            conditions=price_conditions, logical_operator=LogicalOperator.AND
        )

        category_condition = WhereCondition(
            field="prod.category",
            operator=ComparisonOperator.IN,
            value=["electronics", "books", "clothing"],
        )

        main_clause = WhereClause(
            conditions=[active_condition, date_condition, price_clause, category_condition],
            logical_operator=LogicalOperator.AND,
        )
        conditions = ConditionsClause(where=[main_clause])

        # GROUP BY
        group_by = ["u.id", "u.name", "u.email", "p.title"]

        # HAVING with complex conditions
        having = [
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.COUNT, args=["o.id"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=3,
            ),
            WhereCondition(
                field=SqlExpression(function=NumericAggregation.SUM, args=["o.amount"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=500.0,
            ),
        ]

        # ORDER BY
        order_by = ["total_spent DESC", "total_orders DESC", "u.name ASC"]

        config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=joins,
            conditions=conditions,
            group_by=group_by,
            having=having,
            order_by=order_by,
        )

        sql = config.to_sql()

        # Verify all components are present
        assert (
            "SELECT u.id, u.name, u.email, COUNT(o.id) AS total_orders, SUM(o.amount) AS total_spent, AVG(o.amount) AS avg_order_value, UPPER(p.title) AS profile_title"
            in sql
        )
        assert "FROM users u" in sql
        assert "INNER JOIN profiles AS p ON p.user_id = u.id" in sql
        assert "LEFT JOIN orders AS o ON o.user_id = u.id" in sql
        assert "LEFT JOIN order_items AS oi ON oi.order_id = o.id" in sql
        assert "INNER JOIN products AS prod ON prod.id = oi.product_id" in sql
        assert (
            "WHERE u.active = TRUE AND u.created_at > '2023-01-01' AND (o.amount > 50 AND o.amount < 1000) AND prod.category IN ('electronics', 'books', 'clothing')"
            in sql
        )
        assert "GROUP BY u.id, u.name, u.email, p.title" in sql
        assert "HAVING COUNT(o.id) > 3 AND SUM(o.amount) > 500.0" in sql
        assert "ORDER BY total_spent DESC, total_orders DESC, u.name ASC" in sql

    def test_sql_with_subqueries_and_functions(self):
        """Test SQL generation with various SQL functions"""
        select_clause = SelectClause(
            fields=[
                SelectField(expression="id"),
                SelectField(
                    expression=SqlExpression(
                        function=StringFunction.CONCAT, args=["first_name", "' '", "last_name"]
                    ),
                    alias="full_name",
                ),
                SelectField(
                    expression=SqlExpression(function=StringFunction.LENGTH, args=["email"]),
                    alias="email_length",
                ),
                SelectField(
                    expression=SqlExpression(function=StringFunction.UPPER, args=["status"]),
                    alias="status_upper",
                ),
                SelectField(
                    expression=SqlExpression(
                        function=ConditionalFunction.COALESCE, args=["phone", "'N/A'"]
                    ),
                    alias="phone_display",
                ),
                SelectField(
                    expression=SqlExpression(function=DateTimeFunction.YEAR, args=["created_at"]),
                    alias="created_year",
                ),
            ]
        )

        from_table = TableReference(name="customers")

        # WHERE with function conditions
        where_conditions = [
            WhereCondition(
                field=SqlExpression(function=StringFunction.LENGTH, args=["email"]),
                operator=ComparisonOperator.GREATER_THAN,
                value=10,
            ),
            WhereCondition(
                field=SqlExpression(function=DateTimeFunction.YEAR, args=["created_at"]),
                operator=ComparisonOperator.EQUAL,
                value=2023,
            ),
        ]
        where_clause = WhereClause(
            conditions=where_conditions, logical_operator=LogicalOperator.AND
        )
        conditions = ConditionsClause(where=[where_clause])

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)
        sql = config.to_sql()

        # Verify function usage
        assert "CONCAT(first_name, ''' ''', last_name) AS full_name" in sql
        assert "LENGTH(email) AS email_length" in sql
        assert "UPPER(status) AS status_upper" in sql
        assert "COALESCE(phone, '''N/A''') AS phone_display" in sql
        assert "YEAR(created_at) AS created_year" in sql
        assert "WHERE LENGTH(email) > 10 AND YEAR(created_at) = 2023" in sql


class TestRuleConfigEdgeCasesAdvanced:
    """Test advanced edge cases and error scenarios"""

    def test_sql_with_complex_nested_expressions(self):
        """Test SQL with deeply nested expressions"""
        # Nested function: UPPER(CONCAT(COALESCE(first_name, ''), ' ', COALESCE(last_name, '')))
        inner_concat = SqlExpression(
            function=StringFunction.CONCAT,
            args=[
                SqlExpression(function=ConditionalFunction.COALESCE, args=["first_name", "''"]),
                "' '",
                SqlExpression(function=ConditionalFunction.COALESCE, args=["last_name", "''"]),
            ],
        )
        outer_upper = SqlExpression(function=StringFunction.UPPER, args=[inner_concat])

        select_clause = SelectClause(
            fields=[
                SelectField(expression="id"),
                SelectField(expression=outer_upper, alias="full_name_upper"),
            ]
        )

        from_table = TableReference(name="users")
        config = RuleConfig(select=select_clause, from_table=from_table)

        sql = config.to_sql()
        expected = "SELECT id, UPPER(CONCAT(COALESCE(first_name, ''''''), ''' ''', COALESCE(last_name, ''''''))) AS full_name_upper FROM users"
        assert sql == expected

    def test_sql_with_empty_conditions_clause(self):
        """Test SQL generation with empty conditions clause"""
        select_clause = SelectClause(fields=[SelectField(expression="*")])
        from_table = TableReference(name="users")

        # Empty conditions clause
        conditions = ConditionsClause(where=[])

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)
        sql = config.to_sql()

        expected = "SELECT * FROM users"
        assert sql == expected

    def test_sql_with_special_characters_in_values(self):
        """Test SQL generation with special characters in values"""
        select_clause = SelectClause(fields=[SelectField(expression="*")])
        from_table = TableReference(name="users")

        where_conditions = [
            WhereCondition(field="name", operator=ComparisonOperator.EQUAL, value="O'Connor"),
            WhereCondition(
                field="description", operator=ComparisonOperator.LIKE, value='It\'s a "test" value'
            ),
            WhereCondition(
                field="path", operator=ComparisonOperator.EQUAL, value="C:\\\\Users\\\\test"
            ),
        ]
        where_clause = WhereClause(
            conditions=where_conditions, logical_operator=LogicalOperator.AND
        )
        conditions = ConditionsClause(where=[where_clause])

        config = RuleConfig(select=select_clause, from_table=from_table, conditions=conditions)
        sql = config.to_sql()

        # Verify proper escaping
        assert "name = 'O''Connor'" in sql
        assert "description LIKE 'It''s a \"test\" value'" in sql
        assert "path = 'C:\\\\Users\\\\test'" in sql

    def test_sql_generation_performance_with_large_query(self):
        """Test SQL generation performance with a large, complex query"""
        # Create a large SELECT clause
        select_fields = []
        for i in range(50):
            select_fields.append(SelectField(expression=f"field_{i}"))
        select_clause = SelectClause(fields=select_fields)

        from_table = TableReference(name="large_table")

        # Create many JOIN clauses
        joins = []
        for i in range(10):
            joins.append(
                JoinClause(
                    type=JoinType.LEFT,
                    table=f"table_{i}",
                    alias=f"t{i}",
                    on=f"t{i}.id = large_table.table_{i}_id",
                )
            )

        # Create many WHERE conditions
        where_conditions = []
        for i in range(20):
            where_conditions.append(
                WhereCondition(
                    field=f"field_{i}", operator=ComparisonOperator.GREATER_THAN, value=i
                )
            )
        where_clause = WhereClause(
            conditions=where_conditions, logical_operator=LogicalOperator.AND
        )
        conditions = ConditionsClause(where=[where_clause])

        # Create large GROUP BY
        group_by = [f"field_{i}" for i in range(10)]

        # Create large ORDER BY
        order_by = [f"field_{i} ASC" for i in range(10)]

        config = RuleConfig(
            select=select_clause,
            from_table=from_table,
            joins=joins,
            conditions=conditions,
            group_by=group_by,
            order_by=order_by,
        )

        # This should complete without performance issues
        sql = config.to_sql()

        # Basic verification that the query was generated
        assert "SELECT" in sql
        assert "FROM large_table" in sql
        assert len(sql) > 1000  # Should be a large query
        assert sql.count("LEFT JOIN") == 10
        assert sql.count("field_") >= 50  # At least 50 field references
