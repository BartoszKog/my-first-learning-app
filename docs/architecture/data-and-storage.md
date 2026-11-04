# Data and storage

Learning sets and progress are stored as CSV files on disk. The UI routing
layer does not own this data: screens call helpers in `data/` to resolve
paths, update the set catalog, and load or save tables.

```mermaid
flowchart LR
    UI[Screens and components] --> Helpers[data/app_data helpers]
    Helpers --> Paths[FilePathManager]
    Paths --> Disk[csv_files on disk]
    Helpers --> Catalog[files.csv]
    Helpers --> Sets["*_words.csv / *_definitions.csv"]
```

Do not put set content, row statistics, or catalog rows in `AppSession` or
`BodyRegistry`. Those modules hold UI runtime objects only. See
[State and persistence](../guides/state-and-persistence.md).

## Storage layout

`FilePathManager` in `data/file_path_manager.py` resolves directories from Flet
environment variables:

| Path | Source | Contents |
| --- | --- | --- |
| Application data root | `FLET_APP_STORAGE_DATA` | Platform storage for the app |
| CSV directory | `{data}/csv_files/` | Set files and the catalog |
| TTS cache | `{data}/tts_cache/` | Generated pronunciation MP3s and JSON sidecars |
| Catalog | `csv_files/files.csv` | Titles and file names for every set |
| Temporary directory | `FLET_APP_STORAGE_TEMP` | Short-lived files when the platform provides it |

Call `FilePathManager.initialize()` once at startup (already done in
`app.py`) so `csv_files/` exists before any load or save. When
`FLET_APP_STORAGE_DATA` is unset (for example some web setups), the manager
falls back to the process current working directory as the CSV directory.

Helpers such as `get_csv_path()` and `get_files_data_path()` always go through
this manager so screens never hard-code absolute paths.

See the [File path manager API](../reference/file_path_manager.md).

## Set catalog: `files.csv`

The catalog lists every learning set the Home and export UIs can show.
Columns come from `FilesColumns` in `data/constants.py`. Identity and usage
columns:

| Column | Meaning |
| --- | --- |
| `file_name` | Basename of the set CSV (`…_words.csv` or `…_definitions.csv`) |
| `title` | Display title on tiles |
| `subtitle` | Optional secondary text |
| `created_at` | ISO timestamp used for creation-order sorting (newest first) |
| `last_used` | ISO timestamp of last open of the learn screen (empty if never) |
| `use_count` | How many times the learn screen was opened |

Older catalogs that only have the first three columns are migrated on read:
missing fields are filled with defaults and the file is rewritten. The seven
override columns below are added empty, so an existing set keeps the app
settings until someone stores a value. Validation still requires only
`file_name`, `title`, and `subtitle`.

Catalog helpers in `data/app_data.py`:

- `get_file_names_and_titles(sort_mode=…)` / `get_file_names()` — read the
  catalog (creating an empty `files.csv` when missing) and optionally sort.
- `ensure_files_catalog_columns()` — soft-migrate optional catalog columns.
- `add_new_file()` — append a catalog row after a new set file exists.
- `record_set_use()` — bump `use_count` / `last_used` when opening learn.
- `delate_set()` — remove the catalog row and delete the set file when present
  (also prunes unused TTS cache entries).
- `get_set_learn_progress()` — weighted Known / Learned units for Home tile
  bars without starting a learn session.
- `generate_empty_files_data()` — create an empty catalog with the expected
  columns.

Catalog and set readers treat only blank cells as missing
(`read_catalog_csv` / `read_set_csv` with `keep_default_na=False`). Titles or
words that look like pandas NA sentinels (`None`, `null`, `NA`, `nan`) stay
as written. Empty subtitle cells still become empty strings after load.

`get_file_names_and_titles()` returns full paths via `FilePathManager` so tile
code can open the matching CSV without recomputing directories.

### Per-set settings {#per-set-settings}

Seven catalog columns store one set's learning and speech choices. An empty
cell inherits the matching app setting. A non-empty cell is that set's own
value, including `false`. Columns that belong to the other set kind stay
empty and are ignored.

| Column | Applies to | Empty cell uses |
| --- | --- | --- |
| `tts_language` | both kinds | `TtsPreferences.language` |
| `tts_auto_speak` | `definitions` | `TtsPreferences.auto_speak_definitions` |
| `speakers_word_formations` | `words` | `TtsPreferences.speakers_word_formations` |
| `speakers_word` | `definitions` | `TtsPreferences.speakers_word` |
| `speakers_definition` | `definitions` | `TtsPreferences.speakers_definition` |
| `retry_until_correct` | both kinds | `LearnPreferences.retry_until_correct` |
| `queue_size` | both kinds | the queue size for that kind on `LearnPreferences` |

`data/set_settings.py` (`effective_set_settings`) fills the blanks.
`add_new_file` and demo install write empty cells. Home **Set settings** and
the learn-menu settings button open `/set/settings`, where **Use app
settings** copies the current app values into the kind's columns or clears
them again. `set_default_progress` does not touch these cells. Settings
**Restore defaults** resets the app preferences only: sets with empty cells
follow the restored values, and sets with their own cells stay as stored.

A queue cell is clamped when read (word formations 3–10, definitions 4–15).
Text that is not a whole number falls back to the app size. An unknown
language code becomes English on read. Bool cells are the text `true` or
`false`; any other non-empty text is off.

See the [Set settings API](../reference/set_settings.md).

## Set files: words and definitions

Each set is one CSV whose name must end with `_words.csv` or
`_definitions.csv`. `get_kind_of_file_and_validate()` enforces that suffix.
`sanitize_file_name()` strips non-alphanumeric characters and appends the
kind suffix when creating names.

