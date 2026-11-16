"""Local SQLite store: schema, round trip, CSV migration, checks, and visits."""

from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from learning_app.data import repository
from learning_app.data.app_data import (
    AppData,
    add_new_file,
    get_file_names_and_titles,
    record_set_use,
    save_set,
    set_default_progress,
)
from learning_app.data.constants import CHECKS_COLUMN, FilesColumns, PartsOfSpeech, StatsColumns
from learning_app.data.file_path_manager import FilePathManager
from learning_app.data.models import Card
from learning_app.data.repository import (
    cards_for,
    count_migrated,
    count_sets,
    count_visits,
    delete_set,
    ensure_db,
    get_engine,
    get_learning_set,
    visits_for,
)


def _words_row(**overrides) -> dict:
    row = {
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
    row.update(overrides)
    return row


def _remigrate() -> None:
    repository._ready_path = None
    ensure_db()


def test_database_file_sits_beside_csv_files(isolated_csv_dir: Path):
    path = Path(FilePathManager.get_db_path())
    assert path.name == "learning.sqlite"
    assert path.parent == isolated_csv_dir.parent
    assert isolated_csv_dir not in path.parents


def test_fresh_database_has_four_tables_and_null_overrides(isolated_csv_dir: Path):
    add_new_file("fresh_words.csv", "Fresh")
    ensure_db()
    with get_engine().connect() as connection:
        names = {
            row[0]
            for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"learning_set", "card", "set_opened", "migrated_csv_file"} <= names

    stored = get_learning_set("fresh_words.csv")
    assert stored is not None
    assert stored.tts_language is None
    assert stored.tts_auto_speak is None
    assert stored.speakers_word_formations is None
    assert stored.speakers_word is None
    assert stored.speakers_definition is None
    assert stored.retry_until_correct is None
    assert stored.queue_size is None


def test_card_without_a_set_is_rejected(isolated_csv_dir: Path):
    ensure_db()
    with Session(get_engine()) as session:
        session.add(Card(set_id="missing-set", position=0))
        with pytest.raises(IntegrityError):
            session.commit()


def test_round_trip_keeps_empty_text_and_zero_checks(isolated_csv_dir: Path):
    save_set(pd.DataFrame([_words_row()]), "words_words.csv")

    stored = cards_for("words_words.csv")
    assert len(stored) == 1
    assert stored[0].adverb == ""
    assert stored[0].definition == ""
    assert stored[0].word == ""
    assert stored[0].checks == 0
    assert stored[0].position == 0

    learning_set = get_learning_set("words_words.csv")
    assert learning_set is not None
    assert learning_set.retry_until_correct is None

    from learning_app.data.set_settings import set_override_value

    set_override_value("words_words.csv", FilesColumns.RETRY_UNTIL_CORRECT.value, "false")
    set_override_value("words_words.csv", FilesColumns.QUEUE_SIZE.value, "6")
    set_override_value("words_words.csv", FilesColumns.TTS_LANGUAGE.value, "pl")
    set_override_value("words_words.csv", FilesColumns.TTS_AUTO_SPEAK.value, "true")

    again = get_learning_set("words_words.csv")
    assert again is not None
    assert again.retry_until_correct is False
    assert again.queue_size == 6
    assert again.tts_language == "pl"
    assert again.tts_auto_speak is None
    assert again.speakers_word is None
    assert again.speakers_definition is None


def test_startup_migration_is_idempotent_and_skips_deleted_sets(isolated_csv_dir: Path):
    (isolated_csv_dir / "files.csv").write_text(
        "file_name,title,subtitle,created_at,last_used,use_count,"
        "tts_language,tts_auto_speak,speakers_word_formations,speakers_word,"
        "speakers_definition,retry_until_correct,queue_size\n"
        "animals_words.csv,Animals,,2020-01-01T00:00:00+00:00,,4,"
        "pl,true,,x,x,false,6\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            _words_row(
                **{
                    StatsColumns.CORRECT_ANSWERS.value: 3,
                    StatsColumns.GOOD_ANSWER.value: True,
                }
            )
        ]
    ).to_csv(isolated_csv_dir / "animals_words.csv", index=True)

    ensure_db()
    stored = get_learning_set("animals_words.csv")
    assert stored is not None
    assert stored.title == "Animals"
    assert stored.use_count == 4
    assert stored.last_used is None
    assert stored.tts_language == "pl"
    assert stored.retry_until_correct is False
    assert stored.queue_size == 6
    assert stored.tts_auto_speak is None
    assert stored.speakers_word_formations is None
    card = cards_for("animals_words.csv")[0]
    assert card.correct_answers == 3
    assert card.checks == 3
    assert card.adverb == ""
    assert count_visits("animals_words.csv") == 0

    words = AppData("animals_words.csv")
    words.current_word_index = words.words.index[0]
    words.good_answer_at_current_row()
    graded = cards_for("animals_words.csv")[0]
    assert graded.checks == 4
    assert graded.correct_answers == 4

    _remigrate()
    assert count_sets() == 1
    again = cards_for("animals_words.csv")[0]
    assert again.id == graded.id
    assert again.checks == 4
    assert again.correct_answers == 4
    assert get_learning_set("animals_words.csv").tts_language == "pl"

    delete_set("animals_words.csv")
    assert (isolated_csv_dir / "animals_words.csv").is_file()
    _remigrate()
    assert count_sets() == 0
    assert count_migrated("animals_words.csv") is True
    assert get_file_names_and_titles() == []


