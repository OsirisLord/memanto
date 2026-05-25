"""
Tests for extraction module — focus on _parse_answer edge cases and
_store_memories filtering.
"""

from __future__ import annotations
import json
from unittest.mock import MagicMock
from memanto_skills.extraction import _parse_answer, _store_memories


class TestParseAnswer:
    def test_empty_answer(self) -> None:
        assert _parse_answer("") == []

    def test_no_json_in_answer(self) -> None:
        assert _parse_answer("I found no decisions to extract.") == []

    def test_valid_json_array(self) -> None:
        answer = json.dumps([
            {"type": "decision", "title": "Use SWR", "content": "Chose SWR over React Query"},
            {"type": "fact", "title": "API base", "content": "API at /api/v1"},
        ])
        result = _parse_answer(answer)
        assert len(result) == 2
        assert result[0]["type"] == "decision"

    def test_json_array_in_markdown_block(self) -> None:
        answer = """Here are the memories:\n```json\n[{"type": "decision", "title": "Use pnpm", "content": "Switched from npm to pnpm"}]\n```"""
        result = _parse_answer(answer)
        assert len(result) == 1

    def test_malformed_json(self) -> None:
        assert _parse_answer("[{broken: true,]") == []

    def test_not_a_list(self) -> None:
        assert _parse_answer('{"type": "decision"}') == []

    def test_empty_list(self) -> None:
        assert _parse_answer("[]") == []


class TestStoreMemories:
    def test_all_valid(self) -> None:
        client = MagicMock()
        client.store.return_value = {"memory_id": "abc123", "type": "decision"}
        memories = [
            {"type": "decision", "title": "A", "content": "Content A", "tags": ["test"]},
            {"type": "fact", "title": "B", "content": "Content B", "tags": []},
        ]
        result = _store_memories(client, memories)
        assert len(result) == 2

    def test_skips_empty_content(self) -> None:
        client = MagicMock()
        memories = [
            {"type": "decision", "title": "Has content", "content": "Real content"},
            {"type": "fact", "title": "Empty", "content": ""},
        ]
        result = _store_memories(client, memories)
        assert len(result) == 1

    def test_handles_store_failure(self) -> None:
        client = MagicMock()
        client.store.side_effect = [{"memory_id": "ok"}, ValueError("bad type")]
        memories = [
            {"type": "decision", "title": "Good", "content": "Good content"},
            {"type": "invalid", "title": "Bad", "content": "Bad content"},
        ]
        result = _store_memories(client, memories)
        assert len(result) == 1
