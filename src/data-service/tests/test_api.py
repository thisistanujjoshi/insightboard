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
