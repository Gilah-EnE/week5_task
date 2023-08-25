from fastapi import FastAPI, Depends
from dependencies import *
from routers import orders, items

app = FastAPI()

app.include_router(orders.router)
app.include_router(items.router)


@app.on_event("startup")
async def on_startup():
    # await asyncio.sleep(1)    # wait for db to start (for testing, should be uncommented when packed into Docker)
    create_database_if_not_exists()
    populate_database()


@app.get("/stats")
async def stats():
    with get_db_cur() as db_cur:
        stats_data = db_cur.execute(
            """SELECT COUNT(id) AS total_items,
            SUM(price*number) AS total_order_price,
            AVG(price*number) AS avg_order_price,
            AVG(number) AS avg_items
            FROM orders_items"""
        ).fetchone()

        stats_data.update(
            db_cur.execute("SELECT COUNT(id) AS total_orders FROM orders;").fetchone()
        )

        stats_data.update(
            db_cur.execute(
                "SELECT name AS most_ordered_item FROM orders_items WHERE number = (SELECT MAX(number) FROM orders_items);"
            ).fetchone()
        )

        return stats_data
