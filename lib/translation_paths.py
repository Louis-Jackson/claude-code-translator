"""Paths for project-scoped translation output."""

import hashlib
import re
from pathlib import Path
from typing import Optional, Union


PathLike = Union[str, Path]
BASE_CACHE_DIR = Path.home() / ".cache" / "claude-code-translator"


def cache_dir() -> Path:
    """Return the base cache directory."""
    return BASE_CACHE_DIR


def project_slug(project_cwd: PathLike) -> str:
    """Create a stable, readable slug for a project path."""
    project_path = Path(project_cwd).expanduser().resolve(strict=False)
    project_str = str(project_path)
    name = project_path.name or "root"
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "project"
    safe_name = safe_name[:48]
    digest = hashlib.sha1(project_str.encode("utf-8")).hexdigest()[:10]
    return f"{safe_name}-{digest}"


def project_label(project_cwd: Optional[PathLike]) -> str:
    """Return a human-readable project label."""
    if not project_cwd:
        return "global"
    return str(Path(project_cwd).expanduser().resolve(strict=False))


def latest_translation_path(project_cwd: Optional[PathLike] = None) -> Path:
    """Return the latest translation path for a project or the global fallback."""
    if not project_cwd:
        return cache_dir() / "latest_translation.md"
    return cache_dir() / "projects" / project_slug(project_cwd) / "latest_translation.md"
