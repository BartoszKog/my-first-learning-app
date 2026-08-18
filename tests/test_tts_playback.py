"""Tests for session TTS playback wiring (service + one Audio player)."""

from types import SimpleNamespace

import flet_audio as fta
import pytest

from learning_app.tts.provider import TtsProvider
from learning_app.ui.app_session import AppSession
from learning_app.ui.tts_preferences import TtsPreferences


class FakeProvider(TtsProvider):
    name = "fake"
    voice = "test"

    def __init__(self, audio: bytes = b"ID3fake-mp3"):
        self.audio = audio
        self.calls: list[tuple[str, str]] = []

    async def synthesize(self, text: str, language: str) -> bytes:
        self.calls.append((text, language))
        return self.audio


class FakeAudio:
    def __init__(self):
        self.src = None
        self.played: list[str] = []
        self.on_state_change = None
        self.page = None

    async def play(self):
        self.played.append(str(self.src))
        if self.on_state_change is not None:
            self.on_state_change(SimpleNamespace(state=fta.AudioState.COMPLETED))


@pytest.fixture
def tts_session(tmp_path, monkeypatch):
    from learning_app.data.file_path_manager import FilePathManager
    from learning_app.tts.cache import TtsCache
    from learning_app.tts.service import TtsService

    monkeypatch.setattr(FilePathManager, "_data_dir", str(tmp_path / "storage_data"), raising=False)
    monkeypatch.setattr(FilePathManager, "_initialized", True)
    cache = TtsCache(tmp_path / "tts_cache")
    provider = FakeProvider()
    player = FakeAudio()
    page = SimpleNamespace(services=[])
    AppSession.set_page(page)
    AppSession.init_tts(page, service=TtsService(provider, cache=cache), player=player)
    yield SimpleNamespace(provider=provider, player=player, page=page)
    AppSession._page = None
    AppSession._tts_service = None
    AppSession._tts_player = None
    AppSession._tts_retain = []
    AppSession._tts_mounted = False
    AppSession._speak_generation = 0
    AppSession._playback_done = None
    AppSession._src_loaded = None


def test_init_tts_reuses_one_player_without_appending_injected_player(tts_session):
    assert AppSession.get_tts_player() is tts_session.player
    assert tts_session.page.services == []


def test_init_tts_does_not_create_audio_without_src(tmp_path, monkeypatch):
    from learning_app.data.file_path_manager import FilePathManager
    from learning_app.tts.cache import TtsCache
    from learning_app.tts.service import TtsService

    monkeypatch.setattr(FilePathManager, "_data_dir", str(tmp_path / "storage_data"), raising=False)
    monkeypatch.setattr(FilePathManager, "_initialized", True)
    page = SimpleNamespace(services=[])
    AppSession.init_tts(
        page,
        service=TtsService(FakeProvider(), cache=TtsCache(tmp_path / "tts_cache")),
    )
    try:
        assert page.services == []
        assert AppSession._tts_player is None
    finally:
        AppSession._tts_service = None
        AppSession._tts_player = None
        AppSession._tts_retain = []
        AppSession._tts_mounted = False
        AppSession._speak_generation = 0
        AppSession._playback_done = None
        AppSession._src_loaded = None


@pytest.mark.asyncio
async def test_speak_plays_each_slash_member_in_order(tts_session):
    await AppSession.speak(" go / goes / went ", "en")

    assert tts_session.provider.calls == [("go", "en"), ("goes", "en"), ("went", "en")]
    assert len(tts_session.player.played) == 3
    assert all(src.endswith(".mp3") for src in tts_session.player.played)
    assert tts_session.player in tts_session.page.services


@pytest.mark.asyncio
async def test_speak_reattaches_player_after_services_cleared(tts_session):
    tts_session.page.services.clear()
    await AppSession.speak("hello", "en")
    assert tts_session.player in tts_session.page.services
    assert tts_session.player.played


