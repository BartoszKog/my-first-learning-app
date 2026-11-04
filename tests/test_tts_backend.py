"""Tests for the TTS cache, service, and speakable-text collection."""

from pathlib import Path

import pandas as pd
import pytest

from learning_app.data.app_data import add_new_file, delate_set, generate_empty_files_data, save_set
from learning_app.data.file_path_manager import FilePathManager
from learning_app.tts.cache import TtsCache
from learning_app.tts.gtts_provider import GttsProvider
from learning_app.tts.provider import TtsError, TtsProvider
from learning_app.tts.service import TtsService
from learning_app.tts.texts import collect_speakable_texts, normalize_text, speakable_phrases


@pytest.fixture
def english_tts_language():
    from learning_app.ui.tts_preferences import TtsPreferences

    previous = TtsPreferences.language
    TtsPreferences.language = "en"
    yield
    TtsPreferences.language = previous


class FakeProvider(TtsProvider):
    name = "fake"
    voice = "test"

    def __init__(self, audio: bytes = b"ID3fake-mp3"):
        self.audio = audio
        self.calls: list[tuple[str, str]] = []

    async def synthesize(self, text: str, language: str) -> bytes:
        self.calls.append((text, language))
        return self.audio


@pytest.fixture
def tts_cache(tmp_path: Path) -> TtsCache:
    return TtsCache(tmp_path / "tts_cache")


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  insult\n  me  ") == "insult me"
    assert normalize_text("   ") == ""


def test_speakable_phrases_splits_all_slash_members():
    assert speakable_phrases("go/goes/went") == ["go", "goes", "went"]
    assert speakable_phrases("  dependent / dependable ") == ["dependent", "dependable"]
    assert speakable_phrases("go/go/went") == ["go", "went"]
    assert speakable_phrases("insult") == ["insult"]
    assert speakable_phrases("  /  ") == []


def test_gtts_provider_uses_gtts_name():
    assert GttsProvider().name == "gtts"
    assert GttsProvider().voice == ""


def test_cache_key_changes_with_language_and_provider():
    english = TtsCache.make_key("gtts", "en", "gift")
    german = TtsCache.make_key("gtts", "de", "gift")
    other = TtsCache.make_key("elevenlabs", "en", "gift")

    assert english != german
    assert english != other
    assert english == TtsCache.make_key("gtts", "en", "  gift  ")


def test_cache_put_get_roundtrip(tts_cache: TtsCache):
    key = tts_cache.make_key("fake", "en", "insult")
    path = tts_cache.put(
        key,
        b"mp3-bytes",
        text="insult",
        language="en",
        provider="fake",
    )

    assert path.is_file()
    assert path.read_bytes() == b"mp3-bytes"
    assert tts_cache.get_path(key) == path


def test_cache_get_path_miss(tts_cache: TtsCache):
    assert tts_cache.get_path("ab" * 32) is None


def test_cache_get_path_rejects_empty_mp3(tts_cache: TtsCache):
    key = tts_cache.make_key("fake", "en", "insult")
    path = tts_cache.put(
        key,
        b"mp3-bytes",
        text="insult",
        language="en",
        provider="fake",
    )
    path.write_bytes(b"")

    assert tts_cache.get_path(key) is None


def test_garbage_collect_keeps_only_live_language_pairs(tts_cache: TtsCache):
    insult_en = tts_cache.make_key("fake", "en", "insult")
    insult_pl = tts_cache.make_key("fake", "pl", "insult")
    gone = tts_cache.make_key("fake", "en", "obsolete")
    tts_cache.put(insult_en, b"en", text="insult", language="en", provider="fake")
    tts_cache.put(insult_pl, b"pl", text="insult", language="pl", provider="fake")
    tts_cache.put(gone, b"old", text="obsolete", language="en", provider="fake")

    removed = tts_cache.garbage_collect({("insult", "en")})

    assert removed == 2
    assert tts_cache.get_path(insult_en) is not None
    assert tts_cache.get_path(insult_pl) is None
    assert tts_cache.get_path(gone) is None


def test_garbage_collect_removes_orphan_mp3_without_sidecar(tts_cache: TtsCache):
    orphan = tts_cache.root / "aa" / ("b" * 64 + ".mp3")
    orphan.parent.mkdir(parents=True)
    orphan.write_bytes(b"orphan")

    removed = tts_cache.garbage_collect(set())

    assert removed == 1
    assert not orphan.exists()


