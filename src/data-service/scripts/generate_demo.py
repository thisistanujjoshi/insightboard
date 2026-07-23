"""Seed the data service with 90 days of NexusCommerce-shaped demo orders.

Usage: python scripts/generate_demo.py [tenant_id] [base_url]
"""

import random
import sys
from datetime import datetime, timedelta

import httpx

PRODUCTS = [
    ("ELEC-KB-001", "Mechanical Keyboard", 89.99),
    ("ELEC-MS-002", "Wireless Mouse", 24.50),
    ("ELEC-MN-003", '27" 4K Monitor', 379.00),
    ("BOOK-CS-001", "Clean Architecture", 31.99),
    ("BOOK-CS-002", "Designing Data-Intensive Applications", 44.99),
    ("HOME-LT-001", "LED Desk Lamp", 34.95),
]


def main(tenant: str = "demo", base: str = "http://localhost:8000") -> None:
    rng = random.Random(42)  # reproducible demo data
    lines, order_no = [], 0
    today = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)

    for day_offset in range(90, 0, -1):
        day = today - timedelta(days=day_offset)
        weekday_boost = 1.4 if day.weekday() < 5 else 0.8
        for _ in range(int(rng.gauss(8, 3) * weekday_boost // 1) or 1):
            order_no += 1
            for sku, name, price in rng.sample(PRODUCTS, rng.randint(1, 3)):
                lines.append({
                    "order_id": f"demo-{order_no}",
                    "placed_at": (day + timedelta(minutes=rng.randint(0, 600))).isoformat(),
                    "product_sku": sku,
                    "product_name": name,
                    "quantity": rng.randint(1, 4),
                    "unit_price": price,
                })

    r = httpx.post(f"{base}/api/v1/tenants/{tenant}/orders", json=lines, timeout=60)
    r.raise_for_status()
    print(f"Ingested {len(lines)} lines across {order_no} orders for tenant '{tenant}'.")


if __name__ == "__main__":
    main(*sys.argv[1:3])
