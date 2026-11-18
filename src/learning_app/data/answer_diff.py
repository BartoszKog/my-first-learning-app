"""Letter-level diff between a typed answer and the stored answer.

A wrong Check uses these pieces to mark which typed letters are wrong and
which letters are missing. Comparison is case-insensitive, like grading, but
each piece keeps the original spelling of the text it came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

CLOSE_MATCH_RATIO = 0.5
"""Below this similarity the typed text is shown without letter marks."""

PieceKind = Literal["same", "wrong", "missing"]

_SLASH_JOIN = " / "


@dataclass(frozen=True)
class DiffPiece:
    """One run of the typed answer, or of letters it lacks.

    ``same`` and ``wrong`` text comes from the typed answer. ``missing`` text
    comes from the stored answer and is not in the typed answer.
    """

    kind: PieceKind
    text: str


def _alternatives(expected: str) -> list[str]:
    parts = (
        [part.strip() for part in expected.split("/")]
        if "/" in expected
        else [expected]
    )
    return [part for part in parts if part] or [expected]


def _ratio(typed: str, target: str) -> float:
    return SequenceMatcher(None, typed.lower(), target.lower()).ratio()


def closest_alternative(typed: str, expected: str) -> str:
    """Return the slash alternative of ``expected`` most similar to ``typed``.

    Args:
        typed: Typed answer, or one slash piece of it.
        expected: Stored answer, possibly with ``/`` alternatives.

    Returns:
        The trimmed alternative with the highest similarity. Ties keep the
        first alternative.
    """
    typed = typed.strip()
    return max(_alternatives(expected), key=lambda alt: _ratio(typed, alt))


def _append(pieces: list[DiffPiece], kind: PieceKind, text: str) -> None:
    if not text:
        return
    if pieces and pieces[-1].kind == kind:
        pieces[-1] = DiffPiece(kind, pieces[-1].text + text)
    else:
        pieces.append(DiffPiece(kind, text))


def _diff_one(typed: str, target: str, pieces: list[DiffPiece]) -> None:
    matcher = SequenceMatcher(None, typed.lower(), target.lower())
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            _append(pieces, "same", typed[i1:i2])
        if op in ("replace", "delete"):
            _append(pieces, "wrong", typed[i1:i2])
        if op in ("replace", "insert"):
            _append(pieces, "missing", target[j1:j2])


def diff_answer(typed: str, expected: str) -> tuple[list[DiffPiece], float]:
    """Diff ``typed`` against the closest form of ``expected``.

    A typed ``/`` lists several forms. Each form is diffed against its own
    closest alternative, and the forms are joined with ``" / "``.

    Args:
        typed: Text the user typed before Check.
        expected: Stored answer, possibly with ``/`` alternatives.

    Returns:
        The pieces in display order, and the similarity from ``0.0`` to
        ``1.0``. With several typed forms the similarity is the lowest one.
        Blank ``typed`` gives ``([], 0.0)``.
    """
    typed = typed.strip()
    if not typed:
        return [], 0.0
    forms = [form.strip() for form in typed.split("/")] if "/" in typed else [typed]
    pieces: list[DiffPiece] = []
    ratios: list[float] = []
    for index, form in enumerate(forms):
        if index:
            _append(pieces, "same", _SLASH_JOIN)
        target = closest_alternative(form, expected) if form else ""
        _diff_one(form, target, pieces)
        ratios.append(_ratio(form, target) if form else 0.0)
    return pieces, min(ratios)
