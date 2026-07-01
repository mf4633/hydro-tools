r"""
Path utilities that replace the hundreds of hard-coded Z: and C:\Users\... paths.
"""
from pathlib import Path
import os

def get_project_root() -> Path:
    """Walk up from this file until we find a recognizable project marker."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "board-gaming").exists():
            return parent
    return p.parent.parent  # fallback

def resolve_model_path(relative: str) -> Path:
    r"""
    Resolve a path that may be relative to the project or an environment var.
    Supports common patterns seen in the old scripts:
      - Z:/Shared/Projects/...
      - C:\Users\michael.flynn\OneDrive - McGill Associates, PA\...
    """
    root = get_project_root()
    p = Path(relative)

    if p.is_absolute():
        return p

    # Try relative to project root first
    candidate = root / relative
    if candidate.exists():
        return candidate

    # Environment override (recommended for new work)
    base = os.environ.get("HYDRO_PROJECT_BASE")
    if base:
        return Path(base) / relative

    # Last resort: current working dir (old behavior)
    return Path.cwd() / relative
