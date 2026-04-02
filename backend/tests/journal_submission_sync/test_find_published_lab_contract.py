"""Contract tests for published lab lookup in journal projection sync."""

import pytest

from app.models import Lab, Subject
from app.services.submission_journal_sync import journal_sync

from .conftest import scalar_result


class TestFindPublishedLabContract:
    @pytest.mark.asyncio
    async def test_find_published_lab_success(
        self,
        mock_db,
        sample_subject: Subject,
        sample_lab: Lab,
    ):
        mock_db.execute.return_value = scalar_result(sample_lab)

        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=1,
        )

        assert lab is not None
        assert lab.id == sample_lab.id
        assert lab.number == 1
        assert lab.is_published is True

    @pytest.mark.asyncio
    async def test_find_published_lab_not_found(
        self,
        mock_db,
        sample_subject: Subject,
    ):
        mock_db.execute.return_value = scalar_result(None)

        lab = await journal_sync.find_published_lab(
            mock_db,
            sample_subject.id,
            work_number=999,
        )

        assert lab is None
