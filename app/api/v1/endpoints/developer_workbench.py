from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.models.project import Project, Task, WorkItem, Milestone
from app.models.user import User
from app.schemas.developer_workbench import (
    DeveloperStats,
    TaskInfo,
    CodeReviewRequest,
    CodeReviewResponse,
    TimeEntry,
    StatusUpdate,
    AIQuery,
    AIResponse,
    DeveloperActivity,
    TaskStatus,
    TaskPriority,
    ActivityType
)
from app.services.enhanced_ai_orchestrator import get_ai_orchestrator
from app.services.autonomous_decision_engine import get_decision_engine

router = APIRouter()

@router.get("/stats/{user_id}", response_model=DeveloperStats)
async def get_developer_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get developer statistics and metrics"""
    try:
        # Demo mode - return sample data
        return DeveloperStats(
            active_tasks=5,
            completed_this_week=3,
            hours_logged=32.5,
            productivity=85.0,
            code_reviews_pending=2,
            last_activity=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching developer stats: {str(e)}")

@router.get("/tasks/{user_id}", response_model=List[TaskInfo])
async def get_developer_tasks(
    user_id: int,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get tasks assigned to the developer"""
    try:
        # Demo mode - return sample tasks
        sample_tasks = [
            TaskInfo(
                id=1,
                title="Fix Authentication Bug",
                description="Critical authentication issue in login module",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                due_date=datetime.now() + timedelta(days=1),
                estimated_hours=8.0,
                project_name="ALPHA Project"
            ),
            TaskInfo(
                id=2,
                title="Implement User Dashboard",
                description="Create new user dashboard with analytics",
                status=TaskStatus.TODO,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.now() + timedelta(days=5),
                estimated_hours=16.0,
                project_name="BETA Project"
            ),
            TaskInfo(
                id=3,
                title="Code Review: Payment Module",
                description="Review payment processing implementation",
                status=TaskStatus.REVIEW,
                priority=TaskPriority.MEDIUM,
                due_date=datetime.now() + timedelta(days=2),
                estimated_hours=4.0,
                project_name="GAMMA Project"
            )
        ]
        
        if status:
            sample_tasks = [task for task in sample_tasks if task.status.value == status]
        
        return sample_tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@router.post("/code-review", response_model=CodeReviewResponse)
