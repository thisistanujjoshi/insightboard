"""Warehouse schema and session plumbing.

One denormalised order-lines fact table — the right shape for the v1
questions (revenue by day, top products) at small-tenant scale. SQLite for
dev/tests; PostgreSQL in real deployments via INSIGHT_DATABASE_URL.
"""

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from sqlalchemy import DateTime, Index, Numeric, String, Text, create_engine
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


class Feedback(Base):
    """In-app feedback submissions — feeds the product backlog (see docs/backlog.md)
    and doubles as the A/B test's outcome measure (which widget `variant` converts).
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    variant: Mapped[str] = mapped_column(String(16))       # "sidebar" | "footer" — the A/B arm
    rating: Mapped[str] = mapped_column(String(16))        # "up" | "down"
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


@dataclass
class EngineBundle:
    session_factory: sessionmaker
    # Opens an independent, low-level connection onto the SAME data the ORM
    # session writes to — used by the Ask-in-English feature, which needs a
    # sqlite3-level PRAGMA query_only / progress-handler that SQLAlchemy's
    # Session doesn't expose. Never touches the ORM's pooled connection, so
    # it can't leave a write-blocking pragma stuck on a connection that other
    # requests reuse.
    raw_connect: Callable[[], sqlite3.Connection]
    dialect: str  # "sqlite" | "postgresql" | "other"


def make_engine_bundle(database_url: str) -> EngineBundle:
    if database_url in ("sqlite://", "sqlite:///:memory:"):
        # A plain ":memory:" database is private to the connection that
        # opened it, so a second raw_connect() would see an empty database.
        # A named shared-cache URI lets independent connections share one
        # in-memory database for the life of this engine, while a fresh
        # uuid per bundle keeps separate test runs fully isolated from
        # each other.
        from sqlalchemy.pool import StaticPool

        uri = f"file:memdb_{uuid.uuid4().hex}?mode=memory&cache=shared"
        # SQLAlchemy's sqlite dialect only forwards `uri=True` to the DBAPI
        # when it appears as a query param on the URL itself — passing it
        # via connect_args silently drops the rest of the query string
        # instead of handing it to sqlite3.connect().
        engine = create_engine(
            f"sqlite:///{uri}&uri=true", future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool)

        def raw_connect() -> sqlite3.Connection:
            return sqlite3.connect(uri, uri=True)

        dialect = "sqlite"
    elif database_url.startswith("sqlite:///"):
        path = database_url.removeprefix("sqlite:///")
        engine = create_engine(database_url, future=True)

        def raw_connect() -> sqlite3.Connection:
            return sqlite3.connect(path)

        dialect = "sqlite"
    else:
        engine = create_engine(database_url, future=True)

        def raw_connect() -> sqlite3.Connection:
            raise NotImplementedError(
                "Ask-in-English's read-only connection is implemented for "
                "SQLite. A PostgreSQL deployment should instead use a "
                "dedicated read-only DB role plus SET statement_timeout "
                "(see docs/adr for the guardrail design)."
            )

        dialect = "postgresql" if database_url.startswith("postgresql") else "other"

    Base.metadata.create_all(engine)
    return EngineBundle(sessionmaker(engine, expire_on_commit=False), raw_connect, dialect)
