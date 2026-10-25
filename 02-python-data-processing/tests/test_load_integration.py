
import os

import pandas as pd
import pytest
from sqlalchemy import text

from load_to_db import get_engine, load, transform


def test_load_rolls_back_when_insert_fails(monkeypatch):
    """A failed insert must preserve the previously loaded records."""
    if os.getenv("RUN_DB_TESTS") != "1":
        pytest.skip("Set RUN_DB_TESTS=1 to enable PostgreSQL integration tests.")

    engine = get_engine()

    try:
        if engine.url.database != "ecommerce_etl":
            pytest.fail(
                "Safety check failed: integration tests may only use "
                "the ecommerce_etl database."
            )

        with engine.connect() as connection:
            before_ids = connection.execute(
                text("SELECT order_id FROM orders ORDER BY order_id")
            ).scalars().all()

        assert before_ids, "Expected existing records before rollback test."

        incoming_df = transform(
            pd.DataFrame(
                [
                    {
                        "order_id": "9999",
                        "order_date": "2026-10-26",
                        "customer_id": "C999",
                        "product": "Test Product",
                        "category": "Testing",
                        "quantity": "1",
                        "unit_price": "1000",
                    }
                ]
            )
        )

        def fail_insert(*args, **kwargs):
            raise RuntimeError("Simulated insert failure")

        monkeypatch.setattr(pd.DataFrame, "to_sql", fail_insert)

        with pytest.raises(RuntimeError, match="Simulated insert failure"):
            load(incoming_df, engine)

        with engine.connect() as connection:
            after_ids = connection.execute(
                text("SELECT order_id FROM orders ORDER BY order_id")
            ).scalars().all()

        assert after_ids == before_ids

    finally:
        engine.dispose()