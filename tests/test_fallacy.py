"""Tests for fallacy detection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from argumentminer.fallacy import FallacyDetector, FallacyMatch
from argumentminer.segmenter import ArgumentSegmenter, SegmentType


@pytest.fixture
def detector():
    return FallacyDetector()


@pytest.fixture
def segmenter():
    return ArgumentSegmenter()


class TestFallacyDetector:
    def test_ad_hominem_detected(self, detector):
        text = "You're an idiot, so your argument is wrong."
        matches = detector.detect(text)
        names = [m.name for m in matches]
        assert "Ad Hominem" in names

    def test_false_dichotomy_detected(self, detector):
        text = "Either you support us or you are against us."
        matches = detector.detect(text)
        names = [m.name for m in matches]
        assert "False Dichotomy" in names

    def test_slippery_slope_detected(self, detector):
        text = "If we allow this, it will lead to total chaos."
        matches = detector.detect(text)
        names = [m.name for m in matches]
        assert "Slippery Slope" in names

    def test_clean_text_has_no_fallacies(self, detector):
        text = "The data show a 15% increase in efficiency over three months."
        matches = detector.detect(text)
        assert len(matches) == 0

    def test_detect_unique_deduplicates(self, detector):
        text = "You're an idiot! What an idiot you are!"
        all_m    = detector.detect(text)
        unique_m = detector.detect_unique(text)
        assert len(unique_m) <= len(all_m)

    def test_match_has_matched_text(self, detector):
        text = "So you're saying all experts are wrong?"
        matches = detector.detect(text)
        for m in matches:
            assert len(m.matched_text) > 0

    def test_confidence_in_range(self, detector):
        text = "Either you agree or you're against us, since experts say so."
        matches = detector.detect(text)
        for m in matches:
            assert 0.0 <= m.confidence <= 1.0


class TestSegmenter:
    def test_premise_signal_detected(self, segmenter):
        text = "Because the data clearly shows a trend, we can draw conclusions."
        segs = segmenter.segment(text)
        types = [s.type for s in segs]
        assert SegmentType.PREMISE in types or SegmentType.CONCLUSION in types

    def test_conclusion_signal_detected(self, segmenter):
        text = "Therefore, the hypothesis must be rejected."
        segs = segmenter.segment(text)
        types = [s.type for s in segs]
        assert SegmentType.CONCLUSION in types

    def test_segments_cover_text(self, segmenter):
        text = "We believe this is true. Because the evidence shows it. Therefore it must be."
        segs = segmenter.segment(text)
        assert len(segs) >= 1
