"""SQLite tables for the local learning-set store.

The shape is the v1 schema: four tables, UUID text keys, seven nullable
overrides on the set, and ``checks`` on both the card and the visit. There is
no user and no API model. A later server can reuse these tables.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlmodel import Field, SQLModel


def new_id() -> str:
    """Return a new UUID text primary key."""
    return str(uuid.uuid4())


class LearningSet(SQLModel, table=True):
    """One learning set. The table name is ``learning_set``."""

    __tablename__ = "learning_set"

    id: str = Field(default_factory=new_id, primary_key=True)
    kind: str
    title: str
    subtitle: str = ""
    created_at: datetime
    last_used: datetime | None = None
    use_count: int = 0
    # Basename the screens still pass around (``*_words.csv`` / ``*_definitions.csv``).
    # Unique, but not the primary key. NULL only when a row is created without a name.
    # ``migrated_csv_file`` is what stops a deleted CSV from being imported again.
    source_file_name: str | None = Field(default=None, unique=True, index=True)
    tts_language: str | None = None
    tts_auto_speak: bool | None = None
    speakers_word_formations: bool | None = None
    speakers_word: bool | None = None
    speakers_definition: bool | None = None
    retry_until_correct: bool | None = None
    queue_size: int | None = None


class Card(SQLModel, table=True):
    """One row of a set. Word formation is one card; a definition pair is one card."""

    __tablename__ = "card"
    __table_args__ = (UniqueConstraint("set_id", "position", name="uq_card_set_position"),)

    id: str = Field(default_factory=new_id, primary_key=True)
    set_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("learning_set.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    position: int

    verb: str = ""
    person: str = ""
    thing: str = ""
    adjective: str = ""
    adverb: str = ""
    definition: str = ""
    word: str = ""
    # Optional example on a definition card. Empty on word-formation cards.
    example_sentence: str = ""

    correct_answers: int = 0
    good_answer: bool = False
    good_answers_in_a_row: bool = False
    word_to_learn: bool = False
    checks: int = 0


class SetOpened(SQLModel, table=True):
    """One entry into a set's learn screen, plus the grades given during that visit."""

    __tablename__ = "set_opened"

    id: str = Field(default_factory=new_id, primary_key=True)
    set_id: str = Field(
        sa_column=Column(
            String,
            ForeignKey("learning_set.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    opened_at: datetime
    checks: int = 0
    correct_answers: int = 0


class MigratedCsvFile(SQLModel, table=True):
    """CSV basename already copied into SQLite. Deleting the set does not remove this row."""

    __tablename__ = "migrated_csv_file"

    file_name: str = Field(primary_key=True)
