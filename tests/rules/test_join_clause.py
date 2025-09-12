import pytest

from src.modules.rules.domain.value_objects.rule_config.join_clause import JoinClause, JoinType


class TestJoinClause:
    """Test cases for JoinClause class"""

    def test_create_inner_join_with_alias(self):
        """Test creating INNER JOIN with alias"""
        join = JoinClause(type=JoinType.INNER, table="users", alias="u", on="u.id = orders.user_id")

        assert join.type == JoinType.INNER
        assert join.table == "users"
        assert join.alias == "u"
        assert join.on == "u.id = orders.user_id"
        assert join.use_as is True
        assert join.to_sql() == "INNER JOIN users AS u ON u.id = orders.user_id"

    def test_create_left_join_without_alias(self):
        """Test creating LEFT JOIN without alias"""
        join = JoinClause(type=JoinType.LEFT, table="profiles", on="profiles.user_id = users.id")

        assert join.type == JoinType.LEFT
        assert join.table == "profiles"
        assert join.alias is None
        assert join.to_sql() == "LEFT JOIN profiles ON profiles.user_id = users.id"

    def test_create_right_join_with_alias_no_as(self):
        """Test creating RIGHT JOIN with alias but without AS keyword"""
        join = JoinClause(
            type=JoinType.RIGHT,
            table="departments",
            alias="dept",
            on="dept.id = employees.department_id",
            use_as=False,
        )

        assert join.to_sql() == "RIGHT JOIN departments dept ON dept.id = employees.department_id"

    def test_create_full_join(self):
        """Test creating FULL JOIN"""
        join = JoinClause(
            type=JoinType.FULL, table="categories", alias="cat", on="cat.id = products.category_id"
        )

        assert join.to_sql() == "FULL JOIN categories AS cat ON cat.id = products.category_id"

    def test_join_with_complex_on_condition(self):
        """Test JOIN with complex ON condition"""
        join = JoinClause(
            type=JoinType.INNER,
            table="order_items",
            alias="oi",
            on="oi.order_id = o.id AND oi.product_id = p.id",
        )

        expected_sql = "INNER JOIN order_items AS oi ON oi.order_id = o.id AND oi.product_id = p.id"
        assert join.to_sql() == expected_sql

    def test_join_with_schema_qualified_table(self):
        """Test JOIN with schema-qualified table name"""
        join = JoinClause(
            type=JoinType.LEFT, table="public.user_profiles", alias="up", on="up.user_id = u.id"
        )

        assert join.to_sql() == "LEFT JOIN public.user_profiles AS up ON up.user_id = u.id"

    # Validation Tests
    def test_join_validation_empty_table_name(self):
        """Test validation fails for empty table name"""
        with pytest.raises(ValueError, match="Table name cannot be empty"):
            JoinClause(type=JoinType.INNER, table="", on="condition")

    def test_join_validation_whitespace_table_name(self):
        """Test validation fails for whitespace-only table name"""
        with pytest.raises(ValueError, match="Table name cannot be empty"):
            JoinClause(type=JoinType.INNER, table="   ", on="condition")

    def test_join_validation_invalid_alias(self):
        """Test validation fails for invalid alias"""
        with pytest.raises(ValueError, match="Invalid alias"):
            JoinClause(type=JoinType.INNER, table="users", alias="123invalid", on="condition")

    def test_join_validation_alias_with_spaces(self):
        """Test validation fails for alias with spaces"""
        with pytest.raises(ValueError, match="Invalid alias"):
            JoinClause(type=JoinType.INNER, table="users", alias="user alias", on="condition")

    def test_join_validation_alias_with_special_chars(self):
        """Test validation fails for alias with special characters"""
        with pytest.raises(ValueError, match="Invalid alias"):
            JoinClause(type=JoinType.INNER, table="users", alias="user-alias", on="condition")

    def test_join_validation_empty_on_condition(self):
        """Test validation fails for empty ON condition"""
        with pytest.raises(ValueError, match="JoinClause requires a valid ON condition"):
            JoinClause(type=JoinType.INNER, table="users", on="")

    def test_join_validation_whitespace_on_condition(self):
        """Test validation fails for whitespace-only ON condition"""
        with pytest.raises(ValueError, match="JoinClause requires a valid ON condition"):
            JoinClause(type=JoinType.INNER, table="users", on="   ")

    def test_join_validation_none_on_condition(self):
        """Test validation fails for None ON condition"""
        with pytest.raises(ValueError, match="JoinClause requires a valid ON condition"):
            JoinClause(type=JoinType.INNER, table="users", on=None)

    def test_join_valid_aliases(self):
        """Test various valid alias formats"""
        valid_aliases = ["u", "user_table", "USER_TABLE", "_private", "table123", "a"]

        for alias in valid_aliases:
            join = JoinClause(type=JoinType.INNER, table="users", alias=alias, on="condition")
            assert join.alias == alias

    # Serialization Tests
    def test_join_to_dict_with_alias(self):
        """Test to_dict method with alias"""
        join = JoinClause(
            type=JoinType.LEFT, table="profiles", alias="p", on="p.user_id = u.id", use_as=False
        )
        result = join.to_dict()

        expected = {
            "type": "LEFT",
            "table": "profiles",
            "alias": "p",
            "on": "p.user_id = u.id",
            "use_as": False,
        }
        assert result == expected

    def test_join_to_dict_without_alias(self):
        """Test to_dict method without alias"""
        join = JoinClause(type=JoinType.INNER, table="orders", on="orders.user_id = users.id")
        result = join.to_dict()

        expected = {
            "type": "INNER",
            "table": "orders",
            "alias": None,
            "on": "orders.user_id = users.id",
            "use_as": True,
        }
        assert result == expected

    def test_join_from_dict_with_alias(self):
        """Test from_dict method with alias"""
        data = {
            "type": "RIGHT",
            "table": "departments",
            "alias": "dept",
            "on": "dept.id = emp.department_id",
            "use_as": True,
        }
        join = JoinClause.from_dict(data)

        assert join.type == JoinType.RIGHT
        assert join.table == "departments"
        assert join.alias == "dept"
        assert join.on == "dept.id = emp.department_id"
        assert join.use_as is True

    def test_join_from_dict_without_alias(self):
        """Test from_dict method without alias"""
        data = {"type": "FULL", "table": "categories", "on": "categories.id = products.category_id"}
        join = JoinClause.from_dict(data)

        assert join.type == JoinType.FULL
        assert join.table == "categories"
        assert join.alias is None
        assert join.on == "categories.id = products.category_id"
        assert join.use_as is True  # Default value

    def test_join_from_dict_partial_data(self):
        """Test from_dict method with partial data (missing optional fields)"""
        data = {"type": "INNER", "table": "users", "on": "users.id = orders.user_id"}
        join = JoinClause.from_dict(data)

        assert join.type == JoinType.INNER
        assert join.table == "users"
        assert join.alias is None
        assert join.on == "users.id = orders.user_id"
        assert join.use_as is True

    def test_join_serialization_roundtrip(self):
        """Test that to_dict/from_dict roundtrip works correctly"""
        original_join = JoinClause(
            type=JoinType.LEFT,
            table="user_profiles",
            alias="up",
            on="up.user_id = u.id AND up.is_active = true",
            use_as=False,
        )

        # Serialize and deserialize
        data = original_join.to_dict()
        restored_join = JoinClause.from_dict(data)

        # Verify they produce the same SQL
        assert original_join.to_sql() == restored_join.to_sql()
        assert original_join.type == restored_join.type
        assert original_join.table == restored_join.table
        assert original_join.alias == restored_join.alias
        assert original_join.on == restored_join.on
        assert original_join.use_as == restored_join.use_as


