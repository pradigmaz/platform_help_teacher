"""CRUD операции для публичных отчётов."""
from app.crud.report.mutations import ReportMutations
from app.crud.report.queries import ReportQueries


class CRUDReport(ReportQueries, ReportMutations):
    """CRUD операции для GroupReport."""
    pass


# Singleton instance
crud_report = CRUDReport()

__all__ = ["CRUDReport", "crud_report"]
