"""
Run the 3GPP spec ingestion pipeline.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --releases Rel-18 --series 38_series,23_series
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.config import settings
from backend.rag.ingestion.pipeline import run_ingestion
from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="Ingest 3GPP specs into ChromaDB")
    parser.add_argument("--specs-dir", default=settings.specs_dir)
    parser.add_argument("--releases", default=settings.ingest_releases)
    parser.add_argument("--series", default=settings.ingest_series)
    parser.add_argument("--chroma-path", default=settings.chroma_db_path)
    args = parser.parse_args()

    releases = [r.strip() for r in args.releases.split(",")]
    series = [s.strip() for s in args.series.split(",")]

    logger.info(f"Specs dir  : {args.specs_dir}")
    logger.info(f"Releases   : {releases}")
    logger.info(f"Series     : {series}")
    logger.info(f"ChromaDB   : {args.chroma_path}")

    total = run_ingestion(
        specs_dir=args.specs_dir,
        releases=releases,
        series=series,
        chroma_path=args.chroma_path,
    )
    logger.success(f"Done. {total} chunks stored in ChromaDB.")


if __name__ == "__main__":
    main()
