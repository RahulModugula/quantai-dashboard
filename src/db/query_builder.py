"""Query builder for constructing database queries."""
import logging
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class ComparisonOperator(str, Enum):
    """Comparison operators."""

    EQ = "="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class LogicalOperator(str, Enum):
    """Logical operators."""

    AND = "AND"
    OR = "OR"


class SortOrder(str, Enum):
    """Sort order."""

    ASC = "ASC"
    DESC = "DESC"


class QueryBuilder:
    """Build SQL queries programmatically."""

    def __init__(self, table: str):
        """Initialize query builder.

        Args:
            table: Table name
        """
        self.table = table
        self.select_fields = []
        self.where_conditions = []
        self.where_operator = LogicalOperator.AND
        self.order_by_clauses = []
        self.limit_value = None
        self.offset_value = None
        self.join_clauses = []

    def select(self, *fields: str) -> "QueryBuilder":
        """Select specific fields.

        Args:
            fields: Field names

        Returns:
            Self for chaining
        """
        self.select_fields.extend(fields)
        return self

    def select_all(self) -> "QueryBuilder":
        """Select all fields.

        Returns:
            Self for chaining
        """
        self.select_fields = ["*"]
        return self

    def where(
        self,
        field: str,
        operator: Union[ComparisonOperator, str] = ComparisonOperator.EQ,
        value: Any = None,
    ) -> "QueryBuilder":
        """Add WHERE condition.

        Args:
            field: Field name
            operator: Comparison operator
            value: Value to compare

        Returns:
            Self for chaining
        """
        if isinstance(operator, ComparisonOperator):
            operator = operator.value

        self.where_conditions.append({"field": field, "operator": operator, "value": value})
        return self

    def where_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """Add WHERE IN condition.

        Args:
            field: Field name
            values: List of values

        Returns:
            Self for chaining
        """
        self.where(field, ComparisonOperator.IN, values)
        return self

    def where_like(self, field: str, pattern: str) -> "QueryBuilder":
        """Add WHERE LIKE condition.

        Args:
            field: Field name
            pattern: Search pattern

        Returns:
            Self for chaining
        """
        self.where(field, ComparisonOperator.LIKE, pattern)
        return self

    def where_is_null(self, field: str) -> "QueryBuilder":
        """Add WHERE IS NULL condition.

        Args:
            field: Field name

        Returns:
            Self for chaining
        """
        self.where_conditions.append({
            "field": field,
            "operator": ComparisonOperator.IS_NULL.value,
            "value": None,
        })
        return self

    def order_by(self, field: str, order: Union[SortOrder, str] = SortOrder.ASC) -> "QueryBuilder":
        """Add ORDER BY clause.

        Args:
            field: Field name
            order: Sort order

        Returns:
            Self for chaining
        """
        if isinstance(order, SortOrder):
            order = order.value

        self.order_by_clauses.append(f"{field} {order}")
        return self

    def limit(self, limit: int) -> "QueryBuilder":
        """Set LIMIT clause.

        Args:
            limit: Number of rows

        Returns:
            Self for chaining
        """
        self.limit_value = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """Set OFFSET clause.

        Args:
            offset: Number of rows to skip

        Returns:
            Self for chaining
        """
        self.offset_value = offset
        return self

    def join(
        self,
        table: str,
        on_condition: str,
        join_type: str = "INNER",
    ) -> "QueryBuilder":
        """Add JOIN clause.

        Args:
            table: Table to join
            on_condition: Join condition
            join_type: Type of join

        Returns:
            Self for chaining
        """
        self.join_clauses.append(f"{join_type} JOIN {table} ON {on_condition}")
        return self

    def build(self) -> str:
        """Build the SQL query.

        Returns:
            SQL query string
        """
        # SELECT clause
        fields = ", ".join(self.select_fields) if self.select_fields else "*"
        query = f"SELECT {fields} FROM {self.table}"

        # JOIN clauses
        for join in self.join_clauses:
            query += f" {join}"

        # WHERE clause
        if self.where_conditions:
            where_parts = []
            for condition in self.where_conditions:
                field = condition["field"]
                operator = condition["operator"]
                value = condition["value"]

                if operator in (ComparisonOperator.IS_NULL.value, ComparisonOperator.IS_NOT_NULL.value):
                    where_parts.append(f"{field} {operator}")
                elif operator in (ComparisonOperator.IN.value, ComparisonOperator.NOT_IN.value):
                    if isinstance(value, list):
                        values_str = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in value)
                        where_parts.append(f"{field} {operator} ({values_str})")
                else:
                    if isinstance(value, str):
                        where_parts.append(f"{field} {operator} '{value}'")
                    else:
                        where_parts.append(f"{field} {operator} {value}")

            query += " WHERE " + f" {self.where_operator.value} ".join(where_parts)

        # ORDER BY clause
        if self.order_by_clauses:
            query += " ORDER BY " + ", ".join(self.order_by_clauses)

        # LIMIT clause
        if self.limit_value is not None:
            query += f" LIMIT {self.limit_value}"

        # OFFSET clause
        if self.offset_value is not None:
            query += f" OFFSET {self.offset_value}"

        logger.debug(f"Built query: {query}")
        return query

    def to_dict(self) -> Dict[str, Any]:
        """Convert builder state to dictionary."""
        return {
            "table": self.table,
            "select_fields": self.select_fields,
            "where_conditions": self.where_conditions,
            "order_by_clauses": self.order_by_clauses,
            "limit": self.limit_value,
            "offset": self.offset_value,
        }
