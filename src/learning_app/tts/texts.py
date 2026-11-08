"""Normalize phrases and collect live set texts for TTS cache GC."""

from learning_app.data.constants import PartsOfSpeech, WordDefinitions

_CONTENT_COLUMNS = {member.value for member in PartsOfSpeech} | {
    member.value for member in WordDefinitions
}


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


def collect_speakable_texts() -> set[tuple[str, str]]:
    """Return phrases still spoken, paired with each set's TTS language.

    Statistics are ignored. Empty card text is ignored. The language is the
    set's ``tts_language`` override, or the app language when that column is
    NULL. The same spelling in two languages yields two pairs.

    Returns:
        Distinct ``(phrase, language)`` pairs stored on learning-set cards.
    """
    from learning_app.data.repository import iter_speakable_sets
    from learning_app.data.set_settings import language_for_set_file
    from learning_app.ui.tts_preferences import TtsPreferences

    texts: set[tuple[str, str]] = set()
    for learning_set, cards in iter_speakable_sets():
        if learning_set.source_file_name:
            language = language_for_set_file(learning_set.source_file_name)
        elif learning_set.tts_language:
            language = TtsPreferences.normalize_language(learning_set.tts_language)
        else:
            language = TtsPreferences.language
        for card in cards:
            for column in _CONTENT_COLUMNS:
                value = getattr(card, column, "") or ""
                if not str(value).strip():
                    continue
                for phrase in speakable_phrases(str(value)):
                    texts.add((phrase, language))
    return texts
