# app/core/database.py
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings
print("Initializing Neo4j driver...")
# Global driver instance
driver: AsyncDriver | None = None

async def init_driver():
    """Called when FastAPI starts"""
    print('STARTING UP')
    global driver
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )
    await driver.verify_connectivity()
    print("✅ Neo4j driver connected successfully")


async def get_driver() -> AsyncDriver:
    """This is the function we use with FastAPI's Depends()"""
    if driver is None:
        raise RuntimeError("Neo4j driver not initialized")
    return driver


async def close_driver():
    """Called when FastAPI shuts down"""
    global driver
    if driver:
        await driver.close()