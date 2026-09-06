from typing import Any, Dict, Optional

from app.repositories.base_repo import BaseRepository


def _username_from_email(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return None
    return email.split("@", 1)[0].strip() or None


class UserRepository(BaseRepository):
    async def merge_user(
        self,
        user_id: str,
        email: Optional[str],
        name: Optional[str],
        image: Optional[str] = None,
        provider: str = "google",
    ) -> Optional[Dict[str, Any]]:
        # Neo4j property is userId; API/JWT layer uses user_id
        query = """
        MERGE (u:User {userId: $user_id})
        ON CREATE SET
            u.email = $email,
            u.username = $username,
            u.displayName = $display_name,
            u.image = $image,
            u.provider = $provider,
            u.createdAt = datetime(),
            u.lastActiveAt = datetime()
        ON MATCH SET
            u.email = coalesce($email, u.email),
            u.username = coalesce($username, u.username),
            u.displayName = coalesce($display_name, u.displayName, u.name),
            u.image = coalesce($image, u.image),
            u.provider = $provider,
            u.lastActiveAt = datetime()
        RETURN {
            user_id: u.userId,
            email: u.email,
            name: coalesce(u.displayName, u.name),
            image: u.image,
            provider: u.provider
        } AS user
        """
        result = await self.execute_query(
            query,
            {
                "user_id": user_id,
                "email": email,
                "username": _username_from_email(email),
                "display_name": name,
                "image": image,
                "provider": provider,
            },
        )
        return result[0]["user"] if result else None

    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (u:User {userId: $user_id})
        RETURN {
            user_id: u.userId,
            email: u.email,
            name: coalesce(u.displayName, u.name),
            image: u.image,
            provider: u.provider
        } AS user
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
