from typing import Any, List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.db.session import get_db
from app.core.limiter import limiter
from app.models import User, UserRole
from app.models.attendance import Attendance, AttendanceStatus
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceUpdate,
    AttendanceResponse,
    BulkAttendanceCreate,
    BulkAttendanceResponse,
    AttendanceStatsResponse,
    AttendanceStatusSchema,
)
from app.crud.attendance import (
    create_attendance,
    update_attendance,
    get_attendance_by_student,
    get_attendance_by_group_and_date,
    get_attendance_by_group_date_range,
    delete_attendance,
    bulk_create_attendance,
    AttendanceValidationError,
    DuplicateAttendanceError,
    StudentNotInGroupError,
    StudentNotFoundError,
    FutureDateError,
)

router = APIRouter()

def to_attendance_response(attendance: Attendance) -> AttendanceResponse:
    """Helper для конвертации модели Attendance в AttendanceResponse."""
    return AttendanceResponse(
        id=attendance.id,
        student_id=attendance.student_id,
        group_id=attendance.group_id,
        date=attendance.date,
        status=AttendanceStatusSchema(attendance.status.value),
        created_by=attendance.created_by,
        created_at=attendance.created_at,
        updated_at=attendance.updated_at
    )

async def check_group_access(user: User, group_id: UUID) -> None:
    """
    Проверка доступа пользователя к группе.
    Admin имеет доступ ко всем.
    Teacher - проверка привязки (будет реализована позже).
    """
    if user.role == UserRole.ADMIN:
        return
        
    # Placeholder for teacher access logic
    # if user.role == UserRole.TEACHER and user.group_id != group_id:
    #     raise HTTPException(status_code=403, detail="No access to this group")
    pass

# ============== Attendance Management Endpoints ==============
# Requirements: 8.1, 8.2, 8.3, 8.4, 8.5

