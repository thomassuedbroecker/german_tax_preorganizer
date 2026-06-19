# Third-Party Notices

This project uses third-party Python packages. Each dependency remains governed
by its own license. This inventory covers direct dependencies declared in
`pyproject.toml`; it does not replace the license files distributed with those
packages.

Last reviewed: 2026-06-19.

| Dependency | Use | Declared license | Installation |
|---|---|---|---|
| PyYAML | YAML configuration | MIT | Core |
| python-dateutil | Date parsing | Apache-2.0 or BSD-3-Clause (dual licensed) | Core |
| Rich | CLI tables and formatting | MIT | Core |
| pdfplumber | PDF text extraction | MIT | `light` extra |
| pypdf | PDF text extraction | BSD-3-Clause | `light` extra |
| pytesseract | Tesseract integration | Apache-2.0 | `light` extra |
| Pillow | Image loading | HPND / historical PIL-compatible terms | `light` extra |
| Docling | Document extraction | MIT | `docling` extra |
| PySide6 | Desktop GUI | LGPL-3.0-only or commercial/GPL alternatives | `gui` extra |
| python-docx | Planned DOCX output | MIT | `docx` extra |
| pytest | Tests | MIT | `test` extra |

## Important Packaging Notes

- **PySide6 / Qt:** binary redistribution can trigger LGPL obligations, including
  notice, license-text, relinking/replacement, and source-offer considerations
  depending on how Qt is packaged. Review the exact Qt distribution before
  shipping a bundled desktop application.
- **Docling and models:** Docling has transitive dependencies and can obtain
  model artifacts separately. Model and dataset terms are not implied by the
  Docling package license and must be reviewed independently before redistribution.
- **Tesseract:** the external Tesseract executable and language data are system
  components, not vendored here. Their own notices apply when bundled.
- **Transitive dependencies:** create an SBOM or resolved license report from the
  release environment. This file intentionally does not claim completeness for
  packages introduced transitively.

Upstream package metadata and included license files are authoritative if this
summary conflicts with a dependency release.
