#Search by topic to books
    #code to be used by agents??
from app.repositories.base_repo import BaseRepository
from typing import List, Dict, Optional

class BookRepository(BaseRepository):
    # What needs to be created when a book is added to the database? 
        #Book node, Topic relationship, Genre relationship, Author relationship, Module relationship(?)

        #Flow: user enters topic; agent searches for books first (checks neo4j; if none, then searches internet)
            #Agent organizes books into course and modules -- shows the user the course and its modules, allowing the user
            #to review and change the course.  After the user approves the course, then data is saved to the database:
                #In the case when a new book is found, the book node is created; it's relationships to topic and genre are created, assuming those exist.
                    #And if the author node exists, then the relationship to the author is created; if not, the process for identifying the author and creating a node
                    #is triggered.  And the book is added to the appropriate module in the course.  

    # async def create_book(self, title: str, author: str, topic: str, genre: str) -> Dict:



    async def search_unread_books_by_topic(self, topic: str, user_id: str) -> List[Dict]:
        query = """
        MATCH (b:Book)-[:RELATED_TO]->(t:Topic {name: $topic})
        WHERE NOT EXISTS {
            MATCH (u:User {user_id: $user_id})-[:READ]->(b)
        }
        RETURN b
        """
        result = await self.execute_query(query, {"topic": topic, "user_id": user_id})
        return [record['b'] for record in result]

    async def search_unread_books_by_genre(self, genre: str, user_id: str) -> List[Dict]:
        query = """
        MATCH (b:Book)-[:IN_GENRE]->(g:Genre {name: $genre})
        WHERE NOT EXISTS {
            MATCH (u:User {user_id: $user_id})-[:READ]->(b)
        }
        RETURN b
        """
        result = await self.execute_query(query, {"genre": genre, "user_id": user_id})
        return [record['b'] for record in result]