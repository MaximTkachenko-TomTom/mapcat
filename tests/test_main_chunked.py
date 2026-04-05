"""
Integration tests for the begin/chunk/commit protocol in stdin_broadcast_loop.

Strategy: patch loop.run_in_executor to feed lines one by one, and patch
server.broadcast to capture what gets dispatched.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch
from mapcat.main import stdin_broadcast_loop
from mapcat.state import State


def run_loop(lines):
    """
    Drive stdin_broadcast_loop with the given lines, return list of
    broadcast payloads (parsed from JSON). An empty string terminates input.
    """
    it = iter(lines + [""])
    broadcasts = []

    async def fake_broadcast(msg):
        broadcasts.append(json.loads(msg))

    async def run():
        loop = asyncio.get_event_loop()
        with patch.object(loop, "run_in_executor", side_effect=lambda _, fn, *a: asyncio.coroutine(lambda: fn(*a))()):
            pass

        # Simpler: replace run_in_executor so readline returns the next line
        original = loop.run_in_executor

        async def fake_executor(executor, fn, *args):
            val = next(it, "")
            return val + "\n" if val else ""

        loop.run_in_executor = fake_executor
        try:
            with patch("mapcat.server.broadcast", side_effect=fake_broadcast):
                await stdin_broadcast_loop(is_tty=False, state=State(), verbose=False)
        finally:
            loop.run_in_executor = original

    asyncio.run(run())
    return broadcasts


def test_complete_chunked_sequence():
    """Full begin/chunk/commit sequence assembles and dispatches a polyline."""
    broadcasts = run_loop([
        "begin id=abc",
        "abc add-polyline (52.5,13.4);(52.6,13.5) seq=1",
        "abc ;(52.7,13.6) color=blue seq=2",
        "commit id=abc total=2",
    ])

    assert len(broadcasts) == 1
    msg = broadcasts[0]
    assert msg["type"] == "polyline"
    assert len(msg["coords"]) == 3
    assert msg["params"]["color"] == "blue"


def test_out_of_order_chunks():
    """Chunks arriving out of order are reassembled correctly."""
    broadcasts = run_loop([
        "begin id=xyz",
        "xyz ;(52.7,13.6) color=red seq=2",
        "xyz add-polyline (52.5,13.4);(52.6,13.5) seq=1",
        "commit id=xyz total=2",
    ])

    assert len(broadcasts) == 1
    assert broadcasts[0]["coords"][0] == [52.5, 13.4]
    assert broadcasts[0]["coords"][2] == [52.7, 13.6]


def test_split_mid_coordinate():
    """A coordinate split across two chunks is correctly restored."""
    broadcasts = run_loop([
        "begin id=mid",
        "mid add-polyline (52.5,13.4);(52.7,1 seq=1",
        "mid 3.6) color=green seq=2",
        "commit id=mid total=2",
    ])

    assert len(broadcasts) == 1
    assert broadcasts[0]["coords"][1] == [52.7, 13.6]
    assert broadcasts[0]["params"]["color"] == "green"


def test_non_chunked_command_still_works():
    """Regular commands (no chunking) pass through unchanged."""
    broadcasts = run_loop([
        "add-point (52.5,13.4) color=red id=p1",
    ])

    assert len(broadcasts) == 1
    assert broadcasts[0]["type"] == "point"
    assert broadcasts[0]["params"]["color"] == "red"


def test_commit_with_nonnumeric_total_logs_error_no_crash(capsys):
    """commit total=abc logs an error and does not crash the loop."""
    broadcasts = run_loop([
        "begin id=bad",
        "bad add-point (52.5,13.4) seq=1",
        "commit id=bad total=abc",
    ])

    assert broadcasts == []
    captured = capsys.readouterr()
    assert "total" in captured.err.lower()


def test_begin_without_id_logs_error(capsys):
    """begin without id= logs an error and opens no session."""
    broadcasts = run_loop(["begin"])

    assert broadcasts == []
    captured = capsys.readouterr()
    assert "begin" in captured.err.lower()


def test_commit_without_id_logs_error(capsys):
    """commit without id= logs an error."""
    broadcasts = run_loop(["commit total=1"])

    assert broadcasts == []
    captured = capsys.readouterr()
    assert "commit" in captured.err.lower()


def test_concurrent_sessions():
    """Two interleaved sessions are assembled independently."""
    broadcasts = run_loop([
        "begin id=s1",
        "begin id=s2",
        "s1 add-point (52.1,13.1) seq=1",
        "s2 add-point (52.2,13.2) seq=1",
        "commit id=s1 total=1",
        "commit id=s2 total=1",
    ])

    assert len(broadcasts) == 2
    coords = {tuple(b["coords"]) for b in broadcasts}
    assert (52.1, 13.1) in coords
    assert (52.2, 13.2) in coords


def test_chunk_missing_seq_logs_error(capsys):
    """A chunk line with no seq= logs an error and is dropped."""
    broadcasts = run_loop([
        "begin id=noseq",
        "noseq add-point (52.5,13.4)",  # no seq=
        "commit id=noseq total=1",
    ])

    assert broadcasts == []
    captured = capsys.readouterr()
    assert "seq" in captured.err.lower()


def test_assembled_unknown_command_logs_error(capsys):
    """An assembled command with an unrecognised name logs an error and is not broadcast."""
    broadcasts = run_loop([
        "begin id=unk",
        "unk fly-to (52.5,13.4) seq=1",
        "commit id=unk total=1",
    ])

    assert broadcasts == []
    captured = capsys.readouterr()
    assert "unknown" in captured.err.lower()


def test_handler_returns_none_no_broadcast_loop_continues():
    """When the assembled command's handler returns None, nothing is broadcast and
    the loop continues to process subsequent commands normally."""
    broadcasts = run_loop([
        "begin id=bad",
        # add-point with two coordinates — handler returns None
        "bad add-point (52.5,13.4);(52.6,13.5) seq=1",
        "commit id=bad total=1",
        # next command must still execute
        "add-point (52.9,13.9) color=green id=after",
    ])

    assert len(broadcasts) == 1
    assert broadcasts[0]["id"] == "after"
