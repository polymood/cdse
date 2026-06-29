"""Tests for the OData filter and order builders."""

from __future__ import annotations

from datetime import UTC, date, datetime

from cdse.odata.query import FilterBuilder, build_orderby, escape_literal


def test_escape_literal_doubles_single_quotes() -> None:
    assert escape_literal("O'Brien") == "O''Brien"


def test_name_and_collection_conditions() -> None:
    expression = (
        FilterBuilder().collection("SENTINEL-2").name_contains("MSIL2A").build()
    )
    assert expression == "Collection/Name eq 'SENTINEL-2' and contains(Name,'MSIL2A')"


def test_online_condition() -> None:
    assert FilterBuilder().online().build() == "Online eq true"
    assert FilterBuilder().online(False).build() == "Online eq false"


def test_acquired_between_uses_inclusive_bounds() -> None:
    expression = (
        FilterBuilder().acquired_between(date(2022, 5, 3), date(2022, 5, 4)).build()
    )
    assert expression == (
        "ContentDate/Start ge 2022-05-03T00:00:00Z and "
        "ContentDate/Start le 2022-05-04T00:00:00Z"
    )


def test_naive_datetime_is_treated_as_utc() -> None:
    expression = (
        FilterBuilder()
        .published_between(
            datetime(2022, 1, 1, 12, 0, 0),
            datetime(2022, 1, 2, 12, 0, 0, tzinfo=UTC),
        )
        .build()
    )
    assert "PublicationDate ge 2022-01-01T12:00:00Z" in expression
    assert "PublicationDate le 2022-01-02T12:00:00Z" in expression


def test_intersects_builds_geography_literal() -> None:
    expression = FilterBuilder().intersects("POINT(4 50)").build()
    assert expression == ("OData.CSC.Intersects(area=geography'SRID=4326;POINT(4 50)')")


def test_attribute_type_inference() -> None:
    double = FilterBuilder().attribute("cloudCover", "le", 40.0).build()
    assert "OData.CSC.DoubleAttribute" in double
    assert "att/OData.CSC.DoubleAttribute/Value le 40.0)" in double

    integer = FilterBuilder().attribute("orbitNumber", "eq", 12).build()
    assert "OData.CSC.IntegerAttribute" in integer

    text = FilterBuilder().attribute("productType", "eq", "S2MSI2A").build()
    assert "OData.CSC.StringAttribute" in text
    assert "Value eq 'S2MSI2A')" in text

    moment = (
        FilterBuilder()
        .attribute("beginningDateTime", "gt", datetime(2022, 1, 1, tzinfo=UTC))
        .build()
    )
    assert "OData.CSC.DateTimeOffsetAttribute" in moment
    assert "Value gt 2022-01-01T00:00:00Z)" in moment


def test_attribute_string_value_is_escaped() -> None:
    expression = FilterBuilder().attribute("name", "eq", "a'b").build()
    assert "Value eq 'a''b')" in expression


def test_raw_escape_hatch() -> None:
    assert FilterBuilder().raw("Foo eq 1").build() == "Foo eq 1"


def test_empty_builder_is_falsy() -> None:
    assert not FilterBuilder()
    assert FilterBuilder().name("x")


def test_build_orderby() -> None:
    assert build_orderby("ContentDate/Start", "desc") == "ContentDate/Start desc"
    assert build_orderby("PublicationDate") == "PublicationDate asc"
