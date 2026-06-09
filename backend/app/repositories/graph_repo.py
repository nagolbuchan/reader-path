from typing import List, Dict, Optional
from unittest import result
from app.repositories.base_repo import BaseRepository
# from app.models.graph import Graph # Does not exist, but probably a good idea. 

class GraphRepository(BaseRepository):
    print("TESTING GRAPH REPO..."),
    # This is just a test cypher query so i can get familiar with the data. 
    async def get_user_graph(self, user_id: int = 7) -> Dict:
        #Cypher query to get the graph data for the user
        # query = """
        # MATCH (u:User {userId: $user_id})-[:READ]->(b:Book)-[:IN_GENRE]->(g:Genre)
        # RETURN b.title AS book_title, collect(g.genre) AS genres
        # """
        query = """
        MATCH path = (u:User {userId: $user_id})-[:READ]->(b:Book)-[:IN_GENRE]->(g:Genre)
        RETURN path
        """
        print("Executing query to get user graph...", query),
        
        result = await self.execute_query(query, {"user_id": user_id})
        print("GraphRepository.get_user_graph result:", result)

        return result