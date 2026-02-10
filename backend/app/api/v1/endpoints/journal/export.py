"""API эндпоинты для экспорта журнала."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_teacher, get_db
from app.core.limiter import limiter
from app.models import User
from app.schemas.export import ExportFormat, ExportPeriodType
from app.services.export import ExportService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/export")
@limiter.limit("10/minute")
async def export_journal(
    request: Request,
    group_id: UUID = Query(..., description="ID группы"),
    period_type: ExportPeriodType = Query(
        ExportPeriodType.SEMESTER, description="Тип периода: day, week, month, semester, custom"
    ),
    period_value: str | None = Query(
        None, description="Значение периода: 2025-01-22, 2025-W04, 2025-01, 2025-01-01:2025-01-31"
    ),
    format: ExportFormat = Query(ExportFormat.XLSX, description="Формат файла: xlsx, csv, json"),
    include_attendance: bool = Query(True, description="Включить посещаемость"),
    include_grades: bool = Query(True, description="Включить оценки"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher),
):
    """
    Экспорт журнала группы.

    Возвращает файл в указанном формате с данными посещаемости и/или оценок
    за выбранный период.

    Периоды:
    - day: конкретный день (2025-01-22)
    - week: ISO неделя (2025-W04)
    - month: месяц (2025-01)
    - semester: текущий семестр (period_value не нужен)
    - custom: произвольный диапазон (2025-01-01:2025-01-31)
    """
    # TODO: Проверка ownership (преподаватель имеет доступ к группе)
    # await verify_group_access(db, group_id, current_user)

    service = ExportService(db)
    content, filename, media_type = await service.export_journal(
        group_id=group_id,
        period_type=period_type,
        period_value=period_value,
        format=format,
        include_attendance=include_attendance,
        include_grades=include_grades,
    )

    logger.info("Экспорт журнала: user=%s, group=%s, file=%s", current_user.id, group_id, filename)

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content)),
        },
    )
