"""Classify the relation between two argument segments (support vs attack)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from argumentminer.graph import RelationType

_ATTACK_SIGNALS = re.compile(
    r'\b(however|but|yet|although|despite|on the contrary|in contrast|'
    r'this (is wrong|fails|ignores)|not (true|correct|accurate)|'
    r'fails to (account for|consider|address)|contradicts|refutes|undermines)\b',
    re.I
)
_SUPPORT_SIGNALS = re.compile(
    r'\b(furthermore|moreover|additionally|also|in addition|'
    r'this (supports|confirms|demonstrates|shows|proves)|'
    r'as (shown|demonstrated|evidenced)|consistent with|'
    r'which (explains|confirms|supports))\b',
    re.I
)


@dataclass
class RelationResult:
    relation: RelationType
    confidence: float
    trigger_word: str


def classify_relation(text_a: str, text_b: str) -> RelationResult:
    """Classify whether text_b attacks or supports text_a."""
    # check text_b for signals (it's the one making the relation)
    combined = text_b

    attack_m  = _ATTACK_SIGNALS.search(combined)
    support_m = _SUPPORT_SIGNALS.search(combined)

    if attack_m and not support_m:
        return RelationResult(RelationType.ATTACK, 0.75, attack_m.group())
    if support_m and not attack_m:
        return RelationResult(RelationType.SUPPORT, 0.75, support_m.group())
    if attack_m and support_m:
        # both present - default to neutral (mixed signals)
        return RelationResult(RelationType.NEUTRAL, 0.5, "")
    return RelationResult(RelationType.NEUTRAL, 0.5, "")
