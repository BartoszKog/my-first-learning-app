"""SQLite storage for learning sets.

One engine per process. Each method opens a short session and closes it.
SQLite foreign keys are turned on for every connection so ``ON DELETE CASCADE``
runs. The database file sits beside ``csv_files/``, not inside it.

Screens still pass a ``*_words.csv`` / ``*_definitions.csv`` basename. That
name is stored in ``source_file_name`` and is how a row is found. The primary
key is the set UUID. ``migrated_csv_file`` remembers CSV files already copied
in, including after the set itself is deleted.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, func, select

from learning_app.data.constants import (
    CARD_ID_COLUMN,
    CHECKS_COLUMN,
    EXAMPLE_SENTENCE_COLUMN,
    FilesColumns,
    PartsOfSpeech,
    StatsColumns,
    WordDefinitions,
)
from learning_app.data.example_sentence import (
    example_sentence_error,
    normalize_example_sentence,
)
from learning_app.data.file_path_manager import FilePathManager
from learning_app.data.models import (
    Card,
    LearningSet,
    MigratedCsvFile,
    SetOpened,
    new_id,
)

_engine: Engine | None = None
_engine_path: str | None = None
_ready_path: str | None = None
_open_visits: dict[str, str] = {}

_WORD_FIELDS = [member.value for member in PartsOfSpeech]
_DEFINITION_FIELDS = [member.value for member in WordDefinitions]
_CONTENT_FIELDS = _WORD_FIELDS + _DEFINITION_FIELDS
_EXAMPLE_FIELDS = [EXAMPLE_SENTENCE_COLUMN]
_STAT_FIELDS = [member.value for member in StatsColumns]


def reset_storage() -> None:
    """Drop the cached engine so the next call opens the current database path."""
    global _engine, _engine_path, _ready_path
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _engine_path = None
    _ready_path = None
    _open_visits.clear()


def get_engine() -> Engine:
    """Return the process engine for the current ``FilePathManager`` database path."""
    global _engine, _engine_path, _ready_path
    path = FilePathManager.get_db_path()
    if _engine is not None and _engine_path == path:
        return _engine
    if _engine is not None:
        _engine.dispose()
    engine = _create_engine(path)
    _engine = engine
    _engine_path = path
    _ready_path = None
    return engine


def ensure_db() -> None:
    """Create tables on the current file, then copy any not-yet-migrated CSV sets."""
    global _ready_path
    engine = get_engine()
    path = _engine_path
    if _ready_path == path:
        return
    SQLModel.metadata.create_all(engine)
    _ensure_example_sentence_column(engine)
    _ensure_example_mode_column(engine)
    _migrate_csv_files(engine)
    _ready_path = path


def init_db() -> None:
    """Create the schema and run the startup CSV migration. Safe to call again."""
    ensure_db()


def load_set_frame(file_name: str) -> pd.DataFrame:
    """Return one set's cards ordered by ``position``.

    Empty content cells are missing values, matching the old CSV load. The
    frame carries ``card_id`` and ``checks``.

    Raises:
        FileNotFoundError: No set is stored under that basename.
    """
    ensure_db()
    basename = _basename(file_name)
    with _session() as session:
        learning_set = _set_by_name(session, basename)
        if learning_set is None:
            raise FileNotFoundError(basename)
        cards = session.exec(
            select(Card).where(Card.set_id == learning_set.id).order_by(Card.position)
        ).all()
        kind = learning_set.kind
        copied = [_detach_card(card) for card in cards]
    return _cards_to_frame(kind, copied)


def save_set_frame(data: pd.DataFrame, file_name: str) -> None:
    """Replace a set's cards from ``data``, creating the set when it is new.

    Existing card ids in ``CARD_ID_COLUMN`` are kept. Rows without one get a
    new id. A missing ``checks`` value on an existing card keeps the stored
    count. A new card without ``checks`` starts at 0. Metadata and overrides
    already stored on the set are left as they are.
    """
    ensure_db()
    basename = _basename(file_name)
    kind = _kind_from_name(basename)
    with _session() as session:
        learning_set = _set_by_name(session, basename)
        if learning_set is None:
            learning_set = LearningSet(
                kind=kind,
                title=_placeholder_title(basename),
                subtitle="",
                created_at=_utc_now(),
                source_file_name=basename,
            )
            session.add(learning_set)
            session.flush()
        _replace_cards(session, learning_set.id, data, kind)


def set_exists(file_name: str) -> bool:
    """Return whether a set with this basename is stored."""
    ensure_db()
    with _session() as session:
        return _set_by_name(session, _basename(file_name)) is not None


def list_catalog() -> list[dict]:
    """Return catalog dicts. ``use_count`` is the stored balance plus visit rows."""
    ensure_db()
    with _session() as session:
        sets = session.exec(select(LearningSet)).all()
        entries = []
        for learning_set in sets:
            if not learning_set.source_file_name:
                continue
            visits = session.exec(
                select(func.count()).select_from(SetOpened).where(SetOpened.set_id == learning_set.id)
            ).one()
            entries.append(_catalog_dict(learning_set, int(visits)))
        return entries


def list_basenames() -> list[str]:
    """Return stored set basenames."""
    return [entry[FilesColumns.FILE_NAME.value] for entry in list_catalog()]


def add_set(file_name: str, title: str, subtitle: str = "") -> None:
    """Register a set. An existing row keeps its cards, overrides, and counters."""
    ensure_db()
    basename = _basename(file_name)
    kind = _kind_from_name(basename)
    with _session() as session:
        learning_set = _set_by_name(session, basename)
        if learning_set is None:
            session.add(
                LearningSet(
                    kind=kind,
                    title=title,
                    subtitle=subtitle or "",
                    created_at=_utc_now(),
                    source_file_name=basename,
                )
            )
            return
        learning_set.title = title
        learning_set.subtitle = subtitle or ""
        session.add(learning_set)


def update_metadata(file_name: str, title: str, subtitle: str = "") -> None:
    """Change the title and subtitle of an existing set."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return
        learning_set.title = title
        learning_set.subtitle = subtitle or ""
        session.add(learning_set)