def test_startup_migration_keeps_existing_set_when_csv_is_still_listed(isolated_csv_dir: Path):
    save_set(pd.DataFrame([_words_row(verb="live")]), "animals_words.csv")
    add_new_file("animals_words.csv", "Live title")
    original_id = cards_for("animals_words.csv")[0].id
    assert count_migrated("animals_words.csv") is False

    (isolated_csv_dir / "files.csv").write_text(
        "file_name,title,subtitle,created_at,last_used,use_count,"
        "tts_language,tts_auto_speak,speakers_word_formations,speakers_word,"
        "speakers_definition,retry_until_correct,queue_size\n"
        "animals_words.csv,From CSV,,2020-01-01T00:00:00+00:00,,9,"
        "pl,true,,x,x,false,6\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [_words_row(**{PartsOfSpeech.VERB.value: "from csv", StatsColumns.CORRECT_ANSWERS.value: 9})]
    ).to_csv(isolated_csv_dir / "animals_words.csv", index=True)

    _remigrate()
    assert count_sets() == 1
    stored = get_learning_set("animals_words.csv")
    assert stored is not None
    assert stored.title == "Live title"
    card = cards_for("animals_words.csv")[0]
    assert card.id == original_id
    assert card.verb == "live"
    assert card.correct_answers == 0
    assert count_migrated("animals_words.csv") is True

    _remigrate()
    assert count_sets() == 1
    assert cards_for("animals_words.csv")[0].id == original_id


def test_startup_migration_keeps_a_separate_checks_column(isolated_csv_dir: Path):
    (isolated_csv_dir / "files.csv").write_text(
        "file_name,title,subtitle,created_at,last_used,use_count,"
        "tts_language,tts_auto_speak,speakers_word_formations,speakers_word,"
        "speakers_definition,retry_until_correct,queue_size\n"
        "animals_words.csv,Animals,,2020-01-01T00:00:00+00:00,,1,,,,,,,\n",
        encoding="utf-8",
    )
    frame = pd.DataFrame([_words_row(**{StatsColumns.CORRECT_ANSWERS.value: 3})])
    frame[CHECKS_COLUMN] = 5
    frame.to_csv(isolated_csv_dir / "animals_words.csv", index=True)

    ensure_db()
    card = cards_for("animals_words.csv")[0]
    assert card.correct_answers == 3
    assert card.checks == 5


def test_good_and_bad_answers_share_one_visit(isolated_csv_dir: Path):
    save_set(pd.DataFrame([_words_row(), _words_row(verb="see")]), "visit_words.csv")
    add_new_file("visit_words.csv", "Visit")
    before = get_learning_set("visit_words.csv")
    assert before is not None
    assert before.use_count == 0
    assert before.last_used is None

    record_set_use("visit_words.csv")
    record_set_use("visit_words.csv")
    assert count_visits("visit_words.csv") == 2
    opened = get_learning_set("visit_words.csv")
    assert opened is not None
    assert opened.use_count == 0
    assert opened.last_used is not None
    entries = get_file_names_and_titles()
    assert entries[0][FilesColumns.USE_COUNT.value] == 2

    words = AppData("visit_words.csv")
    first = words.words.index[0]
    second = words.words.index[1]
    first_verb = words.words.at[first, PartsOfSpeech.VERB.value]
    second_verb = words.words.at[second, PartsOfSpeech.VERB.value]
    words.current_word_index = first
    words.good_answer_at_current_row()
    words.current_word_index = second
    words.bad_answer_at_current_row()

    visit = next(row for row in visits_for("visit_words.csv") if row.checks)
    assert visit.checks == 2
    assert visit.correct_answers == 1
    graded = {card.verb: card for card in cards_for("visit_words.csv")}
    assert graded[first_verb].checks == 1
    assert graded[first_verb].correct_answers == 1
    assert graded[second_verb].checks == 1
    assert graded[second_verb].correct_answers == 0

    set_default_progress("visit_words.csv")
    reset = {card.verb: card for card in cards_for("visit_words.csv")}
    assert reset[first_verb].checks == 0
    assert reset[first_verb].correct_answers == 0
    kept = next(row for row in visits_for("visit_words.csv") if row.checks)
    assert kept.checks == 2
    assert kept.correct_answers == 1
