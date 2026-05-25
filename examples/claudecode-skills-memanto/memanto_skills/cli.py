"""
CLI — Click-based command line interface for memanto-skills.
"""

from __future__ import annotations
import logging
import sys
import click
from memanto_skills.config import Config
from memanto_skills.injection import build_context_block, context_summary
from memanto_skills.memory import MemoryClient

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="memanto-skills")
def cli() -> None:
    """Cross-session memory for mattpocock/skills."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")


@cli.command()
@click.option("--force", is_flag=True, help="Re-create agent even if it exists.")
@click.option("--inject-limit", type=int, default=5, show_default=True, help="Max memories to inject per session.")
def init(force: bool, inject_limit: int) -> None:
    """Create a memanto agent for the current project."""
    cfg = Config()
    cfg.validate()
    client = MemoryClient(api_key=cfg.api_key)
    try:
        result = client.init_agent(cfg.agent_id, force=force)
        cfg.inject_limit = inject_limit
        cfg.save()
        click.echo(f"\u2713 Agent '{cfg.agent_id}' initialised.")
        click.echo(f"  Session expires: {result.get('expires_at', 'unknown')}")
    except Exception as exc:
        click.echo(f"\u2717 Failed: {exc}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--task", "-t", default="", help="Task description (for semantic query).")
@click.option("--max", "-m", "max_memories", type=int, default=5, help="Max memories to include.")
def inject(task: str, max_memories: int) -> None:
    """Print a context block for injection into an agent prompt."""
    cfg = Config()
    cfg.validate()
    client = MemoryClient(api_key=cfg.api_key)
    try:
        client.init_agent(cfg.agent_id)
    except Exception as exc:
        click.echo(f"\u2717 Failed to init agent: {exc}", err=True)
        sys.exit(1)
    context = build_context_block(client, task_hint=task, max_memories=max_memories)
    if context:
        click.echo(context)
    else:
        click.echo("<!-- memanto: no relevant memories found -->")


@cli.command()
@click.argument("source", required=False)
@click.option("--file", "-f", "file_path", type=click.Path(exists=True), help="File to extract memories from.")
@click.option("--type", "mem_type", default="transcript", show_default=True, help="Artifact type.")
def extract(source: str | None, file_path: str | None, mem_type: str) -> None:
    """Send text or a file to memanto for memory extraction."""
    cfg = Config()
    cfg.validate()
    client = MemoryClient(api_key=cfg.api_key)
    try:
        client.init_agent(cfg.agent_id)
    except Exception as exc:
        click.echo(f"\u2717 Failed to init agent: {exc}", err=True)
        sys.exit(1)
    if file_path:
        content = open(file_path, encoding="utf-8", errors="replace").read()
        source_label = file_path
    elif source:
        content = source
        source_label = "<stdin>"
    else:
        content = sys.stdin.read()
        source_label = "<pipe>"
    if not content.strip():
        click.echo("No content to extract.", err=True)
        sys.exit(1)
    from memanto_skills.extraction import extract_from_artifact
    stored = extract_from_artifact(client, content, artifact_type=mem_type)
    if stored:
        click.echo(f"\u2713 Stored {len(stored)} memories from {source_label}.")
        for s in stored:
            click.echo(f"  \u00b7 {s.get('type', '?')}: {s.get('memory_id', '?')[:12]}...")
    else:
        click.echo("No memories extracted (no new information found).")


@cli.command()
def status() -> None:
    """Show agent health and recent memories."""
    cfg = Config()
    try:
        cfg.validate()
    except RuntimeError as exc:
        click.echo(f"\u2717 {exc}", err=True)
        sys.exit(1)
    client = MemoryClient(api_key=cfg.api_key)
    try:
        client.init_agent(cfg.agent_id)
    except Exception as exc:
        click.echo(f"\u2717 Failed to init agent: {exc}", err=True)
        sys.exit(1)
    click.echo(f"Agent:     {cfg.agent_id}")
    click.echo(f"Project:   {cfg.project_dir}")
    try:
        sess = client.session_status()
        click.echo(f"Session:   active (expires {sess.get('expires_at', '?')})")
    except Exception:
        click.echo("Session:   inactive")
    summary = context_summary(client)
    click.echo(f"Memories:  {summary}")


@cli.command()
@click.argument("command", nargs=-1, required=True)
@click.option("--no-script", is_flag=True, help="Disable script(1) capture.")
@click.option("--task", "-t", default="", help="Task hint for memory retrieval.")
def exec_cmd(command: tuple[str, ...], no_script: bool, task: str) -> None:
    """Wrap a command with autonomous memory hooks (pre-inject, post-extract)."""
    from memanto_skills.executor import exec_command
    exit_code = exec_command(list(command), use_script=not no_script, task_hint=task)
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
