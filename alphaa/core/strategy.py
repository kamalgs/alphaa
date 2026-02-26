"""Strategy definition for AlphaA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from alphaa.core.conditions import ConditionBase

if TYPE_CHECKING:
    from alphaa.core.protocols import Indicator


@dataclass(frozen=True)
class Strategy:
    name: str
    entry: ConditionBase
    exit: ConditionBase
    indicators: list[Indicator] = field(default_factory=list)
    params: dict[str, object] = field(default_factory=dict)
