from app.middleware.security_monitor import strip_query_from_url


def test_strip_query_from_url_keeps_path_uuid_only():
    url = "http://127.0.0.1/api/v1/admin/notes/?entity_id=87a6dea1-a6e6-46fe-9f6f-9315dfab1e"

    assert strip_query_from_url(url) == "http://127.0.0.1/api/v1/admin/notes/"


def test_strip_query_from_url_preserves_path_for_idor_checks():
    url = "http://127.0.0.1/api/v1/admin/users/87a6dea1-a6e6-46fe-9f6f-9315dfab1e?tab=profile"

    assert strip_query_from_url(url) == "http://127.0.0.1/api/v1/admin/users/87a6dea1-a6e6-46fe-9f6f-9315dfab1e"
