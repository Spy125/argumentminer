"""Segment text into argumentative units: claims, premises, and conclusions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class SegmentType(str, Enum):
    CLAIM      = "claim"
    PREMISE    = "premise"
    CONCLUSION = "conclusion"
    BACKGROUND = "background"


@dataclass
class Segment:
    text: str
    type: SegmentType
    confidence: float
    start_char: int
    end_char: int


# signal words that help identify each segment type
_CONCLUSION_SIGNALS = re.compile(
    r'\b(therefore|thus|hence|consequently|so|as a result|in conclusion|'
    r'it follows that|which means|this proves|this shows)\b', re.I
)
_PREMISE_SIGNALS = re.compile(
    r'\b(because|since|given that|as|for|in light of|considering that|'
    r'the fact that|evidence shows|studies show|research indicates)\b', re.I
)
_CLAIM_SIGNALS = re.compile(
    r'\b(I (argue|believe|claim|maintain|contend)|it is (clear|evident|obvious) that|'
    r'we (should|must|ought)|this (demonstrates|suggests|proves))\b', re.I
)


def _split_to_clauses(text: str) -> list[tuple[str, int, int]]:
    """Split text at sentence boundaries, returning (text, start, end) tuples."""
    parts = []
    for m in re.finditer(r'[^.!?]+[.!?]?', text):
        part = m.group().strip()
        if len(part) > 10:
            parts.append((part, m.start(), m.end()))
    return parts


class ArgumentSegmenter:
    """Identifies argument structure in text using signal word patterns."""

    def segment(self, text: str) -> list[Segment]:
        """Break text into typed argument segments."""
        clauses = _split_to_clauses(text)
        segments = []
        for clause, start, end in clauses:
            seg_type, conf = self._classify(clause)
            segments.append(Segment(
                text=clause,
                type=seg_type,
                confidence=conf,
                start_char=start,
                end_char=end,
            ))
        return segments

    def _classify(self, text: str) -> tuple[SegmentType, float]:
        """Return the most likely type and a rough confidence."""
        if _CONCLUSION_SIGNALS.search(text):
            return SegmentType.CONCLUSION, 0.85
        if _PREMISE_SIGNALS.search(text):
            return SegmentType.PREMISE, 0.80
        if _CLAIM_SIGNALS.search(text):
            return SegmentType.CLAIM, 0.75
        # default - treat as background text
        return SegmentType.BACKGROUND, 0.50

    def get_claims(self, text: str) -> list[Segment]:
        return [s for s in self.segment(text) if s.type == SegmentType.CLAIM]

    def get_premises(self, text: str) -> list[Segment]:
        return [s for s in self.segment(text) if s.type == SegmentType.PREMISE]
