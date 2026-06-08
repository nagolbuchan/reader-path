from neo4j import AsyncDriver
from typing import Any, Dict, List

class BaseRepository:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver
    
    async def execute_query(self, query: str, parameters: Dict = None):
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

