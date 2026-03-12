"""Fix HTML entities in lecture text nodes

Revision ID: 081_fix_lecture_html_entities
Revises: 080_add_devices_table
Create Date: 2026-03-04

Исправляет повреждённые данные: bleach.clean экранировал <, >, & в текстовых
нодах Lexical JSON при каждом сохранении лекции. Декодирует html-сущности обратно.
"""
import html
import json
from typing import Any

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "081_fix_lecture_html_entities"
down_revision = "080_add_devices_table"
branch_labels = None
depends_on = None

BATCH_SIZE = 100


def fix_escaped_entities(content: Any) -> Any:
    """Рекурсивно декодирует HTML-сущности в текстовых нодах Lexical JSON."""
    if isinstance(content, dict):
        return {
            k: html.unescape(v) if k == "text" and isinstance(v, str) else fix_escaped_entities(v)
            for k, v in content.items()
        }
    if isinstance(content, list):
        return [fix_escaped_entities(item) for item in content]
    return content


def has_escaped_entities(content: Any) -> bool:
    """Проверяет наличие повреждённых данных в структуре."""
    if isinstance(content, dict):
        for k, v in content.items():
            if k == "text" and isinstance(v, str):
                if any(entity in v for entity in ("&amp;", "&gt;", "&lt;")):
                    return True
            elif has_escaped_entities(v):
                return True
    elif isinstance(content, list):
        return any(has_escaped_entities(item) for item in content)
    return False


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    lecture_columns = {column["name"] for column in inspector.get_columns("lectures")}
    if "deleted_at" not in lecture_columns:
        op.add_column("lectures", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    lecture_indexes = {index["name"] for index in inspector.get_indexes("lectures")}
    if "idx_lectures_deleted_at" not in lecture_indexes:
        op.create_index("idx_lectures_deleted_at", "lectures", ["deleted_at"], unique=False)

    offset = 0
    fixed_count = 0

    while True:
        rows = conn.execute(
            text("SELECT id, content FROM lectures WHERE deleted_at IS NULL ORDER BY id LIMIT :limit OFFSET :offset"),
            {"limit": BATCH_SIZE, "offset": offset},
        ).fetchall()

        if not rows:
            break

        for row in rows:
            content = row.content
            if content and has_escaped_entities(content):
                fixed = fix_escaped_entities(content)
                conn.execute(
                    text("UPDATE lectures SET content = :content WHERE id = :id"),
                    {"content": json.dumps(fixed, ensure_ascii=False), "id": str(row.id)},
                )
                fixed_count += 1

        offset += BATCH_SIZE

    print(f"[081] Fixed {fixed_count} lectures with escaped HTML entities")


def downgrade() -> None:
    # Нельзя восстановить повреждённые данные — downgrade является no-op
    pass
