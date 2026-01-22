"""Главный сервис экспорта журнала."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.export import ExportPeriodType, ExportFormat, JournalExportData
from .period_utils import parse_period
from .data_collector import ExportDataCollector
from .excel_generator import generate_excel
from .csv_generator import generate_csv

logger = logging.getLogger(__name__)


class ExportService:
    """Фасад для экспорта журнала."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._collector = ExportDataCollector(db)

    async def export_journal(
        self,
        group_id: UUID,
        period_type: ExportPeriodType,
        period_value: str | None = None,
        format: ExportFormat = ExportFormat.XLSX,
        include_attendance: bool = True,
        include_grades: bool = True,
    ) -> tuple[bytes, str, str]:
        """
        Экспорт журнала группы.

        Args:
            group_id: ID группы
            period_type: Тип периода
            period_value: Значение периода
            format: Формат файла
            include_attendance: Включить посещаемость
            include_grades: Включить оценки

        Returns:
            Кортеж (content, filename, media_type)
        """
        logger.info(
            "Начало экспорта: group_id=%s, period=%s/%s, format=%s",
            group_id, period_type.value, period_value, format.value
        )

        # 1. Парсим период
        start_date, end_date = parse_period(period_type, period_value)
        logger.debug("Период: %s - %s", start_date, end_date)

        # 2. Собираем данные
        data = await self._collector.collect_all(
            group_id, start_date, end_date,
            include_attendance, include_grades
        )

        # 3. Генерируем файл
        content, media_type, ext = self._generate_file(
            data, format, include_attendance, include_grades
        )

        # 4. Формируем имя файла
        period_str = f"{start_date}_{end_date}"
        filename = f"journal_{data.meta.group_code}_{period_str}.{ext}"

        logger.info(
            "Экспорт завершён: %s, %d байт",
            filename, len(content)
        )

        return content, filename, media_type

    def _generate_file(
        self,
        data: JournalExportData,
        format: ExportFormat,
        include_attendance: bool,
        include_grades: bool,
    ) -> tuple[bytes, str, str]:
        """
        Генерирует файл в указанном формате.

        Args:
            data: Данные журнала
            format: Формат файла
            include_attendance: Включить посещаемость
            include_grades: Включить оценки

        Returns:
            Кортеж (content, media_type, extension)
        """
        if format == ExportFormat.XLSX:
            content = generate_excel(data)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"

        elif format == ExportFormat.CSV:
            csv_content = generate_csv(data, include_attendance, include_grades)
            content = csv_content.encode("utf-8-sig")
            media_type = "text/csv; charset=utf-8"
            ext = "csv"

        else:  # JSON
            content = data.model_dump_json(indent=2).encode("utf-8")
            media_type = "application/json"
            ext = "json"

        return content, media_type, ext

    async def get_export_preview(
        self,
        group_id: UUID,
        period_type: ExportPeriodType,
        period_value: str | None = None,
    ) -> JournalExportData:
        """
        Получить превью данных для экспорта (без генерации файла).

        Args:
            group_id: ID группы
            period_type: Тип периода
            period_value: Значение периода

        Returns:
            Данные журнала для экспорта
        """
        start_date, end_date = parse_period(period_type, period_value)
        return await self._collector.collect_all(
            group_id, start_date, end_date,
            include_attendance=True, include_grades=True
        )
