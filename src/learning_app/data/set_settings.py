"""Per-set learning and TTS overrides stored as empty-or-set cells in ``files.csv``.

An empty cell inherits the matching app setting. A non-empty cell is the set's
own value. Columns that belong to the other set kind stay empty.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import pandas as pd

from learning_app.data.constants import FilesColumns

_WORDS = "words"
_DEFINITIONS = "definitions"

_ALL_OVERRIDE_COLUMNS = (
    FilesColumns.TTS_LANGUAGE.value,
    FilesColumns.TTS_AUTO_SPEAK.value,
    FilesColumns.SPEAKERS_WORD_FORMATIONS.value,
    FilesColumns.SPEAKERS_WORD.value,
    FilesColumns.SPEAKERS_DEFINITION.value,
    FilesColumns.RETRY_UNTIL_CORRECT.value,
    FilesColumns.QUEUE_SIZE.value,
)

_WORDS_COLUMNS = (
    FilesColumns.TTS_LANGUAGE.value,
    FilesColumns.SPEAKERS_WORD_FORMATIONS.value,
    FilesColumns.RETRY_UNTIL_CORRECT.value,
    FilesColumns.QUEUE_SIZE.value,
)

_DEFINITIONS_COLUMNS = (
    FilesColumns.TTS_LANGUAGE.value,
    FilesColumns.TTS_AUTO_SPEAK.value,
    FilesColumns.SPEAKERS_WORD.value,
    FilesColumns.SPEAKERS_DEFINITION.value,
    FilesColumns.RETRY_UNTIL_CORRECT.value,
    FilesColumns.QUEUE_SIZE.value,
)

_TRUE_TOKENS = {"true", "1", "on", "yes"}


@dataclass(frozen=True)
class EffectiveSetSettings:
    """Settings that apply to one set after filling blanks from the app.

    Attributes:
        kind: ``"words"`` or ``"definitions"``.
        language: gTTS language code.
        auto_speak: Pronounce the definition-card word after Check.
        speakers_word_formations: Speaker buttons on word-formation list cards.
        speakers_word: Speaker button on a definition card's word.
        speakers_definition: Speaker button on a definition card's definition.
        retry_until_correct: Require a correct retype before the queue advances.
        queue_size: Maximum items drawn into the next practice round.
        uses_app_defaults: Every override column for this kind is empty.
    """

    kind: str
    language: str
    auto_speak: bool
    speakers_word_formations: bool
    speakers_word: bool
    speakers_definition: bool
    retry_until_correct: bool
    queue_size: int
    uses_app_defaults: bool


def columns_for_kind(kind: str) -> tuple[str, ...]:
    """Return catalog columns that a set of ``kind`` may override."""
    if kind == _DEFINITIONS:
        return _DEFINITIONS_COLUMNS
    return _WORDS_COLUMNS


def read_override_cells(file_name: str) -> dict[str, str]:
    """Return stored override text for ``file_name``.

    Missing catalog rows and blank cells are empty strings. Empty means the
    set inherits the app setting for that column.

    Args:
        file_name: Set basename or path.
    """
    blank = {column: "" for column in _ALL_OVERRIDE_COLUMNS}
    row = _catalog_row(file_name)
    if row is None:
        return blank
    for column in _ALL_OVERRIDE_COLUMNS:
        blank[column] = _cell_text(row[column]) if column in row.index else ""
    return blank


def effective_set_settings(file_name: str) -> EffectiveSetSettings:
    """Resolve one set's settings, using app defaults for empty cells.

    Non-empty booleans are explicit (``false`` stays off). A non-empty queue
    size is clamped to the range for the set's kind; unparseable text falls
    back to the app default. An unknown language code becomes English.

    Args:
        file_name: Set basename or path ending in ``_words.csv`` or
            ``_definitions.csv``.
    """
    from learning_app.data.app_data import get_kind_of_file_and_validate
    from learning_app.ui.learn_preferences import LearnPreferences
    from learning_app.ui.tts_preferences import TtsPreferences

    kind = get_kind_of_file_and_validate(file_name)
    cells = read_override_cells(file_name)
    applicable = columns_for_kind(kind)

    language_cell = cells[FilesColumns.TTS_LANGUAGE.value]
    language = (
        TtsPreferences.normalize_language(language_cell)
        if language_cell
        else TtsPreferences.language
    )

    if kind == _DEFINITIONS:
        queue_default = LearnPreferences.definitions_queue_size
        auto_speak = _bool_or_default(
            cells[FilesColumns.TTS_AUTO_SPEAK.value],
            TtsPreferences.auto_speak_definitions,
        )
        speakers_word = _bool_or_default(
            cells[FilesColumns.SPEAKERS_WORD.value],
            TtsPreferences.speakers_word,
        )
        speakers_definition = _bool_or_default(
            cells[FilesColumns.SPEAKERS_DEFINITION.value],
            TtsPreferences.speakers_definition,
        )
        speakers_word_formations = TtsPreferences.speakers_word_formations
    else:
        queue_default = LearnPreferences.word_formations_queue_size
        auto_speak = TtsPreferences.auto_speak_definitions
        speakers_word = TtsPreferences.speakers_word
        speakers_definition = TtsPreferences.speakers_definition
        speakers_word_formations = _bool_or_default(
            cells[FilesColumns.SPEAKERS_WORD_FORMATIONS.value],
            TtsPreferences.speakers_word_formations,
        )
    queue_size = _queue_or_default(
        cells[FilesColumns.QUEUE_SIZE.value],
        kind=kind,
        default=queue_default,
    )

    return EffectiveSetSettings(
        kind=kind,
        language=language,
        auto_speak=auto_speak,
        speakers_word_formations=speakers_word_formations,
        speakers_word=speakers_word,
        speakers_definition=speakers_definition,
        retry_until_correct=_bool_or_default(
            cells[FilesColumns.RETRY_UNTIL_CORRECT.value],
            LearnPreferences.retry_until_correct,
        ),
        queue_size=queue_size,
        uses_app_defaults=all(cells[column] == "" for column in applicable),
    )


def language_for_set_file(file_name: str) -> str:
    """Return the language used when this set's phrases are spoken."""
    return effective_set_settings(file_name).language


