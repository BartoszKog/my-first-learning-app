"""Home shows an empty state only when the tile list has no sets."""

import os
from types import SimpleNamespace

import flet as ft
import msgpack
import pytest
from flet.controls.base_control import BaseControl
from flet.messaging.connection import Connection
from flet.messaging.protocol import ClientMessage, configure_encode_object_for_msgpack
from flet.messaging.session import Session
from flet.pubsub.pubsub_hub import PubSubHub

from learning_app.data.app_data import (
    add_new_file,
    create_empty_set,
    delate_set,
    get_file_names,
    save_set,
)
from learning_app.ui.app_chrome import AppChrome
from learning_app.ui.app_session import AppSession
from learning_app.ui.body_registry import BodyRegistry
from learning_app.ui.components.content_tile import ContentTile
from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.layout_metrics import LayoutMetrics


EMPTY_COPY = "Start by creating a set with the + button,\nor add the demo sets."


@pytest.fixture
def tile_page():
    previous_page = AppSession._page
    previous_home = BodyRegistry._home
    previous_export = BodyRegistry._export
    dialogs = []
    page = SimpleNamespace(update=lambda: None, dialogs=dialogs)
    page.show_dialog = dialogs.append
    AppSession.set_page(page)
    BodyRegistry._home = None
    BodyRegistry._export = None
    yield page
    AppSession._page = previous_page
    BodyRegistry._home = previous_home
    BodyRegistry._export = previous_export


def _dialog_parts(dialog) -> tuple[str, str]:
    title = dialog.title.value if isinstance(dialog.title, ft.Text) else dialog.title
    content = dialog.content.value if isinstance(dialog.content, ft.Text) else dialog.content
    return title, content


def _add_user_set() -> None:
    save_set(create_empty_set("words"), "Animals_words.csv")
    add_new_file("Animals_words.csv", "Animals", "Pets")


def test_empty_home_state_only_when_there_are_no_tiles(tile_page):
    home = TilesContainer()
    export = TilesContainer(export_mode=True)

    assert home.shows_empty_home_state()
    assert home.content is home.empty_home
    assert home.empty_home.alignment == ft.MainAxisAlignment.CENTER
    assert home.empty_home.horizontal_alignment == ft.CrossAxisAlignment.CENTER
    assert home.empty_home.controls == [home.empty_home_text, home.add_demo_button]
    assert home.empty_home_text.value == EMPTY_COPY
    assert home.empty_home_text.value.split("\n") == [
        "Start by creating a set with the + button,",
        "or add the demo sets.",
    ]
    assert home.empty_home_text.size == 14
    assert home.empty_home_text.text_align == ft.TextAlign.CENTER
    assert home.add_demo_button.content == "Add demo sets"
    assert home.add_demo_button.icon == ft.Icons.PLAYLIST_ADD
    assert home.add_demo_button.width is None
    assert not any(isinstance(control, ContentTile) for control in home.content.controls)

    assert not export.shows_empty_home_state()
    assert export.content is export.list_view
    assert export.add_demo_button is None
    assert export.empty_home is None

    home.apply_flex_layout(
        LayoutMetrics(
            viewport_width=800,
            viewport_height=600,
            body_width=400,
            form_width=360,
            settings_width=320,
            content_height=500,
            breakpoint="normal",
        )
    )
    assert home.empty_home_text.width == 360
    assert home.add_demo_button.width is None

    _add_user_set()
    populated = TilesContainer()
    assert not populated.shows_empty_home_state()
    assert populated.content is populated.list_view
    assert populated.has_content_tiles()
    assert not any(
        isinstance(control, ft.Button) and control.content == "Add demo sets"
        for control in populated.list_view.controls
    )

    delate_set("Animals_words.csv")
    populated.refresh_content()
    assert populated.shows_empty_home_state()
    assert not populated.has_content_tiles()
    assert populated.empty_home_text.value == EMPTY_COPY

    populated.trigger_searching_mode()
    assert populated.shows_empty_home_state()
    populated.turn_off_searching_mode()
    assert populated.shows_empty_home_state()


def test_add_demo_button_calls_the_settings_install_path(tile_page, monkeypatch):
    calls = []

    def missing_demo_files():
        calls.append("install")
        raise FileNotFoundError("missing demo.csv")

    monkeypatch.setattr(
        "learning_app.ui.screens.settings_control.install_demo_sets",
        missing_demo_files,
    )

    home = TilesContainer()
    BodyRegistry.set_home(home)
    home.add_demo_button.on_click(SimpleNamespace(page=tile_page))

    from learning_app.ui.screens.settings_control import SettingsControl

    settings = SettingsControl(tile_page)
    settings.on_add_demo_sets_click(SimpleNamespace())

    assert calls == ["install", "install"]
    assert home.shows_empty_home_state()
    assert len(tile_page.dialogs) == 2
    assert _dialog_parts(tile_page.dialogs[0]) == _dialog_parts(tile_page.dialogs[1])
    title, content = _dialog_parts(tile_page.dialogs[0])
    assert title == "Demo sets"
    assert content == "Could not find demo files.\nmissing demo.csv"


