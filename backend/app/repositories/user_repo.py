from app.repositories.base_repo import BaseRepository
# from typing import List, Dict, Optional

class UserRepository(BaseRepository):
    async def create_user(self, user_id: str, first_name: str, last_name: str):
        query = """
        CREATE (u:User {
            user_id: $user_id,
            first_name: $first_name,
            last_name: $last_name,
            created_at: datetime()
        })
        RETURN u
        """
        result = await self.execute_query(query, {"user_id": user_id, "first_name": first_name, "last_name": last_name})
        return result[0]['u'] if result else None
    
    async def get_user(self, user_id: str):
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u
        """
        result = await self.execute_query(query, {"user_id": user_id})
        return result[0]['u'] if result else None