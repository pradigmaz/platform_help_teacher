from typing import Any, List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.crud.crud_activity import activity as crud_activity
from app.schemas.activity import ActivityCreate, ActivityResponse, ActivityUpdate, ActivityWithStudentResponse
from app.models.user import User, UserRole
from app.models.activity import Activity
from app.models.attestation_settings import AttestationType

router = APIRouter()

@router.get("/activities", response_model=List[ActivityWithStudentResponse])
async def list_all_activities(
    attestation_type: Optional[AttestationType] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get all activities with student/group info.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Query with student relationship loaded
    query = select(Activity).where(Activity.is_active == True)
    if attestation_type:
        query = query.where(Activity.attestation_type == attestation_type)
    
    query = query.options(
        selectinload(Activity.student).selectinload(User.group)
    ).order_by(Activity.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    activities = result.scalars().all()
    
    # Build response with student info
    response = []
    for act in activities:
        student = act.student
        response.append(ActivityWithStudentResponse(
            id=act.id,
            student_id=act.student_id,
            points=act.points,
            description=act.description,
            attestation_type=act.attestation_type,
            is_active=act.is_active,
            batch_id=act.batch_id,
            created_by_id=act.created_by_id,
            created_at=act.created_at,
            updated_at=act.updated_at,
            student_name=student.full_name if student else None,
            group_name=student.group.name if student and student.group else None
        ))
    
    return response

@router.post("/activities", response_model=List[ActivityResponse])
async def create_activity(
    *,
    db: AsyncSession = Depends(deps.get_db),
    activity_in: ActivityCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new activity record(s).
    If group_id is provided, creates for all students in group.
    If student_id is provided, creates for single student.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if activity_in.group_id:
        # Batch create for group
        students_query = select(User).where(
            User.group_id == activity_in.group_id,
            User.role == UserRole.STUDENT,
            User.is_active == True
        )
        result = await db.execute(students_query)
        students = result.scalars().all()
        
        if not students:
            raise HTTPException(status_code=404, detail="No students found in group")
            
        batch_id = uuid4()
        activities = await crud_activity.create_batch(
            db,
            student_ids=[s.id for s in students],
            points=activity_in.points,
            description=activity_in.description,
            attestation_type=activity_in.attestation_type,
            batch_id=batch_id,
            created_by_id=current_user.id
        )
        return activities
        
    elif activity_in.student_id:
        # Single create
        activity = await crud_activity.create(
            db,
            obj_in=activity_in,
            created_by_id=current_user.id
        )
        return [activity]
    else:
        raise HTTPException(status_code=400, detail="Either student_id or group_id must be provided")

@router.get("/activities/student/{student_id}", response_model=List[ActivityResponse])
async def read_student_activities(
    student_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get activities for a student.
    """
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER] and str(current_user.id) != student_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    activities = await crud_activity.get_by_student(db, student_id=student_id)
    return activities

@router.patch("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    activity_in: ActivityUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update activity (e.g. deactivate).
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    activity = await crud_activity.get(db, id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    activity = await crud_activity.update(db, db_obj=activity, obj_in=activity_in)
    return activity

@router.delete("/activities/{activity_id}", response_model=ActivityResponse)
async def delete_activity(
    activity_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete (soft delete) activity.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    activity = await crud_activity.delete(db, id=activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
        
    return activity

