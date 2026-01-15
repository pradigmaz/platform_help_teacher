"""
Хелперы для сбора данных посещаемости.
"""
from typing import List, Dict, Optional
from datetime import date
from uuid import UUID
from collections import defaultdict

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.report import AttendanceDistribution, AttendanceRecord, DateAttendance, AttendanceStats, TodayLessonAttendance
from app.services.schedule_constants import today_msk


async def get_group_attendance_stats(
    db: AsyncSession,
    group_id: UUID,
    students: List[User]
) -> Dict[UUID, Dict]:
    """Получить статистику посещаемости группы."""
    student_ids = [s.id for s in students]
    
    query = (
        select(
            Attendance.student_id,
            Attendance.status,
            func.count(Attendance.id).label('count')
        )
        .where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids)
        )
        .group_by(Attendance.student_id, Attendance.status)
    )
    result = await db.execute(query)
    
    stats = defaultdict(lambda: {'present': 0, 'late': 0, 'excused': 0, 'absent': 0, 'total': 0})
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        stats[row.student_id][status_str] = row.count
        stats[row.student_id]['total'] += row.count
    
    for student_id, data in stats.items():
        total = data['total']
        if total > 0:
            present_equivalent = data['present'] + data['late'] * 0.5 + data['excused'] * 0.5
            data['rate'] = round(present_equivalent / total * 100, 1)
        else:
            data['rate'] = 0.0
    
    return dict(stats)


async def get_attendance_distribution(
    db: AsyncSession,
    group_id: UUID,
    students: List[User],
    semester_start_date: Optional[date] = None
) -> AttendanceDistribution:
    """Получить распределение посещаемости группы."""
    student_ids = [s.id for s in students]
    
    query = (
        select(Attendance.status, func.count(Attendance.id).label('count'))
        .where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids)
        )
    )
    if semester_start_date:
        query = query.where(Attendance.date >= semester_start_date)
    query = query.group_by(Attendance.status)
    result = await db.execute(query)
    
    distribution = AttendanceDistribution()
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        if hasattr(distribution, status_str):
            setattr(distribution, status_str, row.count)
    
    return distribution


async def get_student_attendance_history(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID
) -> List[AttendanceRecord]:
    """Получить историю посещаемости студента с деталями пар."""
    query = (
        select(Attendance)
        .where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id
        )
        .order_by(Attendance.date.desc())
    )
    result = await db.execute(query)
    records = result.scalars().all()
    
    history = []
    for r in records:
        status_str = r.status.value.lower() if hasattr(r.status, 'value') else str(r.status).lower()
        lesson_type_str = None
        if r.lesson_type:
            lesson_type_str = r.lesson_type.value if hasattr(r.lesson_type, 'value') else str(r.lesson_type)
        
        history.append(AttendanceRecord(
            date=r.date,
            status=status_str,
            lesson_topic=None,  # TODO: join с Lesson если нужен topic
            lesson_number=r.lesson_number,
            lesson_type=lesson_type_str,
            subgroup=r.subgroup
        ))
    
    return history


async def get_student_attendance_stats(
    db: AsyncSession,
    student_id: UUID,
    group_id: UUID
) -> Dict:
    """Получить статистику посещаемости студента."""
    query = (
        select(Attendance.status, func.count(Attendance.id).label('count'))
        .where(
            Attendance.student_id == student_id,
            Attendance.group_id == group_id
        )
        .group_by(Attendance.status)
    )
    result = await db.execute(query)
    
    stats = {'present': 0, 'late': 0, 'excused': 0, 'absent': 0, 'total': 0}
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        stats[status_str] = row.count
        stats['total'] += row.count
    
    if stats['total'] > 0:
        present_equivalent = stats['present'] + stats['late'] * 0.5 + stats['excused'] * 0.5
        stats['rate'] = round(present_equivalent / stats['total'] * 100, 1)
    else:
        stats['rate'] = 0.0
    
    return stats


