from fastapi import HTTPException
import psycopg
import asyncio
from pydantic import BaseModel
import contextlib


class Order(BaseModel):
    id: int | None = None
    title: str
    items: list


@contextlib.contextmanager
def get_db_cur() -> psycopg.Cursor:
    with psycopg.connect(
        "dbname=test user=postgres password=password host=localhost",
        autocommit=True,
        row_factory=psycopg.rows.dict_row,
    ).cursor() as db_cur:
        yield db_cur


def create_database_if_not_exists():
    with psycopg.connect(
        "dbname=postgres user=postgres password=password host=localhost",
        autocommit=True,
    ).cursor() as dbms_cur:  # do not refactor, this connection is used only once to create the database
        if (
            dbms_cur.execute(
                "SELECT EXISTS(SELECT datname FROM pg_catalog.pg_database WHERE LOWER(datname) = LOWER('week5'));"
            ).fetchone()[0]
            is False
        ):
            dbms_cur.execute("CREATE DATABASE week5;")


def populate_database():
    with get_db_cur() as db_cur:
        db_cur.execute(
            """CREATE TABLE if NOT EXISTS PUBLIC.orders (id serial NOT NULL PRIMARY KEY,
                created_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                updated_date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                title text NOT NULL);"""
        )
        db_cur.execute(
            """CREATE TABLE if NOT EXISTS PUBLIC.orders_items (id serial NOT NULL PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
                NAME text NOT NULL,
                price INTEGER NOT NULL,
                NUMBER INTEGER NOT NULL DEFAULT 1);"""
        )


async def get_all_items(db_cur: psycopg.Cursor, order_id: int) -> dict:
    return db_cur.execute(
        "SELECT name, price, number FROM orders_items WHERE order_id = %s",
        (order_id,),
    ).fetchall()


async def get_total_price(db_cur: psycopg.Cursor, order_id: int) -> int:
    return db_cur.execute(
        "SELECT SUM(price * number) FROM orders_items WHERE order_id = %s",
        (order_id,),
    ).fetchone()["sum"]


async def order_append_external_data(
    data: dict, db_cur: psycopg.Cursor, order_id: int
) -> None:
    data["total"] = await get_total_price(db_cur, order_id)
    data["items"] = await get_all_items(db_cur, order_id)


async def check_for_order_in_db(db_cur: psycopg.Cursor, order_id: int) -> None:
    if (
        order_id <= 0
        or db_cur.execute(
            "SELECT EXISTS (SELECT 1 FROM orders WHERE id = %s limit 1);",
            (order_id,),
        ).fetchone()["exists"]
        is False
    ):
        raise HTTPException(status_code=404, detail="Order not found")
    else:
        return


async def create_item_in_order(order_id, db_cur, item):
    db_cur.execute(
        "INSERT INTO orders_items (order_id, name, price, number) VALUES (%s, %s, %s, %s);",
        (
            order_id,
            item["name"],
            item["price"],
            item["number"],
        ),
    )
