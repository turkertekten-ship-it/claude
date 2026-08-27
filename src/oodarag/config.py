"""Configuration.

TOML (stdlib `tomllib` since 3.11), with environment overrides, and defaults
that work with no config file at all. A pipeline that requires configuration
before it will run is a pipeline nobody evaluates.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_PATH = "oodarag.toml"


@dataclass
class SourceConfig:
    type: str                      # "filesystem" | "github" | "web" | "chat"
    options: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class Config:
    index_path: str = ".oodarag/index.db"
    state_path: str = ".oodarag/state.json"
    goldens_path: str = "evals/goldens.jsonl"
    embedder: str = "hashing"
    embedder_options: dict[str, Any] = field(default_factory=lambda: {"dim": 768})
    generator: str = "auto"
    top_k: int = 8
    sources: list[SourceConfig] = field(default_factory=list)
    repo_slugs: tuple[str, ...] = ()

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        config = cls()
        target = Path(path or os.environ.get("OODARAG_CONFIG", DEFAULT_PATH))
        if target.exists():
            data = tomllib.loads(target.read_text("utf-8"))
            core = data.get("oodarag", {})
            for key in ("index_path", "state_path", "goldens_path", "embedder",
                        "generator", "top_k"):
                if key in core:
                    setattr(config, key, core[key])
            if "embedder_options" in core:
                config.embedder_options = core["embedder_options"]
            if "repo_slugs" in core:
                config.repo_slugs = tuple(core["repo_slugs"])
            for entry in data.get("source", []):
                config.sources.append(SourceConfig(
                    type=entry.pop("type"),
                    enabled=entry.pop("enabled", True),
                    options=entry,
                ))
        # Environment wins over file: containers configure by env, and a stale
        # committed config file must never silently override a deployment.
        if value := os.environ.get("OODARAG_INDEX"):
            config.index_path = value
        if value := os.environ.get("OODARAG_GENERATOR"):
            config.generator = value
        if value := os.environ.get("OODARAG_EMBEDDER"):
            config.embedder = value
        return config

    def build_connectors(self) -> list[Any]:
        """Instantiate the configured connectors."""
        connectors: list[Any] = []
        for source in self.sources:
            if not source.enabled:
                continue
            options = dict(source.options)
            if source.type == "filesystem":
                from oodarag.ingest.filesystem import FilesystemConnector

                root = options.pop("root", ".")
                if "patterns" in options:
                    options["patterns"] = tuple(options["patterns"])
                if "exclude" in options:
                    options["exclude"] = tuple(options["exclude"])
                connectors.append(FilesystemConnector(root, **options))
            elif source.type == "github":
                from oodarag.ingest.github import GitHubConnector

                if "resources" in options:
                    options["resources"] = tuple(options["resources"])
                connectors.append(GitHubConnector(**options))
            elif source.type == "web":
                from oodarag.ingest.web import WebConnector

                seeds = options.pop("seeds", [])
                connectors.append(WebConnector(seeds, **options))
            elif source.type == "chat":
                from oodarag.ingest.chat import ChatTranscriptConnector

                connectors.append(ChatTranscriptConnector(**options))
            else:
                raise ValueError(f"unknown source type: {source.type!r}")
        return connectors
