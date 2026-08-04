"""Edgmes-owned filesystem layout and home isolation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping


class HomeConfigurationError(ValueError):
    """Raised when the Edgmes home override is invalid."""


@dataclass(frozen=True)
class EdgmesHome:
    """Resolved Edgmes root and its named state directories."""

    root: Path

    @classmethod
    def resolve(
        cls,
        explicit: str | os.PathLike[str] | None = None,
        *,
        environ: Mapping[str, str] | None = None,
        user_home: str | os.PathLike[str] | None = None,
    ) -> "EdgmesHome":
        env = os.environ if environ is None else environ
        configured = explicit if explicit is not None else env.get("EDGMES_HOME")
        if configured is None:
            base = Path.home() if user_home is None else Path(user_home).expanduser()
            root = base / ".edgmes"
        else:
            root = Path(configured).expanduser()
            if not root.is_absolute():
                raise HomeConfigurationError(
                    "EDGMES_HOME must be an absolute path"
                )
        return cls(root.resolve())

    @property
    def config(self) -> Path:
        return self.root / "config"

    @property
    def state(self) -> Path:
        return self.root / "state"

    @property
    def sessions(self) -> Path:
        return self.state / "sessions"

    @property
    def skills(self) -> Path:
        return self.root / "skills"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def runtime(self) -> Path:
        return self.root / "runtime"

    @property
    def directories(self) -> tuple[Path, ...]:
        return (
            self.root,
            self.config,
            self.state,
            self.sessions,
            self.skills,
            self.cache,
            self.logs,
            self.runtime,
        )

    def initialize(self) -> None:
        """Create only Edgmes-owned directories."""
        for directory in self.directories:
            directory.mkdir(parents=True, exist_ok=True)
