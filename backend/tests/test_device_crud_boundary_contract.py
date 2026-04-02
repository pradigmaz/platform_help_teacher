"""Boundary checks for CRUD-layer transaction ownership in device flows."""

import inspect

from app.crud import crud_device


class TestCrudFlushBoundaryContract:
    def test_crud_create_uses_flush_not_commit(self):
        source = inspect.getsource(crud_device.create)
        assert "flush" in source
        assert "commit" not in source

    def test_crud_update_uses_flush_not_commit(self):
        source = inspect.getsource(crud_device.update)
        assert "flush" in source
        assert "commit" not in source

    def test_crud_delete_one_uses_flush_not_commit(self):
        source = inspect.getsource(crud_device.delete_one)
        assert "flush" in source
        assert "commit" not in source

    def test_crud_bulk_delete_uses_flush_not_commit(self):
        source = inspect.getsource(crud_device.bulk_delete_by_user)
        assert "flush" in source
        assert "commit" not in source