async def get_attendance_by_subgroup(
    db: AsyncSession,
    group_id: UUID,
    students: List[User]
) -> Dict[str, AttendanceDistribution]:
    """Получить распределение посещаемости по подгруппам."""
    result = {}
    
    for subgroup in [1, 2]:
        subgroup_students = [s for s in students if s.subgroup == subgroup]
        if not subgroup_students:
            result[str(subgroup)] = AttendanceDistribution()
            continue
            
        student_ids = [s.id for s in subgroup_students]
        query = (
            select(Attendance.status, func.count(Attendance.id).label('count'))
            .where(
                Attendance.group_id == group_id,
                Attendance.student_id.in_(student_ids)
            )
            .group_by(Attendance.status)
        )
        res = await db.execute(query)
        
        dist = AttendanceDistribution()
        for row in res.all():
            status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
            if hasattr(dist, status_str):
                setattr(dist, status_str, row.count)
        result[str(subgroup)] = dist
    
    return result


async def get_attendance_trend(
    db: AsyncSession,
    group_id: UUID,
    students: List[User],
    limit: int = 20,
    semester_start_date: Optional[date] = None,
    subject_id: Optional[UUID] = None
) -> List[DateAttendance]:
    """Получить динамику посещаемости по датам занятий из расписания.
    
    Возвращает данные с указанием подгруппы для каждого занятия:
    - subgroup=None для лекций (все студенты)
    - subgroup=1 или 2 для лабораторных
    """
    student_ids = [s.id for s in students]
    
    # Получаем все занятия из расписания с подгруппами
    lessons_query = (
        select(Lesson.date, Lesson.subgroup, Lesson.lesson_type)
        .where(
            Lesson.group_id == group_id,
            Lesson.is_cancelled == False
        )
        .order_by(Lesson.date.asc())
    )
    if semester_start_date:
        lessons_query = lessons_query.where(Lesson.date >= semester_start_date)
    if subject_id:
        lessons_query = lessons_query.where(Lesson.subject_id == subject_id)
    
    lessons_result = await db.execute(lessons_query)
    lessons = lessons_result.all()
    
    if not lessons:
        return []
    
    # Группируем занятия по (дата, подгруппа)
    lesson_keys = [(l.date, l.subgroup) for l in lessons]
    lesson_dates = list(set(l.date for l in lessons))
    
    # Получаем посещаемость по этим датам
    attendance_query = (
        select(
            Attendance.date,
            Attendance.status,
            Attendance.student_id,
            func.count(Attendance.id).label('count')
        )
        .where(
            Attendance.group_id == group_id,
            Attendance.student_id.in_(student_ids),
            Attendance.date.in_(lesson_dates)
        )
        .group_by(Attendance.date, Attendance.status, Attendance.student_id)
    )
    result = await db.execute(attendance_query)
    
    # Создаём маппинг студент -> подгруппа
    student_subgroups = {s.id: s.subgroup for s in students}
    
    # Группируем посещаемость по (дата, подгруппа)
    date_subgroup_stats: Dict[tuple, Dict[str, int]] = defaultdict(lambda: {'present': 0, 'late': 0, 'excused': 0, 'absent': 0})
    
    for row in result.all():
        status_str = row.status.value.lower() if hasattr(row.status, 'value') else str(row.status).lower()
        student_subgroup = student_subgroups.get(row.student_id)
        
        # Для каждой записи посещаемости определяем к какому занятию она относится
        for lesson_date, lesson_subgroup in lesson_keys:
            if row.date == lesson_date:
                # Лекция (subgroup=None) - все студенты
                # Лаба (subgroup=1 или 2) - только студенты этой подгруппы
                if lesson_subgroup is None or lesson_subgroup == student_subgroup:
                    date_subgroup_stats[(lesson_date, lesson_subgroup)][status_str] += row.count
    
    # Формируем trend для всех занятий
    trend = []
    unique_lessons = list(set(lesson_keys))
    unique_lessons.sort(key=lambda x: (x[0], x[1] or 0))
    
    for lesson_date, lesson_subgroup in unique_lessons[-limit:]:
        stats = date_subgroup_stats.get((lesson_date, lesson_subgroup), {'present': 0, 'late': 0, 'excused': 0, 'absent': 0})
        total = sum(stats.values())
        if total > 0:
            present_eq = stats['present'] + stats['late'] * 0.5 + stats['excused'] * 0.5
            rate = round(present_eq / total * 100, 1)
        else:
            rate = 0.0  # Занятие было, но посещаемость не отмечена
        trend.append(DateAttendance(date=lesson_date.isoformat(), rate=rate, subgroup=lesson_subgroup))
    
    return trend


