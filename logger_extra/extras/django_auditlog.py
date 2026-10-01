from django.db.models import Model
from django.db.models.signals import pre_save

from logger_extra.logger_context import get_logger_context
from logger_extra.utils import json_serialize

DISPATCH_UID = "LoggerExtraDjangoAuditlog"

try:
    from auditlog.models import LogEntry as AuditLogEntry

    LogEntry = AuditLogEntry
    has_auditlog = True
except ImportError:
    LogEntry = None
    has_auditlog = False


def enable_django_auditlog_augment() -> bool:
    """
    Attempts to augment django-auditlog entries with logger context.

    Returns:
        bool: True if auditlog was found and the signal connected, False otherwise.
    """
    if not has_auditlog:
        return False

    pre_save.connect(
        _augment_django_auditlog,
        sender=LogEntry,
        weak=False,
        dispatch_uid=DISPATCH_UID,
    )

    return True


def disable_django_auditlog_augment() -> bool:
    """
    Attempts to disconnect the django-auditlog entry augmentation if it's configured.
    """
    if not has_auditlog:
        return False

    pre_save.disconnect(
        _augment_django_auditlog,
        sender=LogEntry,
        dispatch_uid=DISPATCH_UID,
    )
    return True


def _augment_django_auditlog(sender: type[Model], instance: Model, **kwargs):
    if not has_auditlog or sender != LogEntry or not isinstance(instance, LogEntry):
        return

    context = get_logger_context()

    if not hasattr(instance, "additional_data") or not isinstance(
        instance.additional_data, dict
    ):
        instance.additional_data = {}

    for key, value in context.items():
        instance.additional_data[key] = json_serialize(value)


def patch_mask_actor_email() -> bool:
    """
    Monkey patches django-auditlog's _set_actor to prevent leaking the actor's email
    in plaintext form.

    We patch `_set_actor` directly because auditlog connects its signals dynamically
    per-request. A static pre_save signal here would execute too early (before auditlog
    sets the email).
    """
    if not has_auditlog:
        return False

    import auditlog.context
    import auditlog.diff

    # Prevent double-patching during testing or multi-app setups
    if getattr(auditlog.context, "_logger_extra_patch_mask_actor_email", False):
        return True

    original_set_actor = auditlog.context._set_actor

    def set_actor_with_masked_email(auditlog_data, instance, sender):
        original_set_actor(auditlog_data, instance, sender)
        actor_email = getattr(instance, "actor_email", None)
        if actor_email:
            instance.actor_email = auditlog.diff.mask_str(actor_email)

    auditlog.context._set_actor = set_actor_with_masked_email
    auditlog.context._logger_extra_patch_mask_actor_email = True

    return True
