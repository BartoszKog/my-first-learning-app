"""Tests for learn preference defaults and Settings wiring."""

from types import SimpleNamespace

import flet as ft
import pytest

from learning_app.ui.learn_preferences import LearnPreferences


@pytest.fixture
def restore_learn_preferences():
    retry = LearnPreferences.retry_until_correct
    words_queue = LearnPreferences.word_formations_queue_size
    definitions_queue = LearnPreferences.definitions_queue_size
    example_mode = LearnPreferences.example_mode
    yield
    LearnPreferences.example_mode = example_mode
    LearnPreferences.retry_until_correct = retry
    LearnPreferences.word_formations_queue_size = words_queue
    LearnPreferences.definitions_queue_size = definitions_queue


def _position(controls, control) -> int:
    """Index by identity; Flet controls with equal fields compare equal."""
    return next(i for i, item in enumerate(controls) if item is control)


def test_learn_preferences_default_retry_on():
    assert LearnPreferences.retry_until_correct is True
    assert LearnPreferences.word_formations_queue_size == 5
    assert LearnPreferences.definitions_queue_size == 10


def test_parse_retry_until_correct_defaults_on():
    assert LearnPreferences.parse_retry_until_correct(None) is True
    assert LearnPreferences.parse_retry_until_correct("true") is True
    assert LearnPreferences.parse_retry_until_correct("1") is True
    assert LearnPreferences.parse_retry_until_correct("on") is True
    assert LearnPreferences.parse_retry_until_correct("false") is False
    assert LearnPreferences.parse_retry_until_correct("0") is False
    assert LearnPreferences.parse_retry_until_correct("off") is False


def test_parse_queue_sizes_default_and_clamp():
    assert LearnPreferences.parse_word_formations_queue_size(None) == 5
    assert LearnPreferences.parse_word_formations_queue_size("") == 5
    assert LearnPreferences.parse_word_formations_queue_size("nope") == 5
    assert LearnPreferences.parse_word_formations_queue_size("5.5") == 5
    assert LearnPreferences.parse_word_formations_queue_size("7") == 7
    assert LearnPreferences.parse_word_formations_queue_size("2") == 3
    assert LearnPreferences.parse_word_formations_queue_size("99") == 10
    assert LearnPreferences.parse_word_formations_queue_size(3) == 3
    assert LearnPreferences.parse_word_formations_queue_size(10) == 10

    assert LearnPreferences.parse_definitions_queue_size(None) == 10
    assert LearnPreferences.parse_definitions_queue_size(" ") == 10
    assert LearnPreferences.parse_definitions_queue_size("ten") == 10
    assert LearnPreferences.parse_definitions_queue_size("12") == 12
    assert LearnPreferences.parse_definitions_queue_size("3") == 4
    assert LearnPreferences.parse_definitions_queue_size("16") == 15
    assert LearnPreferences.parse_definitions_queue_size(4) == 4
    assert LearnPreferences.parse_definitions_queue_size(15) == 15


def test_parse_example_mode_defaults_to_hint():
    assert LearnPreferences.EXAMPLE_MODE_DEFAULT == "hint"
    assert LearnPreferences.parse_example_mode(None) == "hint"
    assert LearnPreferences.parse_example_mode("nope") == "hint"
    assert LearnPreferences.parse_example_mode(" Hint ") == "hint"
    assert LearnPreferences.parse_example_mode("after_check") == "after_check"
    assert LearnPreferences.parse_example_mode("off") == "off"


