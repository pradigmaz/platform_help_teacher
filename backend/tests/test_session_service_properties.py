from hypothesis import given
from hypothesis import strategies as st

from app.services.session_service import _mask_ip_for_storage


@given(
    first=st.integers(min_value=0, max_value=255),
    second=st.integers(min_value=0, max_value=255),
    third=st.integers(min_value=0, max_value=255),
    fourth=st.integers(min_value=0, max_value=255),
)
def test_mask_ip_for_storage_redacts_last_two_octets(
    first: int,
    second: int,
    third: int,
    fourth: int,
) -> None:
    masked = _mask_ip_for_storage(f"{first}.{second}.{third}.{fourth}")
    assert masked == f"{first}.{second}.x.x"


@given(value=st.none() | st.text(min_size=0, max_size=64).filter(lambda text: "." not in text or text.count(".") != 3))
def test_mask_ip_for_storage_preserves_non_ipv4_shapes(value: str | None) -> None:
    if not value:
        assert _mask_ip_for_storage(value) is None
        return

    assert _mask_ip_for_storage(value) == value[:8] + "..."
