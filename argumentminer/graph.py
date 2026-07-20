"""Build an argument graph: nodes are segments, edges are support/attack relations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from argumentminer.segmenter import Segment, SegmentType


class RelationType(str, Enum):
    SUPPORT = "support"
    ATTACK  = "attack"
    NEUTRAL = "neutral"


@dataclass
class ArgumentNode:
    id: str
    segment: Segment
    depth: int = 0    # 0 = root claim, 1 = direct premise/rebuttal, etc.


@dataclass
class ArgumentEdge:
    source_id: str
    target_id: str
    relation: RelationType
    confidence: float


@dataclass
class ArgumentGraph:
    nodes: list[ArgumentNode] = field(default_factory=list)
    edges: list[ArgumentEdge] = field(default_factory=list)

    def add_node(self, node: ArgumentNode) -> None:
        self.nodes.append(node)

    def add_edge(self, edge: ArgumentEdge) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> ArgumentNode | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    def children_of(self, node_id: str) -> list[ArgumentNode]:
        child_ids = {e.source_id for e in self.edges if e.target_id == node_id}
        return [n for n in self.nodes if n.id in child_ids]

    def roots(self) -> list[ArgumentNode]:
        """Nodes with no incoming support/attack edges."""
        has_parent = {e.source_id for e in self.edges}
        return [n for n in self.nodes if n.id not in has_parent]

    def to_dict(self) -> dict:
        return {
            "nodes": [{"id": n.id, "text": n.segment.text,
                       "type": n.segment.type, "depth": n.depth}
                      for n in self.nodes],
            "edges": [{"source": e.source_id, "target": e.target_id,
                       "relation": e.relation, "confidence": e.confidence}
                      for e in self.edges],
        }


def build_graph(segments: list[Segment]) -> ArgumentGraph:
    """Build a simple argument graph from segmented text.

    Claims become roots. Premises connect to the nearest claim as support.
    Conclusions are attached to the last claim.
    """
    graph = ArgumentGraph()
    last_claim_id: str | None = None

    for i, seg in enumerate(segments):
        node_id = f"seg_{i}"
        depth   = 0 if seg.type == SegmentType.CLAIM else 1
        node    = ArgumentNode(id=node_id, segment=seg, depth=depth)
        graph.add_node(node)

        if seg.type == SegmentType.CLAIM:
            last_claim_id = node_id

        elif seg.type == SegmentType.PREMISE and last_claim_id:
            graph.add_edge(ArgumentEdge(
                source_id=node_id,
                target_id=last_claim_id,
                relation=RelationType.SUPPORT,
                confidence=seg.confidence,
            ))

        elif seg.type == SegmentType.CONCLUSION and last_claim_id:
            graph.add_edge(ArgumentEdge(
                source_id=last_claim_id,
                target_id=node_id,
                relation=RelationType.SUPPORT,
                confidence=seg.confidence,
            ))

    return graph