def delete_set(file_name: str) -> None:
    """Delete the set, its cards, and its visits. The migration marker stays."""
    ensure_db()
    basename = _basename(file_name)
    with _session() as session:
        learning_set = _set_by_name(session, basename)
        if learning_set is None:
            return
        session.delete(learning_set)
    _open_visits.pop(basename, None)


def reset_card_progress(file_name: str) -> None:
    """Zero card statistics, including ``checks``. Visit rows stay."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return
        cards = session.exec(select(Card).where(Card.set_id == learning_set.id)).all()
        for card in cards:
            card.correct_answers = 0
            card.good_answer = False
            card.good_answers_in_a_row = False
            card.word_to_learn = False
            card.checks = 0
            session.add(card)


def open_visit(file_name: str) -> str | None:
    """Record one entry into the learn screen.

    Sets ``last_used``, appends a ``SetOpened`` row at 0/0, and does not
    change ``use_count``. The new visit id stays current until the learn
    route leaves the stack.
    """
    ensure_db()
    basename = _basename(file_name)
    with _session() as session:
        learning_set = _set_by_name(session, basename)
        if learning_set is None:
            return None
        learning_set.last_used = _utc_now()
        visit = SetOpened(set_id=learning_set.id, opened_at=learning_set.last_used)
        session.add(learning_set)
        session.add(visit)
        session.flush()
        visit_id = visit.id
    _open_visits[basename] = visit_id
    return visit_id


def current_visit_id(file_name: str) -> str | None:
    """Return the visit opened for this set and not yet left."""
    return _open_visits.get(_basename(file_name))


def retain_open_visits(basenames: set[str]) -> None:
    """Forget visit ids whose learn route is no longer on the stack."""
    allowed = {_basename(name) for name in basenames}
    for key in list(_open_visits):
        if key not in allowed:
            _open_visits.pop(key, None)


def save_card_answer(card_id: str, row: pd.Series, *, correct: bool, visit_id: str | None) -> None:
    """Write one card's statistics and, when a visit is open, that visit's counters.

    ``row`` already contains the card's new ``checks``. The visit counter is
    incremented here, once per graded Check.
    """
    ensure_db()
    with _session() as session:
        card = session.get(Card, str(card_id))
        if card is None:
            return
        _apply_progress(card, row)
        session.add(card)
        if not visit_id:
            return
        visit = session.get(SetOpened, visit_id)
        if visit is None or visit.set_id != card.set_id:
            return
        visit.checks += 1
        if correct:
            visit.correct_answers += 1
        session.add(visit)


def get_learning_set(file_name: str) -> LearningSet | None:
    """Return a detached set row, or ``None`` when the basename is unknown."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return None
        session.expunge(learning_set)
        return learning_set


