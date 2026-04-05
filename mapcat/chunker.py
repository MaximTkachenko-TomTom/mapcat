"""
Session-based chunker for reassembling long commands split across multiple log lines.

Android's Log.d breaks lines longer than ~4000 chars into multiple messages that may
arrive out of order. The chunker buffers chunks keyed by seq number and reconstructs
the original command string when commit is received.

Protocol:
    begin id=<id>
    <id> <content> seq=<N>
    commit id=<id> total=<N>
"""
import sys
from typing import Optional, Dict, Any

# ANSI color codes
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


class _PendingSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.chunks: Dict[int, str] = {}  # seq -> raw content (seq= param already removed)


MAX_SESSIONS = 100
MAX_TOTAL_CHUNKS = 1000


class Chunker:
    def __init__(self):
        self._sessions: Dict[str, _PendingSession] = {}
        self._session_order: list = []  # insertion-order tracking for FIFO eviction

    def open_session(self, session_id: str) -> None:
        """Open a new pending session. Warns and replaces if one already exists."""
        if session_id in self._sessions:
            _log_warning(f"Duplicate begin for id='{session_id}', restarting session")
            if session_id in self._session_order:
                self._session_order.remove(session_id)
        elif len(self._sessions) >= MAX_SESSIONS:
            evicted = self._session_order.pop(0)
            del self._sessions[evicted]
            _log_warning(f"Max sessions ({MAX_SESSIONS}) reached, evicted oldest session id='{evicted}'")
        self._sessions[session_id] = _PendingSession(session_id)
        self._session_order.append(session_id)

    def has_session(self, session_id: str) -> bool:
        return session_id in self._sessions

    def add_chunk(self, session_id: str, seq: int, content: str) -> None:
        """Add a chunk to the pending session. Logs error if session doesn't exist."""
        if seq < 1:
            _log_error(f"Invalid seq={seq} for id='{session_id}': seq must be >= 1, ignoring chunk")
            return
        if session_id not in self._sessions:
            _log_error(f"Chunk received for unknown session id='{session_id}' (missing begin?)")
            return
        session = self._sessions[session_id]
        if len(session.chunks) >= MAX_TOTAL_CHUNKS:
            _log_error(f"Session id='{session_id}': chunk count exceeds limit of {MAX_TOTAL_CHUNKS}, ignoring chunk")
            return
        if seq in session.chunks:
            _log_warning(f"Duplicate chunk seq={seq} for id='{session_id}', overwriting")
        session.chunks[seq] = content

    def commit_session(self, session_id: str, total: int) -> Optional[Dict[str, Any]]:
        """
        Commit a session: concatenate chunks in seq order and parse the result.

        Args:
            session_id: The session ID from 'commit id=<id>'
            total: Expected number of chunks from 'total=<N>'

        Returns:
            Parsed command dict {cmd, coords, params} or None on error.
        """
        # Import here to avoid circular imports
        from mapcat import parser

        if session_id not in self._sessions:
            _log_error(f"commit received for unknown session id='{session_id}' (missing begin?)")
            return None

        session = self._sessions.pop(session_id)
        if session_id in self._session_order:
            self._session_order.remove(session_id)

        if total > MAX_TOTAL_CHUNKS:
            _log_error(f"Session id='{session_id}': total={total} exceeds limit of {MAX_TOTAL_CHUNKS}, rejecting")
            return None

        if len(session.chunks) > MAX_TOTAL_CHUNKS:
            _log_error(f"Session id='{session_id}': {len(session.chunks)} chunks received, exceeds limit of {MAX_TOTAL_CHUNKS}, rejecting")
            return None

        if total > 0:
            missing = [seq for seq in range(1, total + 1) if seq not in session.chunks]
            if missing:
                _log_warning(
                    f"Session id='{session_id}': missing chunks {missing}, "
                    f"executing with {len(session.chunks)} of {total} chunks"
                )

        if not session.chunks:
            _log_error(f"Session id='{session_id}': no chunks received, nothing to execute")
            return None

        # Concatenate chunks in seq order — split may occur anywhere, even mid-coordinate
        sorted_seqs = sorted(session.chunks.keys())
        combined = "".join(session.chunks[seq] for seq in sorted_seqs)

        parsed = parser.parse_command(combined)
        if parsed is None:
            _log_error(f"Session id='{session_id}': failed to parse reassembled command")
        return parsed


def _log_error(message: str):
    print(f"{RED}FAIL: chunker{RESET}", file=sys.stderr)
    print(f"{RED}FAIL: {message}{RESET}", file=sys.stderr)


def _log_warning(message: str):
    print(f"{YELLOW}WARN: chunker: {message}{RESET}", file=sys.stderr)
