"""Parse a definition example whose answers sit inside braces.

``I {keep} him {in line}.`` stores the sentence and its gaps in one string.
Braces do not nest. ``/`` inside one pair is another accepted form of that
same gap, matching the slash convention on ``word``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product

MAX_GAPS = 4
"""Most gaps one example sentence may contain."""


class ExampleSentenceError(ValueError):
    """The example sentence breaks the gap rules."""


@dataclass(frozen=True)
class ExamplePiece:
    """One literal or gap segment of an example sentence.

    Gap text is the trimmed interior, without the surrounding braces.
    """

    text: str
    is_gap: bool


def example_sentence_error(text: str) -> str | None:
    """Return a validation message, or ``None`` when the example is usable.

    A blank sentence is usable: the card has no example.

    Args:
        text: Raw field or cell value.

    Returns:
        The first rule the sentence breaks, or ``None``.
    """
    try:
        _checked_pieces(text)
    except ExampleSentenceError as exc:
        return str(exc)
    return None


def normalize_example_sentence(text: str) -> str:
    """Return the sentence with the outer text and each gap trimmed.

    Args:
        text: Raw field or cell value.

    Returns:
        ``""`` when the sentence is blank. Otherwise the sentence with
        trimmed gap interiors.

    Raises:
        ExampleSentenceError: The sentence is not blank and breaks a rule.
    """
    pieces = _checked_pieces(text)
    return _join(pieces, gaps_as_braces=False)


def preview_parts(text: str) -> list[ExamplePiece]:
    """Split a sentence into literal text and gap interiors for a preview.

    A blank sentence yields no pieces. A sentence that breaks the rules
    yields one literal piece with the original text, so the preview can
    show what was typed.

    Args:
        text: Raw field value, including text that is still incomplete.

    Returns:
        Pieces in left-to-right order. Gap pieces do not include braces.
    """
    if text.strip() == "":
        return []
    try:
        return _checked_pieces(text)
    except ExampleSentenceError:
        return [ExamplePiece(text, False)]


def gap_answers(text: str) -> list[str]:
    """Return each gap's trimmed interior, from left to right.

    Args:
        text: Example sentence.

    Returns:
        Gap texts. A blank sentence returns an empty list.

    Raises:
        ExampleSentenceError: The sentence is not blank and breaks a rule.
    """
    return [piece.text for piece in _checked_pieces(text) if piece.is_gap]


def cloze_sentence(text: str) -> str:
    """Return the sentence with each gap replaced by ``{}``.

    Args:
        text: Example sentence.

    Returns:
        The cloze form. A blank sentence returns ``""``.

    Raises:
        ExampleSentenceError: The sentence is not blank and breaks a rule.
    """
    return _join(_checked_pieces(text), gaps_as_braces=True)


def accepted_forms(gap_text: str) -> list[str]:
    """Split one gap on ``/`` into the forms that fill it.

    Empty pieces are dropped. ``keep/keeps`` becomes ``keep`` and ``keeps``.

    Args:
        gap_text: Trimmed interior of one gap.

    Returns:
        Accepted forms in the stored order.
    """
    return [part.strip() for part in gap_text.split("/") if part.strip()]


def display_form(gap_text: str) -> str:
    """Return the form shown when a gap is filled in.

    Args:
        gap_text: Trimmed interior of one gap.

    Returns:
        The first accepted form, or ``gap_text`` when it has none.
    """
    forms = accepted_forms(gap_text)
    return forms[0] if forms else gap_text


def filled_sentence(text: str) -> str:
    """Return the sentence with each gap replaced by its display form.

    Args:
        text: Example sentence.

    Returns:
        The filled sentence. A blank or invalid sentence returns ``""``.
    """
    if text.strip() == "":
        return ""
    try:
        pieces = _checked_pieces(text)
    except ExampleSentenceError:
        return ""
    return "".join(display_form(piece.text) if piece.is_gap else piece.text for piece in pieces)


def matches_gap_answers(typed: str, text: str) -> bool:
    """Return whether ``typed`` fills every gap of ``text`` in order.

    Gaps may be separated by spaces, commas, or semicolons. Case is ignored.
    Each gap accepts any of its ``/`` forms. ``I {keep} him {in line}.``
    accepts ``keep in line`` and ``keep, in line``.

    Args:
        typed: The learner's answer.
        text: Example sentence.

    Returns:
        ``False`` for a blank or invalid sentence.
    """
    try:
        gaps = gap_answers(text)
    except ExampleSentenceError:
        return False
    if not gaps:
        return False
    answer = _loose_answer(typed)
    if answer == "":
        return False
    form_lists = [accepted_forms(gap) for gap in gaps]
    return any(
        _loose_answer(" ".join(combination)) == answer
        for combination in product(*form_lists)
    )


def _loose_answer(text: str) -> str:
    return " ".join(re.split(r"[\s,;]+", text.strip().lower())).strip()


def _checked_pieces(text: str) -> list[ExamplePiece]:
    stripped = text.strip()
    if stripped == "":
        return []
    pieces = _scan(stripped)
    gaps = [piece for piece in pieces if piece.is_gap]
    if not gaps:
        raise ExampleSentenceError("Mark each answer with {}.")
    if len(gaps) > MAX_GAPS:
        raise ExampleSentenceError("Use at most 4 gaps.")
    outside = "".join(piece.text for piece in pieces if not piece.is_gap).strip()
    if outside == "":
        raise ExampleSentenceError("Add words around the braces.")
    return pieces


def _scan(text: str) -> list[ExamplePiece]:
    pieces: list[ExamplePiece] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "}":
            raise ExampleSentenceError("Braces must come in pairs.")
        if char == "{":
            close = text.find("}", index + 1)
            if close < 0:
                raise ExampleSentenceError("Braces must come in pairs.")
            inner = text[index + 1 : close]
            if "{" in inner:
                raise ExampleSentenceError("Do not nest braces.")
            stripped = inner.strip()
            if not accepted_forms(stripped):
                raise ExampleSentenceError("Fill the text inside each {}.")
            pieces.append(ExamplePiece(stripped, True))
            index = close + 1
            continue
        start = index
        while index < length and text[index] not in "{}":
            index += 1
        pieces.append(ExamplePiece(text[start:index], False))
    return pieces


def _join(pieces: list[ExamplePiece], *, gaps_as_braces: bool) -> str:
    parts: list[str] = []
    for piece in pieces:
        if piece.is_gap:
            parts.append("{}" if gaps_as_braces else "{" + piece.text + "}")
        else:
            parts.append(piece.text)
    return "".join(parts)
