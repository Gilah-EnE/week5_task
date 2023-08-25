from fastapi import APIRouter
from dependencies import *

router = APIRouter()


@router.get("/orders")
async def get_all_orders() -> list:
    with get_db_cur() as db_cur:
        all_orders = db_cur.execute("SELECT * FROM orders;").fetchall()

        for order in all_orders:
            await order_append_external_data(order, db_cur, order["id"])

    return all_orders


@router.get("/orders/{order_id}")
async def get_order_by_id(order_id: int) -> dict:
    with get_db_cur() as db_cur:
        await check_for_order_in_db(db_cur, order_id)
        data = db_cur.execute(
            "SELECT * FROM orders WHERE id = %s;", (order_id,)
        ).fetchone()

        await order_append_external_data(data, db_cur, order_id)
    return data


@router.post("/orders")
async def add_order(order: Order) -> dict:
    with get_db_cur() as db_cur:
        created_id = db_cur.execute(
            "INSERT INTO orders (created_date, updated_date, title) VALUES (now(), now(), %s) RETURNING (id);",
            (order.title,),
        ).fetchone()["id"]

        for item in order.items:
            await create_item_in_order(created_id, db_cur, item)

    return await get_order_by_id(created_id)


@router.put("/orders/{order_id}")
async def update_order(order: Order, order_id: int) -> dict:
    with get_db_cur() as db_cur:
        db_cur.execute(
            "UPDATE orders SET title = %s, updated_date = NOW() WHERE id = %s RETURNING (id)",
            (
                order.title,
                order_id,
            ),
        )

    return await get_order_by_id(order_id)


@router.delete("/orders/{order_id}")
async def delete_order(order_id: int) -> dict:
    with get_db_cur() as db_cur:
        db_cur.execute("DELETE FROM orders_items WHERE order_id = %s", (order_id,))
        db_cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))

    return {"id": order_id}
