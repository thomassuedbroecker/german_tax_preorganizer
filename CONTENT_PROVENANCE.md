# Content Provenance

## Development Provenance

This repository has been developed with human direction and review and with
assistance from coding tools, including Claude Code and OpenAI Codex. The project
owner selected requirements, reviewed changes, ran tests, and accepted the
resulting implementation.

The files under `prompts/` document development interactions and requirements.
They are not runtime prompts loaded by the application.

## Review Expectations

AI-assisted content is treated like any other contribution:

- It must be reviewed for correctness, privacy, security, and maintainability.
- It must not knowingly reproduce third-party code without preserving applicable
  license obligations.
- Tests and repository review provide evidence of human selection and validation,
  but do not by themselves prove absence of public-code similarity.
- Contributors should disclose substantial generated content when that context is
  useful for review or provenance.

## Runtime AI

The optional Ollama integration generates a local post-sort review. It does not
classify documents or determine file placement. The runtime prompt is owned by
`src/invoice_sorter/ai_review.py`; full extracted invoice text and private source
paths are excluded from that prompt by design and tests.

## External Artifacts

No model weights, training datasets, or third-party source trees are committed to
this repository. Optional extraction/model downloads remain subject to their own
terms and provenance requirements.

This record is provided for transparency and is not a legal determination of
copyright ownership or license compatibility.
