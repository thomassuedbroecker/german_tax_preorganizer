# Changelog

## 2026-06-20 — GUI & reporting improvements

- UI: added `Export CSV` button to save the current table view as CSV.
- UI: added `Generate Exec PDF` to render the Markdown report (with optional AI review text) to PDF.
- UI: improved confidence coloring: `confidence == 1.0` now dark green with white text; `>= 0.90` remains light green.
- UI: richer progress display: processed / remaining / total, percent complete, ETA, current filename, units (pages), elapsed time, and token count when available.
- Added elapsed time tracking and final elapsed time in summary.
- Tests: verified — all tests pass (50 passed).

