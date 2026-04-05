"""
Unit tests for _extract_seq in main.py.
"""
import pytest
from mapcat.main import _extract_seq


def test_seq_at_end():
    seq, content = _extract_seq("add-polyline (52.5,13.4) color=blue seq=3")
    assert seq == 3
    assert content == "add-polyline (52.5,13.4) color=blue"


def test_seq_in_middle():
    seq, content = _extract_seq("add-polyline (52.5,13.4) seq=1 color=blue")
    assert seq == 1
    assert content == "add-polyline (52.5,13.4) color=blue"


def test_seq_at_start():
    seq, content = _extract_seq("seq=2 add-polyline (52.5,13.4)")
    assert seq == 2
    assert content == "add-polyline (52.5,13.4)"


def test_no_seq_returns_none():
    seq, content = _extract_seq("add-polyline (52.5,13.4) color=blue")
    assert seq is None
    assert content == "add-polyline (52.5,13.4) color=blue"


def test_last_seq_taken_when_multiple():
    """When content contains multiple seq= tokens, the last one is the protocol seq."""
    seq, content = _extract_seq("data seq=10 color=red seq=1")
    assert seq == 1
    assert content == "data seq=10 color=red"


def test_no_false_positive_on_embedded_seq():
    """my_step_seq=5 must not be mistaken for seq=5."""
    seq, content = _extract_seq("add-marker (1,2) my_step_seq=5 seq=10")
    assert seq == 10
    assert content == "add-marker (1,2) my_step_seq=5"


def test_whitespace_preserved_around_mid_seq():
    """Removing seq=N from the middle must not merge adjacent tokens."""
    seq, content = _extract_seq("add-polyline (52.5,13.4) seq=1 color=blue")
    assert ")" in content and "color" in content
    assert content == "add-polyline (52.5,13.4) color=blue"


def test_seq_only():
    seq, content = _extract_seq("seq=7")
    assert seq == 7
    assert content == ""
