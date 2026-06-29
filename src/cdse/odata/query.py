"""Builders for OData ``$filter`` and ``$orderby`` expressions.

These helpers assemble the query strings that the OData API expects while taking
care of the awkward details: escaping string literals, formatting timestamps,
and choosing the correct attribute type. A raw escape hatch is always available
through :meth:`FilterBuilder.raw` for expressions that are not covered here.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal

#: The comparison operators OData supports in a filter expression.
ComparisonOperator = Literal["eq", "ne", "lt", "le", "gt", "ge"]

#: Sort direction for an ``$orderby`` clause.
SortDirection = Literal["asc", "desc"]


def escape_literal(value: str) -> str:
    """Escape a string for use inside a single quoted OData literal.

    OData escapes a single quote by doubling it.
    """
    return value.replace("'", "''")


def _format_datetime(value: datetime | date) -> str:
    """Format a date or datetime as an OData ``DateTimeOffset`` literal."""
    if isinstance(value, datetime):
        moment = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    else:
        moment = datetime(value.year, value.month, value.day, tzinfo=UTC)
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _attribute_type(value: int | float | str | datetime | date) -> str:
    """Return the OData attribute type name for a Python value."""
    # bool is a subclass of int, but the API has no boolean attribute type, so
    # it is treated as an integer here.
    if isinstance(value, datetime | date):
        return "DateTimeOffset"
    if isinstance(value, bool | int):
        return "Integer"
    if isinstance(value, float):
        return "Double"
    return "String"


def _attribute_literal(value: int | float | str | datetime | date) -> str:
    """Format a value as it should appear on the right hand side of a filter."""
    if isinstance(value, datetime | date):
        return _format_datetime(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    return f"'{escape_literal(value)}'"


class FilterBuilder:
    """Accumulate filter conditions and join them with a logical ``and``."""

    def __init__(self) -> None:
        self._conditions: list[str] = []

    def raw(self, expression: str) -> FilterBuilder:
        """Add a raw filter expression verbatim."""
        self._conditions.append(expression)
        return self

    def name(self, value: str) -> FilterBuilder:
        """Match products whose name equals ``value`` exactly."""
        self._conditions.append(f"Name eq '{escape_literal(value)}'")
        return self

    def name_contains(self, value: str) -> FilterBuilder:
        """Match products whose name contains ``value``."""
        self._conditions.append(f"contains(Name,'{escape_literal(value)}')")
        return self

    def collection(self, name: str) -> FilterBuilder:
        """Restrict the query to a collection, for example ``SENTINEL-2``."""
        self._conditions.append(f"Collection/Name eq '{escape_literal(name)}'")
        return self

    def online(self, value: bool = True) -> FilterBuilder:
        """Match products by their online (immediately available) status."""
        self._conditions.append(f"Online eq {'true' if value else 'false'}")
        return self

    def acquired_between(
        self, start: datetime | date, end: datetime | date
    ) -> FilterBuilder:
        """Match products sensed within the given range (inclusive)."""
        self._conditions.append(f"ContentDate/Start ge {_format_datetime(start)}")
        self._conditions.append(f"ContentDate/Start le {_format_datetime(end)}")
        return self

    def published_between(
        self, start: datetime | date, end: datetime | date
    ) -> FilterBuilder:
        """Match products published within the given range (inclusive)."""
        self._conditions.append(f"PublicationDate ge {_format_datetime(start)}")
        self._conditions.append(f"PublicationDate le {_format_datetime(end)}")
        return self

    def intersects(self, geometry: str, *, srid: int = 4326) -> FilterBuilder:
        """Match products intersecting a WKT geometry, for example a polygon."""
        self._conditions.append(
            f"OData.CSC.Intersects(area=geography'SRID={srid};{geometry}')"
        )
        return self

    def attribute(
        self,
        name: str,
        operator: ComparisonOperator,
        value: int | float | str | datetime | date,
    ) -> FilterBuilder:
        """Match products by a named attribute, choosing the type automatically.

        For example ``attribute("cloudCover", "le", 40.0)`` filters on cloud
        cover. The attribute type is inferred from the Python value.
        """
        type_name = _attribute_type(value)
        literal = _attribute_literal(value)
        self._conditions.append(
            f"Attributes/OData.CSC.{type_name}Attribute/any("
            f"att:att/Name eq '{escape_literal(name)}' and "
            f"att/OData.CSC.{type_name}Attribute/Value {operator} {literal})"
        )
        return self

    def build(self) -> str:
        """Return the combined filter expression."""
        return " and ".join(self._conditions)

    def __str__(self) -> str:
        return self.build()

    def __bool__(self) -> bool:
        return bool(self._conditions)


def build_orderby(field: str, direction: SortDirection = "asc") -> str:
    """Build an ``$orderby`` clause, for example ``ContentDate/Start desc``."""
    return f"{field} {direction}"
