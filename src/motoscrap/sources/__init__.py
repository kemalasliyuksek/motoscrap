from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

from motoscrap.sources.base import BaseSource, SourceRegistry, registry

if TYPE_CHECKING:
    pass


def _autodiscover() -> None:
    package = importlib.import_module(__name__)
    for mod_info in pkgutil.iter_modules(package.__path__):
        if mod_info.name in {"base"}:
            continue
        importlib.import_module(f"{__name__}.{mod_info.name}")


_autodiscover()

__all__ = ["BaseSource", "SourceRegistry", "registry"]
