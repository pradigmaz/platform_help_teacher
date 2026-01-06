from typing import Any, List
import logging
from uuid import UUID 
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Request, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app import schemas, models
from app.api import deps
from app.db.session import get_db
from app.services.import_service import SmartImportService
from app.services.group_service import GroupService
from app.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# Лимит размера файла импорта (5 МБ)
MAX_IMPORT_FILE_SIZE = 5 * 1024 * 1024

@router.get("/", response_model=List[schemas.GroupResponse])
async def read_groups(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Получить список всех групп."""
    query = (
        select(models.Group, func.count(models.User.id).label("students_count"))
        .outerjoin(models.User, models.User.group_id == models.Group.id)
        .group_by(models.Group.id)
        .order_by(models.Group.name)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    groups = []
    for group, count in result:
        group_data = schemas.GroupResponse.model_validate(group)
        group_data.students_count = count
        groups.append(group_data)
    return groups

@router.post("/", response_model=schemas.GroupResponse)
@limiter.limit("10/minute")
async def create_group(
    request: Request,
    group_in: schemas.GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Создать новую группу."""
    service = GroupService(db)
    # create_with_students handles validation and creation
    group = await service.create_with_students(group_in)
    
    group_resp = schemas.GroupResponse.model_validate(group)
    group_resp.students_count = len(group_in.students) if group_in.students else 0
    return group_resp

@router.get("/{group_id}", response_model=schemas.GroupDetailResponse)
async def read_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_teacher),
) -> Any:
    """Детали группы."""
    query = (
        select(models.Group)
        .options(selectinload(models.Group.users)) 
        .where(models.Group.id == group_id)
    )
    result = await db.execute(query)
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    students = sorted(group.users, key=lambda u: u.full_name)
    return {
        "id": group.id,
        "name": group.name,
        "code": group.code,
        "invite_code": group.invite_code,
        "created_at": group.created_at,
        "students": students,
        "labs_count": group.labs_count,
        "grading_scale": group.grading_scale,
        "default_max_grade": group.default_max_grade,
    }


