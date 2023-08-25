from fastapi import FastAPI, Depends
from dependencies import *
from routers import orders

app = FastAPI()

app.include_router(orders.router)


@app.on_event("startup")
async def on_startup():
    # await asyncio.sleep(1)    # wait for db to start (for testing, should be uncommented when packed into Docker)
    create_database_if_not_exists()
    populate_database()