@pytest.mark.asyncio
async def test_service_synthesizes_once_then_uses_cache(tts_cache: TtsCache):
    provider = FakeProvider()
    service = TtsService(provider, cache=tts_cache)

    first = await service.resolve_path(" insult ", "en")
    second = await service.resolve_path("insult", "en")

    assert first == second
    assert first.read_bytes() == b"ID3fake-mp3"
    assert provider.calls == [("insult", "en")]


@pytest.mark.asyncio
async def test_service_rejects_empty_text(tts_cache: TtsCache):
    service = TtsService(FakeProvider(), cache=tts_cache)

    with pytest.raises(TtsError, match="empty"):
        await service.resolve_path("   ", "en")
    assert service.provider.calls == []


@pytest.mark.asyncio
async def test_service_resolve_path_rejects_slash_cells(tts_cache: TtsCache):
    service = TtsService(FakeProvider(), cache=tts_cache)

    with pytest.raises(TtsError, match="resolve_paths"):
        await service.resolve_path("go/goes", "en")


@pytest.mark.asyncio
async def test_service_resolve_paths_synthesizes_each_slash_member(tts_cache: TtsCache):
    provider = FakeProvider()
    service = TtsService(provider, cache=tts_cache)

    paths = await service.resolve_paths(" go / goes / went ", "en")

    assert [path.read_bytes() for path in paths] == [b"ID3fake-mp3"] * 3
    assert provider.calls == [("go", "en"), ("goes", "en"), ("went", "en")]
    again = await service.resolve_paths("go/goes/went", "en")
    assert again == paths
    assert provider.calls == [("go", "en"), ("goes", "en"), ("went", "en")]


@pytest.mark.asyncio
async def test_service_get_mp3_bytes(tts_cache: TtsCache):
    service = TtsService(FakeProvider(b"abc"), cache=tts_cache)

    assert await service.get_mp3_bytes("hello", "en") == b"abc"


def test_collect_speakable_texts_ignores_stats_and_empty_cells(isolated_csv_dir: Path):
    from learning_app.ui.tts_preferences import TtsPreferences

    previous_language = TtsPreferences.language
    TtsPreferences.language = "en"
    words = pd.DataFrame(
        {
            "verb": ["analyse", ""],
            "person": ["analyst", None],
            "thing": ["analysis", "unused"],
            "adjective": ["analytical", "  pretty  "],
            "adverb": ["analytically", "dependent/dependable"],
            "correct_answers": [0, 0],
            "good_answers_in_a_row": [False, False],
            "good_answer": [False, False],
            "word_to_learn": [False, False],
        }
    )
    words.to_csv(isolated_csv_dir / "demo_words.csv", index=True)

    definitions = pd.DataFrame(
        {
            "definition": ["znieważać"],
            "word": ["insult"],
            "correct_answers": [0],
            "good_answers_in_a_row": [False],
            "good_answer": [False],
            "word_to_learn": [False],
        }
    )
    definitions.to_csv(isolated_csv_dir / "demo_definitions.csv", index=True)

    try:
        texts = collect_speakable_texts()
    finally:
        TtsPreferences.language = previous_language

    assert ("analyse", "en") in texts
    assert ("insult", "en") in texts
    assert ("znieważać", "en") in texts
    assert ("pretty", "en") in texts
    assert ("unused", "en") in texts
    assert ("dependent", "en") in texts
    assert ("dependable", "en") in texts
    assert ("dependent/dependable", "en") not in texts
    assert "0" not in texts
    assert "False" not in texts
    assert "" not in texts


def test_service_garbage_collect_uses_live_set_texts(
    isolated_csv_dir: Path,
    tts_cache: TtsCache,
    english_tts_language,
):
    definitions = pd.DataFrame({"definition": ["znieważać"], "word": ["insult"]})
    definitions.to_csv(isolated_csv_dir / "live_definitions.csv", index=True)

    service = TtsService(FakeProvider(), cache=tts_cache)
    keep = tts_cache.make_key("fake", "en", "insult", voice="test")
    drop = tts_cache.make_key("fake", "en", "gone", voice="test")
    tts_cache.put(keep, b"keep", text="insult", language="en", provider="fake", voice="test")
    tts_cache.put(drop, b"drop", text="gone", language="en", provider="fake", voice="test")

    removed = service.garbage_collect()

    assert removed == 1
    assert tts_cache.get_path(keep) is not None
    assert tts_cache.get_path(drop) is None