async def get_full_attendance_stats(
    db: AsyncSession,
    group_id: UUID,
    students: List[User],
    has_subgroups: bool = False,
    semester_start_date: Optional[date] = None,
    subject_id: Optional[UUID] = None
) -> AttendanceStats:
    """Получить полную статистику посещаемости."""
    distribution = await get_attendance_distribution(db, group_id, students, semester_start_date)
    
    by_subgroup = {}
    if has_subgroups:
        by_subgroup = await get_attendance_by_subgroup(db, group_id, students)
    
    trend = await get_attendance_trend(db, group_id, students, semester_start_date=semester_start_date, subject_id=subject_id)
    
    # Средняя посещаемость
    total = distribution.present + distribution.late + distribution.excused + distribution.absent
    if total > 0:
        present_eq = distribution.present + distribution.late * 0.5 + distribution.excused * 0.5
        average_rate = round(present_eq / total * 100, 1)
    else:
        average_rate = 0.0
    
    return AttendanceStats(
        distribution=distribution,
        by_subgroup=by_subgroup,
        trend=trend,
        average_rate=average_rate
    )


async def get_today_lessons_attendance(
    db: AsyncSession,
    group_id: UUID,
    students: List[User],
    show_names: bool = True,
    target_date: Optional[date] = None
) -> List[TodayLessonAttendance]:
    """Получить посещаемость по парам на указанную дату (по умолчанию сегодня)."""
    check_date = target_date or today_msk()
    student_ids = [s.id for s in students]
    student_map = {s.id: s for s in students}
    
    # Получаем занятия на эту дату
    lessons_query = (
        select(Lesson)
        .where(
            Lesson.group_id == group_id,
            Lesson.date == check_date,
            Lesson.is_cancelled == False
        )
        .order_by(Lesson.lesson_number)
    )
    lessons_result = await db.execute(lessons_query)
    lessons = lessons_result.scalars().all()
    
    if not lessons:
        return []
    
    # Получаем посещаемость на эту дату
    attendance_query = (
        select(Attendance)
        .where(
            Attendance.group_id == group_id,
            Attendance.date == check_date,
            Attendance.student_id.in_(student_ids)
        )
    )
    attendance_result = await db.execute(attendance_query)
    attendance_records = attendance_result.scalars().all()
    
    # Группируем посещаемость по (lesson_number, student_id)
    att_map: Dict[tuple, Attendance] = {}
    for att in attendance_records:
        key = (att.lesson_number, att.student_id)
        att_map[key] = att
    
    result = []
    for lesson in lessons:
        # Определяем студентов для этого занятия
        if lesson.subgroup is None:
            # Лекция — все студенты
            relevant_students = students
        else:
            # Лаба/практика — только подгруппа
            relevant_students = [s for s in students if s.subgroup == lesson.subgroup]
        
        present, absent, late, excused = [], [], [], []
        
        for student in relevant_students:
            # Имя или ID
            identifier = student.full_name if show_names else str(student.id)
            
            att = att_map.get((lesson.lesson_number, student.id))
            if att:
                status = att.status.value.lower() if hasattr(att.status, 'value') else str(att.status).lower()
                if status == 'present':
                    present.append(identifier)
                elif status == 'late':
                    late.append(identifier)
                elif status == 'excused':
                    excused.append(identifier)
                else:
                    absent.append(identifier)
            else:
                # Нет записи — считаем отсутствующим
                absent.append(identifier)
        
        lesson_type_str = lesson.lesson_type.value if hasattr(lesson.lesson_type, 'value') else str(lesson.lesson_type)
        
        result.append(TodayLessonAttendance(
            date=lesson.date,
            lesson_number=lesson.lesson_number,
            lesson_type=lesson_type_str,
            topic=lesson.topic,
            subgroup=lesson.subgroup,
            present=present,
            absent=absent,
            late=late,
            excused=excused
        ))
    
    return result
