from fastapi import APIRouter, Depends
from app.models.goal import Goal
from app.dependencies import verify_token
from app.controller.goal_controller import create_goal_controller, goals_controller

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.post("/create")
async def create_goal(goal: Goal, user_data=Depends(verify_token)):
    return create_goal_controller(goal)

@router.get("/{month}/{year}")
async def goals(month: str, year: str, user_data=Depends(verify_token)):
    monthYear = f"{month}/{year}"  # p.ej. "10/25"
    return goals_controller(monthYear)
