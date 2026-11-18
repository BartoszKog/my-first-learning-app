"""Check what happens when two save handlers run at the same time.

Flet runs synchronous event handlers in a thread pool, and the Import and
Edit screens keep their buttons enabled while a save runs. A double click on
"Add set" / "Save" (or Ctrl+S twice) therefore runs the same data-layer calls
in two threads at once. This script reproduces that with two threads released
by a barrier and reports exceptions, duplicate sets, and broken card order.

It only exercises the data layer the handlers call, not the Flet UI. Every
run uses a fresh temporary storage folder; real data is never touched.

Usage::

    uv run python scripts/race_save.py
    uv run python scripts/race_save.py --runs 50 --sets 30 --tts-files 2000
    uv run python scripts/race_save.py --scenario double_import --verbose

Scenarios:
    double_import       "Add set" clicked twice for the same picked CSV
    double_edit_create  first Save of a new set in Edit clicked twice
    double_edit_resave  two saves of the same set with different edits
    import_during_home  import while Home refreshes its tiles (user left Import)
"""

from __future__ import annotations

import argparse
import random
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import traceback
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

SCENARIOS = ("double_import", "double_edit_create", "double_edit_resave", "import_during_home")
WORDS_COLUMNS = ("verb", "person", "thing", "adjective", "adverb")
STATS_DEFAULTS = {
    "correct_answers": 0,
    "good_answers_in_a_row": False,
    "good_answer": False,
    "word_to_learn": False,
    "checks": 0,
}
SYLLABLES = ("ka", "lo", "mi", "ra", "te", "su", "no", "vi", "da", "pe", "go", "zu")


def _word(rng: random.Random) -> str:
    return "".join(rng.choice(SYLLABLES) for _ in range(rng.randint(2, 4)))


def _words_row(rng: random.Random) -> dict:
    row = {column: None for column in WORDS_COLUMNS}
    for column in rng.sample(WORDS_COLUMNS, rng.randint(2, 4)):
        row[column] = _word(rng)
    return row


def _isolate(data_dir: Path) -> None:
    from learning_app.data.repository import reset_storage

    from learning_app.data.file_path_manager import FilePathManager

    csv_dir = data_dir / "csv_files"
    csv_dir.mkdir(parents=True, exist_ok=True)
    FilePathManager._data_dir = str(data_dir)
    FilePathManager._temp_dir = str(data_dir.parent / "temp")
    FilePathManager._csv_dir = str(csv_dir)
    FilePathManager._initialized = True
    reset_storage()


def build_template(template: Path, sets: int, cards: int, tts_files: int, seed: int) -> None:
    """Background sets and cached MP3s make the save (and its TTS GC) as slow as in real use."""
    import pandas as pd
    from learning_app.data.repository import init_db, reset_storage

    from learning_app.data.app_data import add_new_file, save_set
    from learning_app.tts.cache import TtsCache
    from learning_app.ui.tts_preferences import TtsPreferences

    _isolate(template)
    init_db()
    rng = random.Random(seed)
    phrases = []
    for index in range(sets):
        rows = [_words_row(rng) for _ in range(cards)]
        frame = pd.DataFrame(rows, columns=list(WORDS_COLUMNS))
        for column, value in STATS_DEFAULTS.items():
            frame[column] = value
        file_name = f"Background{index}_words.csv"
        add_new_file(file_name, f"Background {index}", "")
        save_set(frame, file_name)
        phrases.extend(value for row in rows for value in row.values() if value)
    cache = TtsCache(template / "tts_cache")
    unique = list(dict.fromkeys(phrases))
    for index in range(tts_files):
        text = unique[index] if index < len(unique) else f"orphan {index}"
        key = cache.make_key(provider="gtts", language=TtsPreferences.language, text=text)
        cache.put(key, b"ID3" + bytes(500), text=text, language=TtsPreferences.language, provider="gtts")
    reset_storage()


@dataclass
class Outcome:
    errors: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


SECOND_CLICK_DELAY_S = 0.0


def _describe(exc: BaseException) -> str:
    """Name the real database error and the deepest app frame that raised it."""
    root = getattr(exc, "orig", None) or exc
    message = str(root).splitlines()[0][:160] if str(root) else ""
    frames = traceback.extract_tb(exc.__traceback__)
    app_frames = [f for f in frames if "learning_app" in f.filename.replace("\\", "/")]
    where = app_frames[-1] if app_frames else frames[-1]
    return f"{type(exc).__name__}: {message} (in {Path(where.filename).name}:{where.lineno} {where.name})"


