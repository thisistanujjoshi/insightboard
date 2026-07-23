from datetime import datetime

import pytest

from app.db import OrderLine, make_engine_bundle
from app.nlsql import (
    QueryTimeoutError,
    UnsafeQueryError,
    enforce_row_limit,
    run_readonly_query,
    validate_sql,
)


def test_validate_sql_accepts_simple_select():
    assert validate_sql("SELECT * FROM orders") == "SELECT * FROM orders"


def test_validate_sql_rejects_ctes():
    sql = "WITH totals AS (SELECT product_name, SUM(line_total) AS rev FROM orders GROUP BY product_name) SELECT * FROM totals"
    with pytest.raises(UnsafeQueryError):
        validate_sql(sql)


def test_validate_sql_strips_trailing_semicolon():
    assert validate_sql("SELECT * FROM orders;") == "SELECT * FROM orders"


@pytest.mark.parametrize("keyword", ["insert", "update", "delete", "drop", "attach", "pragma", "vacuum"])
def test_validate_sql_rejects_write_and_ddl_keywords(keyword):
    with pytest.raises(UnsafeQueryError):
        validate_sql(f"{keyword.upper()} something")


def test_validate_sql_rejects_multiple_statements():
    with pytest.raises(UnsafeQueryError):
        validate_sql("SELECT * FROM orders; DROP TABLE orders")


@pytest.mark.parametrize("table", ["order_lines", "feedback", "sqlite_master"])
def test_validate_sql_rejects_tables_outside_the_view(table):
    with pytest.raises(UnsafeQueryError):
        validate_sql(f"SELECT * FROM {table}")


def test_validate_sql_rejects_tenant_id_reference():
    with pytest.raises(UnsafeQueryError):
        validate_sql("SELECT * FROM orders WHERE tenant_id = 'other'")


def test_enforce_row_limit_appends_when_missing():
    assert enforce_row_limit("SELECT * FROM orders", max_rows=50) == "SELECT * FROM orders\nLIMIT 50"


def test_enforce_row_limit_caps_when_over_max():
    assert enforce_row_limit("SELECT * FROM orders LIMIT 10000", max_rows=50) == "SELECT * FROM orders LIMIT 50"


def test_enforce_row_limit_leaves_smaller_limit_untouched():
    assert enforce_row_limit("SELECT * FROM orders LIMIT 5", max_rows=50) == "SELECT * FROM orders LIMIT 5"


def _seed(bundle, tenant_id: str, sku: str, order_id: str) -> None:
    with bundle.session_factory() as session:
        session.add(OrderLine(
            tenant_id=tenant_id, order_id=order_id, placed_at=datetime(2026, 1, 1),
            product_sku=sku, product_name=sku, quantity=1, unit_price=10.0,
        ))
        session.commit()


def test_run_readonly_query_isolates_tenants(tmp_path):
    bundle = make_engine_bundle(f"sqlite:///{tmp_path / 'iso.db'}")
    _seed(bundle, "a", "SKU-A", "o1")
    _seed(bundle, "b", "SKU-B", "o2")

    rows_a = run_readonly_query(bundle.raw_connect, "a", "SELECT product_sku FROM orders")
    rows_b = run_readonly_query(bundle.raw_connect, "b", "SELECT product_sku FROM orders")

    assert rows_a == [{"product_sku": "SKU-A"}]
    assert rows_b == [{"product_sku": "SKU-B"}]


def test_run_readonly_query_rejects_write_even_if_validation_was_skipped(tmp_path):
    bundle = make_engine_bundle(f"sqlite:///{tmp_path / 'iso2.db'}")
    _seed(bundle, "a", "SKU-A", "o1")

    with pytest.raises(UnsafeQueryError):
        run_readonly_query(bundle.raw_connect, "a", "DELETE FROM orders")


def test_run_readonly_query_times_out_on_expensive_query(tmp_path):
    bundle = make_engine_bundle(f"sqlite:///{tmp_path / 'slow.db'}")
    _seed(bundle, "a", "SKU-A", "o1")

    expensive = (
        "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM cnt WHERE x < 2000000000) "
        "SELECT COUNT(*) AS n FROM cnt, orders"
    )
    with pytest.raises(QueryTimeoutError):
        run_readonly_query(bundle.raw_connect, "a", expensive, timeout_seconds=0.1)
