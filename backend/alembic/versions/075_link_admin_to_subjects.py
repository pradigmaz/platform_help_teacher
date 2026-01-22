"""Link admin to subjects and schedule items

Revision ID: 075_link_admin_to_subjects
Revises: 074_add_notification_settings
Create Date: 2026-01-22

Проблема: Админ (единственный преподаватель) не связан с предметами и расписанием.
Решение: 
1. Добавить записи в teacher_subject_assignments для админа
2. Обновить schedule_items.teacher_id = admin.id где teacher_id IS NULL
"""
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '075_link_admin_to_subjects'
down_revision: Union[str, None] = '074_add_notification_settings'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # 1. Найти админа
    admin_result = conn.execute(
        sa.text("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    )
    admin_row = admin_result.fetchone()
    
    if not admin_row:
        print("⚠️ Админ не найден, пропускаем миграцию")
        return
    
    admin_id = admin_row[0]
    print(f"✅ Найден админ: {admin_id}")
    
    # 2. Получить текущий семестр (2024-2 для второго семестра)
    # Январь 2026 = второй семестр 2025-2
    current_semester = "2025-2"
    
    # 3. Связать админа со всеми активными предметами
    subjects_result = conn.execute(
        sa.text("SELECT id, name FROM subjects WHERE is_active = true")
    )
    subjects = subjects_result.fetchall()
    
    for subject_id, subject_name in subjects:
        # Проверяем, нет ли уже связи
        existing = conn.execute(
            sa.text("""
                SELECT id FROM teacher_subject_assignments 
                WHERE teacher_id = :teacher_id 
                AND subject_id = :subject_id 
                AND semester = :semester
                AND group_id IS NULL
            """),
            {"teacher_id": admin_id, "subject_id": subject_id, "semester": current_semester}
        ).fetchone()
        
        if not existing:
            conn.execute(
                sa.text("""
                    INSERT INTO teacher_subject_assignments 
                    (id, teacher_id, subject_id, group_id, semester, is_active, created_at, updated_at)
                    VALUES (gen_random_uuid(), :teacher_id, :subject_id, NULL, :semester, true, now(), now())
                """),
                {"teacher_id": admin_id, "subject_id": subject_id, "semester": current_semester}
            )
            print(f"   ✅ Связан с предметом: {subject_name}")
        else:
            print(f"   ⏭️ Уже связан с предметом: {subject_name}")
    
    # 4. Обновить schedule_items без teacher_id
    updated = conn.execute(
        sa.text("""
            UPDATE schedule_items 
            SET teacher_id = :admin_id, updated_at = now()
            WHERE teacher_id IS NULL AND is_active = true
        """),
        {"admin_id": admin_id}
    )
    print(f"✅ Обновлено schedule_items: {updated.rowcount}")
    
    # 5. Статистика
    total_assignments = conn.execute(
        sa.text("SELECT COUNT(*) FROM teacher_subject_assignments WHERE teacher_id = :admin_id"),
        {"admin_id": admin_id}
    ).scalar()
    
    total_schedule = conn.execute(
        sa.text("SELECT COUNT(*) FROM schedule_items WHERE teacher_id = :admin_id"),
        {"admin_id": admin_id}
    ).scalar()
    
    print(f"\n📊 Итого:")
    print(f"   • teacher_subject_assignments: {total_assignments}")
    print(f"   • schedule_items: {total_schedule}")


def downgrade() -> None:
    conn = op.get_bind()
    
    # Найти админа
    admin_result = conn.execute(
        sa.text("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
    )
    admin_row = admin_result.fetchone()
    
    if not admin_row:
        return
    
    admin_id = admin_row[0]
    
    # Удалить связи админа с предметами (только для текущего семестра)
    conn.execute(
        sa.text("""
            DELETE FROM teacher_subject_assignments 
            WHERE teacher_id = :admin_id AND semester = '2025-2'
        """),
        {"admin_id": admin_id}
    )
    
    # НЕ откатываем schedule_items.teacher_id — это может сломать данные
    print("⚠️ schedule_items.teacher_id НЕ откачен (безопасность данных)")