def write_overrides(file_name: str, values: dict[str, object], *, clear_others: bool) -> None:
    """Store override columns. ``None`` means inherit the app setting."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return
        if clear_others:
            _clear_override_columns(learning_set)
        for column, value in values.items():
            setattr(learning_set, column, value)
        session.add(learning_set)


def iter_speakable_sets() -> list[tuple[LearningSet, list[Card]]]:
    """Return every set with its cards, detached from the session."""
    ensure_db()
    with _session() as session:
        sets = session.exec(select(LearningSet)).all()
        result = []
        for learning_set in sets:
            cards = session.exec(select(Card).where(Card.set_id == learning_set.id)).all()
            session.expunge(learning_set)
            for card in cards:
                session.expunge(card)
            result.append((learning_set, list(cards)))
        return result


def export_set_csv_bytes(file_name: str) -> bytes:
    """Build a set CSV, including ``checks`` and omitting the card id."""
    frame = load_set_frame(file_name)
    if CARD_ID_COLUMN in frame.columns:
        frame = frame.drop(columns=[CARD_ID_COLUMN])
    return frame.to_csv(index=True).encode("utf-8")


def count_migrated(file_name: str) -> bool:
    """Return whether this CSV basename was already copied in."""
    ensure_db()
    with _session() as session:
        return session.get(MigratedCsvFile, _basename(file_name)) is not None


def count_sets() -> int:
    """Return how many learning sets are stored."""
    ensure_db()
    with _session() as session:
        return int(session.exec(select(func.count()).select_from(LearningSet)).one())


def count_visits(file_name: str) -> int:
    """Return how many ``SetOpened`` rows a set has."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return 0
        return int(
            session.exec(
                select(func.count()).select_from(SetOpened).where(SetOpened.set_id == learning_set.id)
            ).one()
        )


def visits_for(file_name: str) -> list[SetOpened]:
    """Return a set's visit rows, oldest first."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return []
        rows = session.exec(
            select(SetOpened)
            .where(SetOpened.set_id == learning_set.id)
            .order_by(SetOpened.opened_at)
        ).all()
        for row in rows:
            session.expunge(row)
        return list(rows)


def cards_for(file_name: str) -> list[Card]:
    """Return a set's cards ordered by position."""
    ensure_db()
    with _session() as session:
        learning_set = _set_by_name(session, _basename(file_name))
        if learning_set is None:
            return []
        rows = session.exec(
            select(Card).where(Card.set_id == learning_set.id).order_by(Card.position)
        ).all()
        for row in rows:
            session.expunge(row)
        return list(rows)


def _create_engine(path: str) -> Engine:
    from sqlalchemy import create_engine

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        "sqlite:///" + Path(path).resolve().as_posix(),
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


@contextmanager
def _session():
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _basename(file_name: str) -> str:
    return os.path.basename(str(file_name))


def _kind_from_name(file_name: str) -> str:
    from learning_app.data.app_data import get_kind_of_file_and_validate

    return get_kind_of_file_and_validate(file_name)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def _placeholder_title(basename: str) -> str:
    for suffix in ("_words.csv", "_definitions.csv"):
        if basename.endswith(suffix):
            stem = basename[: -len(suffix)]
            return stem.capitalize() if stem else basename
    return basename


def _set_by_name(session: Session, basename: str) -> LearningSet | None:
    return session.exec(
        select(LearningSet).where(LearningSet.source_file_name == basename)
    ).first()


def _catalog_dict(learning_set: LearningSet, visits: int) -> dict:
    return {
        FilesColumns.FILE_NAME.value: learning_set.source_file_name,
        FilesColumns.TITLE.value: learning_set.title,
        FilesColumns.SUBTITLE.value: learning_set.subtitle or "",
        FilesColumns.CREATED_AT.value: _iso(learning_set.created_at),
        FilesColumns.LAST_USED.value: _iso(learning_set.last_used) if learning_set.last_used else "",
        FilesColumns.USE_COUNT.value: int(learning_set.use_count or 0) + visits,
    }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()


