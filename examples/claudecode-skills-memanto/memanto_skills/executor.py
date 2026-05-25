"""
Executor — Wraps any CLI command (e.g. claude) with autonomous
pre-inject and post-extract hooks using script(1) to capture the
interactive session transcript.
"""

from __future__ import annotations
import logging
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from memanto_skills.config import Config
from memanto_skills.injection import build_context_block
from memanto_skills.memory import MemoryClient

logger = logging.getLogger(__name__)
_TEMP_PREFIX = "memanto-session-"
_SCRIPT_CMD = "script"


def _can_use_script() -> bool:
    if sys.platform == "win32":
        return False
    try:
        result = subprocess.run(["which", _SCRIPT_CMD], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _find_git_diff(since: float) -> str:
    try:
        since_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(since))
        result = subprocess.run(["git", "diff", f"--since={since_iso}"], capture_output=True, text=True, timeout=10)
        return result.stdout if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _find_artifacts_after(since: float) -> list[Path]:
    candidates: list[Path] = []
    temp_dirs = [Path(tempfile.gettempdir()), Path.home() / ".memanto" / "exports"]
    for d in temp_dirs:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.stat().st_mtime > since:
                candidates.append(f)
    return candidates


def exec_command(command: list[str], use_script: bool | None = None, task_hint: str = "") -> int:
    cfg = Config()
    cfg.validate()
    client = MemoryClient(api_key=cfg.api_key)
    try:
        client.init_agent(cfg.agent_id)
    except Exception as exc:
        logger.error("Failed to init memanto agent: %s", exc)
        return 1
    context = build_context_block(client, task_hint=task_hint)
    if context:
        print(context, file=sys.stderr, flush=True)
        logger.info("Injected %d lines of past context.", len(context.split("\n")))
    can_script = _can_use_script() if use_script is None else use_script
    session_start = time.time()
    transcript_path: Path | None = _exec_with_script(command) if can_script else _exec_without_script(command)
    if transcript_path is None:
        result = subprocess.run(command, check=False)
        return result.returncode
    try:
        if transcript_path.exists():
            transcript = transcript_path.read_text(encoding="utf-8", errors="replace")
            if len(transcript) > 100:
                _extract_and_store(client, transcript, session_start)
    except Exception as exc:
        logger.warning("Post-extract failed (non-fatal): %s", exc)
    finally:
        if transcript_path.exists():
            try:
                transcript_path.unlink()
            except OSError:
                pass
    return 0


def _exec_with_script(command: list[str]) -> Path | None:
    tmp = tempfile.NamedTemporaryFile(prefix=_TEMP_PREFIX, suffix=".log", delete=False)
    log_path = Path(tmp.name)
    tmp.close()
    cmd_str = " ".join(shlex.quote(c) for c in command)
    try:
        subprocess.run([_SCRIPT_CMD, "-q", str(log_path), "sh", "-c", cmd_str], check=False)
    except FileNotFoundError:
        logger.error("script(1) not found.")
        return None
    return log_path


def _exec_without_script(command: list[str]) -> Path | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    except (subprocess.TimeoutExpired, Exception) as exc:
        logger.warning("Command failed or timed out: %s", exc)
        return None
    combined = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    tmp = tempfile.NamedTemporaryFile(prefix=_TEMP_PREFIX, suffix=".log", delete=False, mode="w", encoding="utf-8")
    tmp.write(combined)
    log_path = Path(tmp.name)
    tmp.close()
    return log_path


def _extract_and_store(client: MemoryClient, transcript: str, session_start: float) -> None:
    from memanto_skills.extraction import extract_from_transcript, extract_from_diff
    stored = extract_from_transcript(client, transcript)
    if stored:
        logger.info("Stored %d memories from session transcript.", len(stored))
    diff = _find_git_diff(session_start)
    if diff:
        diff_stored = extract_from_diff(client, diff)
        if diff_stored:
            logger.info("Stored %d memories from git diff.", len(diff_stored))
    artifacts = _find_artifacts_after(session_start)
    for artifact in artifacts:
        try:
            text = artifact.read_text(encoding="utf-8", errors="replace")
            if len(text) > 50:
                from memanto_skills.extraction import extract_from_artifact
                art_stored = extract_from_artifact(client, text, artifact.suffix)
                if art_stored:
                    logger.info("Stored %d memories from artifact %s.", len(art_stored), artifact.name)
        except Exception as exc:
            logger.debug("Skipped artifact %s: %s", artifact.name, exc)
