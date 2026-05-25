"""
Extraction — Uses memanto's own RAG (answer endpoint) to turn session
transcripts, diffs, and handoff docs into structured memories.
No fragile heuristic parsing.
"""

from __future__ import annotations
import json
import logging
import re
from typing import Any
from memanto_skills.memory import MemoryClient

logger = logging.getLogger(__name__)

_EXTRACT_PROMPT = """\
You are an engineering memory curator. Extract key information from the
following session transcript into structured memories.

For each memory, respond with a JSON array of objects. Each object must have:
  - "type": one of "decision", "preference", "fact", "goal", "artifact", "learning"
  - "title": a short title (max 80 chars)
  - "content": a detailed description of the memory
  - "tags": relevant tags (e.g. ["react", "data-fetching"])

Guidelines:
  - Decisions: architectural or design choices
  - Preferences: framework or style preferences
  - Facts: codebase facts ("The API is at /api/v1", "We use pnpm")
  - Goals: active objectives
  - Artifacts: documents or files created
  - Learning: insights or lessons learned

Return ONLY valid JSON. If nothing to extract, return [].
"""

_DIFF_EXTRACT_PROMPT = """\
You are an engineering memory curator. Extract codebase conventions,
refactoring decisions, and structural changes from the following git diff.

Respond with a JSON array of memory objects. Each object must have:
  - "type": one of "decision", "preference", "fact", "goal", "artifact", "learning"
  - "title": a short title (max 80 chars)
  - "content": a detailed description
  - "tags": relevant tags

Return ONLY valid JSON. If nothing to extract, return [].
"""


def extract_from_transcript(client: MemoryClient, transcript: str) -> list[dict[str, Any]]:
    if not transcript.strip():
        logger.info("Empty transcript — nothing to extract.")
        return []
    result = client.answer(
        question=_EXTRACT_PROMPT + "\n\n---\n" + transcript,
        limit=20,
        header_prompt="Extract structured memories from this transcript.",
    )
    memories = _parse_answer(result.get("answer", ""))
    stored = _store_memories(client, memories)
    logger.info("Extracted %d memories from transcript.", len(stored))
    return stored


def extract_from_diff(client: MemoryClient, diff_content: str) -> list[dict[str, Any]]:
    if not diff_content.strip():
        return []
    result = client.answer(
        question=_DIFF_EXTRACT_PROMPT + "\n\n---\n" + diff_content,
        limit=15,
        header_prompt="Extract codebase conventions from this diff.",
    )
    memories = _parse_answer(result.get("answer", ""))
    stored = _store_memories(client, memories)
    logger.info("Extracted %d memories from diff.", len(stored))
    return stored


def extract_from_artifact(client: MemoryClient, text: str, artifact_type: str = "general") -> list[dict[str, Any]]:
    return extract_from_transcript(client, f"[Artifact type: {artifact_type}]\n\n{text}")


def _parse_answer(answer_text: str) -> list[dict[str, Any]]:
    if not answer_text:
        return []
    match = re.search(r"\[\s*\{.*\}\s*\]", answer_text, re.DOTALL)
    if not match:
        logger.warning("No JSON array found in LLM answer.")
        return []
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse LLM answer as JSON: %s", exc)
        return []


def _store_memories(client: MemoryClient, memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored: list[dict[str, Any]] = []
    for mem in memories:
        mem_type = mem.get("type", "fact")
        title = mem.get("title", "")[:80]
        content = mem.get("content", "")
        tags = mem.get("tags", [])
        if not content:
            continue
        try:
            result = client.store(mem_type, title, content, tags=tags)
            stored.append(result)
        except Exception as exc:
            logger.warning("Failed to store memory '%s': %s", title, exc)
    return stored
