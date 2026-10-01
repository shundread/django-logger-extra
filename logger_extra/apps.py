import logging

from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


class LoggerExtraConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "logger_extra"

    def ready(self):
        from logger_extra.extras.django_auditlog import (
            enable_django_auditlog_augment,
            patch_mask_actor_email,
        )

        augment_enabled = getattr(
            settings, "LOGGER_EXTRA_AUGMENT_DJANGO_AUDITLOG", False
        )
        if augment_enabled and not enable_django_auditlog_augment():
            logger.error("failed to augment django-auditlog.")

        mask_actor_email = getattr(settings, "LOGGER_EXTRA_MASK_ACTOR_EMAIL", False)
        if mask_actor_email and not patch_mask_actor_email():
            logger.error("failed to patch django-auditlog to mask actor email.")
