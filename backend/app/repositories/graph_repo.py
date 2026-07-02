from typing import List, Dict, Optional
from unittest import result
from app.repositories.base_repo import BaseRepository
# from app.models.graph import Graph # Does not exist, but probably a good idea. 

class GraphRepository(BaseRepository):
    print("TESTING GRAPH REPO..."),
    # This is just a test cypher query so i can get familiar with the data. 

    async def get_user_graph(self, user_id: int = 7) -> Dict:
        query = """
            MATCH path = (u:User {userId: $user_id})-[:READ]->(b:Book)-[:IN_GENRE]->(g:Genre)
            RETURN path
        """
        #-[:IN_GENRE]->(g:Genre)
        # This calls BaseRepository.execute_query and gives a standard Python list of dicts
        results = await self.execute_query(query, {"user_id": user_id})

        nodes_map = {}
        relationships = []

        # Helper function to get consistent string IDs from raw dictionary properties
        def get_node_id_from_dict(item: dict) -> str:
            if 'userId' in item:
                return f"user_{item['userId']}"
            elif 'bookId' in item:
                return f"book_{item['bookId']}"
            elif 'genre_id' in item:
                return f"genre_{item['genre_id']}"
            return None

        for record in results:
            # result.data() converts the 'path' return variable into a native Python list
            path_list = record.get("path")
            if not isinstance(path_list, list):
                continue

            # 1. Process all nodes (found at all even indices: 0, 2, 4)
            for i in range(0, len(path_list), 2):
                node_item = path_list[i]
                if not isinstance(node_item, dict):
                    continue

                node_id = get_node_id_from_dict(node_item)
                if not node_id:
                    continue

                # Determine the frontend structural details
                if 'userId' in node_item:
                    node_type = "User"
                    label = f"{node_item.get('firstName', '')} {node_item.get('lastName', '')}".strip()
                elif 'bookId' in node_item:
                    node_type = "Book"
                    label = node_item.get('title', 'Unknown Book')
                elif 'genre_id' in node_item:
                    node_type = "Genre"
                    label = node_item.get('genre', 'Unknown Genre')

                if node_id not in nodes_map:
                    nodes_map[node_id] = {
                        "id": node_id,
                        "type": node_type,
                        "label": label,
                        "properties": node_item
                    }

            # 2. Process all relationships (found at all odd indices: 1, 3)
            for i in range(1, len(path_list), 2):
                # In result.data(), the relationship index contains relationship properties.
                # The actual source node is right before it (i-1), and target node is right after it (i+1).
                source_node_dict = path_list[i-1]
                target_node_dict = path_list[i+1]

                if not (isinstance(source_node_dict, dict) and isinstance(target_node_dict, dict)):
                    continue

                source_id = get_node_id_from_dict(source_node_dict)
                target_id = get_node_id_from_dict(target_node_dict)

                if source_id and target_id:
                    # If your backend requires the relationship type string (e.g. "READ"),
                    # path_list[i] for a relationship can sometimes just be the raw properties dict.
                    # If you need a fallback name, we can check standard keys or hardcode based on position.
                    rel_type = "CONNECTED_TO"
                    if "userId" in source_node_dict and "bookId" in target_node_dict:
                        rel_type = "READ"
                    elif "bookId" in source_node_dict and "genre_id" in target_node_dict:
                        rel_type = "IN_GENRE"

                    rel_obj = {
                        "from": source_id,
                        "to": target_id,
                        "type": rel_type
                    }

                    # Deduplicate connections to keep React Flow running smoothly
                    if rel_obj not in relationships:
                        relationships.append(rel_obj)

        return {
            "nodes": list(nodes_map.values()),
            "relationships": relationships
        }