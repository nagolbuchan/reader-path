from typing import Any, Dict, List, Optional 
from app.repositories.graph_repo import GraphRepository

class GraphService:
    print("TESTING GRAPH SERVICE..."),
    def __init__(self, driver):
        self.graph_repo = GraphRepository(driver)

    def get_user_graph(self, user_id: int = 4) -> Dict:
        print("GraphService.get_user_graph called with user_id:", user_id)
        raw_data = self.graph_repo.get_user_graph(user_id)
        print("GraphService.get_user_graph raw_data:", raw_data)
        return raw_data