from typing import List, Dict, Optional
from unittest import result
from app.repositories.base_repo import BaseRepository
# from app.models.graph import Graph # Does not exist, but probably a good idea. 

class GraphRepository(BaseRepository):
    print("TESTING GRAPH REPO..."),
    # This is just a test cypher query so i can get familiar with the data. 
    def get_user_graph(self, user_id: int = 4) -> Dict:
        #Cypher query to get the graph data for the user
        # query = """
        # MATCH (u:User {id: $user_id})-[:READ]->(b:Book)-[:IN_GENRE]->(g:Genre)
        # RETURN b, g, u
        # """
        query = """
        MATCH (u:User)
        RETURN u LIMIT 10
        """
        print("Executing query to get user graph...", query),
        # driver.verify_connectivity()
        # result = await driver.execute_query(query, {"user_id": user_id})
        # print("GraphRepository.get_user_graph result:", result)

        # print("GraphRepository.get_user_graph result:", result)

        # return result
        return { 1, 2, 3 }

        # return result[0] if result else {
        #     "nodes": [],
        #     "relationships": [],
        #     "total_courses": 0,
        #     "total_books": 0,
        # }