def _run_pair(first, second) -> list[str]:
    """Start both callables together (B after ``--delay-ms``); return formatted exceptions."""
    barrier = threading.Barrier(2)
    errors: list[str] = []
    lock = threading.Lock()

    def runner(func, name):
        barrier.wait()
        if name == "thread B" and SECOND_CLICK_DELAY_S:
            time.sleep(SECOND_CLICK_DELAY_S)
        try:
            func()
        except Exception as exc:  # noqa: BLE001 - every failure is part of the report
            with lock:
                errors.append(f"{name}: {_describe(exc)}")

    threads = [
        threading.Thread(target=runner, args=(first, "thread A")),
        threading.Thread(target=runner, args=(second, "thread B")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return errors


def _db_rows(data_dir: Path, prefix: str) -> dict[str, list[tuple]]:
    """Return ``{basename: [(position, verb), ...]}`` for sets whose name starts with ``prefix``."""
    from learning_app.data.repository import reset_storage

    reset_storage()
    with sqlite3.connect(data_dir / "learning.sqlite") as connection:
        sets = connection.execute(
            "select id, source_file_name from learning_set where source_file_name like ?",
            (prefix + "%",),
        ).fetchall()
        result = {}
        for set_id, name in sets:
            result[name] = connection.execute(
                "select position, verb from card where set_id = ? order by position", (set_id,)
            ).fetchall()
    return result


def _check_positions(rows: dict[str, list[tuple]], outcome: Outcome) -> None:
    for name, cards in rows.items():
        positions = [position for position, _ in cards]
        if positions != list(range(len(positions))):
            outcome.problems.append(f"{name}: card positions are {positions[:10]}..., expected 0..{len(positions) - 1}")


def _frame(rows: list[dict]):
    import pandas as pd

    frame = pd.DataFrame(rows, columns=list(WORDS_COLUMNS))
    for column, value in STATS_DEFAULTS.items():
        frame[column] = value
    return frame


def _write_picked_csv(path: Path, rng: random.Random, rows: int) -> None:
    import pandas as pd

    pd.DataFrame([_words_row(rng) for _ in range(rows)], columns=list(WORDS_COLUMNS)).to_csv(path, index=True)


def _import_once(picked: Path, title: str) -> None:
    from learning_app.data.csv_processor import CSVProcessor

    result = CSVProcessor.validate_file(str(picked), original_name=picked.name)
    assert result["is_valid"] and not result["requires_specific_actions"], result
    CSVProcessor.save_set_with_no_specific_actions(str(picked), picked.name, title, "", result["has_statistics"])


def scenario_double_import(data_dir: Path, rng: random.Random) -> Outcome:
    picked = data_dir.parent / "RaceImport_words.csv"
    _write_picked_csv(picked, rng, 30)
    outcome = Outcome()
    outcome.errors = _run_pair(lambda: _import_once(picked, "Race import"), lambda: _import_once(picked, "Race import"))
    rows = _db_rows(data_dir, "RaceImport")
    if len(rows) > 1:
        outcome.problems.append(f"duplicate sets created: {sorted(rows)}")
    if not rows:
        outcome.problems.append("no set was created")
    for name, cards in rows.items():
        if len(cards) != 30:
            outcome.problems.append(f"{name}: {len(cards)} cards, expected 30")
    _check_positions(rows, outcome)
    return outcome


def scenario_double_edit_create(data_dir: Path, rng: random.Random) -> Outcome:
    import pandas as pd

    from learning_app.data.app_data import AppData, create_empty_set, save_set

    file_name = "RaceCreate_words.csv"
    data = pd.concat([create_empty_set("words"), _frame([_words_row(rng) for _ in range(10)])], ignore_index=True)

    def first_save():
        AppData.create_data_file_words(file_name, title="Race create", subtitle="")
        save_set(data.copy(), file_name, prune_tts=True)

    outcome = Outcome()
    outcome.errors = _run_pair(first_save, first_save)
    rows = _db_rows(data_dir, "RaceCreate")
    if len(rows) != 1:
        outcome.problems.append(f"expected 1 set, found {sorted(rows)}")
    for name, cards in rows.items():
        if len(cards) != 10:
            outcome.problems.append(f"{name}: {len(cards)} cards, expected 10")
    _check_positions(rows, outcome)
    return outcome


def scenario_double_edit_resave(data_dir: Path, rng: random.Random) -> Outcome:
    import pandas as pd

    from learning_app.data.app_data import add_new_file, load_set, save_set

    file_name = "RaceResave_words.csv"
    add_new_file(file_name, "Race resave", "")
    save_set(_frame([_words_row(rng) for _ in range(20)]), file_name)
    loaded = load_set(file_name)

    def edited(drop_index: int, verb: str):
        frame = loaded.drop(loaded.index[drop_index])
        row = _words_row(rng)
        row["verb"] = verb
        new_df = pd.DataFrame([{**row, **STATS_DEFAULTS}])
        return pd.concat([frame, new_df], ignore_index=True).reset_index(drop=True)

    frame_a = edited(0, "edit-from-A")
    frame_b = edited(1, "edit-from-B")
    outcome = Outcome()
    outcome.errors = _run_pair(
        lambda: save_set(frame_a, file_name, prune_tts=True),
        lambda: save_set(frame_b, file_name, prune_tts=True),
    )
    rows = _db_rows(data_dir, "RaceResave")
    cards = rows.get(file_name, [])
    verbs = {verb for _, verb in cards}
    if len(cards) != 20:
        outcome.problems.append(f"{file_name}: {len(cards)} cards, expected 20")
    if "edit-from-A" in verbs and "edit-from-B" in verbs:
        outcome.problems.append("cards from both saves were mixed into one set")
    elif "edit-from-A" in verbs or "edit-from-B" in verbs:
        winner = "A" if "edit-from-A" in verbs else "B"
        outcome.notes.append(f"last save won ({winner})")
    _check_positions(rows, outcome)
    return outcome


def scenario_import_during_home(data_dir: Path, rng: random.Random) -> Outcome:
    from learning_app.data.app_data import (
        get_file_names_and_titles,
        get_set_learn_progress,
    )
    from learning_app.data.constants import FilesColumns

    picked = data_dir.parent / "RaceHome_words.csv"
    _write_picked_csv(picked, rng, 30)

    def refresh_home():
        for entry in get_file_names_and_titles():
            get_set_learn_progress(entry[FilesColumns.FILE_NAME.value])

    outcome = Outcome()
    outcome.errors = _run_pair(lambda: _import_once(picked, "Race home"), refresh_home)
    rows = _db_rows(data_dir, "RaceHome")
    if len(rows) != 1:
        outcome.problems.append(f"expected 1 set, found {sorted(rows)}")
    _check_positions(rows, outcome)
    return outcome


SCENARIO_FUNCS = {
    "double_import": scenario_double_import,
    "double_edit_create": scenario_double_edit_create,
    "double_edit_resave": scenario_double_edit_resave,
    "import_during_home": scenario_import_during_home,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs", type=int, default=20, help="Repetitions per scenario (default 20).")
    parser.add_argument("--sets", type=int, default=15, help="Background sets in each run (default 15).")
    parser.add_argument("--cards", type=int, default=30, help="Cards per background set (default 30).")
    parser.add_argument("--tts-files", type=int, default=300, help="Cached MP3s in each run (default 300).")
    parser.add_argument("--scenario", choices=SCENARIOS, action="append", help="Run only these scenarios.")
    parser.add_argument(
        "--delay-ms",
        type=float,
        default=0.0,
        help="Start the second thread this much later, like the gap between two clicks (default 0).",
    )
    parser.add_argument("--verbose", action="store_true", help="Print every run, not only the summary.")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    global SECOND_CLICK_DELAY_S
    SECOND_CLICK_DELAY_S = args.delay_ms / 1000

    try:
        import learning_app.data.repository  # noqa: F401
    except ImportError as exc:
        raise SystemExit(f"This script needs the SQLite storage (learning_app.data.repository): {exc}") from exc

    root = Path(tempfile.mkdtemp(prefix="race_save_"))
    try:
        template = root / "template"
        print(
            f"Preparing {args.sets} background sets and {args.tts_files} cached MP3s; "
            f"second thread starts {args.delay_ms:g} ms after the first ..."
        )
        build_template(template, args.sets, args.cards, args.tts_files, args.seed)

        summary = {}
        for scenario in args.scenario or SCENARIOS:
            errors: Counter[str] = Counter()
            problems: Counter[str] = Counter()
            notes: Counter[str] = Counter()
            failed_runs = 0
            for run in range(args.runs):
                run_dir = root / f"{scenario}_{run}"
                data_dir = run_dir / "data"
                shutil.copytree(template, data_dir)
                _isolate(data_dir)
                outcome = SCENARIO_FUNCS[scenario](data_dir, random.Random(args.seed + run))
                if outcome.errors or outcome.problems:
                    failed_runs += 1
                errors.update(_without_thread(e) for e in outcome.errors)
                problems.update(_generalize(p) for p in outcome.problems)
                notes.update(outcome.notes)
                if args.verbose:
                    status = "FAIL" if outcome.errors or outcome.problems else "ok"
                    print(f"  {scenario} run {run + 1}: {status} {outcome.errors + outcome.problems + outcome.notes}")
                shutil.rmtree(run_dir, ignore_errors=True)
            summary[scenario] = (failed_runs, errors, problems, notes)

        print()
        for scenario, (failed_runs, errors, problems, notes) in summary.items():
            print(f"== {scenario}: {failed_runs}/{args.runs} runs had an exception or bad data")
            for message, count in errors.most_common():
                print(f"   exception x{count}: {message}")
            for message, count in problems.most_common():
                print(f"   data problem x{count}: {message}")
            for message, count in notes.most_common():
                print(f"   note x{count}: {message}")
    finally:
        from learning_app.data.repository import reset_storage

        reset_storage()
        shutil.rmtree(root, ignore_errors=True)


def _without_thread(message: str) -> str:
    return message.split(": ", 1)[1] if message.startswith("thread ") else message


def _generalize(message: str) -> str:
    """Group messages that differ only by the allocated set name."""
    import re

    return re.sub(r"Race(\w+?)\d*_words\.csv", r"Race\1*_words.csv", message)


if __name__ == "__main__":
    main()