def test_settings_example_mode_dropdown_updates_runtime_flag(restore_learn_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    LearnPreferences.example_mode = "after_check"
    calls = []
    page = SimpleNamespace(run_task=lambda *args, **kwargs: calls.append(args))
    screen = SettingsControl(page)
    assert screen.example_mode_dropdown.value == "after_check"
    controls = screen.learning_section.controls
    assert screen.retry_heading.value == "Retyping"
    assert screen.example_mode_heading.value == "Example sentences"
    assert _position(controls, screen.learning_heading) + 1 == _position(
        controls, screen.retry_heading
    )
    assert (
        _position(controls, screen.retry_until_correct_description)
        < _position(controls, screen.example_mode_divider)
        < _position(controls, screen.example_mode_heading)
        < _position(controls, screen.example_mode_dropdown)
        < _position(controls, screen.queue_size_divider)
    )

    screen.example_mode_dropdown.value = "hint"
    screen.on_example_mode_select(SimpleNamespace(control=screen.example_mode_dropdown))

    assert LearnPreferences.example_mode == "hint"
    assert calls == [(LearnPreferences.save_example_mode, "hint")]


def test_settings_includes_learning_section(restore_learn_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    LearnPreferences.retry_until_correct = True
    screen = SettingsControl(SimpleNamespace())

    assert screen.learning_heading.value == "Learning"
    assert screen.retry_until_correct_switch.value is True
    assert "do not change statistics" in screen.retry_until_correct_description.value
    assert screen.learning_section in screen.controls
    assert screen.controls.index(screen.tts_section) < screen.controls.index(
        screen.learning_section
    )
    assert screen.controls.index(screen.learning_section) < screen.controls.index(
        screen.demo_section
    )


def test_settings_includes_queue_size_sliders(restore_learn_preferences):
    from learning_app.ui.screens.settings_control import DashedDivider, SettingsControl

    LearnPreferences.word_formations_queue_size = 5
    LearnPreferences.definitions_queue_size = 10
    screen = SettingsControl(SimpleNamespace())
    words = screen.word_formations_queue_slider
    definitions = screen.definitions_queue_slider
    learning_controls = screen.learning_section.controls

    assert words.slider.min == 3
    assert words.slider.max == 10
    assert words.slider.divisions == 7
    assert words.slider.value == 5
    assert words.label.value == "Word formations: 5"
    assert definitions.slider.min == 4
    assert definitions.slider.max == 15
    assert definitions.slider.divisions == 11
    assert definitions.slider.value == 10
    assert definitions.label.value == "Definitions: 10"
    assert screen.queue_size_heading.value == "Queue size"
    assert screen.queue_size_heading.size == 16
    assert screen.queue_size_heading.weight == ft.FontWeight.BOLD
    assert screen.queue_size_description.value == (
        "How many items are drawn into the next practice round. Word "
        "formations and definitions have separate defaults here. A set "
        "uses one queue size and can override it from its menu "
        "(Set settings). The round already started keeps its length."
    )
    assert screen.queue_size_description.size == 14
    assert _position(learning_controls, screen.retry_until_correct_description) < _position(
        learning_controls, screen.queue_size_divider
    )
    assert isinstance(screen.queue_size_divider, DashedDivider)
    assert _position(learning_controls, screen.queue_size_divider) + 1 == _position(
        learning_controls, screen.queue_size_heading
    )
    assert (
        _position(learning_controls, screen.queue_size_heading)
        < _position(learning_controls, screen.queue_size_description)
        < _position(learning_controls, words)
        < _position(learning_controls, definitions)
    )
    assert words.slider.width == screen._content_width
    assert definitions.slider.width == screen._content_width
    assert screen.queue_size_heading.width == screen._content_width
    assert screen.queue_size_description.width == screen._content_width

    from learning_app.ui.layout_metrics import LayoutMetrics

    screen.apply_layout(
        LayoutMetrics(
            viewport_width=800,
            viewport_height=600,
            body_width=400,
            form_width=400,
            settings_width=420,
            content_height=500,
            breakpoint="normal",
        )
    )
    assert screen.queue_size_heading.width == 420
    assert screen.queue_size_description.width == 420
    assert screen.queue_size_divider.width == 420

    words.apply_layout(420)
    definitions.apply_layout(420)
    assert words.width == 420
    assert words.slider.width == 420
    assert words.label.width == 420
    assert definitions.slider.width == 420


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


def test_settings_queue_sliders_update_runtime_flags(restore_learn_preferences):
    from learning_app.ui.screens.settings_control import SettingsControl

    LearnPreferences.word_formations_queue_size = 5
    LearnPreferences.definitions_queue_size = 10
    calls = []
    page = SimpleNamespace(run_task=lambda *args, **kwargs: calls.append(args))
    screen = SettingsControl(page)

    screen.word_formations_queue_slider.slider.value = 8.0
    screen.word_formations_queue_slider.on_slider_change(
        SimpleNamespace(control=screen.word_formations_queue_slider.slider)
    )
    screen.definitions_queue_slider.slider.value = 14.0
    screen.definitions_queue_slider.on_slider_change(
        SimpleNamespace(control=screen.definitions_queue_slider.slider)
    )

    assert LearnPreferences.word_formations_queue_size == 8
    assert LearnPreferences.definitions_queue_size == 14
    assert screen.word_formations_queue_slider.label.value == "Word formations: 8"
    assert screen.definitions_queue_slider.label.value == "Definitions: 14"
    assert calls == [
        (LearnPreferences.save_word_formations_queue_size, 8),
        (LearnPreferences.save_definitions_queue_size, 14),
    ]
