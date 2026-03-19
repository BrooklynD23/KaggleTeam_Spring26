"""Disk usage tracker for pipeline outputs (figures, tables, curated data)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TrackDiskUsage:
    """Disk usage for one track or shared outputs."""

    figures_bytes: int
    tables_bytes: int
    curated_bytes: int  # shared only; 0 for tracks
    logs_bytes: int

    @property
    def total_bytes(self) -> int:
        return self.figures_bytes + self.tables_bytes + self.curated_bytes + self.logs_bytes


def _dir_size(path: Path) -> int:
    """Return total size in bytes of all files under path (recursive)."""
    if not path.is_dir():
        return 0
    total = 0
    try:
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def _files_matching_prefix(dir_path: Path, prefix: str) -> int:
    """Return total size in bytes of files whose name starts with prefix."""
    if not dir_path.is_dir():
        return 0
    total = 0
    try:
        for p in dir_path.iterdir():
            if p.is_file() and p.name.startswith(prefix):
                try:
                    total += p.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def format_bytes(n: int) -> str:
    """Format byte count as human-readable string (e.g. 1.2 MB)."""
    if n < 0:
        return "0 B"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.1f} GB"


def compute_outputs_disk_usage(repo_root: Path) -> dict[str, TrackDiskUsage]:
    """Compute disk usage for figures, tables, curated data, and logs per track.

    Returns a dict mapping approach id (shared, track_a, ...) to TrackDiskUsage.
    """
    figures_dir = repo_root / "outputs" / "figures"
    tables_dir = repo_root / "outputs" / "tables"
    curated_dir = repo_root / "data" / "curated"
    logs_dir = repo_root / "outputs" / "logs"

    tracks = ("track_a", "track_b", "track_c", "track_d", "track_e")

    result: dict[str, TrackDiskUsage] = {}

    # Shared: curated data + orchestrator/shared logs
    shared_curated = _dir_size(curated_dir)
    shared_logs = 0
    shared_logs_path = logs_dir / "orchestrator" / "shared"
    if shared_logs_path.is_dir():
        shared_logs = _dir_size(shared_logs_path)
    result["shared"] = TrackDiskUsage(
        figures_bytes=0,
        tables_bytes=0,
        curated_bytes=shared_curated,
        logs_bytes=shared_logs,
    )

    # Per-track: figures + tables + orchestrator/<track> logs
    for track in tracks:
        fig = _files_matching_prefix(figures_dir, f"{track}_")
        tab = _files_matching_prefix(tables_dir, f"{track}_")
        track_logs = 0
        track_logs_path = logs_dir / "orchestrator" / track
        if track_logs_path.is_dir():
            track_logs = _dir_size(track_logs_path)
        # Also count track-specific logs in logs/ root (e.g. track_a_s6_leakage_audit.log)
        track_logs_root = _files_matching_prefix(logs_dir, f"{track}_")
        result[track] = TrackDiskUsage(
            figures_bytes=fig,
            tables_bytes=tab,
            curated_bytes=0,
            logs_bytes=track_logs + track_logs_root,
        )

    return result


def total_outputs_bytes(usage: dict[str, TrackDiskUsage]) -> int:
    """Return total bytes across all tracks."""
    return sum(u.total_bytes for u in usage.values())
