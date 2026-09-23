"""Page-level keyboard shortcut dispatch.

Flet exposes a single ``page.on_keyboard_event`` handler. This module owns that
handler for the app lifetime:

- **Ctrl+Left** (or Meta+Left): navigational back via ``go_back`` (same as
  system back / in-app Back — closes in-place search first when open).
- **Ctrl+Enter** (or Meta+Enter): topmost learn-screen primary action, when
  a screen has pushed one while mounted.
- **Ctrl+S** (or Meta+S): topmost definitions-session speak action, when
  registered while that session is mounted.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

ShortcutAction = Callable[[ft.KeyboardEvent], None]

_ENTER_KEYS = frozenset({"Enter", "Return", "Numpad Enter"})
_LEFT_KEYS = frozenset({"Arrow Left", "ArrowLeft", "Left"})
_S_KEYS = frozenset({"S", "s"})

_ctrl_enter_actions: list[ShortcutAction] = []
_ctrl_s_actions: list[ShortcutAction] = []
_bound_page: ft.Page | None = None


def is_ctrl_enter(e: ft.KeyboardEvent) -> bool:
    """Return True when the event is Control (or Meta) + Enter."""
    key = (e.key or "").strip()
    if key not in _ENTER_KEYS:
        return False
    return bool(e.ctrl or e.meta)


def is_ctrl_left_arrow(e: ft.KeyboardEvent) -> bool:
    """Return True when the event is Control (or Meta) + Left Arrow."""
    key = (e.key or "").strip()
    if key not in _LEFT_KEYS:
        return False
    return bool(e.ctrl or e.meta)


def is_ctrl_s(e: ft.KeyboardEvent) -> bool:
    """Return True when the event is Control (or Meta) + S."""
    key = (e.key or "").strip()
    if key not in _S_KEYS:
        return False
    return bool(e.ctrl or e.meta)


def _dispatch(e: ft.KeyboardEvent) -> None:
    if is_ctrl_left_arrow(e):
        page = getattr(e, "page", None) or _bound_page
        if page is not None:
            from learning_app.ui.navigation import go_back

            go_back(page)
        return
    if is_ctrl_enter(e) and _ctrl_enter_actions:
        _ctrl_enter_actions[-1](e)
        return
    if is_ctrl_s(e) and _ctrl_s_actions:
        _ctrl_s_actions[-1](e)


def install_keyboard_shortcuts(page: ft.Page) -> None:
    """Install the app-wide keyboard shortcut handler on ``page``."""
    global _bound_page
    _bound_page = page
    page.on_keyboard_event = _dispatch


def _ensure_handler(page: ft.Page) -> None:
    global _bound_page
    if page.on_keyboard_event is not _dispatch:
        install_keyboard_shortcuts(page)
    else:
        _bound_page = page


def push_ctrl_enter_action(page: ft.Page | None, action: ShortcutAction) -> None:
    """Register ``action`` as the active Ctrl+Enter handler for ``page``."""
    if page is None:
        return
    _ensure_handler(page)
    _ctrl_enter_actions.append(action)


def pop_ctrl_enter_action(page: ft.Page | None, action: ShortcutAction) -> None:
    """Remove a previously pushed Ctrl+Enter ``action``."""
    if action in _ctrl_enter_actions:
        _ctrl_enter_actions.remove(action)
    if page is not None:
        _ensure_handler(page)


def push_ctrl_s_action(page: ft.Page | None, action: ShortcutAction) -> None:
    """Register ``action`` as the active Ctrl+S handler for ``page``."""
    if page is None:
        return
    _ensure_handler(page)
    _ctrl_s_actions.append(action)


def pop_ctrl_s_action(page: ft.Page | None, action: ShortcutAction) -> None:
    """Remove a previously pushed Ctrl+S ``action``."""
    if action in _ctrl_s_actions:
        _ctrl_s_actions.remove(action)
    if page is not None:
        _ensure_handler(page)


def reset_ctrl_enter_actions_for_tests() -> None:
    """Clear shortcut state between unit tests."""
    global _bound_page
    if _bound_page is not None and _bound_page.on_keyboard_event is _dispatch:
        _bound_page.on_keyboard_event = None
    _ctrl_enter_actions.clear()
    _ctrl_s_actions.clear()
    _bound_page = None