def catalog_title(file_name: str) -> str:
    """Return the display title for ``file_name`` from ``files.csv``.

    Falls back to the basename when the catalog row is missing or the title
    cell is blank.
    """
    row = _catalog_row(file_name)
    if row is None or FilesColumns.TITLE.value not in row.index:
        return os.path.basename(file_name)
    title = _cell_text(row[FilesColumns.TITLE.value])
    return title or os.path.basename(file_name)


def enable_set_overrides(file_name: str) -> None:
    """Copy the current app settings into this set's override columns.

    Columns for the other kind are cleared. After this call the set no longer
    follows later changes to the app settings.

    Args:
        file_name: Set basename or path present in ``files.csv``.
    """
    from learning_app.data.app_data import get_kind_of_file_and_validate

    kind = get_kind_of_file_and_validate(file_name)
    _write_overrides(file_name, _global_values(kind), clear_others=True)


def clear_set_overrides(file_name: str) -> None:
    """Blank every override column so the set uses app settings again.

    Args:
        file_name: Set basename or path present in ``files.csv``.
    """
    _write_overrides(file_name, {}, clear_others=True)


def set_override_value(file_name: str, column: str, value: str) -> None:
    """Store one override cell when ``column`` applies to this set's kind.

    Args:
        file_name: Set basename or path present in ``files.csv``.
        column: A ``FilesColumns`` override name.
        value: Explicit stored text, such as ``"true"``, ``"pl"``, or ``"8"``.
    """
    from learning_app.data.app_data import get_kind_of_file_and_validate

    kind = get_kind_of_file_and_validate(file_name)
    if column not in columns_for_kind(kind):
        return
    _write_overrides(file_name, {column: value}, clear_others=False)


