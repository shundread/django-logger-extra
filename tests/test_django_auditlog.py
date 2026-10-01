import uuid

import auditlog.context
import pytest
from auditlog.models import LogEntry
from django.apps import apps
from django.contrib.auth import get_user_model

from logger_extra.extras.django_auditlog import (
    disable_django_auditlog_augment,
    enable_django_auditlog_augment,
)
from logger_extra.logger_context import logger_context
from tests.models import DummyModel


@pytest.fixture(autouse=True)
def setup_and_teardown():
    enable_django_auditlog_augment()
    yield
    disable_django_auditlog_augment()


@pytest.mark.django_db
def test_auditlog_augment():
    instance: DummyModel
    expected1 = str(uuid.uuid4())
    expected2 = str(uuid.uuid4())
    expected3 = str(uuid.uuid4())

    with logger_context({"value1": expected1}):
        with logger_context({"value2": expected2}):
            with logger_context({"value3": expected3}):
                instance = DummyModel.objects.create(message="Hello")

    audit_log_instance = LogEntry.objects.get(object_pk=instance.id)
    assert audit_log_instance is not None

    additional_data = audit_log_instance.additional_data
    assert additional_data.get("value1", None) == expected1
    assert additional_data.get("value2", None) == expected2
    assert additional_data.get("value3", None) == expected3


@pytest.fixture()
def mock_user():
    return get_user_model()(email="erkki.esimerkki@example.com")


@pytest.fixture
def cleanup_auditlog_patch():
    """
    Fixture to ensure the monkey patch is reverted after the test,
    preventing state leakage into other tests.
    """
    original_set_actor = auditlog.context._set_actor
    yield
    auditlog.context._set_actor = original_set_actor
    if hasattr(auditlog.context, "_logger_extra_patch_mask_actor_email"):
        delattr(auditlog.context, "_logger_extra_patch_mask_actor_email")


def test_app_config_patches_when_setting_true(
    cleanup_auditlog_patch, mock_user, settings
):
    settings.LOGGER_EXTRA_MASK_ACTOR_EMAIL = True
    app_config = apps.get_app_config("logger_extra")
    app_config.ready()

    log_entry = LogEntry()
    auditlog.context._set_actor({"actor": mock_user}, log_entry, LogEntry)

    assert (
        log_entry.actor_email != mock_user.email
    ), "LogEntry leaked full actor email even though mask actor email setting was on"
    assert log_entry.actor_email == auditlog.diff.mask_str(
        mock_user.email
    ), "LogEntry.actor_email did not match masked version"


def test_app_config_does_not_patch_when_setting_false(
    cleanup_auditlog_patch, mock_user, settings
):
    settings.LOGGER_EXTRA_MASK_ACTOR_EMAIL = False
    app_config = apps.get_app_config("logger_extra")
    app_config.ready()

    log_entry = LogEntry()
    auditlog.context._set_actor({"actor": mock_user}, log_entry, LogEntry)

    assert log_entry.actor_email, (
        "LogEntry.actor_email was empty or missing, check django-auditlog have breaking"
        "changes?"
    )
    assert log_entry.actor_email == mock_user.email, (
        "LogEntry.actor_email did not match mock_user.email, does django-auditlog have"
        "breaking changes?"
    )
