# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

When bumping `project.version` in `pyproject.toml`, add a matching `## [x.y.z]`
section here. The release workflow publishes that section as the GitHub Release
body and fails if it is missing.

## [Unreleased]

### Added
- Speaker buttons on set word-list cards, with Settings switches for word formations, word, and definition fields
- Separate Word formations and Definitions speaker controls in Settings, with always-visible sample cards under each group and a note that definition TTS uses the global language
- Ctrl+Enter shortcut for Start on the word list and for Check / Try again / Next in a learn session, with focus moved to the first empty answer field afterward
- Ctrl+Left Arrow shortcut for navigational back (same as system back / in-app Back)
- Ctrl+S shortcut to pronounce the revealed word in a definitions learn session

### Changed
- Default **Retype until correct** to on for new installs (existing saved preference is unchanged)

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

[Unreleased]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.5...HEAD
[1.0.6]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.3...v1.0.4
