# app/routers/graph.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_driver
from app.services.graph_service import GraphService
# from app.dependencies import get_current_user  # We'll create this soon

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("/test-route")
def test_route():
    return {"message": "Test route is working!"}

#Do you need to add Annotated to the dependencies?  I think you do, but check other routers for reference.  You also need to import get_current_user, which is a dependency that checks the auth token and retrieves the user info.  This is important for ensuring that users can only access their own graphs and courses.
@router.get("/user-graph")
async def get_my_learning_graph(
    driver=Depends(get_driver),
    # current_user=Depends(get_current_user)
):
    print('get_my_learning_graph')
    """Main endpoint for the interactive homepage graph"""
    service = GraphService(driver)
    graph = await service.get_user_graph(7) # Replace with current_user.id when auth is set up
    print("Graph retrieved:", graph)
    return graph


@router.get("/courses/{course_id}/subgraph")
async def get_course_subgraph(
    course_id: str,
    driver=Depends(get_driver),
    # current_user=Depends(get_current_user)
):
    """Get detailed subgraph when user clicks on a course"""
    service = GraphService(driver)
    subgraph = await service.get_course_subgraph(course_id, 4) # Replace with current_user.id when auth is set up
    if not subgraph:
        raise HTTPException(status_code=404, detail="Course not found")
    return subgraph