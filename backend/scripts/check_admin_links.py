"""
Скрипт для проверки связей админа с предметами и расписанием.
Запуск: docker exec edu-backend python scripts/check_admin_links.py
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select, func, text
from app.db.session import AsyncSessionLocal
from app.models import User, UserRole, Subject, Group
from app.models.teacher_subject import TeacherSubjectAssignment
from app.models.schedule import ScheduleItem
from app.models.lesson import Lesson
from app.models.lesson_grade import LessonGrade
from app.models.attendance import Attendance


async def check_admin_links():
    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("ПРОВЕРКА СВЯЗЕЙ АДМИНА С ПРЕДМЕТАМИ И РАСПИСАНИЕМ")
        print("=" * 60)
        
        # 1. Найти админа
        result = await db.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ АДМИН НЕ НАЙДЕН!")
            return
        
        print(f"\n✅ Админ: {admin.full_name} (id={admin.id})")
        print(f"   telegram_id: {admin.telegram_id}")
        print(f"   vk_id: {admin.vk_id}")
        
        # 2. Предметы
        print("\n" + "-" * 40)
        print("ПРЕДМЕТЫ:")
        result = await db.execute(select(Subject).order_by(Subject.name))
        subjects = result.scalars().all()
        
        if not subjects:
            print("   (нет предметов)")
        else:
            for s in subjects:
                print(f"   • {s.name} (id={s.id}, active={s.is_active})")
        
        # 3. Связи админа с предметами
        print("\n" + "-" * 40)
        print("СВЯЗИ АДМИНА С ПРЕДМЕТАМИ (teacher_subject_assignments):")
        result = await db.execute(
            select(TeacherSubjectAssignment)
            .where(TeacherSubjectAssignment.teacher_id == admin.id)
        )
        assignments = result.scalars().all()
        
        if not assignments:
            print("   ❌ НЕТ СВЯЗЕЙ! Админ не привязан к предметам.")
        else:
            for a in assignments:
                print(f"   • subject_id={a.subject_id}, group_id={a.group_id}, semester={a.semester}")
        
        # 4. Расписание админа
        print("\n" + "-" * 40)
        print("РАСПИСАНИЕ АДМИНА (schedule_items.teacher_id):")
        result = await db.execute(
            select(ScheduleItem)
            .where(ScheduleItem.teacher_id == admin.id)
        )
        schedule_items = result.scalars().all()
        
        if not schedule_items:
            print("   ❌ НЕТ РАСПИСАНИЯ! Бот не сможет показать /schedule.")
        else:
            print(f"   ✅ Найдено {len(schedule_items)} элементов расписания")
            for item in schedule_items[:5]:
                print(f"      • {item.day_of_week.value} #{item.lesson_number}: {item.subject}")
            if len(schedule_items) > 5:
                print(f"      ... и ещё {len(schedule_items) - 5}")
        
        # 5. Группы и студенты
        print("\n" + "-" * 40)
        print("ГРУППЫ И СТУДЕНТЫ:")
        result = await db.execute(
            select(Group, func.count(User.id).label('count'))
            .outerjoin(User, (User.group_id == Group.id) & (User.role == UserRole.STUDENT))
            .group_by(Group.id)
            .order_by(Group.name)
        )
        groups = result.all()
        
        for group, count in groups:
            print(f"   • {group.name} ({group.code}): {count} студентов")
        
        # 6. Данные (занятия, оценки, посещаемость)
        print("\n" + "-" * 40)
        print("ДАННЫЕ (НЕ БУДУТ ЗАТРОНУТЫ):")
        
        lessons_count = await db.scalar(select(func.count()).select_from(Lesson))
        grades_count = await db.scalar(select(func.count()).select_from(LessonGrade))
        attendance_count = await db.scalar(select(func.count()).select_from(Attendance))
        
        print(f"   • Занятий (lessons): {lessons_count}")
        print(f"   • Оценок (lesson_grades): {grades_count}")
        print(f"   • Посещаемость (attendance): {attendance_count}")
        
        # 7. Расписание без teacher_id
        print("\n" + "-" * 40)
        print("РАСПИСАНИЕ БЕЗ ПРЕПОДАВАТЕЛЯ:")
        result = await db.execute(
            select(func.count())
            .select_from(ScheduleItem)
            .where(ScheduleItem.teacher_id == None)
        )
        orphan_count = result.scalar()
        print(f"   • Элементов без teacher_id: {orphan_count}")
        
        if orphan_count > 0:
            result = await db.execute(
                select(ScheduleItem)
                .where(ScheduleItem.teacher_id == None)
                .limit(5)
            )
            orphans = result.scalars().all()
            for item in orphans:
                print(f"      • {item.day_of_week.value} #{item.lesson_number}: {item.subject} (group_id={item.group_id})")
        
        print("\n" + "=" * 60)
        print("РЕКОМЕНДАЦИИ:")
        
        if not assignments:
            print("1. Нужно добавить записи в teacher_subject_assignments")
        
        if not schedule_items and orphan_count > 0:
            print("2. Нужно обновить schedule_items.teacher_id = admin.id")
        elif not schedule_items:
            print("2. Расписание пустое — нужно спарсить или создать вручную")
        
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(check_admin_links())
