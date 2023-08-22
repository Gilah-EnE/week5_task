import fastapi
from fastapi import FastAPI
import psycopg
import asyncio

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    # await asyncio.sleep(1)

    with psycopg.connect(
        "dbname=postgres user=postgres password=password host=localhost",
        autocommit=True,
    ) as dbms_conn:
        with dbms_conn.cursor() as dbms_cur:
            try:
                dbms_cur.execute("CREATE DATABASE week5;")
            except:
                dbms_cur.execute("DROP DATABASE week5;")
                dbms_cur.execute("CREATE DATABASE week5;")

    with psycopg.connect(
        "dbname=week5 user=postgres password=password host=localhost", autocommit=True
    ) as db_conn:
        with db_conn.cursor() as db_cur:
            db_cur.execute("DROP TABLE IF EXISTS public.orders_items;")
            db_cur.execute("DROP TABLE IF EXISTS public.items;")
            db_cur.execute("DROP TABLE IF EXISTS public.orders;")

            db_cur.execute(
                """CREATE TABLE IF NOT EXISTS public.items(
                id serial PRIMARY KEY NOT NULL,
                name text NOT NULL,
                price numeric NOT NULL);"""
            )

            db_cur.execute(
                """CREATE TABLE IF NOT EXISTS public.orders(
                id serial PRIMARY KEY NOT NULL,
                created_date timestamp without time zone NOT NULL,
                updated_date timestamp without time zone NOT NULL,
                title text NOT NULL);"""
            )
            db_cur.execute(
                """CREATE TABLE IF NOT EXISTS public.orders_items (
                orders_id integer NOT NULL REFERENCES orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
                items_order_id integer NOT NULL REFERENCES items(id) ON UPDATE CASCADE ON DELETE CASCADE,
                CONSTRAINT orders_items_pkey PRIMARY KEY (orders_id, items_order_id));"""
            )


@app.get("/orders")
async def get_all_orders():
    with psycopg.connect(
        "dbname=test user=postgres password=password host=localhost",
        autocommit=True,
        row_factory=psycopg.rows.dict_row,
    ) as db_conn:
        with db_conn.cursor() as db_cur:
            db_cur.execute("SELECT * FROM orders;")
            data = db_cur.fetchall()
            for order in data:
                db_cur.execute(
                    "SELECT items_order_id FROM orders_items WHERE orders_id = %s",
                    (order["id"],),
                )
                items_data = db_cur.fetchall()
                items = [list(i.values())[0] for i in items_data]

                db_cur.execute(
                    f"SELECT SUM(price) FROM items WHERE id IN {str(tuple(items))}"
                )
                total_price = db_cur.fetchone()["sum"]
                order["items"] = items
                order["total"] = total_price
    return data


@app.get("/orders/{order_id}")
async def get_order_by_id(order_id: int):
    with psycopg.connect(
        "dbname=test user=postgres password=password host=localhost",
        autocommit=True,
        row_factory=psycopg.rows.dict_row,
    ) as db_conn:
        with db_conn.cursor() as db_cur:
            if order_id:
                if (
                    db_cur.execute(
                        "SELECT exists (SELECT 1 FROM orders WHERE id = %s LIMIT 1);",
                        (order_id,),
                    ).fetchone()["exists"]
                    is False
                    or order_id <= 0
                ):
                    raise fastapi.HTTPException(
                        status_code=404, detail="Order not found"
                    )
                db_cur.execute("SELECT * FROM orders WHERE id = %s;", (order_id,))
                order_data = db_cur.fetchone()
                db_cur.execute(
                    "SELECT items_order_id FROM orders_items WHERE orders_id = %s",
                    (order_id,),
                )
                items_data = db_cur.fetchall()
                items = [list(i.values())[0] for i in items_data]

                db_cur.execute(
                    f"SELECT SUM(price) FROM items WHERE id IN {str(tuple(items))}"
                )
                total_price = db_cur.fetchone()["sum"]
                order_data["items"] = items
                order_data["total"] = total_price
                pass
    return order_data
