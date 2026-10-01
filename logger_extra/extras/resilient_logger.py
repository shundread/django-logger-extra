import uuid

try:
    import auditlog

    has_auditlog = True
except ImportError:
    has_auditlog = False


def _parse_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    """
    Parses the given value into a UUID instance or returns None if parsing fails.
    """
    if value is None:
        return None

    if isinstance(value, uuid.UUID):
        return value

    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        return None


def resolve_actor_with_masked_email(actor) -> dict:
    """
    resolve_actor function for django-resilient-logger. Includes actor email (masked)
    and UUID in the resilient log entry
    """

    if not has_auditlog:
        return False

    actor_data = {
        "uuid": None,
        "version": None,
        "email": None,
    }

    if not actor:
        return actor_data

    raw_uuid = getattr(actor, "uuid", None)
    raw_email = getattr(actor, "email", None)
    parsed_uuid = _parse_uuid(raw_uuid)

    if parsed_uuid:
        actor_data["uuid"] = str(parsed_uuid)
        actor_data["version"] = parsed_uuid.version
    if raw_email:
        actor_data["email"] = auditlog.diff.mask_str(raw_email)

    return actor_data
