from typing import Any, Dict, Optional

from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):
    async def merge_user(
        self,
        user_id: str,
        email: Optional[str],
        name: Optional[str],
        image: Optional[str] = None,
        provider: str = "google",
    ) -> Optional[Dict[str, Any]]:
        query = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET
            u.email = $email,
            u.name = $name,
            u.image = $image,
            u.provider = $provider,
            u.created_at = datetime()
        ON MATCH SET
            u.email = coalesce($email, u.email),
            u.name = coalesce($name, u.name),
            u.image = coalesce($image, u.image),
            u.provider = $provider,
            u.updated_at = datetime()
        RETURN u { .user_id, .email, .name, .image, .provider } AS user
        """
        result = await self.execute_query(
            query,
            {
                "user_id": user_id,
                "email": email,
                "name": name,
                "image": image,
                "provider": provider,
            },
        )
        return result[0]["user"] if result else None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (u:User {user_id: $user_id})
        RETURN u { .user_id, .email, .name, .image, .provider } AS user
        """
        result = await self.execute_query(query, {"user_id": user_id})
        return result[0]["user"] if result else None

    async def create_user(
        self, user_id: str, first_name: str, last_name: str
    ) -> Optional[Dict[str, Any]]:
        name = f"{first_name} {last_name}".strip()
        return await self.merge_user(
            user_id=user_id,
            email=None,
            name=name or "Reader",
            provider="local",
        )
