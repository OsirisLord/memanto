"""
Injection — Builds a concise Markdown context block from stored memories
to inject into the agent's system prompt at session start.
"""

from __future__ import annotations
import logging
from typing import Any
from memanto_skills.memory import MemoryClient

logger = logging.getLogger(__name__)


def build_context_block(client: MemoryClient, task_hint: str = "", max_memories: int = 5) -> str:
    blocks: list[str] = []
    if task_hint:
        memories = client.recall(query=task_hint, limit=max_memories)
    else:
        memories = client.recall_recent(limit=max_memories)
    if not memories:
        return ""
    by_type: dict[str, list[dict[str, Any]]] = {}
    for m in memories:
        mt = m.get("type", "fact") or "fact"
        by_type.setdefault(mt, []).append(m)
    blocks.append("<!-- memanto: past context -->\n")
    type_labels = {
        "decision": "Past decisions",
        "preference": "Preferences",
        "fact": "Codebase facts",
        "goal": "Active goals",
        "artifact": "Artifacts",
        "learning": "Past learnings",
    }
    for mem_type in ("decision", "preference", "fact", "goal", "artifact", "learning"):
        entries = by_type.pop(mem_type, [])
        if not entries:
            continue
        label = type_labels.get(mem_type, mem_type)
        bullets = "\n".join(f"- {e.get('title', '(no title)')}" for e in entries[:3])
        blocks.append(f"**{label}:**\n{bullets}\n")
    for rest_type, entries in by_type.items():
        blocks.append(f"**{rest_type.capitalize()}:**\n" + "\n".join(f"- {e.get('title', '(no title)')}" for e in entries[:2]) + "\n")
    result = "\n".join(blocks)
    lines = result.split("\n")
    if len(lines) > 20:
        result = "\n".join(lines[:18]) + "\n... _(more memories available)_"
    return result


def context_summary(client: MemoryClient) -> str:
    try:
        recent = client.recall_recent(limit=1)
        count = len(recent)
        if count == 0:
            return "No memories stored yet."
        first = recent[0]
        title = first.get("title", "?")
        return f'{count}+ memories. Most recent: "{title}"'
    except Exception as exc:
        return f"Memory unavailable: {exc}"
