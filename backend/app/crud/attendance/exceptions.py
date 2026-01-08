"""Attendance validation exceptions."""


class AttendanceValidationError(Exception):
    """Ошибка валидации данных посещаемости"""
    pass


class DuplicateAttendanceError(AttendanceValidationError):
    """Ошибка: дублирующая запись посещаемости"""
    pass


class StudentNotInGroupError(AttendanceValidationError):
    """Ошибка: студент не принадлежит указанной группе"""
    pass


class StudentNotFoundError(AttendanceValidationError):
    """Ошибка: студент не найден"""
    pass


class FutureDateError(AttendanceValidationError):
    """Ошибка: дата посещаемости в будущем"""
    pass
