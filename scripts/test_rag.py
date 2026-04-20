"""
Quick test of the RAG pipeline after ingestion.

Usage:
    python scripts/test_rag.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.agents.rag_agent import answer

TEST_QUESTIONS = [
    "What is 5G NR numerology and what subcarrier spacings are supported?",
    "Explain the 5G standalone and non-standalone architecture.",
    "What are the security features in 5G core network?",
]

for q in TEST_QUESTIONS:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print("-" * 60)
    result = answer(q)
    print(f"A: {result['answer'][:500]}...")
    print(f"\nSources ({len(result['sources'])}):")
    for s in result["sources"]:
        print(f"  - {s['spec_name']} ({s['release']}) score={s['score']}")
    print(f"Sub-queries: {result['sub_queries']}")
