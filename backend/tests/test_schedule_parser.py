"""
Тесты для парсера расписания.
"""

from datetime import date

import pytest

from app.services.html_parser import ParseResult, ScheduleHtmlParser


class TestParseHtmlStructure:
    """test_parse_html_structure — парсинг разных вариантов HTML"""

    def setup_method(self):
        self.parser = ScheduleHtmlParser()

    def test_parse_standard_structure(self):
        """Стандартная структура kis.vgltu.ru"""
        html = """
        <div class="table">
            <div style="margin-bottom: 25px;">
                <strong>15 января 2025</strong>
                <table>
                    <tr>
                        <td>08:30-10:00</td>
                        <td>лек. Математика<br/>ИС-241<br/>101</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        result = self.parser.parse_with_metadata(html)

        assert not result.is_empty
        assert not result.structure_changed
        assert len(result.lessons) == 1
        assert result.lessons[0].subject == "Математика"
        assert result.lessons[0].lesson_type == "lecture"
        assert result.lessons[0].lesson_number == 1

    def test_parse_room_from_kis_auditory_link(self):
        """Аудитория берётся из официальной ссылки KIS вместе с корпусом."""
        html = """
        <div class="table">
            <div style="margin-bottom: 25px;">
                <strong>16 апреля 2026</strong>
                <table>
                    <tr>
                        <td>08:30-10:00</td>
                        <td>
                            лек. Тестирование информационных систем<br/>
                            <br/>
                            ИС1-235-ОТ <br/>
                            ИС1-236-ОТ <br/>
                            <br/>
                            <a href="https://kis.vgltu.ru/map/rasp?auditory=119Л/7к">119Л/7к</a><br/>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
        """
        result = self.parser.parse_with_metadata(html)

        assert len(result.lessons) == 1
        assert result.lessons[0].groups == ["ИС1-235-ОТ", "ИС1-236-ОТ"]
        assert result.lessons[0].room == "119Л/7к"

    def test_parse_fallback_no_table_class(self):
        """Fallback когда нет class='table'"""
        html = """
        <div>
            <div style="margin-bottom: 10px;">
                <strong>15 января 2025</strong>
                <table>
                    <tr>
                        <td>10:10-11:40</td>
                        <td>пр. Физика<br/>ИС-242</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        result = self.parser.parse_with_metadata(html)

        assert len(result.lessons) == 1
        assert result.lessons[0].lesson_type == "practice"

    def test_parse_structure_changed_no_container(self):
        """Обнаружение изменения структуры"""
        html = "<div>Просто текст без таблиц</div>"
        result = self.parser.parse_with_metadata(html)

        assert result.structure_changed
        assert result.error is not None


class TestParseSubgroupFormats:
    """test_parse_subgroup_formats — разные форматы подгрупп"""

    def setup_method(self):
        self.parser = ScheduleHtmlParser()

    @pytest.mark.parametrize(
        "subgroup_text,expected",
        [
            ("1 п.г.", 1),
            ("1 п.г", 1),
            ("1п.г.", 1),
            ("1 п/г", 1),
            ("подгр. 1", 1),
            ("2 п.г.", 2),
            ("2 п.г", 2),
            ("2п.г.", 2),
            ("2 п/г", 2),
            ("подгр. 2", 2),
        ],
    )
    def test_subgroup_patterns(self, subgroup_text, expected):
        """Тест разных форматов подгрупп"""
        html = f"""
        <div class="table">
            <div style="margin-bottom: 25px;">
                <strong>15 января 2025</strong>
                <table>
                    <tr>
                        <td>08:30-10:00</td>
                        <td>лаб. Программирование<br/>{subgroup_text}<br/>ИС-241</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        result = self.parser.parse_with_metadata(html)

        assert len(result.lessons) == 1
        assert result.lessons[0].subgroup == expected


class TestParseEmptySchedule:
    """test_parse_empty_schedule — пустое расписание"""

    def setup_method(self):
        self.parser = ScheduleHtmlParser()

    def test_empty_html(self):
        """Пустой HTML"""
        result = self.parser.parse_with_metadata("")
        assert result.is_empty
        assert not result.structure_changed

    def test_whitespace_only(self):
        """Только пробелы"""
        result = self.parser.parse_with_metadata("   \n\t  ")
        assert result.is_empty

    def test_valid_structure_no_lessons(self):
        """Валидная структура, но нет занятий"""
        html = """
        <div class="table">
            <div style="margin-bottom: 25px;">
                <strong>15 января 2025</strong>
                <table></table>
            </div>
        </div>
        """
        result = self.parser.parse_with_metadata(html)
        assert result.is_empty
        assert not result.structure_changed


class TestParseGroupPatterns:
    """Тест паттернов групп разных факультетов"""

    def setup_method(self):
        self.parser = ScheduleHtmlParser()

    @pytest.mark.parametrize(
        "group_name",
        [
            "ИС-241",
            "ИС241",
            "ЛД-221",
            "ЛХ-201",
            "МТ-231",
            "ЭК-211",
            "СТ-241",
            "ДИ-221",
            "АР-201",
        ],
    )
    def test_group_patterns(self, group_name):
        """Тест распознавания групп разных факультетов"""
        html = f"""
        <div class="table">
            <div style="margin-bottom: 25px;">
                <strong>15 января 2025</strong>
                <table>
                    <tr>
                        <td>08:30-10:00</td>
                        <td>лек. Предмет<br/>{group_name}</td>
                    </tr>
                </table>
            </div>
        </div>
        """
        result = self.parser.parse_with_metadata(html)

        assert len(result.lessons) == 1
        assert group_name in result.lessons[0].groups
