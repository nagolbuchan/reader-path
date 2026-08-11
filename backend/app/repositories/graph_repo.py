from typing import Any, Dict, List, Optional

from app.repositories.base_repo import BaseRepository


class GraphRepository(BaseRepository):
    async def get_user_graph(self, user_id: str) -> Dict[str, List]:
        """
        Return learning-journey graph:
        User -> Course -> Module -> Book | Assignment
        Plus Topic and Author nodes when present.
        """
        query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[:CREATED]->(c:Course)
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        OPTIONAL MATCH (m)-[:ASSIGNS_READING]->(b:Book)
        OPTIONAL MATCH (m)-[:HAS_ASSIGNMENT]->(a:Assignment)
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
        OPTIONAL MATCH (b)-[:WRITTEN_BY]->(auth:Author)
        RETURN u, collect(DISTINCT c) AS courses,
               collect(DISTINCT m) AS modules,
               collect(DISTINCT b) AS books,
               collect(DISTINCT a) AS assignments,
               collect(DISTINCT t) AS topics,
               collect(DISTINCT auth) AS authors
        """
        rows = await self.execute_query(query, {"user_id": user_id})
        if not rows:
            return {"nodes": [], "relationships": []}

        row = rows[0]
        user = row.get("u")
        if not user:
            return {"nodes": [], "relationships": []}

        nodes_map: Dict[str, Dict[str, Any]] = {}
        relationships: List[Dict[str, str]] = []

        def add_node(node_id: str, node_type: str, label: str, properties: Any = None):
            if node_id not in nodes_map:
                nodes_map[node_id] = {
                    "id": node_id,
                    "type": node_type,
                    "label": label,
                    "properties": properties or {},
                }

        user_props = dict(user)
        user_node_id = f"user_{user_props.get('user_id')}"
        add_node(
            user_node_id,
            "User",
            user_props.get("name") or user_props.get("email") or "You",
            user_props,
        )

        # Re-query relationships explicitly for clean edge list
        rel_query = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)-[:CREATED]->(c:Course)
        OPTIONAL MATCH (c)-[:HAS_MODULE]->(m:Module)
        OPTIONAL MATCH (m)-[:ASSIGNS_READING]->(b:Book)
        OPTIONAL MATCH (m)-[:HAS_ASSIGNMENT]->(a:Assignment)
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
        OPTIONAL MATCH (b)-[:WRITTEN_BY]->(auth:Author)
        RETURN u, c, m, b, a, t, auth
        """
        rel_rows = await self.execute_query(rel_query, {"user_id": user_id})

        for record in rel_rows:
            c = record.get("c")
            m = record.get("m")
            b = record.get("b")
            a = record.get("a")
            t = record.get("t")
            auth = record.get("auth")

            if c:
                c_props = dict(c)
                c_id = f"course_{c_props.get('course_id')}"
                add_node(c_id, "Course", c_props.get("title") or "Course", c_props)
                edge = {"from": user_node_id, "to": c_id, "type": "CREATED"}
                if edge not in relationships:
                    relationships.append(edge)

                if t:
                    t_props = dict(t)
                    t_id = f"topic_{t_props.get('slug') or t_props.get('name')}"
                    add_node(t_id, "Topic", t_props.get("name") or "Topic", t_props)
                    edge = {"from": c_id, "to": t_id, "type": "ABOUT"}
                    if edge not in relationships:
                        relationships.append(edge)

            if c and m:
                m_props = dict(m)
                m_id = f"module_{m_props.get('module_id')}"
                add_node(m_id, "Module", m_props.get("title") or "Module", m_props)
                c_id = f"course_{dict(c).get('course_id')}"
                edge = {"from": c_id, "to": m_id, "type": "HAS_MODULE"}
                if edge not in relationships:
                    relationships.append(edge)

            if m and b:
                b_props = dict(b)
                b_id = f"book_{b_props.get('book_id') or b_props.get('title')}"
                add_node(b_id, "Book", b_props.get("title") or "Book", b_props)
                m_id = f"module_{dict(m).get('module_id')}"
                edge = {"from": m_id, "to": b_id, "type": "ASSIGNS_READING"}
                if edge not in relationships:
                    relationships.append(edge)

            if m and a:
                a_props = dict(a)
                a_id = f"assignment_{a_props.get('assignment_id')}"
                add_node(
                    a_id,
                    "Assignment",
                    a_props.get("title") or "Assignment",
                    a_props,
                )
                m_id = f"module_{dict(m).get('module_id')}"
                edge = {"from": m_id, "to": a_id, "type": "HAS_ASSIGNMENT"}
                if edge not in relationships:
                    relationships.append(edge)

            if b and auth:
                auth_props = dict(auth)
                auth_id = f"author_{auth_props.get('name')}"
                add_node(
                    auth_id,
                    "Author",
                    auth_props.get("name") or "Author",
                    auth_props,
                )
                b_id = f"book_{dict(b).get('book_id') or dict(b).get('title')}"
                edge = {"from": b_id, "to": auth_id, "type": "WRITTEN_BY"}
                if edge not in relationships:
                    relationships.append(edge)

        return {"nodes": list(nodes_map.values()), "relationships": relationships}
