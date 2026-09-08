# Data

This repository does **not** commit private institutional documents.

Supported ingestion inputs:

- text-based PDF (`.pdf`)
- Word (`.docx`)
- text / Markdown (`.txt`, `.md`)
- HTML files
- explicit public HTTP/HTTPS URLs

`demo_sources.yaml` contains a small set of official public TDTU pages for a reproducible demo. For a real deployment, replace them with the documents for your own organization/domain.

Place local documents under `data/uploads/` in Colab. This path is ignored by Git so private documents are not committed accidentally.

Scanned-image PDFs are intentionally not OCR'd in v1. The system fails visibly instead of pretending a blank extraction succeeded; multimodal ingestion can be added as a separate evaluated feature.
