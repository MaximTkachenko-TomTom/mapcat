"""
Tests for the chunked protocol (Chunker class).
"""
import pytest
from mapcat.chunker import Chunker, MAX_SESSIONS, MAX_TOTAL_CHUNKS


def test_in_order_chunks():
    """Two chunks arriving in order are reassembled into a valid parsed command."""
    chunker = Chunker()
    chunker.open_session("s1")
    chunker.add_chunk("s1", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5)")
    chunker.add_chunk("s1", seq=2, content=";(52.7,13.6) color=blue")
    result = chunker.commit_session("s1", total=2)

    assert result is not None
    assert result['cmd'] == 'add-polyline'
    assert len(result['coords']) == 3
    assert result['coords'][2] == [52.7, 13.6]
    assert result['params']['color'] == 'blue'


def test_out_of_order_chunks():
    """Chunks arriving out of order are sorted by seq before concatenation."""
    chunker = Chunker()
    chunker.open_session("s2")
    # seq=2 arrives first
    chunker.add_chunk("s2", seq=2, content=";(52.7,13.6) color=blue")
    chunker.add_chunk("s2", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5)")
    result = chunker.commit_session("s2", total=2)

    assert result is not None
    assert result['cmd'] == 'add-polyline'
    assert len(result['coords']) == 3
    assert result['coords'][0] == [52.5, 13.4]
    assert result['params']['color'] == 'blue'


