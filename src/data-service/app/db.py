"""Warehouse schema and session plumbing.

One denormalised order-lines fact table — the right shape for the v1
questions (revenue by day, top products) at small-tenant scale. SQLite for
dev/tests; PostgreSQL in real deployments via INSIGHT_DATABASE_URL.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    order_id: Mapped[str] = mapped_column(String(64))
    placed_at: Mapped[datetime] = mapped_column(DateTime)
    product_sku: Mapped[str] = mapped_column(String(64))
    product_name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int]
    unit_price: Mapped[float] = mapped_column(Numeric(18, 2))

    __table_args__ = (Index("ix_tenant_date", "tenant_id", "placed_at"),)


def make_session_factory(database_url: str) -> sessionmaker:
    if database_url in ("sqlite://", "sqlite:///:memory:"):
        # In-memory SQLite: share the single connection across sessions,
        # otherwise every session sees its own empty database.
        from sqlalchemy.pool import StaticPool

        engine = create_engine(
            database_url, future=True,
            connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)