def test_save_set_prune_tts_drops_removed_phrase(isolated_csv_dir: Path, english_tts_language):
    generate_empty_files_data()
    frame = pd.DataFrame({"definition": ["znieważać"], "word": ["insult"]})
    save_set(frame, "live_definitions.csv")
    cache = TtsCache()
    keep = cache.make_key("fake", "en", "insult")
    drop = cache.make_key("fake", "en", "obsolete")
    cache.put(keep, b"keep", text="insult", language="en", provider="fake")
    cache.put(drop, b"drop", text="obsolete", language="en", provider="fake")

    save_set(frame, "live_definitions.csv")
    assert cache.get_path(drop) is not None

    save_set(frame, "live_definitions.csv", prune_tts=True)

    assert cache.get_path(keep) is not None
    assert cache.get_path(drop) is None


def test_delate_set_prunes_unused_tts_cache(isolated_csv_dir: Path, english_tts_language):
    generate_empty_files_data()
    frame = pd.DataFrame({"definition": ["znieważać"], "word": ["insult"]})
    save_set(frame, "live_definitions.csv")
    add_new_file("live_definitions.csv", "Live")
    cache = TtsCache()
    key = cache.make_key("fake", "en", "insult")
    cache.put(key, b"keep", text="insult", language="en", provider="fake")

    delate_set("live_definitions.csv")

    assert cache.get_path(key) is None


def test_delate_set_releases_only_the_unused_language(isolated_csv_dir: Path, english_tts_language):
    from learning_app.data.constants import FilesColumns
    from learning_app.data.set_settings import enable_set_overrides, set_override_value

    generate_empty_files_data()
    frame = pd.DataFrame({"definition": ["meaning"], "word": ["kot"]})
    save_set(frame, "polish_definitions.csv")
    save_set(frame, "german_definitions.csv")
    add_new_file("polish_definitions.csv", "Polish")
    add_new_file("german_definitions.csv", "German")
    enable_set_overrides("polish_definitions.csv")
    enable_set_overrides("german_definitions.csv")
    set_override_value("polish_definitions.csv", FilesColumns.TTS_LANGUAGE.value, "pl")
    set_override_value("german_definitions.csv", FilesColumns.TTS_LANGUAGE.value, "de")

    cache = TtsCache()
    polish = cache.make_key("fake", "pl", "kot")
    german = cache.make_key("fake", "de", "kot")
    cache.put(polish, b"pl", text="kot", language="pl", provider="fake")
    cache.put(german, b"de", text="kot", language="de", provider="fake")

    delate_set("polish_definitions.csv")

    assert cache.get_path(polish) is None
    assert cache.get_path(german) is not None

    delate_set("german_definitions.csv")

    assert cache.get_path(german) is None


def test_delate_set_keeps_cache_while_another_set_uses_the_language(
    isolated_csv_dir: Path,
    english_tts_language,
):
    from learning_app.data.constants import FilesColumns
    from learning_app.data.set_settings import enable_set_overrides, set_override_value

    generate_empty_files_data()
    frame = pd.DataFrame({"definition": ["meaning"], "word": ["kot"]})
    save_set(frame, "first_definitions.csv")
    save_set(frame, "second_definitions.csv")
    add_new_file("first_definitions.csv", "First")
    add_new_file("second_definitions.csv", "Second")
    enable_set_overrides("first_definitions.csv")
    enable_set_overrides("second_definitions.csv")
    set_override_value("first_definitions.csv", FilesColumns.TTS_LANGUAGE.value, "pl")
    set_override_value("second_definitions.csv", FilesColumns.TTS_LANGUAGE.value, "pl")

    cache = TtsCache()
    polish = cache.make_key("fake", "pl", "kot")
    cache.put(polish, b"pl", text="kot", language="pl", provider="fake")

    delate_set("first_definitions.csv")
    assert cache.get_path(polish) is not None

    delate_set("second_definitions.csv")
    assert cache.get_path(polish) is None


@pytest.mark.asyncio
async def test_gtts_provider_maps_value_error(monkeypatch: pytest.MonkeyPatch):
    import gtts

    def boom(*args, **kwargs):
        raise ValueError("unsupported language")

    monkeypatch.setattr(gtts, "gTTS", boom)

    with pytest.raises(TtsError, match="rejected"):
        await GttsProvider().synthesize("hello", "zz")


def test_tts_cache_dir_lives_under_data_dir():
    cache_dir = Path(FilePathManager.get_tts_cache_dir())
    data_dir = Path(FilePathManager.get_data_dir())

    assert cache_dir == data_dir / "tts_cache"
    assert cache_dir.is_dir()
