"""Tests for app keyboard shortcut dispatch."""

from types import SimpleNamespace
from unittest.mock import patch

from learning_app.ui.keyboard_shortcuts import (
    install_keyboard_shortcuts,
    is_ctrl_enter,
    is_ctrl_left_arrow,
    is_ctrl_s,
    pop_ctrl_enter_action,
    pop_ctrl_s_action,
    push_ctrl_enter_action,
    push_ctrl_s_action,
    reset_ctrl_enter_actions_for_tests,
)


def _event(*, key="Enter", ctrl=False, meta=False, shift=False, alt=False, page=None):
    return SimpleNamespace(
        key=key,
        ctrl=ctrl,
        meta=meta,
        shift=shift,
        alt=alt,
        page=page,
    )


def _fake_page():
    return SimpleNamespace(on_keyboard_event=None)


def test_is_ctrl_enter_accepts_ctrl_or_meta_enter():
    assert is_ctrl_enter(_event(ctrl=True))
    assert is_ctrl_enter(_event(meta=True, key="Return"))
    assert is_ctrl_enter(_event(ctrl=True, key="Numpad Enter"))
    assert not is_ctrl_enter(_event(ctrl=True, key="A"))
    assert not is_ctrl_enter(_event(key="Enter"))


def test_is_ctrl_left_arrow_accepts_variants():
    assert is_ctrl_left_arrow(_event(ctrl=True, key="Arrow Left"))
    assert is_ctrl_left_arrow(_event(meta=True, key="ArrowLeft"))
    assert is_ctrl_left_arrow(_event(ctrl=True, key="Left"))
    assert not is_ctrl_left_arrow(_event(key="Arrow Left"))
    assert not is_ctrl_left_arrow(_event(ctrl=True, key="Arrow Right"))


def test_push_pop_dispatches_topmost_action():
    reset_ctrl_enter_actions_for_tests()
    page = _fake_page()
    calls = []

    def first(e):
        calls.append("first")

    def second(e):
        calls.append("second")

    push_ctrl_enter_action(page, first)
    push_ctrl_enter_action(page, second)
    page.on_keyboard_event(_event(ctrl=True, key="Enter"))
    assert calls == ["second"]

    pop_ctrl_enter_action(page, second)
    page.on_keyboard_event(_event(ctrl=True, key="Enter"))
    assert calls == ["second", "first"]

    pop_ctrl_enter_action(page, first)
    # Handler stays installed app-wide; Ctrl+Enter with empty stack is a no-op.
    assert page.on_keyboard_event is not None
    page.on_keyboard_event(_event(ctrl=True, key="Enter"))
    assert calls == ["second", "first"]
    reset_ctrl_enter_actions_for_tests()


def test_non_ctrl_enter_does_not_fire_action():
    reset_ctrl_enter_actions_for_tests()
    page = _fake_page()
    calls = []

    def action(e):
        calls.append("hit")

    push_ctrl_enter_action(page, action)
    page.on_keyboard_event(_event(key="Enter"))
    page.on_keyboard_event(_event(ctrl=True, key="A"))
    assert calls == []

    pop_ctrl_enter_action(page, action)
    reset_ctrl_enter_actions_for_tests()


def test_ctrl_left_arrow_calls_go_back():
    reset_ctrl_enter_actions_for_tests()
    page = _fake_page()
    install_keyboard_shortcuts(page)

    with patch("learning_app.ui.navigation.go_back") as go_back:
        page.on_keyboard_event(_event(ctrl=True, key="Arrow Left", page=page))
        go_back.assert_called_once_with(page)

        go_back.reset_mock()
        page.on_keyboard_event(_event(ctrl=True, key="Enter", page=page))
        go_back.assert_not_called()

    reset_ctrl_enter_actions_for_tests()


def test_ctrl_left_takes_priority_over_ctrl_enter_action():
    reset_ctrl_enter_actions_for_tests()
    page = _fake_page()
    calls = []
    push_ctrl_enter_action(page, lambda e: calls.append("enter"))

    with patch("learning_app.ui.navigation.go_back") as go_back:
        page.on_keyboard_event(_event(ctrl=True, key="Arrow Left", page=page))
        go_back.assert_called_once_with(page)
        assert calls == []

    reset_ctrl_enter_actions_for_tests()


def test_is_ctrl_s_accepts_ctrl_or_meta():
    assert is_ctrl_s(_event(ctrl=True, key="S"))
    assert is_ctrl_s(_event(meta=True, key="s"))
    assert not is_ctrl_s(_event(key="S"))
    assert not is_ctrl_s(_event(ctrl=True, key="A"))


def test_ctrl_s_dispatches_topmost_action():
    reset_ctrl_enter_actions_for_tests()
    page = _fake_page()
    calls = []

    def speak(e):
        calls.append("speak")

    push_ctrl_s_action(page, speak)
    page.on_keyboard_event(_event(ctrl=True, key="S"))
    assert calls == ["speak"]
    pop_ctrl_s_action(page, speak)
    page.on_keyboard_event(_event(ctrl=True, key="S"))
    assert calls == ["speak"]
    reset_ctrl_enter_actions_for_tests()


def test_word_field_is_awaiting_input():
    from learning_app.ui.components.controls import WordField

    field = WordField(label="Verb", read_only=False)
    field.value = ""
    assert field.is_awaiting_input() is True

    field.value = "go"
    assert field.is_awaiting_input() is False

    field.value = ""
    field.read_only = True
    assert field.is_awaiting_input() is False

    field.read_only = False
    field.disabled = True
    assert field.is_awaiting_input() is False
