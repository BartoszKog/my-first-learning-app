"""Page-level keyboard shortcut dispatch.

Flet exposes a single ``page.on_keyboard_event`` handler. This module owns that
handler for the app lifetime:

- **Ctrl+B** (or Meta+B): topmost registered back action when a screen has
  pushed one (e.g. edit-set unsaved-changes confirm); otherwise navigational
  back via ``go_back`` (same as system back / in-app Back — closes in-place
  search first when open).
- **Ctrl+Enter** (or Meta+Enter): topmost learn-screen primary action, when
  a screen has pushed one while mounted.
- **Ctrl+S** (or Meta+S): topmost registered action — Save on the edit-set
  screen, or speak on a definitions learn session while that screen is mounted.
"""

from __future__ import annotations

from typing import Callable

import flet as ft

ShortcutAction = Callable[[ft.KeyboardEvent], None]

_ENTER_KEYS = frozenset({"Enter", "Return", "Numpad Enter"})
_B_KEYS = frozenset({"B", "b"})
_S_KEYS = frozenset({"S", "s"})

_ctrl_b_actions: list[ShortcutAction] = []
_ctrl_enter_actions: list[ShortcutAction] = []
_ctrl_s_actions: list[ShortcutAction] = []
_bound_page: ft.Page | None = None


def _is_ctrl_or_meta_shortcut(e: ft.KeyboardEvent, keys: frozenset[str]) -> bool:
    """Match Ctrl/Meta + key, ignoring AltGr (Ctrl+Alt on Windows)."""
    key = (e.key or "").strip()
    if key not in keys:
        return False
    if e.alt:
        return False
    return bool(e.ctrl or e.meta)


def is_ctrl_enter(e: ft.KeyboardEvent) -> bool:
    """Return True when the event is Control (or Meta) + Enter."""
    return _is_ctrl_or_meta_shortcut(e, _ENTER_KEYS)


def is_ctrl_b(e: ft.KeyboardEvent) -> bool:
    """Return True when the event is Control (or Meta) + B."""
    return _is_ctrl_or_meta_shortcut(e, _B_KEYS)


def is_ctrl_s(e: ft.KeyboardEvent) -> bool:
    """Return True when the event is Control (or Meta) + S."""
    return _is_ctrl_or_meta_shortcut(e, _S_KEYS)


def _dispatch(e: ft.KeyboardEvent) -> None:
    if is_ctrl_b(e):
        if _ctrl_b_actions:
            _ctrl_b_actions[-1](e)
            return
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


def push_ctrl_b_action(page: ft.Page | None, action: ShortcutAction) -> None:
    """Register ``action`` as the active Ctrl+B handler (screen-specific back)."""
    if page is None:
        return
    _ensure_handler(page)
    _ctrl_b_actions.append(action)


def pop_ctrl_b_action(page: ft.Page | None, action: ShortcutAction) -> None:
    """Remove a previously pushed Ctrl+B ``action``."""
    if action in _ctrl_b_actions:
        _ctrl_b_actions.remove(action)
    if page is not None:
        _ensure_handler(page)


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
    """Register ``action`` as the active Ctrl+S handler (save or speak)."""
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
    _ctrl_b_actions.clear()
    _ctrl_enter_actions.clear()
    _ctrl_s_actions.clear()
    _bound_page = None