def test_add_demo_button_hides_empty_state_after_tiles_exist(tile_page):
    home = TilesContainer()
    export = TilesContainer(export_mode=True)
    BodyRegistry.set_home(home)
    BodyRegistry.set_export(export)

    assert home.shows_empty_home_state()
    assert not export.shows_empty_home_state()

    home.add_demo_button.on_click(SimpleNamespace(page=tile_page))

    assert not home.shows_empty_home_state()
    assert home.has_content_tiles()
    assert home.content is home.list_view
    assert not export.shows_empty_home_state()
    assert export.has_content_tiles()
    assert get_file_names()
    assert len(tile_page.dialogs) == 1
    title, content = _dialog_parts(tile_page.dialogs[0])
    assert title == "Demo sets"
    assert content.startswith("Added all demo sets:")
    for demo_title in ("Demo Word formation", "Demo EN definitions", "Demo EN-PL"):
        assert demo_title in content

    for file_name in list(get_file_names()):
        delate_set(file_name)
    home.refresh_content()
    export.refresh_content()

    assert home.shows_empty_home_state()
    assert not home.has_content_tiles()
    assert not export.shows_empty_home_state()
    assert not export.has_content_tiles()
    assert export.content is export.list_view


class _EncodingConnection(Connection):
    """Record patches and encode them so Flet stores list snapshots."""

    def __init__(self):
        super().__init__()
        self.messages: list[ClientMessage] = []
        self.patch_events: list[list[tuple]] = []
        self.pubsubhub = PubSubHub()

    def send_message(self, message: ClientMessage):
        msgpack.packb(
            [message.action, message.body],
            default=configure_encode_object_for_msgpack(BaseControl),
        )
        self.messages.append(message)
        # Freeze ids now. The patch keeps live controls, which later updates mutate.
        events = []
        patch = getattr(message.body, "patch", None)
        if isinstance(patch, list):
            for op in patch[1:]:
                name = getattr(op[0], "name", "")
                value = op[3] if len(op) > 3 else None
                if name == "Replace":
                    events.append(
                        (
                            "replace",
                            tuple(
                                control._i
                                for control in _walk_controls(value)
                                if isinstance(control, ContentTile)
                            ),
                        )
                    )
                elif name == "Add" and isinstance(value, ContentTile):
                    events.append(("add", value._i))
        self.patch_events.append(events)


def _walk_controls(value, seen: set[int] | None = None):
    if seen is None:
        seen = set()
    if value is None or id(value) in seen:
        return
    seen.add(id(value))
    yield value
    controls = getattr(value, "controls", None)
    if isinstance(controls, list):
        for child in controls:
            yield from _walk_controls(child, seen)
    content = getattr(value, "content", None)
    if content is not None:
        yield from _walk_controls(content, seen)


def _tile_basenames(container: TilesContainer) -> set[str]:
    return {
        os.path.basename(tile.file_name)
        for tile in container.list_view.controls
        if isinstance(tile, ContentTile)
    }


def _snapshot_tiles(container: TilesContainer) -> list[ContentTile]:
    snapshot = getattr(container.list_view, "__prev_lists", {}).get("controls", [])
    return [control for control in snapshot if isinstance(control, ContentTile)]


def test_second_demo_install_matches_catalog_without_ghost_tiles():
    """Install, delete every set, install again: visible tiles are the catalog."""
    previous_page = AppSession._page
    previous_home = BodyRegistry._home
    previous_export = BodyRegistry._export
    previous_chrome = (
        AppChrome._appbar,
        AppChrome._bottom_appbar,
    )
    AppChrome._appbar = ft.AppBar()
    AppChrome._bottom_appbar = ft.BottomAppBar()
    connection = _EncodingConnection()
    session = Session(connection)
    page = session.page
    AppSession.set_page(page)
    BodyRegistry._home = None
    BodyRegistry._export = None
    try:
        home = TilesContainer()
        export = TilesContainer(export_mode=True)
        BodyRegistry.set_home(home)
        BodyRegistry.set_export(export)
        page.controls.extend([home, export])
        initial = session.get_page_patch()
        msgpack.packb(initial, default=configure_encode_object_for_msgpack(BaseControl))

        home.add_demo_button.on_click(SimpleNamespace(page=page))
        assert _tile_basenames(home) == set(get_file_names())
        assert _tile_basenames(export) == set(get_file_names())

        while home.has_content_tiles():
            tile = next(
                control
                for control in home.list_view.controls
                if isinstance(control, ContentTile)
            )
            tile.delete_item(SimpleNamespace(page=page))

        assert get_file_names() == []
        assert home.shows_empty_home_state()
        assert not home.has_content_tiles()
        # The list is off-screen, but its last client snapshot must not still
        # contain the tile that was removed in the same update.
        assert _snapshot_tiles(home) == []

        before = len(connection.patch_events)
        home.add_demo_button.on_click(SimpleNamespace(page=page))
        catalog = set(get_file_names())
        assert catalog
        home_tiles = [
            tile for tile in home.list_view.controls if isinstance(tile, ContentTile)
        ]
        export_tiles = [
            tile for tile in export.list_view.controls if isinstance(tile, ContentTile)
        ]
        assert _tile_basenames(home) == catalog
        assert _tile_basenames(export) == catalog
        assert len(home_tiles) == len(catalog)
        assert len(export_tiles) == len(catalog)
        assert len(home.list_view.controls) == len(catalog) + 1
        assert len(export.list_view.controls) == len(catalog) + 1
        assert len({tile._i for tile in home_tiles}) == len(catalog)
        assert [tile._i for tile in _snapshot_tiles(home)] == [tile._i for tile in home_tiles]
        assert [tile._i for tile in _snapshot_tiles(export)] == [tile._i for tile in export_tiles]

        for events in connection.patch_events[before:]:
            replaced = {
                tile_id
                for kind, payload in events
                if kind == "replace"
                for tile_id in payload
            }
            added = {payload for kind, payload in events if kind == "add"}
            assert replaced.isdisjoint(added)
    finally:
        AppSession._page = previous_page
        BodyRegistry._home = previous_home
        BodyRegistry._export = previous_export
        AppChrome._appbar, AppChrome._bottom_appbar = previous_chrome
