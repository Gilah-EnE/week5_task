from fastapi import HTTPException
import psycopg
import asyncio
from pydantic import BaseModel
import contextlib


class Item(BaseModel):
    """
    Pydantic Item class, used for some queries
    """
    id: int | None = None
    name: str
    price: int
    number: int = 1


class Order(BaseModel):
    """
    Pydantic Order class, used for some queries
    """
    id: int | None = None
    title: str
    items: list


@contextlib.contextmanager
def get_db_cur() -> psycopg.Cursor:
    """
    Context manager for database cursor with predefined parameters to work with containerized database.
    Returns:
        db_cur: database cursor with predefined parameters
    """
    with psycopg.connect(
        "dbname=week5 user=postgres password=supersecretpassword host=psql",
        autocommit=True,
        row_factory=psycopg.rows.dict_row,
    ).cursor() as db_cur:
        yield db_cur


def create_database_if_not_exists():
    """
    Detects if database is created, and if not, creates one for us.
    Returns:
        None.
    """
    with psycopg.connect(
        "dbname=postgres user=postgres password=supersecretpassword host=psql",
        autocommit=True,
    ).cursor() as dbms_cur:  # do not refactor, this connection is used only once to create the database
        if (
            dbms_cur.execute(
                "SELECT EXISTS(SELECT datname FROM pg_catalog.pg_database WHERE LOWER(datname) = LOWER('week5'));"
            ).fetchone()[
                0
            ]  # database detection using pg_catalog as PostgreSQL doesn't know what "CREATE DATABASE IF NOT EXISTS" is!
            is False
        ):
            dbms_cur.execute("CREATE DATABASE week5;")  # create database


def populate_database():
    """
    Populates created database with some tables, which are used by the API.
    Returns:
        None.
    """
    with get_db_cur() as db_cur:
        db_cur.execute(
            """CREATE TABLE if NOT EXISTS PUBLIC.orders (id serial NOT NULL PRIMARY KEY,
                created_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                updated_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                title text NOT NULL);"""
        )  # creating table for orders

        db_cur.execute(
            """CREATE TABLE if NOT EXISTS PUBLIC.orders_items (id serial NOT NULL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
                NAME text NOT NULL,
                price INTEGER NOT NULL,
                NUMBER INTEGER NOT NULL DEFAULT 1);"""
        )  # creating table for items in orders from the previous table


async def get_all_items(db_cur: psycopg.Cursor, order_id: int) -> list:
    """
    Gets all items by the order ID
    Args:
        db_cur: database cursor, handled by get_db_cur()
        order_id: ID of order to get items for
    Returns:
        items: list of all items by ID
    """
    return db_cur.execute(
        "SELECT id, name, price, number FROM orders_items WHERE order_id = %s",
        (order_id,),
    ).fetchall()


async def get_total_price(db_cur: psycopg.Cursor, order_id: int) -> float:
    """
    Calculates total order price (sum of prices multiplied by quantities of the item) using native SUM() aggregate function.
    Args:
        db_cur: database cursor, handled by get_db_cur()
        order_id: ID of order to calculate the sum for
    Returns:
        sum: total price of an order
    """
    return db_cur.execute(
        "SELECT SUM(price * number) FROM orders_items WHERE order_id = %s",  # calculating total order price using SUM() aggregate function
        (order_id,),
    ).fetchone()["sum"]


async def order_append_external_data(
    data: dict, db_cur: psycopg.Cursor, order_id: int
) -> None:
    """
    Appends total price and items list data to the order
    Args:
        data: item entry in dict format
        db_cur: database cursor, handled by get_db_cur()
        order_id: ID of order to get additional data for
    Returns:
        None.
    """
    data["total"] = await get_total_price(db_cur, order_id)
    data["items"] = await get_all_items(db_cur, order_id)


async def check_for_order_in_db(db_cur: psycopg.Cursor, order_id: int) -> None:
    """
    Checks if order with given number exists, raises HTTP 404 error if not.
    Args:
        db_cur: database cursor, handled by get_db_cur()
        order_id: ID of order to check
    Returns:
        None if the order of given ID is present.
    Raises:
        HTTPException: if order of given ID is not found.
    """
    if (
        order_id <= 0
        or db_cur.execute(
            "SELECT EXISTS (SELECT 1 FROM orders WHERE id = %s limit 1);",  # using EXISTS() function of Postgres
            (order_id,),
        ).fetchone()["exists"]
        is False
    ):
        raise HTTPException(
            status_code=404, detail="Order not found"
        )  # raising 404 error with custom description
    else:
        return


async def create_item_in_order(
    order_id: int, db_cur: psycopg.Cursor, item: dict
) -> int:
    """
    Appends an item to an existing order by its ID.
    Args:
        order_id: ID of order to which append a new item
        db_cur: database cursor, handled by get_db_cursor()
        item: item description in dict format
    Returns:
        id: ID of created item
    """
    item = await dict_to_item_model(item)  # converting item format to Item class object
    return db_cur.execute(
        "INSERT INTO orders_items (order_id, name, price, number) VALUES (%s, %s, %s, %s) RETURNING id;",
        (
            order_id,
            item.name,
            item.price,
            item.number,
        ),
    ).fetchone()[
        "id"
    ]  # creating an item entry and returning id of the created item


async def dict_to_item_model(item_dict: dict) -> Item:
    """
    Converts item from Python's dictionary format to Item class object, derived from Pydantic's BaseModel
    Args:
        item_dict: item description in dict format
    Returns:
        item_obj: item description in class object format
    """
    return Item.model_validate(item_dict)
