from typing import Dict, Optional

from app.repositories.graph_repo import GraphRepository


class GraphService:
    def __init__(self, driver):
        self.graph_repo = GraphRepository(driver)

    async def get_user_graph(self, user_id: str) -> Dict:
        return await self.graph_repo.get_user_graph(user_id)
