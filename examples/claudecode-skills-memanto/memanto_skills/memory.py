"""
Memanto SDK wrapper — thin facade over memanto SdkClient tailored for the
skills lifecycle.

Exposes: init_agent, store_memories, recall_context, query_llm
"""

from __future__ import annotations
import logging
from typing import Any
from memanto.cli.client.sdk_client import SdkClient
from memanto.app.utils.errors import AgentNotFoundError

logger = logging.getLogger(__name__)
_MEMORY_TYPES = ("decision", "preference", "fact", "goal", "artifact", "learning")


class MemoryClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: SdkClient | None = None
        self._agent_id: str | None = None

    def init_agent(self, agent_id: str, force: bool = False) -> dict[str, Any]:
        self._client = SdkClient(api_key=self._api_key)
        try:
            self._client.create_agent(agent_id=agent_id, pattern="project")
            logger.info("Created new agent '%s'", agent_id)
        except Exception as exc:
            err_msg = str(exc).lower()
            if "already" in err_msg or "exists" in err_msg:
                logger.info("Agent '%s' already exists, reusing.", agent_id)
            elif "not found" in err_msg:
                if force:
                    logger.warning("Agent resources missing; forcing reinit.")
                else:
                    raise AgentNotFoundError(f"Agent '{agent_id}' not found.") from exc
            else:
                raise
        activation = self._client.activate_agent(agent_id)
        self._agent_id = agent_id
        return activation

    @property
    def agent_id(self) -> str:
        if self._agent_id is None:
            raise RuntimeError("No agent initialised. Call init_agent() first.")
        return self._agent_id

    def store(self, memory_type: str, title: str, content: str, tags: list[str] | None = None, confidence: float = 0.85) -> dict[str, Any]:
        if memory_type not in _MEMORY_TYPES:
            raise ValueError(f"Unsupported memory_type '{memory_type}'.")
        return self._client.remember(
            agent_id=self.agent_id,
            memory_type=memory_type,
            title=title[:100],
            content=content,
            confidence=confidence,
            tags=tags or [],
            source="skill-execution",
            provenance="explicit_statement",
        )

    def recall(self, query: str, limit: int = 5, type_filter: list[str] | None = None) -> list[dict[str, Any]]:
        result = self._client.recall(
            agent_id=self.agent_id,
            query=query,
            limit=limit,
            type=type_filter,
        )
        return result.get("memories", [])

    def recall_recent(self, limit: int = 5, type_filter: list[str] | None = None) -> list[dict[str, Any]]:
        result = self._client.recall_recent(
            agent_id=self.agent_id,
            limit=limit,
            type=type_filter,
        )
        return result.get("memories", [])

    def answer(self, question: str, limit: int = 10, header_prompt: str | None = None) -> dict[str, Any]:
        return self._client.answer(
            agent_id=self.agent_id,
            question=question,
            limit=limit,
            header_prompt=header_prompt,
        )

    def session_status(self) -> dict[str, Any]:
        return self._client.get_session_info()

    def deactivate(self) -> dict[str, Any]:
        result = self._client.deactivate_agent(self.agent_id)
        self._agent_id = None
        return result