@router.post("/{group_id}/students", response_model=schemas.StudentInGroupResponse)
@limiter.limit("30/minute")
async def add_student(
    request: Request,
    group_id: UUID,
    student_data: schemas.StudentImport,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Добавить студента в группу вручную."""
    # Проверяем группу
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Создаём студента
    student = models.User(
        full_name=student_data.full_name,
        username=student_data.username,
        group_id=group_id,
        role=models.user.UserRole.STUDENT,
    )
    db.add(student)
    
    try:
        await db.commit()
        await db.refresh(student)
        return student
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error adding student: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.patch("/{group_id}/lab-settings", response_model=schemas.GroupResponse)
async def update_lab_settings(
    group_id: UUID,
    settings: schemas.LabSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Обновить настройки лабораторных для группы."""
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        if settings.labs_count is not None:
            group.labs_count = settings.labs_count
        if settings.grading_scale is not None:
            group.grading_scale = settings.grading_scale
        if settings.default_max_grade is not None:
            group.default_max_grade = settings.default_max_grade
        
        await db.commit()
        await db.refresh(group)
        
        # Подсчёт студентов
        count_query = select(func.count(models.User.id)).where(models.User.group_id == group_id)
        count_result = await db.execute(count_query)
        students_count = count_result.scalar() or 0
        
        group_resp = schemas.GroupResponse.model_validate(group)
        group_resp.students_count = students_count
        return group_resp
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error updating lab settings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/parse", response_model=List[schemas.StudentImport])
async def parse_students_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Парсинг файла."""
    # 1. Проверка размера файла
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_IMPORT_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    return await SmartImportService.parse_file(file)

@router.delete("/{group_id}")
@limiter.limit("5/minute")
async def delete_group(
    request: Request,
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Удалить группу."""
    result = await db.execute(select(models.Group).where(models.Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    try:
        await db.delete(group)
        await db.commit()
        return {"status": "success"}
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@router.delete("/{group_id}/students/{student_id}")
@limiter.limit("20/minute")
async def remove_student(
    request: Request,
    group_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Удалить студента."""
    result = await db.execute(select(models.User).where(models.User.id == student_id, models.User.group_id == group_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        await db.delete(student)
        await db.commit()
        return {"status": "success"}
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@router.patch("/{group_id}/students/{student_id}")
async def update_student(
    group_id: UUID,
    student_id: UUID,
    student_in: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Обновить студента (ФИО, подгруппа)."""
    result = await db.execute(select(models.User).where(models.User.id == student_id, models.User.group_id == group_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        if student_in.full_name is not None:
            student.full_name = student_in.full_name
        if student_in.subgroup is not None or 'subgroup' in student_in.model_fields_set:
            student.subgroup = student_in.subgroup
        await db.commit()
        await db.refresh(student)
        return {"status": "success", "student": schemas.StudentInGroupResponse.model_validate(student)}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error updating student: {e}")
        raise HTTPException(status_code=500, detail="Database error")

@router.post("/{group_id}/regenerate-invite-code")
async def regenerate_group_invite_code(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Сгенерировать/обновить инвайт-код группы."""
    service = GroupService(db)
    invite_code = await service.regenerate_group_invite_code(group_id)
    return {"invite_code": invite_code}

@router.post("/{group_id}/generate-codes")
async def regenerate_group_codes(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Сгенерировать коды."""
    service = GroupService(db)
    return await service.regenerate_group_codes(group_id)

@router.post("/users/{user_id}/regenerate-code")
async def regenerate_user_code(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Регенерировать код студента."""
    service = GroupService(db)
    invite_code = await service.regenerate_user_code(user_id)
    return {"invite_code": invite_code}


def normalize_name(name: str) -> str:
    """Нормализация ФИО для сравнения."""
    return ' '.join(name.lower().split())


def names_match(name1: str, name2: str) -> bool:
    """Проверка совпадения ФИО (fuzzy)."""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    # Точное совпадение
    if n1 == n2:
        return True
    
    # Совпадение по словам (фамилия + имя без отчества)
    parts1 = n1.split()
    parts2 = n2.split()
    
    if len(parts1) >= 2 and len(parts2) >= 2:
        # Фамилия + имя совпадают
        if parts1[0] == parts2[0] and parts1[1] == parts2[1]:
            return True
    
    return False


@router.post("/{group_id}/assign-subgroup", response_model=schemas.AssignSubgroupResponse)
async def assign_subgroup(
    group_id: UUID,
    request: schemas.AssignSubgroupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Массовое назначение подгруппы по списку ФИО."""
    # Получаем всех студентов группы
    result = await db.execute(
        select(models.User).where(
            models.User.group_id == group_id,
            models.User.role == models.UserRole.STUDENT
        )
    )
    students = list(result.scalars().all())
    
    if not students:
        raise HTTPException(status_code=404, detail="No students in group")
    
    # Нормализуем входные имена
    input_names = [name.strip() for name in request.names if name.strip()]
    
    matched_students = []
    not_found = []
    
    for input_name in input_names:
        found = False
        for student in students:
            if names_match(input_name, student.full_name):
                student.subgroup = request.subgroup
                matched_students.append(student.full_name)
                found = True
                break
        if not found:
            not_found.append(input_name)
    
    try:
        await db.commit()
        return schemas.AssignSubgroupResponse(
            matched=len(matched_students),
            updated_students=matched_students,
            not_found=not_found
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error assigning subgroups: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.post("/{group_id}/clear-subgroups")
async def clear_subgroups(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Убрать подгруппы у всех студентов группы."""
    result = await db.execute(
        select(models.User).where(
            models.User.group_id == group_id,
            models.User.role == models.UserRole.STUDENT
        )
    )
    students = list(result.scalars().all())
    
    count = 0
    for student in students:
        if student.subgroup is not None:
            student.subgroup = None
            count += 1
    
    try:
        await db.commit()
        return {"status": "success", "cleared": count}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Error clearing subgroups: {e}")
        raise HTTPException(status_code=500, detail="Database error")
