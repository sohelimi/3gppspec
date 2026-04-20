# Contributing to 3gppSpec

Thank you for your interest in contributing!

## Ways to Contribute

- **Add more spec series** — extend ingestion to cover more 3GPP series
- **Improve chunking** — better section-aware splitting for 3GPP document structure
- **UI improvements** — enhance the chat interface
- **Bug fixes** — open an issue first to discuss

## Getting Started

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Set up locally following the README Quick Start
4. Make your changes
5. Open a Pull Request with a clear description

## Adding New Spec Series

Edit `INGEST_SERIES` in `.env` and re-run:
```bash
python scripts/ingest.py --releases Rel-18 --series YOUR_SERIES
```

## Reporting Issues

Open a GitHub issue with:
- Your OS and Python version
- The error message
- Steps to reproduce
