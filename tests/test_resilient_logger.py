import uuid

import auditlog.diff

from logger_extra.extras.resilient_logger import resolve_actor_with_masked_email


class MockActor:
    def __init__(self, user_uuid=None, email=None):
        if user_uuid is not None:
            self.uuid = user_uuid
        if email is not None:
            self.email = email


def test_resolve_actor_no_actor():
    result = resolve_actor_with_masked_email(None)
    assert result == {"uuid": None, "version": None, "email": None}


def test_resolve_actor_with_string_uuid_and_email():
    test_uuid_str = "12345678-1234-5678-1234-567812345678"
    test_email = "erkki.esimerkki@example.com"
    actor = MockActor(user_uuid=test_uuid_str, email=test_email)

    result = resolve_actor_with_masked_email(actor)

    assert result["uuid"] == test_uuid_str
    assert result["version"] == uuid.UUID(test_uuid_str).version
    assert result["email"] == auditlog.diff.mask_str(test_email)
    assert result["email"] != test_email


def test_resolve_actor_with_uuid_object_and_no_email():
    test_uuid = uuid.uuid4()
    actor = MockActor(user_uuid=test_uuid)

    result = resolve_actor_with_masked_email(actor)

    assert result["uuid"] == str(test_uuid)
    assert result["version"] == test_uuid.version
    assert result["email"] is None


def test_resolve_actor_with_invalid_uuid():
    test_email = "erkki.esimerkki@example.com"
    actor = MockActor(user_uuid="not-a-valid-uuid", email=test_email)

    result = resolve_actor_with_masked_email(actor)

    assert result["uuid"] is None
    assert result["version"] is None
    assert result["email"] != test_email
    assert result["email"] == auditlog.diff.mask_str(test_email)
