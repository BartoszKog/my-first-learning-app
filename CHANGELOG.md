# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

When bumping `project.version` in `pyproject.toml`, add a matching `## [x.y.z]`
section here. The release workflow publishes that section as the GitHub Release
body and fails if it is missing.

## [Unreleased]

### Added
- Local SQLite store (`learning.sqlite`) for sets, cards, per-set overrides, and a visit log opened from the learn screen; graded Checks update that card and the open visit
- One-time startup copy of existing `files.csv` sets into the database, without importing the same file again or bringing a deleted set back
- Optional example sentence on definition cards. One `{}` is one gap and can hold a word or a phrase (`{on purpose}`); another pair is for sentence words between the answers (`I {keep} him {in line}.`). A sentence can hold up to four gaps, and `/` inside a gap is another accepted form
- Definition learn mode shows that example after Check (default), as one `_____` per gap before Check (Hint), or not at all (Off). Typing the gap texts in order counts as correct while the blanks are on screen. The word list shows the filled sentence and can speak it
- Example field on the definition edit card, with a preview that highlights the gaps

### Changed
- Delete and Set default progress confirmations name the set. The title is teal, without quotation marks, and the sentence still says whether the set is words or definitions
- With Retype until correct on, the learn-session bar counts a card answered wrong only after Next, not on the first Check
- Progress bars count a card whose last answer was correct but is not Known yet as half a word (was a quarter). Checked cards with a wrong last answer stay at a quarter
- CSV is the import, export, and demo-template format. Home, create, edit, learn, reset, and delete read and write the database
- Tile use count is the old catalog balance plus later visits. Opening a set records a visit and does not increment that balance
- Document the SQLite store, visit log, `checks`, and the CSV migration
- Raise the per-set card limit from 40 to 80 for import, create, and edit
- Changed theme seed to teal and changed some buttons to filled ones
- Group adjacent words into one gap in the demo definition examples
- Document example sentences in the developer docs, README, and in-app Info, including a sample `example_sentence` column

## [1.0.8] - 2026-11-05

### Added
- Per-set learning and speech settings from the set tile menu: a set can keep its own language, speakers, retype-until-correct rule, and queue size, while empty catalog cells still follow the app defaults; deleting a set drops TTS audio for languages no remaining set still uses
- Set settings screen with a top bar (back, set title, kind chip) and Source / Text to speech / Learning section cards, including a Use app settings switch
- Icon-only shortcut beside Start on the word list that opens that set's settings
- Icons on set tile popup menu items (Edit, Set settings, Change title, Set default progress, Delete)
- Ctrl+S shortcut to Save on the edit-set screen, with Save (Ctrl+S) and Back (Ctrl+B) button tooltips
- Ctrl+B on the edit-set screen uses the same Back path as the button (unsaved-changes dialog when needed)
- Settings sliders for the practice-queue size of word formations (3–10, default 5) and definitions (4–15, default 10)
- Defaults section at the top of Settings with Restore defaults, which resets every preference on that page to the original values; a snackbar offers Undo for 4 seconds, and if settings are already default the snackbar only says so and has no Undo; learning sets, demo data, and CSV progress are not changed
- Home empty state when there are no set tiles, with a two-line prompt to create a set with the + button or add the demo sets, and an Add demo sets button (playlist-add icon) that installs the same demo sets as Settings; the prompt and button disappear once tiles exist and return if every set is deleted; Import/Export does not show this empty state

### Changed
- Require Flet 1.1.0+ and flet-audio 1.1.0+; migrate TextField / Dropdown borders to `OutlineInputBorder` (including focused-state maps where needed)
- TTS Audio sets `AudioContext(focus=DUCK_OTHERS)`, so other phone audio is ducked for the pronunciation instead of stopped
- Document per-set learning and speech settings, and that app Settings values are the defaults for sets without overrides
- Navigational back shortcut from Ctrl+Left Arrow to Ctrl+B (Meta/Cmd+B); word-list Back button tooltip shows the shortcut
- Accept a typed answer of several slash-separated forms when every piece is a stored alternative; order does not matter, and one unknown or empty piece fails the whole answer

### Fixed
- Update the empty-home patch test for the Flet 1.0 `Message` API so pytest collection succeeds after the upgrade
- Ignore AltGr (Ctrl+Alt) in Ctrl shortcuts so typing Polish ś with AltGr+S does not trigger Save / speak
- Strip spaces around `/` when splitting a stored answer into alternatives, so `to rely on STH / SB` accepts `to rely on STH` or `SB`

## [1.0.7] - 2026-09-23

### Added
- Speaker buttons on set word-list cards, with Settings switches for word formations, word, and definition fields
- Separate Word formations and Definitions speaker controls in Settings, with always-visible sample cards under each group and a note that definition TTS uses the global language
- Ctrl+Enter shortcut for Start on the word list and for Check / Try again / Next in a learn session, with focus moved to the first empty answer field afterward
- Ctrl+Left Arrow shortcut for navigational back (same as system back / in-app Back)
- Ctrl+S shortcut to pronounce the revealed word in a definitions learn session

### Changed
- Default **Retype until correct** to on for new installs (existing saved preference is unchanged)

### Fixed
- Use the word-list card border color on Settings and Create set text fields and dropdowns so outlines stay visible in dark mode

## [1.0.6] - 2026-09-14

### Added
- Learn progress bars on Home set tiles, using the same Known / Learned weights as the learn session
- Settings switch to retype until correct: after a wrong Check, stay on the same card until the answer is typed correctly; extra attempts do not change set statistics
- On word-formation retries, keep green fields filled so only missed forms need to be typed again

### Changed
- Restyle in-place search on Home and Export: host the field in the app bar, use a slightly lighter teal fill with white text and icon buttons, enlarge the actions, and match tile width on wide screens
- Update developer documentation for in-place search chrome, learn-queue retry, Home tile progress, and CSV text loading

### Fixed
- Replay a pronunciation immediately when the speaker is pressed after auto-speak of the same word
- Keep numeric-looking card text and catalog titles or subtitles such as None, null, or NA when loading CSVs

## [1.0.5] - 2026-08-17

### Added
- Pronounce the revealed word on definition sets (speaker next to Check, optional auto-speak)
- Text-to-speech language and auto-speak switches in Settings
- Cached gTTS pronunciations, pruned when a set is deleted or its content is rewritten

### Changed
- Separate Settings sections with horizontal dividers
- Document TTS playback, preferences, and the pronunciation cache

## [1.0.4] - 2026-08-15

### Added
- In-place search on Home and Export, replacing the dedicated search screen
- Sorting for set tiles, shared between Home and Export
- Rename a set title and subtitle from the set tile menu
- Add bundled demo sets from Settings (word formation, English definitions, English–Polish)
- Swap cards while editing a set, save without leaving the editor, and go back when creating a set

### Changed
- Move the app into a `src/` layout for Flet packaging
- Match Export set tiles to the Home list width and center wrapped tile labels
- Match the search field color to the app bar and add spacing above it
- Point the README Download APK button at the latest `learning-app.apk` asset
- Drop the parenthetical build number from GitHub Release titles
- Update developer documentation for the new screens, demo sets, and packaging layout

### Fixed
- Recreate a missing `files.csv` catalog during repair and close stacked catalog dialogs
- Restore Home chrome after Android Back from a newly created set

[Unreleased]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.8...HEAD
[1.0.8]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.3...v1.0.4