def test_split_mid_coordinate():
    """A coordinate split across two chunks is correctly restored by concatenation."""
    chunker = Chunker()
    chunker.open_session("s3")
    # (52.7,13.6) is split: chunk 1 ends with "(52.7,1", chunk 2 starts with "3.6)"
    chunker.add_chunk("s3", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5);(52.7,1")
    chunker.add_chunk("s3", seq=2, content="3.6);(52.8,13.7) color=red")
    result = chunker.commit_session("s3", total=2)

    assert result is not None
    assert len(result['coords']) == 4
    assert result['coords'][2] == [52.7, 13.6]
    assert result['coords'][3] == [52.8, 13.7]
    assert result['params']['color'] == 'red'


def test_commit_without_begin(capsys):
    """commit for an unknown session logs an error and returns None."""
    chunker = Chunker()
    result = chunker.commit_session("nonexistent", total=1)

    assert result is None
    captured = capsys.readouterr()
    assert "nonexistent" in captured.err


def test_chunk_without_begin(capsys):
    """A chunk for an unknown session logs an error and is silently dropped."""
    chunker = Chunker()
    chunker.add_chunk("ghost", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5)")

    captured = capsys.readouterr()
    assert "ghost" in captured.err

    # commit should also fail
    result = chunker.commit_session("ghost", total=1)
    assert result is None


def test_duplicate_begin_resets_session(capsys):
    """A second begin for the same ID resets the session and warns."""
    chunker = Chunker()
    chunker.open_session("s4")
    chunker.add_chunk("s4", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5)")

    # Second begin — should warn and restart
    chunker.open_session("s4")
    captured = capsys.readouterr()
    assert "s4" in captured.err  # warning was printed

    # Old chunk is gone; new session has no chunks
    chunker.add_chunk("s4", seq=1, content="add-point (52.5,13.4) color=red")
    result = chunker.commit_session("s4", total=1)

    assert result is not None
    assert result['cmd'] == 'add-point'
    assert len(result['coords']) == 1


def test_missing_chunks_warns_but_executes(capsys):
    """When some chunks are missing, a warning is logged but available chunks are executed."""
    chunker = Chunker()
    chunker.open_session("s5")
    # Only seq=1 arrives; total=2 expected
    chunker.add_chunk("s5", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5)")
    result = chunker.commit_session("s5", total=2)

    captured = capsys.readouterr()
    assert "missing" in captured.err.lower() or "warn" in captured.err.lower()

    assert result is not None
    assert result['cmd'] == 'add-polyline'
    assert len(result['coords']) == 2


def test_duplicate_seq_overwrites(capsys):
    """A duplicate seq number overwrites the previous chunk and warns."""
    chunker = Chunker()
    chunker.open_session("s6")
    chunker.add_chunk("s6", seq=1, content="add-polyline (52.5,13.4);(52.6,13.5)")
    chunker.add_chunk("s6", seq=1, content="add-point (52.9,13.9)")  # overwrites

    captured = capsys.readouterr()
    assert "s6" in captured.err  # duplicate warning

    result = chunker.commit_session("s6", total=1)
    assert result is not None
    assert result['cmd'] == 'add-point'


def test_single_chunk_no_split():
    """A command that fits in one chunk works correctly."""
    chunker = Chunker()
    chunker.open_session("s7")
    chunker.add_chunk("s7", seq=1, content="add-point (52.5,13.4) color=green label=\"Home\"")
    result = chunker.commit_session("s7", total=1)

    assert result is not None
    assert result['cmd'] == 'add-point'
    assert result['coords'] == [[52.5, 13.4]]
    assert result['params']['color'] == 'green'
    assert result['params']['label'] == 'Home'


def test_session_removed_after_commit():
    """After commit, the session is cleaned up and a second commit returns None."""
    chunker = Chunker()
    chunker.open_session("s8")
    chunker.add_chunk("s8", seq=1, content="add-point (52.5,13.4)")
    chunker.commit_session("s8", total=1)

    assert not chunker.has_session("s8")
    result = chunker.commit_session("s8", total=1)
    assert result is None


def test_seq_zero_rejected(capsys):
    """seq=0 is rejected with an error; the chunk is not stored."""
    chunker = Chunker()
    chunker.open_session("s9")
    chunker.add_chunk("s9", seq=0, content="add-point (52.5,13.4)")

    captured = capsys.readouterr()
    assert "seq" in captured.err.lower()

    result = chunker.commit_session("s9", total=1)
    assert result is None  # no chunks were stored


def test_max_sessions_evicts_oldest(capsys):
    """Opening more than MAX_SESSIONS sessions evicts the oldest with a warning."""
    chunker = Chunker()
    for i in range(MAX_SESSIONS):
        chunker.open_session(f"sess{i}")

    assert len(chunker._sessions) == MAX_SESSIONS

    # Opening one more should evict sess0
    chunker.open_session("sess_new")
    captured = capsys.readouterr()
    assert "evicted" in captured.err.lower()

    assert len(chunker._sessions) == MAX_SESSIONS
    assert not chunker.has_session("sess0")
    assert chunker.has_session("sess_new")


def test_max_chunks_per_session_rejected(capsys):
    """Chunks beyond MAX_TOTAL_CHUNKS in a single session are rejected with an error."""
    chunker = Chunker()
    chunker.open_session("big")
    for i in range(1, MAX_TOTAL_CHUNKS + 2):
        chunker.add_chunk("big", seq=i, content=f"(52.{i},13.{i})")

    captured = capsys.readouterr()
    assert "exceeds limit" in captured.err.lower()
    assert len(chunker._sessions["big"].chunks) == MAX_TOTAL_CHUNKS


def test_commit_total_exceeds_limit_rejected(capsys):
    """commit with total > MAX_TOTAL_CHUNKS is rejected before assembly."""
    chunker = Chunker()
    chunker.open_session("s10")
    chunker.add_chunk("s10", seq=1, content="add-point (52.5,13.4)")
    result = chunker.commit_session("s10", total=MAX_TOTAL_CHUNKS + 1)

    assert result is None
    captured = capsys.readouterr()
    assert "exceeds limit" in captured.err.lower()


def test_commit_actual_chunks_exceed_limit_rejected(capsys):
    """commit is rejected if actual chunk count somehow exceeds MAX_TOTAL_CHUNKS."""
    chunker = Chunker()
    chunker.open_session("s11")
    # Bypass add_chunk limit by stuffing chunks directly into the session
    session = chunker._sessions["s11"]
    for i in range(1, MAX_TOTAL_CHUNKS + 2):
        session.chunks[i] = f"(52.{i},13.{i})"

    result = chunker.commit_session("s11", total=MAX_TOTAL_CHUNKS + 1)
    assert result is None
    captured = capsys.readouterr()
    assert "exceeds limit" in captured.err.lower()
