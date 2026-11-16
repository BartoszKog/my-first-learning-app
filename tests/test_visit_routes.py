"""Open visit ids are dropped when a stack rewrite removes the learn screen."""

from types import SimpleNamespace

import pandas as pd
import pytest

from learning_app.data.app_data import add_new_file, record_set_use, save_set
from learning_app.data.constants import PartsOfSpeech, StatsColumns
from learning_app.data.repository import count_visits, current_visit_id, visits_for
from learning_app.ui import router
from learning_app.ui.route_paths import HOME_ROUTE, SET_EDIT_ROUTE, SET_LEARN_ROUTE
from learning_app.ui.route_url import build_route


def _words_row() -> dict:
    return {
        PartsOfSpeech.VERB.value: "go",
        PartsOfSpeech.PERSON.value: "walker",
        PartsOfSpeech.THING.value: "path",
        PartsOfSpeech.ADJECTIVE.value: "quick",
        PartsOfSpeech.ADVERB.value: "",
        StatsColumns.CORRECT_ANSWERS.value: 0,
        StatsColumns.GOOD_ANSWER.value: False,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
        StatsColumns.WORD_TO_LEARN.value: False,
    }


class _StackPage:
    def __init__(self, *routes: str):
        self.views = [SimpleNamespace(route=route) for route in routes]
        self.padding = 0
        self.route = routes[-1]
        self.dialogs: list = []

    async def push_route(self, route: str) -> None:
        self.route = route

    def update(self) -> None:
        return None

    def show_dialog(self, dialog) -> None:
        self.dialogs.append(dialog)


def _silence_route_chrome(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(router.LayoutMetricsStore, "refresh", lambda page: None)
    monkeypatch.setattr(router.AppTheme, "apply_to_page", staticmethod(lambda page: None))
    monkeypatch.setattr(router, "_detach_shared_chrome_from_views", lambda page: None)
    monkeypatch.setattr(router, "_update_drawer_selection", lambda route: None)
    monkeypatch.setattr(router, "_sync_chrome_for_route", lambda route, page: None)
    monkeypatch.setattr(
        "learning_app.ui.inplace_search.close_inplace_search",
        lambda page: None,
    )


def _open_kept_set() -> str:
    save_set(pd.DataFrame([_words_row()]), "kept_words.csv")
    add_new_file("kept_words.csv", "Kept")
    record_set_use("kept_words.csv")
    visit_id = current_visit_id("kept_words.csv")
    assert visit_id is not None
    assert count_visits("kept_words.csv") == 1
    return visit_id


async def test_push_route_fallback_forgets_open_visit_id(monkeypatch: pytest.MonkeyPatch):
    visit_id = _open_kept_set()
    _silence_route_chrome(monkeypatch)
    monkeypatch.setattr(
        router,
        "_build_route_view",
        lambda full_route, page: SimpleNamespace(route=HOME_ROUTE),
    )

    page = _StackPage(build_route(SET_LEARN_ROUTE, file="kept_words.csv"))
    await router.push_route_view(page, build_route(SET_EDIT_ROUTE, file="missing_words.csv"))

    assert current_visit_id("kept_words.csv") is None
    assert count_visits("kept_words.csv") == 1
    assert visits_for("kept_words.csv")[0].id == visit_id
    assert page.views[0].route == HOME_ROUTE


async def test_reanchor_on_home_forgets_open_visit_id(monkeypatch: pytest.MonkeyPatch):
    visit_id = _open_kept_set()
    _silence_route_chrome(monkeypatch)
    monkeypatch.setattr(
        router,
        "_build_route_view",
        lambda full_route, page: SimpleNamespace(route=full_route),
    )

    edit_route = build_route(SET_EDIT_ROUTE, file="kept_words.csv")
    page = _StackPage(build_route(SET_LEARN_ROUTE, file="kept_words.csv"))
    await router.reanchor_active_deep_view_on_home(page, edit_route)

    assert [view.route for view in page.views] == [HOME_ROUTE, edit_route]
    assert current_visit_id("kept_words.csv") is None
    assert count_visits("kept_words.csv") == 1
    assert visits_for("kept_words.csv")[0].id == visit_id
