from neo4j import GraphDatabase, AsyncGraphDatabase
from app.core.config import settings
import structlog
from typing import Optional

logger = structlog.get_logger(__name__)

class Neo4jConnection:
    def __init__(self):
        self.driver = None
        self.async_driver = None

    def connect(self):
        """Sync driver - useful for simple operations"""
        if not self.driver:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            logger.info("Neo4j sync driver connected successfully")
        return self.driver

    async def connect_async(self):
        """Async driver - better for FastAPI"""
        if not self.async_driver:
            self.async_driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            logger.info("Neo4j async driver connected successfully")
        return self.async_driver

    async def close(self):
        """Close both drivers"""
        if self.driver:
            await self.driver.close()
            self.driver = None
        if self.async_driver:
            await self.async_driver.close()
            self.async_driver = None
        logger.info("Neo4j connections closed")

    async def verify_connection(self):
        """Test the connection"""
        try:
            driver = await self.connect_async()
            async with driver.session() as session:
                result = await session.run("RETURN 1 AS connected")
                record = await result.single()
                if record and record["connected"] == 1:
                    logger.info("Neo4j connection verified successfully")
                    return True
            return False
        except Exception as e:
            logger.error("Failed to verify Neo4j connection", error=str(e))
            return False


# Global instance
neo4j_conn = Neo4jConnection()