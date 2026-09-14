"""Normalize phrases and collect live set texts for TTS cache GC."""

from pathlib import Path

import pandas as pd

from learning_app.data.constants import PartsOfSpeech, WordDefinitions
from learning_app.data.app_data import read_set_csv
from learning_app.data.file_path_manager import FilePathManager

_CONTENT_COLUMNS = {member.value for member in PartsOfSpeech} | {
    member.value for member in WordDefinitions
}
_SET_SUFFIXES = ("_words.csv", "_definitions.csv")


def normalize_text(text: str) -> str:
    """Strip and collapse whitespace so cache keys stay stable.

    Args:
        text: Raw cell value from a learning set.

    Returns:
        Normalized phrase, or an empty string when nothing remains.
    """
    return " ".join(str(text).split())


def speakable_phrases(text: str) -> list[str]:
    """Split a cell on ``/`` and return each normalized member.

    Empty members are dropped. Order is preserved and duplicates are removed.
    A cell such as ``go/goes/went`` becomes three phrases. A cell without
    slashes is a one-item list.

    Args:
        text: Raw cell value from a learning set.

    Returns:
        Distinct normalized phrases to synthesize and keep in the TTS cache.
    """
    phrases: list[str] = []
    seen: set[str] = set()
    for part in str(text).split("/"):
        normalized = normalize_text(part)
        if normalized and normalized not in seen:
            seen.add(normalized)
            phrases.append(normalized)
    return phrases


def collect_speakable_texts() -> set[str]:
    """Return normalized content phrases still present in set CSVs.

    Statistics columns and empty cells are ignored. Unreadable set files are
    skipped so GC can still run after a partial catalog failure.

    Returns:
        Distinct slash-split phrases from ``*_words.csv`` and
        ``*_definitions.csv`` under the CSV directory.
    """
    csv_dir = Path(FilePathManager.get_csv_dir())
    texts: set[str] = set()
    if not csv_dir.is_dir():
        return texts

    for path in csv_dir.iterdir():
        if not path.name.endswith(_SET_SUFFIXES):
            continue
        texts.update(_texts_from_set_csv(path))
    return texts


def _texts_from_set_csv(path: Path) -> set[str]:
    try:
        frame = read_set_csv(path, index_col=0)
    except (OSError, UnicodeError, ValueError, pd.errors.ParserError):
        return set()

    columns = [column for column in frame.columns if column in _CONTENT_COLUMNS]
    if not columns:
        return set()

    texts: set[str] = set()
    for value in frame[columns].to_numpy().ravel():
        if pd.isna(value):
            continue
        texts.update(speakable_phrases(str(value)))
    return texts
