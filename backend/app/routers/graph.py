from fastapi import APIRouter, Depends, HTTPException
from neo4j import AsyncDriver

from app.core.database import get_driver
from app.core.security import get_current_user
from app.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/test-route")
def test_route():
    return {"message": "Test route is working!"}


@router.get("/user-graph")
async def get_my_learning_graph(
    driver: AsyncDriver = Depends(get_driver),
    current_user=Depends(get_current_user),
):
    service = GraphService(driver)
    return await service.get_user_graph(current_user["user_id"])


@router.get("/users/{user_id}")
async def get_public_user_graph(
    user_id: str,
    driver: AsyncDriver = Depends(get_driver),
):
    service = GraphService(driver)
    graph = await service.get_user_graph(user_id)
    if not graph.get("nodes"):
        raise HTTPException(status_code=404, detail="User graph not found")
    return graph
