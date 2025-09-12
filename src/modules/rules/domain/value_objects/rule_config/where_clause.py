from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

from .common import SqlExpression


class ComparisonOperator(Enum):
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class LogicalOperator(Enum):
    AND = "AND"
    OR = "OR"


# -------------------------------
# WHERE Condition
# -------------------------------
# ============================================================
# WHERE
# ============================================================
@dataclass(frozen=True)
class WhereCondition:
    field: str | SqlExpression
    operator: ComparisonOperator
    value: str | int | float | bool | list[Any] | datetime | date | None

    def __post_init__(self):
        if isinstance(self.field, str) and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", self.field):
            raise ValueError(f"Invalid field name: {self.field}")

        if (
            self.operator in {ComparisonOperator.IS_NULL, ComparisonOperator.IS_NOT_NULL}
            and self.value is not None
        ):
            raise ValueError(f"{self.operator.value} cannot have a value")

        if self.operator in {ComparisonOperator.IN, ComparisonOperator.NOT_IN}:
            if not isinstance(self.value, list) or not self.value:
                raise ValueError(f"{self.operator.value} requires a non-empty list")

        if self.operator is ComparisonOperator.BETWEEN:
            if not isinstance(self.value, list) or len(self.value) != 2:
                raise ValueError("BETWEEN requires exactly 2 values")
            if not isinstance(self.value[0], type(self.value[1])):
                raise ValueError("BETWEEN values must have the same type")

    def _format_value(self, val: Any) -> str:
        result: str

        if val is None:
            result = "NULL"
        elif isinstance(val, bool):
            result = "TRUE" if val else "FALSE"
        elif isinstance(val, (int, float)):
            result = str(val)
        elif isinstance(val, str):
            safe = val.replace("'", "''")
            result = f"'{safe}'"
        elif isinstance(val, datetime):
            result = f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(val, date):
            result = f"'{val.strftime('%Y-%m-%d')}'"
        elif isinstance(val, SqlExpression):
            result = val.to_sql()
        else:
            raise ValueError(f"Unsupported value type: {type(val)}")

        return result

    def to_sql(self) -> str:
        field_sql = self.field.to_sql() if isinstance(self.field, SqlExpression) else self.field
        if self.operator in {ComparisonOperator.IS_NULL, ComparisonOperator.IS_NOT_NULL}:
            return f"{field_sql} {self.operator.value}"
        if self.operator in {ComparisonOperator.IN, ComparisonOperator.NOT_IN}:
            values_str = ", ".join(self._format_value(v) for v in self.value)
            return f"{field_sql} {self.operator.value} ({values_str})"
        if self.operator == ComparisonOperator.BETWEEN:
            v1, v2 = self.value
            return f"{field_sql} BETWEEN {self._format_value(v1)} AND {self._format_value(v2)}"
        return f"{field_sql} {self.operator.value} {self._format_value(self.value)}"

    def to_dict(self) -> dict:
        return {
            "field": self.field.to_dict() if isinstance(self.field, SqlExpression) else self.field,
            "operator": self.operator.value,
            "value": (
                [v.to_dict() if isinstance(v, SqlExpression) else v for v in self.value]
                if isinstance(self.value, list)
                else self.value.to_dict()
                if isinstance(self.value, SqlExpression)
                else self.value
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> WhereCondition:
        field = data["field"]
        if isinstance(field, dict):
            field = SqlExpression.from_dict(field)

        value = data.get("value")
        if isinstance(value, dict) and "function" in value:
            value = SqlExpression.from_dict(value)
        elif isinstance(value, list):
            value = [
                SqlExpression.from_dict(v) if isinstance(v, dict) and "function" in v else v
                for v in value
            ]

        return cls(field=field, operator=ComparisonOperator(data["operator"]), value=value)


@dataclass(frozen=True)
class WhereClause:
    conditions: list[WhereCondition | WhereClause]
    logical_operator: LogicalOperator = LogicalOperator.AND

    def __post_init__(self):
        if not self.conditions:
            raise ValueError("WhereClause must have at least one condition")
        if len(self.conditions) > 1 and not self.logical_operator:
            raise ValueError("Logical operator required for multiple conditions")

    def to_sql(self) -> str:
        if len(self.conditions) == 1:
            return self.conditions[0].to_sql()
        parts = [
            f"({c.to_sql()})"
            if isinstance(c, WhereClause) and len(c.conditions) > 1
            else c.to_sql()
            for c in self.conditions
        ]
        return f" {self.logical_operator.value} ".join(parts)

    def to_dict(self) -> dict:
        return {
            "logical_operator": self.logical_operator.value,
            "conditions": [c.to_dict() for c in self.conditions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> WhereClause:
        conditions = []
        for c in data["conditions"]:
            if "operator" in c:  # WhereCondition
                conditions.append(WhereCondition.from_dict(c))
            else:  # nested WhereClause
                conditions.append(WhereClause.from_dict(c))
        return cls(
            conditions=conditions,
            logical_operator=LogicalOperator(data["logical_operator"]),
        )


@dataclass
class ConditionsClause:
    where: list[WhereCondition | WhereClause] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.where, list):
            raise ValueError("ConditionsClause.where must be a list")

    def to_sql(self) -> str:
        if not self.where:
            return ""
        if len(self.where) == 1:
            return f"WHERE {self.where[0].to_sql()}"
        return "WHERE " + " AND ".join(
            f"({c.to_sql()})"
            if isinstance(c, WhereClause) and len(c.conditions) > 1
            else c.to_sql()
            for c in self.where
        )

    def to_dict(self) -> dict:
        return {"where": [c.to_dict() for c in self.where]}

    @classmethod
    def from_dict(cls, data: dict) -> ConditionsClause:
        where = []
        for c in data.get("where", []):
            if "operator" in c:
                where.append(WhereCondition.from_dict(c))
            else:
                where.append(WhereClause.from_dict(c))
        return cls(where=where)
