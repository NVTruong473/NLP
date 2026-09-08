from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv


def load_provider_env(path: str | Path = "/content/providers.env") -> Path:
    """Load API keys without ever printing their values."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Upload providers.env to /content in Colab or copy it from your private Google Drive."
        )
    load_dotenv(path, override=True)
    return path


def _sorted_keys(prefix: str) -> list[str]:
    pattern = re.compile(rf"^{re.escape(prefix)}(?:_(\d+))?$")
    found: list[tuple[int, str]] = []
    for name, value in os.environ.items():
        m = pattern.match(name)
        if m and value.strip():
            order = int(m.group(1)) if m.group(1) else 0
            found.append((order, value.strip()))
    return [value for _, value in sorted(found, key=lambda x: x[0])]


def gemini_keys() -> list[str]:
    return _sorted_keys("GEMINI_API_KEY")


def openrouter_keys() -> list[str]:
    return _sorted_keys("OPENROUTER_API_KEY")


def key_summary() -> dict[str, int]:
    return {"gemini_keys": len(gemini_keys()), "openrouter_keys": len(openrouter_keys())}


class KeyPool:
    def __init__(self, keys: Iterable[str]):
        self.keys = [k for k in keys if k]
        self.index = 0

    def __bool__(self) -> bool:
        return bool(self.keys)

    def ordered(self) -> list[str]:
        if not self.keys:
            return []
        i = self.index % len(self.keys)
        return self.keys[i:] + self.keys[:i]

    def mark_success(self, key: str) -> None:
        if key in self.keys:
            self.index = self.keys.index(key)

    def mark_failure(self, key: str) -> None:
        if key in self.keys:
            self.index = (self.keys.index(key) + 1) % len(self.keys)
