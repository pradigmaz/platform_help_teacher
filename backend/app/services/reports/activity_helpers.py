"""
Хелперы для работы с активностью студентов.
"""
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.schemas.report import ActivityRecord


async def get_student_activity(
    db: AsyncSession,
    student_id: UUID
) -> List[ActivityRecord]:
    """Получить записи активности студента."""
    query = (
        select(Activity)
        .where(Activity.student_id == student_id, Activity.is_active == True)
        .order_by(Activity.created_at.desc())
    )
    result = await db.execute(query)
    activities = result.scalars().all()
    
    return [
        ActivityRecord(date=a.created_at, description=a.description or "", points=a.points)
        for a in activities
    ]


def generate_recommendations(
    result: Any,
    att_stats: Dict,
    labs_completed: int,
    labs_total: int
) -> List[str]:
    """Генерация рекомендаций для студента."""
    recommendations = []
    
    if result and result.breakdown:
        # Проверяем баллы за лабы относительно максимума компонента
        if result.breakdown.labs_score < result.breakdown.labs_max * 0.3:
            missing_labs = labs_total - labs_completed
            if missing_labs > 0:
                recommendations.append(f"Необходимо сдать {missing_labs} лабораторных работ")
        
        # Проверяем баллы за посещаемость относительно максимума компонента
        if result.breakdown.attendance_score < result.breakdown.attendance_max * 0.5:
            recommendations.append("Рекомендуется улучшить посещаемость занятий")
    
    if att_stats:
        absent_rate = att_stats.get('absent', 0) / max(att_stats.get('total', 1), 1)
        if absent_rate > 0.3:
            recommendations.append(
                f"Пропущено {att_stats.get('absent', 0)} занятий. "
                "Рекомендуется посещать все занятия."
            )
    
    if not recommendations:
        recommendations.append("Обратитесь к преподавателю для уточнения требований")
    
    return recommendations