class TestJoinClauseEdgeCases:
    """Test edge cases and complex scenarios"""

    def test_all_join_types_sql_generation(self):
        """Test SQL generation for all JOIN types"""
        join_configs = [
            (JoinType.INNER, "INNER JOIN"),
            (JoinType.LEFT, "LEFT JOIN"),
            (JoinType.RIGHT, "RIGHT JOIN"),
            (JoinType.FULL, "FULL JOIN"),
        ]

        for join_type, expected_prefix in join_configs:
            join = JoinClause(
                type=join_type, table="test_table", alias="t", on="t.id = main.test_id"
            )
            sql = join.to_sql()
            assert sql.startswith(expected_prefix)
            assert "test_table AS t" in sql
            assert "ON t.id = main.test_id" in sql

    def test_join_with_long_table_names(self):
        """Test JOIN with very long table names"""
        long_table_name = "very_long_table_name_with_many_characters_and_underscores"
        join = JoinClause(
            type=JoinType.INNER, table=long_table_name, alias="vlt", on="vlt.id = main.ref_id"
        )

        expected_sql = f"INNER JOIN {long_table_name} AS vlt ON vlt.id = main.ref_id"
        assert join.to_sql() == expected_sql

    def test_join_with_complex_on_conditions(self):
        """Test JOIN with various complex ON conditions"""
        complex_conditions = [
            "t1.id = t2.ref_id AND t1.status = 'active'",
            "t1.user_id = t2.id AND t1.created_at > t2.last_login",
            "t1.category_id = t2.id AND (t1.price > 100 OR t1.discount > 0.1)",
            "COALESCE(t1.parent_id, 0) = t2.id",
        ]

        for condition in complex_conditions:
            join = JoinClause(type=JoinType.LEFT, table="test_table", alias="t1", on=condition)
            sql = join.to_sql()
            assert condition in sql
            assert sql.endswith(f"ON {condition}")

    def test_join_case_sensitivity(self):
        """Test that JOIN preserves case sensitivity in table names and conditions"""
        join = JoinClause(
            type=JoinType.INNER, table="CamelCaseTable", alias="CCT", on="CCT.UserId = Users.ID"
        )

        sql = join.to_sql()
        assert "CamelCaseTable" in sql
        assert "CCT" in sql
        assert "CCT.UserId = Users.ID" in sql

    def test_join_with_numbers_in_names(self):
        """Test JOIN with numbers in table names and aliases"""
        join = JoinClause(
            type=JoinType.LEFT, table="table_v2", alias="t2", on="t2.id = main.table2_id"
        )

        assert join.to_sql() == "LEFT JOIN table_v2 AS t2 ON t2.id = main.table2_id"

    def test_join_minimal_valid_configuration(self):
        """Test JOIN with minimal valid configuration"""
        join = JoinClause(type=JoinType.INNER, table="t", on="1=1")

        assert join.to_sql() == "INNER JOIN t ON 1=1"
        assert join.alias is None
        assert join.use_as is True
