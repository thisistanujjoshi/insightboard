from datetime import datetime

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from sqlalchemy import func, select

from .db import OrderLine, make_session_factory
from .search import SearchIndex, create_index


class Settings(BaseSettings):
    database_url: str = "sqlite:///data.dev.db"
    search: str = "memory"           # memory | elasticsearch
    es_url: str = "http://localhost:9200"

    model_config = {"env_prefix": "INSIGHT_"}


class IngestLine(BaseModel):
    order_id: str
    placed_at: datetime
    product_sku: str
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


def create_app(settings: Settings | None = None, search: SearchIndex | None = None) -> FastAPI:
    settings = settings or Settings()
    search = search or create_index(settings.search, settings.es_url)
    session_factory = make_session_factory(settings.database_url)

    app = FastAPI(title="InsightBoard Data API", version="1.0")

    # Dev-time CORS for the dashboard dev server (any localhost port);
    # in production both sit behind one origin.
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def db():
        with session_factory() as session:
            yield session

    @app.get("/health")
    def health():
        return {"status": "Healthy", "search": settings.search}

    @app.post("/api/v1/tenants/{tenant_id}/orders", status_code=202)
    def ingest(tenant_id: str, lines: list[IngestLine], session=Depends(db)):
        for line in lines:
            session.add(OrderLine(tenant_id=tenant_id, **line.model_dump()))
            search.index_product(tenant_id, line.product_sku, line.product_name)
        session.commit()
        return {"ingested": len(lines)}

    @app.get("/api/v1/tenants/{tenant_id}/summary")
    def summary(tenant_id: str, session=Depends(db)):
        revenue, orders = session.execute(
            select(
                func.coalesce(func.sum(OrderLine.quantity * OrderLine.unit_price), 0),
                func.count(func.distinct(OrderLine.order_id)),
            ).where(OrderLine.tenant_id == tenant_id)
        ).one()
        return {"tenantId": tenant_id, "revenue": float(revenue), "orders": orders}

    @app.get("/api/v1/tenants/{tenant_id}/revenue-daily")
    def revenue_daily(tenant_id: str, session=Depends(db)):
        day = func.date(OrderLine.placed_at)
        rows = session.execute(
            select(day, func.sum(OrderLine.quantity * OrderLine.unit_price))
            .where(OrderLine.tenant_id == tenant_id)
            .group_by(day).order_by(day)
        ).all()
        return [{"date": str(d), "revenue": float(r)} for d, r in rows]

    @app.get("/api/v1/tenants/{tenant_id}/top-products")
    def top_products(tenant_id: str, limit: int = Query(default=5, le=50), session=Depends(db)):
        rows = session.execute(
            select(
                OrderLine.product_sku,
                OrderLine.product_name,
                func.sum(OrderLine.quantity),
                func.sum(OrderLine.quantity * OrderLine.unit_price),
            )
            .where(OrderLine.tenant_id == tenant_id)
            .group_by(OrderLine.product_sku, OrderLine.product_name)
            .order_by(func.sum(OrderLine.quantity * OrderLine.unit_price).desc())
            .limit(limit)
        ).all()
        return [
            {"sku": s, "name": n, "units": int(u), "revenue": float(r)}
            for s, n, u, r in rows
        ]

    @app.get("/api/v1/tenants/{tenant_id}/products/search")
    def product_search(tenant_id: str, q: str):
        return search.search(tenant_id, q)

    return app


app = create_app()
