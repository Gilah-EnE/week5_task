from fastapi import FastAPI, Depends
from app.dependencies import *
from app.routers import orders, items

app = FastAPI()

app.include_router(orders.router)  # connecting orders endpoints
app.include_router(items.router)  # connecting items endpoints


@app.on_event("startup")
async def on_startup() -> None:
    """
    Startup function to initialize database and tables if they don't exist
    Returns:
        None.
    """
    await asyncio.sleep(
        10
    )  # wait for db to start (for testing, should be uncommented when packed into Docker)
    create_database_if_not_exists()
    populate_database()


@app.get("/stats")
async def stats() -> dict:
    """
    Endpoint, returns statistics of the database
    Returns:
        stats: statistics about orders and items
    """
    with get_db_cur() as db_cur:
        stats_data = db_cur.execute(
            """SELECT COUNT(id) AS total_items,
            SUM(price*number) AS total_order_price,
            AVG(price*number) AS avg_order_price,
            AVG(number) AS avg_items
            FROM orders_items"""
        ).fetchone()  # first query for statistics

        stats_data.update(
            db_cur.execute(
                "SELECT COUNT(id) AS total_orders FROM orders;"
            ).fetchone()  # adding data about total orders count
        )

        stats_data.update(
            db_cur.execute(
                "SELECT name AS most_ordered_item FROM orders_items WHERE number = (SELECT MAX(number) FROM orders_items);"  # pretty complicated SQL query to get the most ordered item
            ).fetchone()
        )

        return stats_data
