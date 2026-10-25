
import csv
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "raw" / "orders.csv"
ENV_FILE = BASE_DIR / ".env"

TABLE_NAME = "orders"
EXPECTED_COLUMNS = (
    "order_id",
    "order_date",
    "customer_id",
    "product",
    "category",
    "quantity",
    "unit_price",
)
TEXT_COLUMNS = ("customer_id", "product", "category")
INTEGER_COLUMNS = ("order_id", "quantity", "unit_price")

MAX_BIGINT = 2**63 - 1
MAX_INTEGER = 2**31 - 1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """Build a PostgreSQL engine from local environment configuration."""
    load_dotenv(ENV_FILE)

    required_vars = (
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    )
    missing_vars = [
        name for name in required_vars if not os.getenv(name)
    ]

    if missing_vars:
        raise ValueError(
            "Missing database configuration: "
            + ", ".join(missing_vars)
        )

    try:
        port = int(os.environ["DB_PORT"])
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer.") from exc

    if not 1 <= port <= 65535:
        raise ValueError("DB_PORT must be between 1 and 65535.")

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=port,
        database=os.environ["DB_NAME"],
    )

    return create_engine(database_url, pool_pre_ping=True)


def extract() -> pd.DataFrame:
    """Read the CSV and validate its header structure."""
    if not DATA_FILE.is_file():
        raise FileNotFoundError(f"CSV file not found: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        header = next(csv.reader(file), None)

    if not header:
        raise ValueError("CSV file is empty or has no header.")

    if len(header) != len(set(header)):
        raise ValueError("CSV contains duplicate column names.")

    missing = sorted(set(EXPECTED_COLUMNS) - set(header))
    unexpected = sorted(set(header) - set(EXPECTED_COLUMNS))

    if missing or unexpected:
        raise ValueError(
            f"Invalid CSV schema. Missing: {missing}; "
            f"unexpected: {unexpected}"
        )

    df = pd.read_csv(
        DATA_FILE,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    if df.empty:
        raise ValueError("CSV contains no data rows.")

    logger.info("Extracted %d rows from %s", len(df), DATA_FILE.name)
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and validate records before loading."""
    if df.empty:
        raise ValueError("Cannot transform an empty dataset.")

    if len(df.columns) != len(set(df.columns)):
        raise ValueError("Input contains duplicate column names.")

    missing = sorted(set(EXPECTED_COLUMNS) - set(df.columns))
    unexpected = sorted(set(df.columns) - set(EXPECTED_COLUMNS))

    if missing or unexpected:
        raise ValueError(
            f"Invalid input schema. Missing: {missing}; "
            f"unexpected: {unexpected}"
        )

    result = df.loc[:, EXPECTED_COLUMNS].copy()

    # Normalize required text fields.
    for column in TEXT_COLUMNS:
        result[column] = result[column].astype("string").str.strip()

        if result[column].isna().any() or result[column].eq("").any():
            raise ValueError(
                f"Column '{column}' contains missing or blank values."
            )

    # Require an exact ISO date representation.
    raw_dates = result["order_date"].astype("string").str.strip()

    valid_format = raw_dates.str.fullmatch(
        r"\d{4}-\d{2}-\d{2}",
        na=False,
    )

    parsed_dates = pd.to_datetime(
        raw_dates.where(valid_format),
        format="%Y-%m-%d",
        errors="coerce",
    )

    invalid_dates = parsed_dates.isna()

    if invalid_dates.any():
        invalid_rows = invalid_dates.to_numpy().nonzero()[0] + 2
        raise ValueError(
            "Invalid or missing order_date at CSV row(s): "
            f"{invalid_rows.tolist()}"
        )

    result["order_date"] = parsed_dates.dt.date


    # Parse integer fields without floating-point conversion.
    for column in INTEGER_COLUMNS:
        raw_values = result[column].astype("string").str.strip()

        valid_format = raw_values.str.fullmatch(r"[+-]?\d+", na=False)

        if not valid_format.all():
            invalid_rows = valid_format.index[~valid_format].to_numpy() + 2
            raise ValueError(
                f"Column '{column}' contains invalid integers "
                f"at CSV row(s): {invalid_rows.tolist()}"
            )

        # Python int preserves precision for large integer values.
        parsed_values = raw_values.map(int)

        upper_bound = MAX_INTEGER if column == "quantity" else MAX_BIGINT
        out_of_range = parsed_values.map(
            lambda value: value < 0 or value > upper_bound
        )

        if out_of_range.any():
            invalid_rows = out_of_range.index[out_of_range].to_numpy() + 2
            raise ValueError(
                f"Column '{column}' contains values outside its "
                f"supported range at row(s): {invalid_rows.tolist()}"
            )

        result[column] = parsed_values.astype("int64")

    if result["order_id"].le(0).any():
        raise ValueError("order_id must be greater than zero.")

    if result["quantity"].le(0).any():
        raise ValueError("quantity must be greater than zero.")

    if result["unit_price"].lt(0).any():
        raise ValueError("unit_price cannot be negative.")

    duplicates = result.loc[
        result["order_id"].duplicated(keep=False), "order_id"
    ].tolist()

    if duplicates:
        raise ValueError(f"Duplicate order_id values: {duplicates}")

    result = result.sort_values("order_id").reset_index(drop=True)

    logger.info("Validated %d rows", len(result))
    return result


def validate_orders_constraints(connection) -> None:
    """Validate required CHECK constraints by their definitions."""
    rows = connection.execute(
        text(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = to_regclass(:table_name)
              AND contype = 'c'
            """
        ),
        {"table_name": TABLE_NAME},
    ).scalars().all()

    actual_definitions = {
        " ".join(definition.lower().split())
        for definition in rows
    }

    required_definitions = {
        "order_id must be positive": {
            "check ((order_id > 0))",
            "check ((order_id >= 1))",
        },
        "customer_id must not be blank": {
            "check ((btrim(customer_id) <> ''::text))",
        },
        "product must not be blank": {
            "check ((btrim(product) <> ''::text))",
        },
        "category must not be blank": {
            "check ((btrim(category) <> ''::text))",
        },
        "quantity must be positive": {
            "check ((quantity > 0))",
        },
        "unit_price must be nonnegative": {
            "check ((unit_price >= 0))",
        },
    }

    missing_rules = [
        rule
        for rule, accepted_definitions in required_definitions.items()
        if actual_definitions.isdisjoint(accepted_definitions)
    ]

    if missing_rules:
        raise RuntimeError(
            f"Table '{TABLE_NAME}' is missing required or compatible "
            f"CHECK constraints: {missing_rules}. "
            "Review and migrate the database schema before loading."
        )