def _detach_card(card: Card) -> Card:
    return Card(
        id=card.id,
        set_id=card.set_id,
        position=card.position,
        verb=card.verb,
        person=card.person,
        thing=card.thing,
        adjective=card.adjective,
        adverb=card.adverb,
        definition=card.definition,
        word=card.word,
        example_sentence=card.example_sentence,
        correct_answers=card.correct_answers,
        good_answer=card.good_answer,
        good_answers_in_a_row=card.good_answers_in_a_row,
        word_to_learn=card.word_to_learn,
        checks=card.checks,
    )


def _cards_to_frame(kind: str, cards: list[Card]) -> pd.DataFrame:
    content = _WORD_FIELDS if kind == "words" else _DEFINITION_FIELDS + _EXAMPLE_FIELDS
    rows = []
    for card in cards:
        row: dict[str, object] = {}
        for column in content:
            text = getattr(card, column) or ""
            row[column] = text if text != "" else pd.NA
        row[StatsColumns.CORRECT_ANSWERS.value] = int(card.correct_answers)
        row[StatsColumns.GOOD_ANSWER.value] = bool(card.good_answer)
        row[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = bool(card.good_answers_in_a_row)
        row[StatsColumns.WORD_TO_LEARN.value] = bool(card.word_to_learn)
        row[CHECKS_COLUMN] = int(card.checks)
        row[CARD_ID_COLUMN] = card.id
        rows.append(row)
    frame = pd.DataFrame(rows, columns=[*content, *_STAT_FIELDS, CHECKS_COLUMN, CARD_ID_COLUMN])
    if cards:
        frame.index = [card.position for card in cards]
    return frame


def _replace_cards(session: Session, set_id: str, data: pd.DataFrame, kind: str) -> None:
    existing = {
        card.id: card
        for card in session.exec(select(Card).where(Card.set_id == set_id)).all()
    }
    kept_ids: list[str] = []
    ordered_rows: list[tuple[str, pd.Series, Card | None]] = []
    has_id_column = CARD_ID_COLUMN in data.columns
    for _, row in data.iterrows():
        card_id = _existing_card_id(row) if has_id_column else None
        previous = existing.get(card_id) if card_id else None
        if previous is None:
            card_id = new_id()
        kept_ids.append(card_id)
        ordered_rows.append((card_id, row, previous))

    for card_id, card in existing.items():
        if card_id not in kept_ids:
            session.delete(card)
    session.flush()

    for position, (card_id, row, previous) in enumerate(ordered_rows):
        if previous is not None and previous.id == card_id:
            card = previous
        else:
            card = Card(id=card_id, set_id=set_id, position=-(position + 1))
        card.set_id = set_id
        card.position = -(position + 1)
        _apply_content(card, row, kind)
        _apply_progress(card, row, previous=previous)
        session.add(card)
    session.flush()
    for position, (card_id, _, _) in enumerate(ordered_rows):
        card = session.get(Card, card_id)
        if card is not None:
            card.position = position
            session.add(card)


def _existing_card_id(row: pd.Series) -> str | None:
    if CARD_ID_COLUMN not in row.index:
        return None
    value = row[CARD_ID_COLUMN]
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text or None


def _apply_content(card: Card, row: pd.Series, kind: str) -> None:
    own = _WORD_FIELDS if kind == "words" else _DEFINITION_FIELDS
    for column in _CONTENT_FIELDS:
        if column in own and column in row.index:
            setattr(card, column, _content_text(row[column]))
        else:
            setattr(card, column, "")
    if kind == "definitions" and EXAMPLE_SENTENCE_COLUMN in row.index:
        card.example_sentence = _example_sentence_text(row[EXAMPLE_SENTENCE_COLUMN])
    else:
        card.example_sentence = ""


def _example_sentence_text(value: object) -> str:
    text = _content_text(value).strip()
    if text == "" or example_sentence_error(text):
        return text
    return normalize_example_sentence(text)


def _ensure_example_sentence_column(engine: Engine) -> None:
    """Add ``example_sentence`` when the card table predates that column.

    ``create_all`` creates missing tables and does not alter an existing
    ``card`` table. A database from before this column gets one ``ALTER``.
    """
    with engine.begin() as connection:
        rows = connection.exec_driver_sql("PRAGMA table_info(card)").fetchall()
        names = {row[1] for row in rows}
        if not names or EXAMPLE_SENTENCE_COLUMN in names:
            return
        connection.exec_driver_sql(
            "ALTER TABLE card ADD COLUMN example_sentence TEXT NOT NULL DEFAULT ''"
        )


def _ensure_example_mode_column(engine: Engine) -> None:
    """Add the nullable ``example_mode`` override to an older ``learning_set`` table."""
    with engine.begin() as connection:
        rows = connection.exec_driver_sql("PRAGMA table_info(learning_set)").fetchall()
        names = {row[1] for row in rows}
        if not names or FilesColumns.EXAMPLE_MODE.value in names:
            return
        connection.exec_driver_sql("ALTER TABLE learning_set ADD COLUMN example_mode TEXT")


def _apply_progress(card: Card, row: pd.Series, previous: Card | None = None) -> None:
    card.correct_answers = _as_int(row.get(StatsColumns.CORRECT_ANSWERS.value), 0)
    card.good_answer = _as_bool(row.get(StatsColumns.GOOD_ANSWER.value), False)
    card.good_answers_in_a_row = _as_bool(row.get(StatsColumns.GOOD_ANSWERS_IN_A_ROW.value), False)
    card.word_to_learn = _as_bool(row.get(StatsColumns.WORD_TO_LEARN.value), False)
    if CHECKS_COLUMN not in row.index:
        card.checks = previous.checks if previous is not None else 0
        return
    raw = row[CHECKS_COLUMN]
    if _is_missing(raw):
        card.checks = previous.checks if previous is not None else 0
        return
    card.checks = _as_int(raw, 0)


def _content_text(value: object) -> str:
    if _is_missing(value):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return str(value)


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _as_int(value: object, default: int) -> int:
    if _is_missing(value):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if _is_missing(value):
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(int(value))
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return default


def _clear_override_columns(learning_set: LearningSet) -> None:
    learning_set.tts_language = None
    learning_set.tts_auto_speak = None
    learning_set.speakers_word_formations = None
    learning_set.speakers_word = None
    learning_set.speakers_definition = None
    learning_set.retry_until_correct = None
    learning_set.queue_size = None
    learning_set.example_mode = None


def _migrate_csv_files(engine: Engine) -> None:
    """Copy each catalogued CSV that is not already listed in ``migrated_csv_file``."""
    from learning_app.data.app_data import (
        ensure_files_catalog_columns,
        read_catalog_csv,
    )
    from learning_app.data.set_settings import db_override_from_text, override_cell_text

    catalog_path = FilePathManager.get_files_data_path()
    if not os.path.exists(catalog_path):
        return
    try:
        catalog = ensure_files_catalog_columns(read_catalog_csv(catalog_path), persist=False)
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError, ValueError):
        return

    for _, catalog_row in catalog.iterrows():
        basename = _basename(str(catalog_row[FilesColumns.FILE_NAME.value]))
        with Session(engine) as session:
            if session.get(MigratedCsvFile, basename) is not None:
                continue
        set_path = FilePathManager.get_csv_path(basename)
        if not os.path.exists(set_path):
            continue
        loaded = _read_set_for_migration(basename, set_path)
        if loaded is None:
            continue
        kind, frame = loaded
        _import_catalog_row(engine, catalog_row, frame, basename, kind, db_override_from_text, override_cell_text)


