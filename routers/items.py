from fastapi import APIRouter
from dependencies import *

router = APIRouter(prefix="/orders/{order_id}")


@router.get("/items/")
async def get_order_items(order_id: int) -> list:
    with get_db_cur() as db_cur:
        return await get_all_items(db_cur, order_id)


@router.get("/items/{item_id}")
async def get_single_item(order_id: int, item_id: int):
    with get_db_cur() as db_cur:
        return db_cur.execute(
            "SELECT id, name, price, number FROM orders_items WHERE order_id = %s AND id = %s",
            (order_id, item_id),
        ).fetchone()


@router.post("/items/")
async def create_item(order_id: int, item: Item) -> dict:
    with get_db_cur() as db_cur:
        item_id = await create_item_in_order(order_id, db_cur, item)

        return await get_single_item(order_id, item_id)


@router.put("/items/{item_id}")
async def update_single_item(order_id: int, item_id: int, item_dict: dict) -> dict:
    with get_db_cur() as db_cur:
        item_model = Item.model_validate(item_dict)
        db_cur.execute(
            "UPDATE orders_items SET name = %s, price = %s, number = %s WHERE order_id = %s AND id = %s",
            (
                item_model.name,
                item_model.price,
                item_model.number,
                order_id,
                item_id,
            ),
        )

        return await get_single_item(order_id, item_id)


@router.delete("/items/{item_id}")
async def delete_item(order_id: int, item_id: int) -> list:
    with get_db_cur() as db_cur:
        db_cur.execute(
            "DELETE from orders_items WHERE order_id = %s AND id = %s",
            (
                order_id,
                item_id,
            ),
        )

    return await get_order_items(order_id)
