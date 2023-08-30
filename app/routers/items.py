from fastapi import APIRouter
from app.dependencies import *

router = APIRouter(prefix="/orders/{order_id}")


@router.get("/items/")
async def get_order_items(order_id: int) -> list:
    """
    Endpoint, returns all items of the order with given ID
    Args:
        order_id: ID of order to get items for

    Returns:
        items: list of dicts with items of given order
    """
    with get_db_cur() as db_cur:
        return await get_all_items(db_cur, order_id)


@router.get("/items/{item_id}")
async def get_single_item(order_id: int, item_id: int) -> dict:
    """
    Endpoint, returns single item details by both order ID and item ID
    Args:
        order_id: ID of order to get item for
        item_id: ID of item to get details for

    Returns:
        item: details of a single item in order
    """
    with get_db_cur() as db_cur:
        return db_cur.execute(
            "SELECT id, name, price, number FROM orders_items WHERE order_id = %s AND id = %s",
            (order_id, item_id),
        ).fetchone()


@router.post("/items/")
async def create_item(order_id: int, item: dict) -> dict:
    """
    Endpoint, creates a new item tied to a given order
    Args:
        order_id: ID of order to add item to
        item: item description in Python's dict format

    Returns:
        created_item: details of created item
    """
    with get_db_cur() as db_cur:
        item_id = await create_item_in_order(order_id, db_cur, item)

        return await get_single_item(order_id, item_id)


@router.put("/items/{item_id}")
async def update_single_item(order_id: int, item_id: int, item_dict: dict) -> dict:
    """
    Endpoint, updated details of item in order, defined by item ID and order ID
    Args:
        order_id: ID of order
        item_id: ID of item to update
        item_dict: new item details in Python's dict format

    Returns:
        updated_item: details of updated item
    """
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
    """
    Endpoint, deletes the item defined by item ID and order ID
    Args:
        order_id: ID of order
        item_id: ID of item to delete

    Returns:
        items: list of dicts with items of given order
    """
    with get_db_cur() as db_cur:
        db_cur.execute(
            "DELETE from orders_items WHERE order_id = %s AND id = %s",
            (
                order_id,
                item_id,
            ),
        )

    return await get_order_items(order_id)
