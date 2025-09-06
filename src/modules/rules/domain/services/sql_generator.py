import re
from typing import Any

from modules.rules.domain.value_objects.rule_config import (
    ComparisonOperator,
    JoinType,
    LogicalOperator,
    RuleConfig,
    WhereCondition,
)


class SqlGenerator:
    """Service to generate SQL queries from RuleConfig"""

    def generate_sql(self, config: RuleConfig, parameters: dict[str, Any] = None) -> str:
        """
        Generates SQL query from RuleConfig

        Args:
            config: The RuleConfig to convert to SQL
            parameters: Dictionary of parameter values to substitute

        Returns:
            Generated SQL query string

        """
        if parameters is None:
            parameters = {}

        # Validate config before generating SQL
        config.validate()

        # Build SQL parts
        select_clause = self._build_select_clause(config)
        from_clause = self._build_from_clause(config)
        joins_clause = self._build_joins_clause(config)
        where_clause = self._build_where_clause(config, parameters)
        group_by_clause = self._build_group_by_clause(config)
        having_clause = self._build_having_clause(config, parameters)
        order_by_clause = self._build_order_by_clause(config)

        # Combine all parts
        sql_parts = [select_clause, from_clause]

        if joins_clause:
            sql_parts.append(joins_clause)
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if having_clause:
            sql_parts.append(having_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)

        return "\n".join(sql_parts)

    def validate_sql_syntax(self, sql: str) -> dict[str, Any]:
        """
        Validates SQL syntax and returns validation results

        Args:
            sql: The SQL query string to validate

        Returns:
            Dictionary containing validation results with keys:
            - is_valid: Boolean indicating if SQL is valid
            - errors: List of validation error messages
            - warnings: List of potential issues or warnings

        """
        errors = []
        warnings = []

        # Remove extra whitespace and normalize
        sql = re.sub(r"\s+", " ", sql.strip())

        if not sql:
            errors.append("SQL query cannot be empty")
            return {"is_valid": False, "errors": errors, "warnings": warnings}

        # Basic SQL structure validation
        errors.extend(self._validate_basic_structure(sql))
        errors.extend(self._validate_keywords(sql))
        errors.extend(self._validate_parentheses(sql))
        errors.extend(self._validate_quotes(sql))
        errors.extend(self._validate_identifiers(sql))

        # Generate warnings for potential issues
        warnings.extend(self._check_potential_issues(sql))

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _validate_basic_structure(self, sql: str) -> list[str]:
        """Validates basic SQL structure"""
        errors = []
        sql_upper = sql.upper()

        # Check if it starts with a valid SQL command
        valid_starts = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH", "CREATE", "ALTER", "DROP"]
        if not any(sql_upper.startswith(start) for start in valid_starts):
            errors.append(
                "SQL must start with a valid command (SELECT, INSERT, UPDATE, DELETE, etc.)"
            )

        # For SELECT statements, check basic structure
        if sql_upper.startswith("SELECT"):
            if "FROM" not in sql_upper:
                errors.append("SELECT statement must contain a FROM clause")

        return errors

    def _validate_keywords(self, sql: str) -> list[str]:
        """Validates SQL keywords and their usage"""
        errors = []
        sql_upper = sql.upper()

        # Check for common SQL injection patterns
        dangerous_patterns = [
            r";\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER)",
            r"UNION\s+SELECT",
            r"--\s*$",
            r"/\*.*\*/",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                errors.append(f"Potentially dangerous SQL pattern detected: {pattern}")

        # Check for proper keyword spacing
        if re.search(r"\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING)\b\s*$", sql_upper):
            errors.append("SQL keywords cannot be at the end without proper clauses")

        return errors

    def _validate_parentheses(self, sql: str) -> list[str]:
        """Validates parentheses matching"""
        errors = []

        # Count parentheses
        open_count = sql.count("(")
        close_count = sql.count(")")

        if open_count != close_count:
            errors.append(f"Mismatched parentheses: {open_count} opening, {close_count} closing")

        # Check for proper nesting
        level = 0
        for char in sql:
            if char == "(":
                level += 1
            elif char == ")":
                level -= 1
                if level < 0:
                    errors.append("Closing parenthesis without matching opening parenthesis")
                    break

        return errors

    def _validate_quotes(self, sql: str) -> list[str]:
        """Validates quote matching"""
        errors = []

        # Check single quotes
        single_quote_count = sql.count("'")
        if single_quote_count % 2 != 0:
            errors.append("Unmatched single quotes in SQL")

        # Check double quotes
        double_quote_count = sql.count('"')
        if double_quote_count % 2 != 0:
            errors.append("Unmatched double quotes in SQL")

        return errors

    def _validate_identifiers(self, sql: str) -> list[str]:
        """Validates SQL identifiers (table names, column names, etc.)"""
        errors = []

        # Check for invalid identifier patterns
        # SQL identifiers should not start with numbers (unless quoted)
        identifier_pattern = r"\b\d+[a-zA-Z_][a-zA-Z0-9_]*\b"
        if re.search(identifier_pattern, sql):
            errors.append("Invalid identifier: identifiers cannot start with numbers")

        # Check for reserved words used as identifiers (basic check)
        reserved_words = ["SELECT", "FROM", "WHERE", "GROUP", "ORDER", "BY", "HAVING", "JOIN", "ON"]
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", sql.upper())

        for word in words:
            if word in reserved_words:
                # This is a warning rather than error as it might be intentional
                pass

        return errors

    def _check_potential_issues(self, sql: str) -> list[str]:
        """Checks for potential issues that might not be syntax errors but could cause problems"""
        warnings = []
        sql_upper = sql.upper()

        # Check for SELECT * which might be inefficient
        if "SELECT *" in sql_upper:
            warnings.append(
                "Using SELECT * might be inefficient; consider specifying columns explicitly"
            )

        # Check for missing WHERE clause in UPDATE/DELETE
        if ("UPDATE" in sql_upper or "DELETE" in sql_upper) and "WHERE" not in sql_upper:
            warnings.append("UPDATE/DELETE without WHERE clause will affect all rows")

        # Check for potential Cartesian products
        if "JOIN" not in sql_upper and sql_upper.count("FROM") == 1 and "," in sql:
            table_count = len([t for t in sql.split(",") if "FROM" not in t.upper()])
            if table_count > 1:
                warnings.append(
                    "Multiple tables without explicit JOIN might create Cartesian product"
                )

        # Check for very long queries
        if len(sql) > 1000:
            warnings.append("Very long SQL query; consider breaking into smaller parts")

        return warnings

    def _build_select_clause(self, config: RuleConfig) -> str:
        """Builds the SELECT clause"""
        fields = []
        for field in config.select.fields:
            if field.alias:
                fields.append(f"{field.expression} AS {field.alias}")
            else:
                fields.append(field.expression)

        return f"SELECT {', '.join(fields)}"

    def _build_from_clause(self, config: RuleConfig) -> str:
        """Builds the FROM clause"""
        if config.from_table.alias:
            return f"FROM {config.from_table.main_table} {config.from_table.alias}"
        return f"FROM {config.from_table.main_table}"

    def _build_joins_clause(self, config: RuleConfig) -> str:
        """Builds the JOIN clauses"""
        if not config.joins:
            return ""

        join_parts = []
        for join in config.joins:
            join_type = self._get_join_type_sql(join.type)
            table_part = f"{join.table}"
            if join.alias:
                table_part += f" {join.alias}"

            join_parts.append(f"{join_type} {table_part} ON {join.on}")

        return "\n".join(join_parts)

    def _build_where_clause(self, config: RuleConfig, parameters: dict[str, Any]) -> str:
        """Builds the WHERE clause"""
        if not config.conditions.where:
            return ""

        conditions = []
        for i, condition in enumerate(config.conditions.where):
            condition_sql = self._build_condition_sql(condition, parameters)

            if i == 0:
                conditions.append(condition_sql)
            else:
                logical_op = self._get_logical_operator_sql(condition.logical_operator)
                conditions.append(f"{logical_op} {condition_sql}")

        return f"WHERE {' '.join(conditions)}"

    def _build_group_by_clause(self, config: RuleConfig) -> str:
        """Builds the GROUP BY clause"""
        if not config.group_by:
            return ""

        return f"GROUP BY {', '.join(config.group_by)}"

    def _build_having_clause(self, config: RuleConfig, parameters: dict[str, Any]) -> str:
        """Builds the HAVING clause"""
        if not config.having:
            return ""

        conditions = []
        for i, condition in enumerate(config.having):
            condition_sql = self._build_having_condition_sql(condition, parameters)

            if i == 0:
                conditions.append(condition_sql)
            else:
                conditions.append(f"AND {condition_sql}")

        return f"HAVING {' '.join(conditions)}"

    def _build_order_by_clause(self, config: RuleConfig) -> str:
        """Builds the ORDER BY clause"""
        if not config.order_by:
            return ""

        order_parts = []
        for order in config.order_by:
            direction = order.direction.value if order.direction else "ASC"
            order_parts.append(f"{order.field} {direction}")

        return f"ORDER BY {', '.join(order_parts)}"

    def _build_condition_sql(self, condition: WhereCondition, parameters: dict[str, Any]) -> str:
        """Builds SQL for a single WHERE condition"""
        field = condition.field
        operator = self._get_comparison_operator_sql(condition.operator)
        value = self._format_value(condition.value, parameters)

        if condition.operator == ComparisonOperator.BETWEEN:
            if isinstance(condition.value, list) and len(condition.value) == 2:
                value1 = self._format_value(condition.value[0], parameters)
                value2 = self._format_value(condition.value[1], parameters)
                return f"{field} BETWEEN {value1} AND {value2}"
            raise ValueError("BETWEEN operator requires a list of exactly 2 values")
        if condition.operator in [ComparisonOperator.IN, ComparisonOperator.NOT_IN]:
            if isinstance(condition.value, list):
                formatted_values = [self._format_value(v, parameters) for v in condition.value]
                value_list = f"({', '.join(formatted_values)})"
                return f"{field} {operator} {value_list}"
            return f"{field} {operator} ({value})"
        if condition.operator in [ComparisonOperator.IS_NULL, ComparisonOperator.IS_NOT_NULL]:
            return f"{field} {operator}"
        return f"{field} {operator} {value}"

    def _build_having_condition_sql(
        self, condition: WhereCondition, parameters: dict[str, Any]
    ) -> str:
        """Builds SQL for a single HAVING condition"""
        field = condition.field
        operator = self._get_comparison_operator_sql(condition.operator)
        value = self._format_value(condition.value, parameters)

        return f"{field} {operator} {value}"

    def _format_value(self, value: Any, parameters: dict[str, Any]) -> str:
        """Formats a value for SQL, handling parameter substitution"""
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            # Parameter substitution
            param_name = value[2:-2]
            if param_name in parameters:
                return self._format_literal_value(parameters[param_name])
            # Keep parameter placeholder for later substitution
            return value
        return self._format_literal_value(value)

    def _format_literal_value(self, value: Any) -> str:
        """Formats a literal value for SQL"""
        if value is None:
            return "NULL"
        if isinstance(value, str):
            # Escape single quotes in strings
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            return str(value)
        # For other types, convert to string and quote
        return f"'{value!s}'"

    def _get_join_type_sql(self, join_type: JoinType) -> str:
        """Converts JoinType enum to SQL"""
        mapping = {
            JoinType.INNER: "INNER JOIN",
            JoinType.LEFT: "LEFT JOIN",
            JoinType.RIGHT: "RIGHT JOIN",
            JoinType.FULL: "FULL OUTER JOIN",
        }
        return mapping.get(join_type, "INNER JOIN")

    def _get_comparison_operator_sql(self, operator: ComparisonOperator) -> str:
        """Converts ComparisonOperator enum to SQL"""
        mapping = {
            ComparisonOperator.EQUAL: "=",
            ComparisonOperator.NOT_EQUAL: "!=",
            ComparisonOperator.GREATER_THAN: ">",
            ComparisonOperator.GREATER_EQUAL: ">=",
            ComparisonOperator.LESS_THAN: "<",
            ComparisonOperator.LESS_EQUAL: "<=",
            ComparisonOperator.IN: "IN",
            ComparisonOperator.NOT_IN: "NOT IN",
            ComparisonOperator.LIKE: "LIKE",
            ComparisonOperator.NOT_LIKE: "NOT LIKE",
            ComparisonOperator.BETWEEN: "BETWEEN",
            ComparisonOperator.IS_NULL: "IS NULL",
            ComparisonOperator.IS_NOT_NULL: "IS NOT NULL",
        }
        return mapping.get(operator, "=")

    def _get_logical_operator_sql(self, operator: LogicalOperator) -> str:
        """Converts LogicalOperator enum to SQL"""
        if operator is None:
            return ""

        mapping = {LogicalOperator.AND: "AND", LogicalOperator.OR: "OR"}
        return mapping.get(operator, "AND")