def _global_values(kind: str) -> dict[str, str]:
    from learning_app.ui.learn_preferences import LearnPreferences
    from learning_app.ui.tts_preferences import TtsPreferences

    if kind == _DEFINITIONS:
        queue = LearnPreferences.definitions_queue_size
        return {
            FilesColumns.TTS_LANGUAGE.value: TtsPreferences.language,
            FilesColumns.TTS_AUTO_SPEAK.value: _bool_text(
                TtsPreferences.auto_speak_definitions
            ),
            FilesColumns.SPEAKERS_WORD.value: _bool_text(TtsPreferences.speakers_word),
            FilesColumns.SPEAKERS_DEFINITION.value: _bool_text(
                TtsPreferences.speakers_definition
            ),
            FilesColumns.RETRY_UNTIL_CORRECT.value: _bool_text(
                LearnPreferences.retry_until_correct
            ),
            FilesColumns.QUEUE_SIZE.value: str(queue),
        }
    return {
        FilesColumns.TTS_LANGUAGE.value: TtsPreferences.language,
        FilesColumns.SPEAKERS_WORD_FORMATIONS.value: _bool_text(
            TtsPreferences.speakers_word_formations
        ),
        FilesColumns.RETRY_UNTIL_CORRECT.value: _bool_text(
            LearnPreferences.retry_until_correct
        ),
        FilesColumns.QUEUE_SIZE.value: str(LearnPreferences.word_formations_queue_size),
    }


def _write_overrides(
    file_name: str,
    values: dict[str, str],
    *,
    clear_others: bool,
) -> None:
    from learning_app.data.app_data import ensure_files_catalog_columns, read_catalog_csv
    from learning_app.data.file_path_manager import FilePathManager

    path = FilePathManager.get_files_data_path()
    if not os.path.exists(path):
        return
    frame = ensure_files_catalog_columns(read_catalog_csv(path))
    basename = os.path.basename(file_name)
    mask = frame[FilesColumns.FILE_NAME.value] == basename
    if not mask.any():
        return
    for column in _ALL_OVERRIDE_COLUMNS:
        frame[column] = frame[column].astype("object")
        if clear_others:
            frame.loc[mask, column] = ""
    for column, value in values.items():
        frame.loc[mask, column] = value
    frame.to_csv(path, index=False)


def _catalog_row(file_name: str) -> pd.Series | None:
    from learning_app.data.app_data import ensure_files_catalog_columns, read_catalog_csv
    from learning_app.data.file_path_manager import FilePathManager

    path = FilePathManager.get_files_data_path()
    if not os.path.exists(path):
        return None
    frame = ensure_files_catalog_columns(read_catalog_csv(path))
    basename = os.path.basename(file_name)
    mask = frame[FilesColumns.FILE_NAME.value] == basename
    if not mask.any():
        return None
    return frame.loc[mask].iloc[0]


def _cell_text(value: object) -> str:
    """Return catalog text, undoing pandas bool and integer inference.

    ``read_csv`` may turn ``false`` into a numpy bool and ``7`` beside a blank
    cell into ``7.0``. Callers still see ``"false"`` and ``"7"``.
    """
    if isinstance(value, str):
        text = value.strip()
        if text.lower() == "nan":
            return ""
        if text.lower() in {"true", "false"}:
            return text.lower()
        return text
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    item = value.item() if hasattr(value, "item") else value
    if isinstance(item, bool):
        return _bool_text(item)
    if isinstance(item, int) and not isinstance(item, bool):
        return str(item)
    if isinstance(item, float) and item.is_integer():
        return str(int(item))
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    if text.lower() in {"true", "false"}:
        return text.lower()
    return text


def _bool_text(enabled: bool) -> str:
    return "true" if enabled else "false"


def _bool_or_default(raw: str, default: bool) -> bool:
    if raw == "":
        return bool(default)
    return raw.strip().lower() in _TRUE_TOKENS


def _queue_or_default(raw: str, *, kind: str, default: int) -> int:
    from learning_app.ui.learn_preferences import LearnPreferences

    if raw == "":
        return int(default)
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return int(default)
    if not number.is_integer():
        return int(default)
    value = int(number)
    if kind == _DEFINITIONS:
        minimum = LearnPreferences.DEFINITIONS_QUEUE_MIN
        maximum = LearnPreferences.DEFINITIONS_QUEUE_MAX
    else:
        minimum = LearnPreferences.WORD_FORMATIONS_QUEUE_MIN
        maximum = LearnPreferences.WORD_FORMATIONS_QUEUE_MAX
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value