def test_definition_learn_places_speaker_right_of_check(isolated_csv_dir):
    import pandas as pd

    from learning_app.data.app_data import generate_empty_files_data, save_set
    from learning_app.data.constants import StatsColumns, WordDefinitions
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["znieważać"],
                WordDefinitions.WORD.value: ["insult"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "live_definitions.csv",
    )
    screen = WordDefinitionField("live_definitions.csv", session=True)

    assert screen.check_row.controls == [screen.checkButton, screen.speakButton]
    assert screen.speakButton.disabled is True
    assert screen._speak_unlocked is False


@pytest.mark.asyncio
async def test_definition_speak_uses_word_not_definition(isolated_csv_dir, monkeypatch):
    import pandas as pd

    from learning_app.data.app_data import generate_empty_files_data, save_set
    from learning_app.data.constants import StatsColumns, WordDefinitions
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["znieważać"],
                WordDefinitions.WORD.value: ["insult"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "live_definitions.csv",
    )
    spoken: list[tuple[str, str]] = []

    async def fake_speak(text, language):
        spoken.append((text, language))

    monkeypatch.setattr(AppSession, "speak", fake_speak)
    screen = WordDefinitionField("live_definitions.csv", session=True)
    previous_language = TtsPreferences.language
    TtsPreferences.language = "pl"
    screen._set_speak_unlocked(True)
    try:
        await screen.on_speak_click(SimpleNamespace())
    finally:
        TtsPreferences.language = previous_language

    assert spoken == [("insult", "pl")]


@pytest.mark.asyncio
async def test_definition_speak_is_ignored_before_check(isolated_csv_dir, monkeypatch):
    import pandas as pd

    from learning_app.data.app_data import generate_empty_files_data, save_set
    from learning_app.data.constants import StatsColumns, WordDefinitions
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["znieważać"],
                WordDefinitions.WORD.value: ["insult"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "live_definitions.csv",
    )
    spoken: list[tuple[str, str]] = []

    async def fake_speak(text, language):
        spoken.append((text, language))

    monkeypatch.setattr(AppSession, "speak", fake_speak)
    screen = WordDefinitionField("live_definitions.csv", session=True)
    await screen.on_speak_click(SimpleNamespace())

    assert spoken == []
    assert screen.speakButton.disabled is True


@pytest.mark.asyncio
async def test_auto_speak_swallows_errors_without_snackbar(isolated_csv_dir, monkeypatch):
    import pandas as pd

    from learning_app.data.app_data import generate_empty_files_data, save_set
    from learning_app.data.constants import StatsColumns, WordDefinitions
    from learning_app.tts import TtsNetworkError
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["znieważać"],
                WordDefinitions.WORD.value: ["insult"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "live_definitions.csv",
    )
    errors: list[str] = []

    async def boom(text, language):
        raise TtsNetworkError("offline")

    monkeypatch.setattr(AppSession, "speak", boom)
    screen = WordDefinitionField("live_definitions.csv", session=True)
    screen._show_tts_error = errors.append
    screen._set_speak_unlocked(True)
    await screen._speak_current_word(False)

    assert errors == []


@pytest.mark.asyncio
async def test_manual_speak_still_reports_errors(isolated_csv_dir, monkeypatch):
    import pandas as pd

    from learning_app.data.app_data import generate_empty_files_data, save_set
    from learning_app.data.constants import StatsColumns, WordDefinitions
    from learning_app.tts import TtsNetworkError
    from learning_app.ui.components.word_definition_field import WordDefinitionField

    generate_empty_files_data()
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: ["znieważać"],
                WordDefinitions.WORD.value: ["insult"],
                StatsColumns.CORRECT_ANSWERS.value: [0],
                StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False],
                StatsColumns.GOOD_ANSWER.value: [False],
                StatsColumns.WORD_TO_LEARN.value: [False],
            }
        ),
        "live_definitions.csv",
    )
    errors: list[str] = []

    async def boom(text, language):
        raise TtsNetworkError("offline")

    monkeypatch.setattr(AppSession, "speak", boom)
    screen = WordDefinitionField("live_definitions.csv", session=True)
    screen._show_tts_error = errors.append
    screen._set_speak_unlocked(True)
    await screen.on_speak_click(SimpleNamespace())

    assert errors == ["Could not play pronunciation. Check your internet connection."]

