"""
Query Planning Agent.
Decomposes a complex user question into focused sub-queries
that can each be answered by the vector store.
"""

import json
import re
from loguru import logger
from backend.llm.groq_client import generate

PLANNER_SYSTEM = """You are an expert in 3GPP telecommunications standards.
Your job is to decompose a user question into 2-4 focused sub-queries
that together cover all aspects of the question.
Each sub-query should be self-contained and retrievable from a vector database of 3GPP specs.

Respond ONLY with a JSON array of strings. Example:
["What is the 5G NR frame structure?", "What are the numerology options in 5G NR?"]
"""


def plan_queries(question: str) -> list[str]:
    """
    Returns a list of sub-queries for a given user question.
    Falls back to the original question if planning fails.
    """
    prompt = f"Decompose this question into focused sub-queries:\n\n{question}"
    try:
        response = generate(prompt, system_prompt=PLANNER_SYSTEM, temperature=0.1)
        # Extract JSON array from response
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            queries = json.loads(match.group())
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                logger.debug(f"Planned {len(queries)} sub-queries for: {question[:60]}")
                return queries
    except Exception as e:
        logger.warning(f"Query planning failed, using original question: {e}")
    return [question]
