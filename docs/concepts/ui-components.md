# UI components

Reusable controls under `ui/components/` build the bodies that routes host.
Screens and factories compose these pieces; they should not reimplement tile
lists, learn-session loops, or edit cards.

Route ownership is in
[Routing and screens](../architecture/routing-and-screens.md). Shared Home and
export tile instances are in [Body registry](body-registry.md). Learn-queue
rules are in [Learning algorithm](learning-algorithm.md).

## When to open this page

| Need | Look at |
| --- | --- |
| List sets and tile actions | Tiles |
| Learn menu / session UI | Learn fields |
| Create or edit set rows | Edit cards |
| Search bar over tiles | Search control |

There is no per-component API Reference page. Prefer this map plus the source
files under `ui/components/`.

## Tiles

| Class | Source | Role |
| --- | --- | --- |
| `TilesContainer` | `ui/components/tiles_container.py` | Scrollable list of set tiles; Home and export modes |
| `ContentTile` | `ui/components/content_tile.py` | One catalog entry and its actions |

`TilesContainer` loads the catalog through `get_file_names_and_titles`, builds
`ContentTile` children, and supports search filtering / focus used by Search.
A session-scoped sort dropdown (last used, date created newest-first, title,
use count) sits above the tiles outside search mode; Home and export stay in
sync via `BodyRegistry` when both are on-page. Home registers the container
with `BodyRegistry`; Import/Export does the same for export mode.

`ContentTile` opens learn or edit via `push_view`, and offers menu actions such
as reset progress (`set_default_progress`), delete (`delate_set`), and export
through `AppSession.get_export_csv_picker()` with `save_file(..., src_bytes=...)`.
In export mode the tile is oriented toward picking a set to save out rather
than full Home management.

```text
files.csv → TilesContainer → ContentTile → learn / edit / delete / export
```

## Learn fields

| Class | Source | Role |
| --- | --- | --- |
| `BaseWordField` | `ui/components/base_word_field.py` | Shared learn menu/session loop over `AppData` |
| `WordFields` | `ui/components/word_fields.py` | Words-set UI (`*_words.csv`) |
| `WordDefinitionField` | `ui/components/word_definition_field.py` | Definitions-set UI (`*_definitions.csv`) |
| `ProgressBar` | `ui/components/controls.py` | Session progress display |
| `WordField` | `ui/components/controls.py` | Styled text field used in learn/edit forms |

Route factories construct `WordFields` or `WordDefinitionField` with
`session=False` (learn menu) or `session=True` (active session). Subclasses
supply the visible fields; `BaseWordField` owns starting/stopping the session,
calling `good_answer_at_current_row` / `bad_answer_at_current_row`, and
resetting progress when all words are learned.

`WordDefinitionField` adds a speaker button to the right of Check. It stays
disabled until Check reveals the word, then `AppSession.speak` plays the
**word** column (not the definition) in the language from `TtsPreferences`.
Optional auto-speak after Check does not show error snackbars.

`WordListMenu` in `ui/screens/word_list_menu.py` sits beside these controls for
the learn menu list; it is a screen helper, not under `components/`.

Responsive widths for learn fields come from
[Layout](../guides/layout.md) (`form_width` and field-width helpers).

## Edit cards

| Class | Source | Role |
| --- | --- | --- |
| `EditCardBase` | `ui/components/edit_cards.py` | Shared card validation and field wiring |
| `EditCardWords` | same | Words-set row editor |
| `EditCardDefinitions` | same | Definitions-set row editor |

`EditSetMenu` builds a list of edit cards for the open set. Cards wrap the
content columns for the set kind and track whether the user has edited them
before save. Prefer extending `EditCardBase` over copying field layout into a
new screen.

## Search control

| Class | Source | Role |
| --- | --- | --- |
| `SearchControl` | `ui/components/search_control.py` | Search field plus next/previous match over a `TilesContainer` |

In-place search (`ui/inplace_search.py`) inserts `SearchControl` above the
shared Home or export `TilesContainer` from `BodyRegistry`. Filtering stays on
that existing instance; the control only drives the pattern and focus. Closing
restores shell chrome (and the Import/Export tab bar plus export tip when
searching export). System back closes in-place search the same way as the
search close button, without popping the shell route.

## Ownership checklist

| Concern | Owner |
| --- | --- |
| Which route hosts which body | `route_registry` / screen map |
| Shared Home/export tile instance | `BodyRegistry` |
| Practice queue and stats | `AppData` |
| Tile list / learn loop / edit cards | `ui/components/` |
| Screen chrome and navigation | Shell chrome + navigation helpers |

## Continue reading

- [Routing and screens](../architecture/routing-and-screens.md)
- [Body registry](body-registry.md)
- [Learning algorithm](learning-algorithm.md)
- [Layout](../guides/layout.md)
- [Import and export](../guides/import-export.md)
