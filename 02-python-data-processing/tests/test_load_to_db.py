
import pandas as pd
import pytest

from load_to_db import EXPECTED_COLUMNS, transform


@pytest.fixture
def valid_orders():
    return pd.DataFrame(
        [
            {
                "order_id": "1002",
                "order_date": "2026-10-02",
                "customer_id": " C002 ",
                "product": " Keyboard ",
                "category": " Accessories ",
                "quantity": "1",
                "unit_price": "450000",
            },
            {
                "order_id": "1001",
                "order_date": "2026-10-01",
                "customer_id": "C001",
                "product": "Mouse",
                "category": "Accessories",
                "quantity": "2",
                "unit_price": "150000",
            },
        ],
        columns=EXPECTED_COLUMNS,
    )


def test_transform_normalizes_and_sorts_rows(valid_orders):
    result = transform(valid_orders)

    assert result["order_id"].tolist() == [1001, 1002]
    assert result["customer_id"].tolist() == ["C001", "C002"]
    assert result["product"].tolist() == ["Mouse", "Keyboard"]
    assert result["order_date"].iloc[0].isoformat() == "2026-10-01"


@pytest.mark.parametrize(
    "invalid_date",
    [
        "2026-13-01",
        "2026-02-30",
        "2026-1-1",
        "",
        "not-a-date",
    ],
)
def test_transform_rejects_invalid_dates(valid_orders, invalid_date):
    valid_orders.loc[0, "order_date"] = invalid_date

    with pytest.raises(ValueError, match="order_date"):
        transform(valid_orders)


def test_transform_rejects_duplicate_order_ids(valid_orders):
    valid_orders.loc[1, "order_id"] = "1002"

    with pytest.raises(ValueError, match="Duplicate order_id"):
        transform(valid_orders)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("order_id", "0"),
        ("quantity", "0"),
        ("quantity", "-1"),
        ("quantity", "1.5"),
        ("unit_price", "-100"),
        ("unit_price", "invalid"),
    ],
)
def test_transform_rejects_invalid_numeric_values(
    valid_orders, column, value
):
    valid_orders.loc[0, column] = value

    with pytest.raises(ValueError):
        transform(valid_orders)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("customer_id", "   "),
        ("product", ""),
        ("category", "  "),
    ],
)
def test_transform_rejects_blank_text(valid_orders, column, value):
    valid_orders.loc[0, column] = value

    with pytest.raises(ValueError, match=column):
        transform(valid_orders)


def test_transform_rejects_missing_columns(valid_orders):
    invalid_df = valid_orders.drop(columns=["category"])

    with pytest.raises(ValueError, match="Invalid input schema"):
        transform(invalid_df)


def test_transform_rejects_empty_dataframe():
    empty_df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    with pytest.raises(ValueError, match="empty"):
        transform(empty_df)