### Words schema

Content columns (`PartsOfSpeech`): `verb`, `person`, `thing`, `adjective`,
`adverb`.

### Definitions schema

Content columns (`WordDefinitions`): `definition`, `word`.

### Shared statistics columns

Every set also stores progress columns (`StatsColumns`):

| Column | Role |
| --- | --- |
| `correct_answers` | Integer count of successful answers |
| `good_answer` | Last-answer / known-state flag |
| `good_answers_in_a_row` | Streak flag used by the learning queue |
| `word_to_learn` | Priority flag for the next draw group |

`create_empty_set(kind)` builds an empty DataFrame with the correct columns
and dtypes. `load_set` / `save_set` read and write through
`FilePathManager.get_csv_path()`, keeping the DataFrame index in the CSV
(`index_col=0` on load, `index=True` on save). After load, content columns
are coerced to strings (`stringify_content_columns`) so numeric-looking
cells such as `123` stay text for edit and learn UIs; statistics columns
keep inferred numeric/bool dtypes. Import validation uses the same readers.

`MAX_ROWS` in `data/constants.py` caps how many content rows a set may
contain (currently `40`). Import validation enforces that limit.

`set_default_progress(file_name)` resets all statistics columns on an
existing set without removing content rows. `get_set_learn_progress(file_name)`
returns the weighted Home / learn-menu bar values described in
[Learning algorithm](../concepts/learning-algorithm.md#progress-helpers).

See the [Constants API](../reference/constants.md) and
[App data API](../reference/app_data.md).

## TTS cache {#tts-cache}

Pronunciation MP3s live under `tts_cache/<hash[:2]>/<hash>.mp3` plus a JSON
sidecar (`learning_app/tts/`). Cache keys include provider, voice, language,
and normalized text. Garbage collection keeps a recording while some set still
speaks that phrase in that language. The language is the set's
`tts_language` cell, or the app language when the cell is empty. The same
spelling in two languages is two live pairs. GC runs after `delate_set` and
content saves with `prune_tts=True`. Saving a set's language from
`/set/settings` does not run GC until the next content edit or delete. Empty
shard folders may remain after GC.

Playback is session-owned (`AppSession.speak`); screens must not construct
`Audio`. The language and auto-speak used for a set are the effective values
from [Per-set settings](#per-set-settings). App defaults live in preferences —
see [Text to speech](../guides/state-and-persistence.md#text-to-speech).
Signatures are in the [TTS API](../reference/tts.md).

## `AppData` versus catalog helpers

Module-level functions in `data/app_data.py` manage the catalog and raw
DataFrames on disk. The `AppData` class loads one set into memory for a
learning session, draws word groups from the statistics columns, and calls
`save_set` after each answer.

Use the helpers when listing, creating, deleting, or editing sets. Use
`AppData` when running a learn session over an existing file. Queue and
answer rules are documented in
[Learning algorithm](../concepts/learning-algorithm.md); storage ownership
stays in this layer either way.

## Import path (overview)

`CSVProcessor` in `data/csv_processor.py` validates imported files, may repair
`files.csv`, and saves sets with or without keeping existing statistics. The
full task flow is in the [Import and export guide](../guides/import-export.md).
Column and message enums for errors and warnings live in `data/constants.py`.

## Demo sets

Bundled sample CSVs live under `src/assets/demos/` (read-only templates). They
are not user storage: Settings calls `install_demo_sets()` in
`data/demo_sets.py`, which copies each missing template into `csv_files/`,
resets statistics columns, and registers a catalog row with a **fixed**
basename (for example `DemoWordFormation_words.csv`).

```mermaid
flowchart LR
    Assets["assets/demos/*.csv"] --> Install["install_demo_sets()"]
    Install -->|skip if already catalogued or on disk| Done[Result lists]
    Install -->|copy reset stats add_new_file| Storage["csv_files/ + files.csv"]
```

Resolution uses `FLET_ASSETS_DIR` after `flet build`, with a local fallback to
`src/assets`. Create and import must not claim those basenames:
`allocate_unique_set_basename()` treats `RESERVED_DEMO_SET_NAMES` as occupied
even when a demo is not installed yet, so a user set gets a numbered variant
instead. Installation itself uses `is_demo_already_installed()` (catalog or
disk only), so Add can recreate a demo after the user deletes it.

After a successful install, Settings refreshes Home and export tile lists
through `BodyRegistry` when those bodies exist.

See the [Demo sets API](../reference/demo_sets.md).

## Module map

| Module | Responsibility |
| --- | --- |
| `data/file_path_manager.py` | Storage roots, CSV paths, and `tts_cache/` |
| `data/constants.py` | Schema enums, `MAX_ROWS`, import messages |
| `data/app_data.py` | Catalog CRUD, load/save, empty sets, `AppData` |
| `data/csv_processor.py` | Import validation and specialized save paths |
| `data/demo_sets.py` | Bundled demo registry, reserved names, install |
| `tts/` | Pronunciation cache, gTTS provider, and GC |

## Continue reading

- [Architecture overview](index.md)
- [Learning algorithm](../concepts/learning-algorithm.md)
- [Import and export](../guides/import-export.md)
- [State and persistence](../guides/state-and-persistence.md)
- [File path manager API](../reference/file_path_manager.md)
- [App data API](../reference/app_data.md)
- [Constants API](../reference/constants.md)
- [CSV processor API](../reference/csv_processor.md)
- [Demo sets API](../reference/demo_sets.md)
- [TTS API](../reference/tts.md)