async def request_code_review(
    request: CodeReviewRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request AI-powered code review"""
    try:
        ai_orchestrator = get_ai_orchestrator()
        
        # Analyze code using AI
        analysis_prompt = f"""
        Please review the following code for:
        1. Code quality and best practices
        2. Potential bugs and issues
        3. Security vulnerabilities
        4. Performance optimizations
        5. Maintainability improvements
        
        Code:
        {request.code}
        
        Language: {request.language}
        Context: {request.context}
        """
        
        analysis_result = await ai_orchestrator.generate_response(
            query=analysis_prompt,
            context={"task_type": "code_review"},
            model_override="gpt-oss:20B"
        )
        analysis = analysis_result.get("response", "Analysis not available")
        
        # Generate recommendations
        recommendations_prompt = f"""
        Based on the code analysis above, provide specific, actionable recommendations for improvement.
        Focus on:
        - Critical issues that need immediate attention
        - Performance improvements
        - Code structure and readability
        - Security considerations
        """
        
        recommendations_result = await ai_orchestrator.generate_response(
            query=recommendations_prompt,
            context={"task_type": "code_review"},
            model_override="gpt-oss:20B"
        )
        recommendations = recommendations_result.get("response", "Recommendations not available")
        
        return CodeReviewResponse(
            analysis=analysis,
            recommendations=recommendations,
            score=85,  # TODO: Implement scoring algorithm
            issues_found=3,  # TODO: Count actual issues
            review_date=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing code review: {str(e)}")

@router.post("/time-entry")
async def log_time_entry(
    entry: TimeEntry,
    db: AsyncSession = Depends(get_db)
):
    """Log time spent on tasks"""
    try:
        # Insert time entry
        await db.execute(
            text("""
            INSERT INTO time_entries (user_id, task_id, hours, description, date)
            VALUES (:user_id, :task_id, :hours, :description, :date)
            """),
            {
                "user_id": entry.user_id,
                "task_id": entry.task_id,
                "hours": entry.hours,
                "description": entry.description,
                "date": entry.date
            }
        )
        
        # Update task progress if provided
        if entry.task_progress:
            await db.execute(
                text("UPDATE tasks SET progress = :progress WHERE id = :task_id"),
                {"progress": entry.task_progress, "task_id": entry.task_id}
            )
        
        await db.commit()
        
        return {"message": "Time entry logged successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error logging time entry: {str(e)}")

@router.post("/status-update")
async def save_status_update(
    update: StatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Save developer status update"""
    try:
        await db.execute(
            text("""
            INSERT INTO status_updates (user_id, content, project_id, date)
            VALUES (:user_id, :content, :project_id, :date)
            """),
            {
                "user_id": update.user_id,
                "content": update.content,
                "project_id": update.project_id,
                "date": update.date
            }
        )
        
        await db.commit()
        
        return {"message": "Status update saved successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving status update: {str(e)}")

@router.post("/ai-query", response_model=AIResponse)
async def query_ai_assistant(
    query: AIQuery,
    db: AsyncSession = Depends(get_db)
):
    """Query AI development assistant"""
    try:
        ai_orchestrator = get_ai_orchestrator()
        
        # Get context from user's recent activities
        context_query = f"""
        User Context:
        - User ID: {query.user_id}
        - Query Type: {query.query_type}
        - Current Project: {query.project_id if query.project_id else 'None'}
        
        Recent Activities:
        - Tasks: {query.recent_tasks if query.recent_tasks else 'None'}
        - Code Changes: {query.code_context if query.code_context else 'None'}
        """
        
        # Create enhanced prompt with context
        enhanced_prompt = f"""
        {context_query}
        
        User Question: {query.question}
        
        Please provide a helpful, actionable response that considers the user's context and current work.
        """
        
        response_result = await ai_orchestrator.generate_response(
            query=enhanced_prompt,
            context={"task_type": query.query_type},
            model_override="gpt-oss:20B"
        )
        response = response_result.get("response", "Response not available")
        
        return AIResponse(
            response=response,
            suggestions=generate_suggestions(query.query_type),
            related_resources=[]  # TODO: Implement resource suggestions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing AI query: {str(e)}")

@router.get("/activity/{user_id}", response_model=List[DeveloperActivity])
async def get_developer_activity(
    user_id: int,
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """Get developer's recent activity"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Demo mode - return sample activities
        sample_activities = [
            DeveloperActivity(
                type=ActivityType.TASK_COMPLETED,
                description="Authentication module implementation",
                timestamp=datetime.now() - timedelta(hours=2),
                project_name="ALPHA Project"
            ),
            DeveloperActivity(
                type=ActivityType.TIME_LOGGED,
                description="Worked on user dashboard",
                timestamp=datetime.now() - timedelta(hours=4),
                project_name="BETA Project"
            ),
            DeveloperActivity(
                type=ActivityType.CODE_REVIEW,
                description="Reviewed payment processing code",
                timestamp=datetime.now() - timedelta(hours=6),
                project_name="GAMMA Project"
            ),
            DeveloperActivity(
                type=ActivityType.BUG_FIXED,
                description="Fixed login validation bug",
                timestamp=datetime.now() - timedelta(days=1),
                project_name="ALPHA Project"
            )
        ]
        
        return sample_activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activity: {str(e)}")

@router.post("/generate-status")
async def generate_ai_status_update(
    user_id: int,
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI-powered status update based on recent activities"""
    try:
        # Get recent activities for context
        recent_activities = await get_developer_activity(user_id, 7, db)
        
        # Get current tasks
        current_tasks = await get_developer_tasks(user_id, "in_progress", db)
        
        # Create context for AI
        context = f"""
        Recent Activities:
        {json.dumps([activity.dict() for activity in recent_activities[:5]], default=str)}
        
        Current Tasks:
        {json.dumps([task.dict() for task in current_tasks[:3]], default=str)}
        """
        
        ai_orchestrator = get_ai_orchestrator()
        
        prompt = f"""
        Based on the following developer activities and current tasks, generate a professional status update:
        
        {context}
        
        Please create a status update that includes:
        1. What was accomplished today/this week
        2. Current blockers or challenges
        3. Next steps and priorities
        4. Any help needed from the team
        
        Make it concise, professional, and actionable.
        """
        
        status_update_result = await ai_orchestrator.generate_response(
            query=prompt,
            context={"task_type": "status_generation"},
            model_override="gpt-oss:20B"
        )
        status_update = status_update_result.get("response", "Status update not available")
        
        return {"status_update": status_update}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating status update: {str(e)}")

def generate_suggestions(query_type: str) -> List[str]:
    """Generate contextual suggestions based on query type"""
    suggestions = {
        "code_review": [
            "Review code for security vulnerabilities",
            "Check for performance optimizations",
            "Verify coding standards compliance"
        ],
        "debug": [
            "Check error logs and stack traces",
            "Verify input validation",
            "Test edge cases and boundary conditions"
        ],
        "optimize": [
            "Profile code performance",
            "Review database queries",
            "Check for memory leaks"
        ],
        "test": [
            "Write unit tests for core functionality",
            "Create integration tests",
            "Add test coverage for edge cases"
        ]
    }
    
    return suggestions.get(query_type, ["Consider best practices", "Review documentation", "Ask for peer review"])