def _read_set_for_migration(basename: str, set_path: str):
    """Return ``(kind, frame)`` or ``None`` when this CSV cannot be copied."""
    from learning_app.data.app_data import (
        get_kind_of_file_and_validate,
        read_set_csv,
        stringify_content_columns,
    )

    if not basename.endswith(("_words.csv", "_definitions.csv")):
        return None
    try:
        kind = get_kind_of_file_and_validate(basename)
        frame = stringify_content_columns(read_set_csv(set_path, index_col=0))
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError, ValueError):
        return None
    return kind, frame


def _import_catalog_row(engine, catalog_row, frame, basename, kind, db_override_from_text, override_cell_text) -> None:
    from learning_app.data.constants import FilesColumns as Columns

    with Session(engine) as session:
        if session.get(MigratedCsvFile, basename) is not None:
            return
        # A set created in the app has no migration marker. Mark the CSV done
        # and keep the live row; inserting again would hit the unique name.
        if _set_by_name(session, basename) is not None:
            session.add(MigratedCsvFile(file_name=basename))
            session.commit()
            return

        created = _parse_datetime(catalog_row.get(Columns.CREATED_AT.value)) or _utc_now()
        learning_set = LearningSet(
            kind=kind,
            title=_catalog_title(catalog_row, basename),
            subtitle=_catalog_subtitle(catalog_row),
            created_at=created,
            last_used=_parse_datetime(catalog_row.get(Columns.LAST_USED.value)),
            use_count=_as_int(catalog_row.get(Columns.USE_COUNT.value), 0),
            source_file_name=basename,
            tts_language=db_override_from_text(
                Columns.TTS_LANGUAGE.value,
                override_cell_text(catalog_row.get(Columns.TTS_LANGUAGE.value)),
                kind,
            ),
            tts_auto_speak=db_override_from_text(
                Columns.TTS_AUTO_SPEAK.value,
                override_cell_text(catalog_row.get(Columns.TTS_AUTO_SPEAK.value)),
                kind,
            ),
            speakers_word_formations=db_override_from_text(
                Columns.SPEAKERS_WORD_FORMATIONS.value,
                override_cell_text(catalog_row.get(Columns.SPEAKERS_WORD_FORMATIONS.value)),
                kind,
            ),
            speakers_word=db_override_from_text(
                Columns.SPEAKERS_WORD.value,
                override_cell_text(catalog_row.get(Columns.SPEAKERS_WORD.value)),
                kind,
            ),
            speakers_definition=db_override_from_text(
                Columns.SPEAKERS_DEFINITION.value,
                override_cell_text(catalog_row.get(Columns.SPEAKERS_DEFINITION.value)),
                kind,
            ),
            retry_until_correct=db_override_from_text(
                Columns.RETRY_UNTIL_CORRECT.value,
                override_cell_text(catalog_row.get(Columns.RETRY_UNTIL_CORRECT.value)),
                kind,
            ),
            queue_size=db_override_from_text(
                Columns.QUEUE_SIZE.value,
                override_cell_text(catalog_row.get(Columns.QUEUE_SIZE.value)),
                kind,
            ),
            example_mode=db_override_from_text(
                Columns.EXAMPLE_MODE.value,
                override_cell_text(catalog_row.get(Columns.EXAMPLE_MODE.value)),
                kind,
            ),
        )
        session.add(learning_set)
        session.flush()
        for position, (_, row) in enumerate(frame.iterrows()):
            correct = _as_int(
                row.get(StatsColumns.CORRECT_ANSWERS.value)
                if StatsColumns.CORRECT_ANSWERS.value in row.index
                else 0,
                0,
            )
            card = Card(
                set_id=learning_set.id,
                position=position,
                correct_answers=correct,
                good_answer=_as_bool(
                    row.get(StatsColumns.GOOD_ANSWER.value) if StatsColumns.GOOD_ANSWER.value in row.index else False,
                    False,
                ),
                good_answers_in_a_row=_as_bool(
                    row.get(StatsColumns.GOOD_ANSWERS_IN_A_ROW.value)
                    if StatsColumns.GOOD_ANSWERS_IN_A_ROW.value in row.index
                    else False,
                    False,
                ),
                word_to_learn=_as_bool(
                    row.get(StatsColumns.WORD_TO_LEARN.value) if StatsColumns.WORD_TO_LEARN.value in row.index else False,
                    False,
                ),
                checks=_migrated_checks(row, correct),
            )
            _apply_content(card, row, kind)
            session.add(card)
        session.add(MigratedCsvFile(file_name=basename))
        session.commit()


def _migrated_checks(row: pd.Series, correct: int) -> int:
    """Keep a CSV ``checks`` column; otherwise copy ``correct_answers``.

    Same rule as ``CSVProcessor.__ensure_checks_column`` when statistics are kept.
    """
    if CHECKS_COLUMN in row.index:
        return _as_int(row.get(CHECKS_COLUMN), 0)
    return correct


def _catalog_title(catalog_row: pd.Series, basename: str) -> str:
    raw = catalog_row.get(FilesColumns.TITLE.value)
    if _is_missing(raw):
        return _placeholder_title(basename)
    text = str(raw).strip()
    return text or _placeholder_title(basename)


def _catalog_subtitle(catalog_row: pd.Series) -> str:
    raw = catalog_row.get(FilesColumns.SUBTITLE.value)
    if _is_missing(raw):
        return ""
    return str(raw)


def _parse_datetime(value: object) -> datetime | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
