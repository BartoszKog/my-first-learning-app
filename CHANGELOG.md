# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

When bumping `project.version` in `pyproject.toml`, add a matching `## [x.y.z]`
section here. The release workflow publishes that section as the GitHub Release
body and fails if it is missing.

## [Unreleased]

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

[Unreleased]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.4...HEAD
[1.0.4]: https://github.com/BartoszKog/my-first-learning-app/compare/v1.0.3...v1.0.4
