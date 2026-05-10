def is_identity_proven(headers: dict) -> bool:
    return bool(headers.get("Authorization"))


def test_userid_only_request_rejected():
    headers = {"x-user-id": "user-123"}
    assert not is_identity_proven(headers)
