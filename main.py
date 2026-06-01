from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI(title="Order Management API")


# -----------------------------
# Mock Data
# -----------------------------

products = [
    {
        "id": 1,
        "name": 'MacBook Pro 16" (M3 Max)',
        "sku": "APP-MBP16-M3M",
        "price": 3499.00,
        "quantity_in_stock": 14,
    },
    {
        "id": 2,
        "name": "Sony WH-1000XM5 Headphones",
        "sku": "SNY-WH1000XM5",
        "price": 398.00,
        "quantity_in_stock": 7,
    },
    {
        "id": 3,
        "name": 'Dell UltraSharp 32" 4K Monitor',
        "sku": "DEL-U3223QE",
        "price": 849.99,
        "quantity_in_stock": 22,
    },
    {
        "id": 4,
        "name": "Keychron Q1 Max Keyboard",
        "sku": "KEY-Q1M-US",
        "price": 219.00,
        "quantity_in_stock": 3,
    },
    {
        "id": 5,
        "name": "Logitech MX Master 3S Mouse",
        "sku": "LOG-MX3S-GRY",
        "price": 99.99,
        "quantity_in_stock": 45,
    },
    {
        "id": 6,
        "name": 'iPad Pro 13" (M4)',
        "sku": "APP-IPP13-M4",
        "price": 1299.00,
        "quantity_in_stock": 0,
    },
]

customers = [
    {
        "id": 1,
        "name": "Alice Vance",
        "email": "alice.vance@stripe.com",
    },
    {
        "id": 2,
        "name": "Bob Miller",
        "email": "bob@vercel.com",
    },
    {
        "id": 3,
        "name": "Charlie Day",
        "email": "charlie.day@linear.app",
    },
    {
        "id": 4,
        "name": "Diana Prince",
        "email": "diana@amazon.com",
    },
]

orders = [
    {
        "id": 1,
        "customer_id": 1,
        "product_id": 2,
        "quantity": 2,
        "total_amount": 796.00,
        "created_at": datetime.utcnow().isoformat(),
    }
]


# -----------------------------
# Schemas
# -----------------------------

class OrderCreate(BaseModel):
    customer_id: int
    product_id: int
    quantity: int


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_id: int
    quantity: int
    total_amount: float
    created_at: str


# -----------------------------
# Health Check
# -----------------------------

@app.get("/")
async def root():
    return {"status": "healthy"}


# -----------------------------
# Customers
# -----------------------------

@app.get("/customers")
async def get_customers():
    return customers


@app.get("/customers/{customer_id}")
async def get_customer(customer_id: int):
    customer = next(
        (c for c in customers if c["id"] == customer_id),
        None
    )

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# -----------------------------
# Products
# -----------------------------

@app.get("/products")
async def get_products():
    return products


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    product = next(
        (p for p in products if p["id"] == product_id),
        None
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# -----------------------------
# Orders
# -----------------------------

@app.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate):

    customer = next(
        (c for c in customers if c["id"] == order.customer_id),
        None
    )

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    product = next(
        (p for p in products if p["id"] == order.product_id),
        None
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if order.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    if product["quantity_in_stock"] < order.quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    total_amount = round(
        product["price"] * order.quantity,
        2
    )

    new_order = {
        "id": max([o["id"] for o in orders], default=0) + 1,
        "customer_id": order.customer_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "total_amount": total_amount,
        "created_at": datetime.utcnow().isoformat(),
    }

    orders.append(new_order)

    # Reduce inventory
    product["quantity_in_stock"] -= order.quantity

    return new_order


@app.get("/orders")
async def get_orders():
    return orders


@app.get("/orders/{order_id}")
async def get_order(order_id: int):

    order = next(
        (o for o in orders if o["id"] == order_id),
        None
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):

    order = next(
        (o for o in orders if o["id"] == order_id),
        None
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Restore stock
    product = next(
        (
            p
            for p in products
            if p["id"] == order["product_id"]
        ),
        None,
    )

    if product:
        product["quantity_in_stock"] += order["quantity"]

    orders.remove(order)

    return {
        "message": "Order deleted successfully",
        "order_id": order_id
    }
