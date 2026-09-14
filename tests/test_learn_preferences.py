"""Tests for learn preference defaults and Settings wiring."""

from types import SimpleNamespace

import pytest

from learning_app.ui.learn_preferences import LearnPreferences


@pytest.fixture
def restore_learn_preferences():
    retry = LearnPreferences.retry_until_correct
    yield
    LearnPreferences.retry_until_correct = retry


def test_learn_preferences_default_retry_off():
    assert LearnPreferences.retry_until_correct is False


def test_parse_retry_until_correct_defaults_off():
    assert LearnPreferences.parse_retry_until_correct(None) is False
    assert LearnPreferences.parse_retry_until_correct("false") is False
    assert LearnPreferences.parse_retry_until_correct("0") is False
    assert LearnPreferences.parse_retry_until_correct("true") is True
    assert LearnPreferences.parse_retry_until_correct("1") is True
    assert LearnPreferences.parse_retry_until_correct("on") is True


def test_settings_includes_learning_section(restore_learn_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    LearnPreferences.retry_until_correct = False
    screen = SettingsControl(SimpleNamespace())

    assert screen.learning_heading.value == "Learning"
    assert screen.retry_until_correct_switch.value is False
    assert "do not change statistics" in screen.retry_until_correct_description.value
    assert screen.learning_section in screen.controls
    assert screen.controls.index(screen.tts_section) < screen.controls.index(
        screen.learning_section
    )
    assert screen.controls.index(screen.learning_section) < screen.controls.index(
        screen.demo_section
    )


def test_settings_retry_switch_updates_runtime_flag(restore_learn_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    LearnPreferences.retry_until_correct = False
    page = SimpleNamespace(run_task=lambda *args, **kwargs: None)
    screen = SettingsControl(page)
    screen.retry_until_correct_switch.value = True
    screen.on_retry_until_correct_change(
        SimpleNamespace(control=screen.retry_until_correct_switch)
    )

    assert LearnPreferences.retry_until_correct is True
