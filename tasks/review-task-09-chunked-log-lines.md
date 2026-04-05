# Code Review: Task-09 Chunked Log Lines

## 🔴 Critical

### ~~DoS via large `total` parameter — `chunker.py:72`~~ ✅ Fixed
~~Sending `commit id=x total=10000000000` causes the missing-chunks list comprehension to iterate billions of times, hanging or exhausting memory.~~

```python
missing = [seq for seq in range(1, total + 1) if seq not in session.chunks]
# Hangs/OOMs when total is extremely large
```

~~**Fix:** Add an upper bound on `total` (e.g., 1000 chunks max). Reject and log an error if exceeded.~~

Added `MAX_TOTAL_CHUNKS = 1000` constant. `commit_session` now rejects and returns `None` if `total > MAX_TOTAL_CHUNKS`.

---

## 🟠 High

### ~~1. `ValueError` crash on invalid `total` — `main.py:107`~~ ✅ Fixed
~~`int(parsed['params'].get('total', 0))` with a non-numeric value (e.g., `total=abc`) raises an unhandled `ValueError` that crashes the main event loop.~~

~~**Fix:** Wrap in try/except, log to stderr, and continue.~~

Wrapped in `try/except ValueError`, logs error and `continue`s the loop.

### ~~2. Unlimited concurrent sessions / memory leak — `chunker.py:32–36`~~ ✅ Fixed
~~No cap on open sessions. Sending endless `begin id=<unique>` without `commit` will exhaust memory.~~

~~**Fix:** Add a max-sessions limit (e.g., 100) with FIFO eviction and a warning log.~~

Added `MAX_SESSIONS = 100`. `open_session` now tracks insertion order in `_session_order` and evicts the oldest session (with a warning log) when the limit is reached.

---

## 🟡 Medium

### ~~1. Whitespace corruption when `seq=N` appears mid-content — `main.py:237`~~ ✅ Fixed
~~`_extract_seq("some content seq=1 more")` returns `"some contentmore"` — the space is dropped.~~

Replaced slice-concatenation with `re.sub(r'\s*seq=\d+\s*', ' ', text, count=1).strip()`.

### ~~2. False positive match in `_extract_seq` — `main.py:238`~~ ✅ Fixed
~~The `re.sub(r'\s*seq=\d+\s*', ...)` pattern is too broad — it matches `seq=` inside longer parameter names like `my_step_seq=5`.~~

Both the search and sub now use `(?:^|\s)seq=\d+(?:\s|$)`, requiring `seq=` to be preceded by whitespace or start of string.

### ~~2. No integration tests for end-to-end chunked flow — `tests/`~~ ⚠️ Partial
`test_chunker.py` tests the `Chunker` class in isolation, but the `main.py` handling of `begin`/`chunk`/`commit` (lines 73–132) is entirely untested. The `ValueError` crash above is invisible to the current unit tests.

Tests added in `tests/test_main_chunked.py` go through the `main.py` integration layer. The original crash (invalid `total`) is now tested.

**What's covered ✅**
- Happy path: complete begin/chunk/commit → correct output
- Out-of-order chunks
- Mid-coordinate chunk splits
- Non-chunked commands still work alongside chunked protocol
- Invalid `total` (non-numeric) — the original ValueError crash
- `begin` / `commit` without `id`

**Additionally covered ✅**
- Multiple concurrent interleaved sessions
- Chunk line missing `seq=`
- Assembled command with unknown name (main.py lines 122–127)

**Intentionally skipped**
- Duplicate `begin`, commit/chunk for unknown session — unit tests in `test_chunker.py` are sufficient
- Assembled handler returns `None` — handler failure, not a protocol concern

---

## 🟡 Medium (re-review)

### ~~Session ID can shadow command names — `main.py:73–83`~~ 🚫 Won't fix
~~The `chunker.has_session(first_token)` check runs before command parsing. Opening a session with a reserved name (e.g., `begin id=clear`) causes any subsequent `clear` command to be silently swallowed as a chunk line.~~

Not a practical concern: session IDs are generated on the Android side as random 8-character hex strings (e.g. `a3f9c12b`), which will never collide with command names like `clear`, `add-polyline`, etc.

---

## 🟠 High (round 4)

### ~~`_extract_seq` matches first `seq=` instead of last — `main.py:238`~~ ✅ Fixed
~~`re.search()` finds the first occurrence, extracting the wrong seq when content contains earlier `seq=N` substrings.~~

Replaced `re.search` with `re.finditer(...); match = matches[-1]`. Substitution now uses `match.start()`/`match.end()` directly to remove exactly the last occurrence.

---

## 🟡 Medium (round 4)

### ~~`open_session` can crash on duplicate `begin` — `chunker.py:41`~~ ✅ Fixed
~~`self._session_order.remove(session_id)` raises `ValueError` if `_sessions` and `_session_order` get out of sync.~~

Added the same `if session_id in self._session_order:` guard already present in `commit_session`.

---

## 🟠 High (round 5)

### ~~`MAX_TOTAL_CHUNKS` limit bypassable — `chunker.py:88–106`~~ ✅ Fixed
~~The guard checked only the declared `total`, not the actual chunks received.~~

`add_chunk` now rejects any chunk that would push `session.chunks` past `MAX_TOTAL_CHUNKS`.

---

## 🟡 Medium (round 5)

### ~~Tab-separated chunk lines silently dropped — `main.py:75`~~ 🚫 Won't fix
~~`' ' in line` uses a space literal while `split(None, 1)` splits on any whitespace.~~

Not a practical concern: the Android sender in `MapcatHelpers.kt` always formats chunk lines with space literals (`"$sessionId $chunk seq=${i + 1}"`), so tabs will never appear in protocol output.

---

## 🟡 Medium (round 6)

### ~~Actual chunk count not validated against `total` at commit — `chunker.py:91–93`~~ ✅ Fixed
~~`commit_session` never checked `len(session.chunks)` against the limit independently of `total`.~~

Added a defence-in-depth check on `len(session.chunks)` after popping the session, before assembly.

---

## 🔵 Low (original review)

### ~~`seq=0` not rejected — `chunker.py:41–49`~~ ✅ Fixed
~~Protocol states seq starts at 1, but `seq=0` is silently accepted and then incorrectly reported as a missing chunk during commit.~~

~~**Fix:** Validate `seq >= 1` in `add_chunk`; reject and log an error for invalid values.~~

`add_chunk` now rejects `seq < 1` with an error log before touching the session.
