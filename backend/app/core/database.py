# app/core/database.py
from pathlib import Path

from neo4j import AsyncDriver, AsyncGraphDatabase

from app.core.config import settings

print("Initializing Neo4j driver...")
# Global driver instance
driver: AsyncDriver | None = None

_SCHEMA_FILE = Path(__file__).resolve().parents[1] / "schema" / "constraints.cypher"


def _cypher_statements(text: str) -> list[str]:
    statements: list[str] = []
    buf: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            if stmt:
                statements.append(stmt)
            buf = []
    if buf:
        stmt = "\n".join(buf).strip().rstrip(";").strip()
        if stmt:
            statements.append(stmt)
    return statements


async def apply_schema(graph_driver: AsyncDriver) -> None:
    if not _SCHEMA_FILE.exists():
        print(f"Schema file missing: {_SCHEMA_FILE}")
        return
    statements = _cypher_statements(_SCHEMA_FILE.read_text(encoding="utf-8"))
    async with graph_driver.session() as session:
        for stmt in statements:
            await session.run(stmt)
    print(f"Applied {len(statements)} Neo4j schema statement(s)")


async def init_driver():
    """Called when FastAPI starts"""
    print("STARTING UP")
    global driver
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    )
    await driver.verify_connectivity()
    print("Neo4j driver connected successfully")
    await apply_schema(driver)


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
