import httpx

from app.main import Settings, create_app
from app.search import InMemorySearchIndex


def make_client() -> httpx.AsyncClient:
    app = create_app(
        settings=Settings(database_url="sqlite://", search="memory"),
        search=InMemorySearchIndex(),
    )
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")


LINES = [
    {"order_id": "o1", "placed_at": "2026-07-01T10:00:00", "product_sku": "KB-1",
     "product_name": "Mechanical Keyboard", "quantity": 2, "unit_price": 90.0},
    {"order_id": "o1", "placed_at": "2026-07-01T10:00:00", "product_sku": "MS-1",
     "product_name": "Wireless Mouse", "quantity": 1, "unit_price": 25.0},
    {"order_id": "o2", "placed_at": "2026-07-02T12:00:00", "product_sku": "KB-1",
     "product_name": "Mechanical Keyboard", "quantity": 1, "unit_price": 90.0},
]


async def test_ingest_and_summary():
    async with make_client() as c:
        assert (await c.post("/api/v1/tenants/t1/orders", json=LINES)).status_code == 202
        s = (await c.get("/api/v1/tenants/t1/summary")).json()
    assert s["revenue"] == 295.0
    assert s["orders"] == 2


async def test_revenue_daily_grouped():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        days = (await c.get("/api/v1/tenants/t1/revenue-daily")).json()
    assert [d["revenue"] for d in days] == [205.0, 90.0]


async def test_top_products_ranked():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        top = (await c.get("/api/v1/tenants/t1/top-products")).json()
    assert top[0]["sku"] == "KB-1" and top[0]["revenue"] == 270.0


async def test_tenant_isolation():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        other = (await c.get("/api/v1/tenants/OTHER/summary")).json()
    assert other["revenue"] == 0 and other["orders"] == 0


async def test_product_search_scoped():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        hits = (await c.get("/api/v1/tenants/t1/products/search", params={"q": "keyboard"})).json()
        none = (await c.get("/api/v1/tenants/OTHER/products/search", params={"q": "keyboard"})).json()
    assert hits and hits[0]["sku"] == "KB-1"
    assert none == []


async def test_ingest_rejects_bad_quantity():
    bad = [dict(LINES[0], quantity=0)]
    async with make_client() as c:
        assert (await c.post("/api/v1/tenants/t1/orders", json=bad)).status_code == 422


async def test_forecast_degrades_gracefully_for_sparse_tenant():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)  # 2 distinct days
        forecast = (await c.get("/api/v1/tenants/t1/forecast")).json()

    assert forecast["method"] == "moving_average"
    assert forecast["confidence"] == "low"
    assert len(forecast["points"]) == 14


async def test_anomalies_empty_for_sparse_tenant():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        anomalies = (await c.get("/api/v1/tenants/t1/anomalies")).json()

    assert anomalies == []


async def test_feedback_submit_and_stats_roundtrip():
    async with make_client() as c:
        up = await c.post("/api/v1/tenants/t1/feedback",
                           json={"variant": "sidebar", "rating": "up", "comment": "love the chart"})
        assert up.status_code == 201
        await c.post("/api/v1/tenants/t1/feedback", json={"variant": "footer", "rating": "down"})

        stats = (await c.get("/api/v1/tenants/t1/feedback/stats")).json()

    assert stats["sidebar"]["up"] == 1
    assert stats["footer"]["down"] == 1


async def test_feedback_rejects_unknown_variant():
    async with make_client() as c:
        response = await c.post("/api/v1/tenants/t1/feedback",
                                 json={"variant": "banner", "rating": "up"})
    assert response.status_code == 422


async def test_ask_stub_mode_returns_sql_and_rows():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        response = await c.post("/api/v1/tenants/t1/ask", json={"question": "what are the top products?"})

    assert response.status_code == 200
    body = response.json()
    assert "orders" in body["sql"]
    assert "tenant_id" not in body["sql"].lower()
    assert body["rowCount"] == len(body["rows"])
    assert body["rows"][0]["product_name"] == "Mechanical Keyboard"


async def test_ask_is_tenant_scoped():
    async with make_client() as c:
        await c.post("/api/v1/tenants/t1/orders", json=LINES)
        other = await c.post("/api/v1/tenants/OTHER/ask", json={"question": "how many orders?"})

    assert other.status_code == 200
    assert other.json()["rows"] == [{"order_count": 0}]


async def test_ask_rejects_empty_question():
    async with make_client() as c:
        response = await c.post("/api/v1/tenants/t1/ask", json={"question": ""})
    assert response.status_code == 422


async def test_features_reports_defaults():
    async with make_client() as c:
        response = await c.get("/api/v1/features")
    assert response.json() == {"ask": True, "forecast": True}


async def test_ask_disabled_via_feature_flag():
    app = create_app(
        settings=Settings(database_url="sqlite://", search="memory", feature_ask=False),
        search=InMemorySearchIndex(),
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        response = await c.post("/api/v1/tenants/t1/ask", json={"question": "top products?"})
    assert response.status_code == 404


async def test_forecast_and_anomalies_disabled_via_feature_flag():
    app = create_app(
        settings=Settings(database_url="sqlite://", search="memory", feature_forecast=False),
        search=InMemorySearchIndex(),
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        forecast_response = await c.get("/api/v1/tenants/t1/forecast")
        anomalies_response = await c.get("/api/v1/tenants/t1/anomalies")
    assert forecast_response.status_code == 404
    assert anomalies_response.status_code == 404
