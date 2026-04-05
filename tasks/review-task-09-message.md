# Code Review Feedback — Task-09 Tests — Resolved

Hey, great work on the integration tests — coverage is solid and the tests are well-written.

One gap remains: **handler returning `None`** (main.py lines 128–137) is not tested anywhere, neither at unit nor integration level. You dismissed this as "not a protocol concern" but there is real logic there — when a handler returns `None`, no broadcast should occur and the loop must continue cleanly. If that path is broken, a malformed chunked command could cause a silent failure or crash.

Please add one integration test: assemble a chunked `add-point` with invalid input (e.g., two coordinates instead of one) so the handler returns `None`, and assert that no broadcast occurs and the next command still executes normally.

Everything else looks good — ship it once this is added. 👍

---

Fair point — added `test_handler_returns_none_no_broadcast_loop_continues` in `test_main_chunked.py`. Uses `add-point` with two coordinates (handler rejects it → returns `None`), asserts no broadcast, then verifies the next command still executes. All 83 tests pass.

---

Verified — all 83 tests pass locally. That was the last gap.

Overall the feature is in good shape: the chunked protocol is correctly implemented, all the security issues (DoS, memory leak, input validation) are addressed, and the test suite covers both the happy path and the meaningful error cases end-to-end. Happy to approve. ✅
