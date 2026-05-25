"""
Configuration loader — resolves MOORCHEH_API_KEY and project-level settings.
"""

import os
import json
from pathlib import Path

_DEFAULT_INJECT_LIMIT = 5
_CONFIG_DIR_NAME = ".memanto-skills"
_CONFIG_FILE = "project.json"


def _project_root() -> Path:
    markers = ("pyproject.toml", "package.json", "go.mod", "Cargo.toml", ".git")
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if any((parent / m).exists() for m in markers):
            return parent
    return cwd


class Config:
    def __init__(self) -> None:
        self.api_key: str = os.environ.get("MOORCHEH_API_KEY", "")
        self.project_dir: Path = _project_root()
        self.agent_id: str = self.project_dir.name
        self.inject_limit: int = _DEFAULT_INJECT_LIMIT
        self._load_project_config()

    def _load_project_config(self) -> None:
        config_dir = Path.home() / _CONFIG_DIR_NAME
        config_file = config_dir / self.agent_id / _CONFIG_FILE
        if config_file.exists():
            try:
                data = json.loads(config_file.read_text())
                self.inject_limit = int(data.get("inject_limit", self.inject_limit))
            except (json.JSONDecodeError, ValueError):
                pass

    def save(self) -> None:
        config_dir = Path.home() / _CONFIG_DIR_NAME / self.agent_id
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / _CONFIG_FILE).write_text(
            json.dumps({"inject_limit": self.inject_limit}, indent=2)
        )

    def validate(self) -> None:
        if not self.api_key:
            raise RuntimeError(
                "MOORCHEH_API_KEY environment variable is not set."
            )