def create_orders_table(connection) -> None:
    """Create the target table and verify its schema and constraints."""
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id BIGINT NOT NULL,
                order_date DATE NOT NULL,
                customer_id TEXT NOT NULL,
                product TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price BIGINT NOT NULL,

                CONSTRAINT orders_pkey PRIMARY KEY (order_id),
                CONSTRAINT orders_order_id_positive CHECK (order_id > 0),
                CONSTRAINT orders_customer_id_nonblank CHECK (BTRIM(customer_id) <> ''),
                CONSTRAINT orders_product_nonblank CHECK (BTRIM(product) <> ''),
                CONSTRAINT orders_category_nonblank CHECK (BTRIM(category) <> ''),
                CONSTRAINT orders_quantity_positive CHECK (quantity > 0),
                CONSTRAINT orders_unit_price_nonnegative CHECK (unit_price >= 0)
            )
            """
        )
    )

        # Add the missing positive-ID constraint to an existing table.
    existing_checks = connection.execute(
        text(
            """
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = to_regclass(:table_name)
              AND contype = 'c'
            """
        ),
        {"table_name": TABLE_NAME},
    ).scalars().all()

    normalized_checks = {
        " ".join(definition.lower().split())
        for definition in existing_checks
    }

    positive_id_checks = {
        "check ((order_id > 0))",
        "check ((order_id >= 1))",
    }

    if normalized_checks.isdisjoint(positive_id_checks):
        connection.execute(
            text(
                """
                ALTER TABLE orders
                ADD CONSTRAINT orders_order_id_positive
                CHECK (order_id > 0)
                """
            )
        )

    validate_orders_constraints(connection)


    actual_columns = connection.execute(
        text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = :table_name
            ORDER BY ordinal_position
            """
        ),
        {"table_name": TABLE_NAME},
    ).all()

    expected_columns = [
        ("order_id", "bigint", "NO"),
        ("order_date", "date", "NO"),
        ("customer_id", "text", "NO"),
        ("product", "text", "NO"),
        ("category", "text", "NO"),
        ("quantity", "integer", "NO"),
        ("unit_price", "bigint", "NO"),
    ]

    normalized_columns = [
        (row[0], row[1], row[2]) for row in actual_columns
    ]

    if normalized_columns != expected_columns:
        raise RuntimeError(
            f"Table '{TABLE_NAME}' has an incompatible schema. "
            f"Expected: {expected_columns}; "
            f"actual: {normalized_columns}"
        )

    primary_key_columns = connection.execute(
        text(
            """
            SELECT kcu.column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_catalog = kcu.constraint_catalog
             AND tc.constraint_schema = kcu.constraint_schema
             AND tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
             AND tc.table_name = kcu.table_name
            WHERE tc.table_schema = current_schema()
              AND tc.table_name = :table_name
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
            """
        ),
        {"table_name": TABLE_NAME},
    ).scalars().all()

    if primary_key_columns != ["order_id"]:
        raise RuntimeError(
            f"Table '{TABLE_NAME}' must have order_id as its "
            f"only primary key. Actual: {primary_key_columns}"
        )

    check_constraints = connection.execute(
        text(
            """
            SELECT pg_get_constraintdef(c.oid)
            FROM pg_constraint AS c
            JOIN pg_class AS t ON t.oid = c.conrelid
            JOIN pg_namespace AS n ON n.oid = t.relnamespace
            WHERE n.nspname = current_schema()
              AND t.relname = :table_name
              AND c.contype = 'c'
            """
        ),
        {"table_name": TABLE_NAME},
    ).scalars().all()

    normalized_checks = [
        definition.lower().replace(" ", "")
        for definition in check_constraints
    ]

    required_check_fragments = (
        "btrim(customer_id)",
        "btrim(product)",
        "btrim(category)",
        "quantity>0",
        "unit_price>=0",
    )

    missing_checks = [
        fragment
        for fragment in required_check_fragments
        if not any(
            fragment in definition for definition in normalized_checks
        )
    ]

    if missing_checks:
        raise RuntimeError(
            f"Table '{TABLE_NAME}' is missing required CHECK "
            f"constraints: {missing_checks}"
        )

    # Fail clearly if an older or manually altered table has a
    # different column layout. Do not silently load into it.
    actual_columns = connection.execute(
        text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = :table_name
            ORDER BY ordinal_position
            """
        ),
        {"table_name": TABLE_NAME},
    ).scalars().all()

    if tuple(actual_columns) != EXPECTED_COLUMNS:
        raise RuntimeError(
            f"Table '{TABLE_NAME}' has an unexpected column layout: "
            f"{actual_columns}. Apply the project schema migration first."
        )


def load(df: pd.DataFrame, engine: Engine) -> None:
    """Replace target data atomically while preserving the table schema."""
    with engine.begin() as connection:
        create_orders_table(connection)

        # DELETE and INSERT are in one transaction. If loading fails,
        # the previous rows are restored by transaction rollback.
        connection.execute(text("DELETE FROM orders"))

        df.to_sql(
            name=TABLE_NAME,
            con=connection,
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi",
        )

        loaded_count = connection.execute(
            text("SELECT COUNT(*) FROM orders")
        ).scalar_one()

        if loaded_count != len(df):
            raise RuntimeError(
                f"Row count mismatch: expected {len(df)}, "
                f"found {loaded_count}."
            )

    logger.info("Loaded %d rows into table '%s'", len(df), TABLE_NAME)


def run_pipeline() -> None:
    """Execute extract, transform, and load in sequence."""
    extracted_df = extract()
    transformed_df = transform(extracted_df)

    engine = get_engine()
    try:
        load(transformed_df, engine)
    finally:
        engine.dispose()

    logger.info("ETL pipeline completed successfully.")


def main() -> int:
    try:
        run_pipeline()
    except Exception:
        logger.exception("ETL pipeline failed.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