@router.post("/attendance", response_model=AttendanceResponse)
@limiter.limit("50/minute")
async def create_attendance_record(
    request: Request,
    attendance_in: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Создать запись посещаемости.
    
    Requirements:
    - 8.1: store attendance records with student, group, date, and status
    - 8.3: validate student belongs to specified group
    - 8.4: prevent duplicate attendance records
    
    Args:
        attendance_in: Данные для создания записи
    
    Returns:
        AttendanceResponse с созданной записью
    
    Raises:
        400: Если студент не принадлежит группе или запись уже существует
        404: Если студент не найден
    """
    # Проверка доступа к группе
    await check_group_access(current_user, attendance_in.group_id)

    # Конвертируем статус из схемы в модель
    model_status = AttendanceStatus(attendance_in.status.value)
    
    try:
        attendance = await create_attendance(
            db=db,
            student_id=attendance_in.student_id,
            group_id=attendance_in.group_id,
            attendance_date=attendance_in.date,
            status=model_status,
            created_by=current_user.id
        )
        await db.commit()
        await db.refresh(attendance)
        
        return to_attendance_response(attendance)
    except StudentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StudentNotInGroupError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (DuplicateAttendanceError, FutureDateError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/attendance/{attendance_id}", response_model=AttendanceResponse)
async def update_attendance_record(
    attendance_id: UUID,
    attendance_in: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Обновить статус посещаемости.
    
    Args:
        attendance_id: ID записи посещаемости
        attendance_in: Новый статус
    
    Returns:
        AttendanceResponse с обновлённой записью
    
    Raises:
        404: Если запись не найдена
    """
    model_status = AttendanceStatus(attendance_in.status.value)
    
    attendance = await update_attendance(
        db=db,
        attendance_id=attendance_id,
        status=model_status
    )
    
    if not attendance:
        raise HTTPException(status_code=404, detail="Запись посещаемости не найдена")
    
    await db.commit()
    await db.refresh(attendance)
    
    return to_attendance_response(attendance)


@router.post("/attendance/bulk", response_model=BulkAttendanceResponse)
@limiter.limit("5/minute")
async def create_bulk_attendance(
    request: Request,
    bulk_in: BulkAttendanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Массовое создание записей посещаемости для группы.
    
    Валидирует каждого студента и пропускает невалидные записи.
    
    Args:
        bulk_in: Данные для массового создания
    
    Returns:
        BulkAttendanceResponse со статистикой и созданными записями
    """
    # Проверка доступа к группе
    await check_group_access(current_user, bulk_in.group_id)

    student_statuses = [
        (record.student_id, AttendanceStatus(record.status.value))
        for record in bulk_in.records
    ]
    
    created_records = await bulk_create_attendance(
        db=db,
        group_id=bulk_in.group_id,
        attendance_date=bulk_in.date,
        student_statuses=student_statuses,
        created_by=current_user.id
    )
    
    await db.commit()
    
    # Оптимизация: получаем все созданные записи одним запросом вместо цикла refresh
    response_records = []
    if created_records:
        record_ids = [r.id for r in created_records]
        query = select(Attendance).where(Attendance.id.in_(record_ids))
        result = await db.execute(query)
        fetched_records = result.scalars().all()
        response_records = [to_attendance_response(r) for r in fetched_records]
    
    return BulkAttendanceResponse(
        created_count=len(created_records),
        skipped_count=len(bulk_in.records) - len(created_records),
        records=response_records
    )


@router.get("/attendance/student/{student_id}", response_model=List[AttendanceResponse])
async def get_student_attendance(
    student_id: UUID,
    group_id: Optional[UUID] = Query(default=None, description="Фильтр по группе"),
    skip: int = Query(default=0, ge=0, description="Пропустить записей"),
    limit: int = Query(default=100, ge=1, le=1000, description="Лимит записей"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить записи посещаемости студента.
    
    Requirements: 8.5 - efficient querying of attendance data
    
    Args:
        student_id: ID студента
        group_id: ID группы (опционально)
        skip: Смещение
        limit: Лимит
    
    Returns:
        List[AttendanceResponse] с записями посещаемости
    """
    # Note: crud method doesn't support pagination yet, so slicing in memory for now
    # Ideally should pass skip/limit to crud
    records = await get_attendance_by_student(
        db=db,
        student_id=student_id,
        group_id=group_id
    )
    
    # Simple pagination implementation
    paginated_records = records[skip : skip + limit]
    
    return [to_attendance_response(r) for r in paginated_records]


@router.get("/attendance/group/{group_id}", response_model=List[AttendanceResponse])
async def get_group_attendance(
    group_id: UUID,
    attendance_date: Optional[date] = Query(default=None, description="Фильтр по дате"),
    start_date: Optional[date] = Query(default=None, description="Начало периода"),
    end_date: Optional[date] = Query(default=None, description="Конец периода"),
    skip: int = Query(default=0, ge=0, description="Пропустить записей"),
    limit: int = Query(default=100, ge=1, le=1000, description="Лимит записей"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить записи посещаемости группы.
    
    Requirements: 8.5 - efficient querying (использует индекс idx_attendance_group_date)
    
    Args:
        group_id: ID группы
        attendance_date: Конкретная дата (опционально)
        start_date: Начало периода (опционально)
        end_date: Конец периода (опционально)
        skip: Смещение
        limit: Лимит
    
    Returns:
        List[AttendanceResponse] с записями посещаемости
    """
    # Проверка доступа к группе
    await check_group_access(current_user, group_id)

    if attendance_date:
        records = await get_attendance_by_group_and_date(
            db=db,
            group_id=group_id,
            attendance_date=attendance_date
        )
    elif start_date and end_date:
        records = await get_attendance_by_group_date_range(
            db=db,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date
        )
    else:
        # Если не указаны фильтры - возвращаем все записи группы
        query = select(Attendance).where(
            Attendance.group_id == group_id
        ).order_by(Attendance.date.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        records = list(result.scalars().all())
        # Since we use direct query with limit here, we don't need slicing
        return [to_attendance_response(r) for r in records]
    
    # For other cases where we use crud functions that return all records
    paginated_records = records[skip : skip + limit]
    
    return [to_attendance_response(r) for r in paginated_records]


@router.get("/attendance/stats/{student_id}", response_model=AttendanceStatsResponse)
async def get_student_attendance_stats(
    student_id: UUID,
    group_id: Optional[UUID] = Query(default=None, description="Фильтр по группе"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Получить статистику посещаемости студента.
    
    Args:
        student_id: ID студента
        group_id: ID группы (опционально)
    
    Returns:
        AttendanceStatsResponse со статистикой
    """
    records = await get_attendance_by_student(
        db=db,
        student_id=student_id,
        group_id=group_id
    )
    
    present_count = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    late_count = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    excused_count = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)
    absent_count = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    total_classes = len(records)
    
    # Процент посещаемости (присутствие + опоздание считаются как посещение)
    attendance_rate = 0.0
    if total_classes > 0:
        attendance_rate = round((present_count + late_count) / total_classes * 100, 1)
    
    return AttendanceStatsResponse(
        student_id=student_id,
        total_classes=total_classes,
        present_count=present_count,
        late_count=late_count,
        excused_count=excused_count,
        absent_count=absent_count,
        attendance_rate=attendance_rate
    )


@router.delete("/attendance/{attendance_id}")
async def delete_attendance_record(
    attendance_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
):
    """
    Удалить запись посещаемости.
    
    Args:
        attendance_id: ID записи
    
    Returns:
        Статус удаления
    
    Raises:
        404: Если запись не найдена
    """
    deleted = await delete_attendance(db=db, attendance_id=attendance_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Запись посещаемости не найдена")
    
    await db.commit()
    return {"status": "deleted", "id": str(attendance_id)}
