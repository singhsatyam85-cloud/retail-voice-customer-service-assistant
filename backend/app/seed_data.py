from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from backend.app.database import Base, SessionLocal, engine
from backend.app.models import Customer, Order, OrderItem


def seed_data():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_customer = db.scalar(
            select(Customer).where(
                Customer.customer_id == "CUST-101"
            )
        )

        if existing_customer:
            print(
                "Seed data already exists. "
                "No new records were added."
            )
            return

        current_time = datetime.now(timezone.utc)

        customers = [
            Customer(
                customer_id="CUST-101",
                full_name="Test Customer One",
                registered_phone="+447700900101",
                is_active=True,
            ),
            Customer(
                customer_id="CUST-102",
                full_name="Test Customer Two",
                registered_phone="+447700900102",
                is_active=True,
            ),
            Customer(
                customer_id="CUST-103",
                full_name="Test Customer Three",
                registered_phone="+447700900103",
                is_active=True,
            ),
        ]

        orders = [
            Order(
                order_id="ORD-5001",
                customer_id="CUST-101",
                status="delayed",
                total_amount=Decimal("24.99"),
                currency_code="GBP",
                placed_at=current_time - timedelta(days=7),
                expected_delivery_at=(
                    current_time - timedelta(days=1)
                ),
                delivered_at=None,
            ),
            Order(
                order_id="ORD-5002",
                customer_id="CUST-102",
                status="delivered",
                total_amount=Decimal("14.99"),
                currency_code="GBP",
                placed_at=current_time - timedelta(days=12),
                expected_delivery_at=(
                    current_time - timedelta(days=7)
                ),
                delivered_at=current_time - timedelta(days=7),
            ),
            Order(
                order_id="ORD-5003",
                customer_id="CUST-102",
                status="processing",
                total_amount=Decimal("7.99"),
                currency_code="GBP",
                placed_at=current_time - timedelta(days=1),
                expected_delivery_at=(
                    current_time + timedelta(days=4)
                ),
                delivered_at=None,
            ),
        ]

        order_items = [
            OrderItem(
                order_id="ORD-5001",
                product_name="Wireless Headphones",
                quantity=1,
                unit_price=Decimal("19.99"),
                item_status="ordered",
            ),
            OrderItem(
                order_id="ORD-5001",
                product_name="USB Charging Cable",
                quantity=1,
                unit_price=Decimal("5.00"),
                item_status="ordered",
            ),
            OrderItem(
                order_id="ORD-5002",
                product_name="Electric Kettle",
                quantity=1,
                unit_price=Decimal("14.99"),
                item_status="delivered",
            ),
            OrderItem(
                order_id="ORD-5003",
                product_name="Mobile Phone Case",
                quantity=1,
                unit_price=Decimal("7.99"),
                item_status="ordered",
            ),
        ]

        db.add_all(customers)
        db.add_all(orders)
        db.add_all(order_items)
        db.commit()

        print(
            "UK fictional customer and order data "
            "added successfully."
        )


if __name__ == "__main__":
    seed_data()