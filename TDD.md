# Recorded vertical TDD execution

Each numbered behavior was tested, observed failing, implemented, then retested with the whole current suite before proceeding to the next behavior. The logs are actual captured stdout/stderr, not reconstructed example output. Commands were run from this project directory with Python 3.12.3. Every expected-red process returned nonzero; a shell guard confirmed that exit status after `tee`.

Typical capture commands:

```sh
set -o pipefail
python3 -m unittest -v test_usdg 2>&1 | tee tdd_logs/NN_behavior_RED.log
test ${PIPESTATUS[0]} -ne 0
# Implement that behavior, then:
python3 -m unittest -v test_usdg 2>&1 | tee tdd_logs/NN_behavior_GREEN.log
```

The initial missing-module tests assert absence explicitly, so missing features are reported as intentional assertion failures rather than accidental import errors. Full suite logs show earlier vertical slices remaining green as later features are introduced.

| Cycle | Behavior | Observed RED | Observed GREEN |
| --- | --- | --- | --- |
| 01 | Exact decimal scaling, minimum base unit and trailing zeros | Parser missing (1 failure) | 1 test passed |
| 02 | Strict whole-input ASCII grammar | 20 malformed input subtests accepted incorrectly | 2 tests passed |
| 03 | uint256 bounds, input length and wrong types | Missing length guard and amounts over uint256 accepted | 3 tests passed |
| 04 | Canonical formatter, exact integer types and integer round trips | Formatter missing | 4 tests passed |
| 05 | Independent character-state oracle | Reference parser missing | 5 tests passed |
| 06 | Deterministic seeded case generation | Generator missing | 6 tests passed |
| 07 | Actual publication, explicit edge fixtures, oracle/round-trip evidence and float demonstrations | Publisher missing | 7 tests passed |
| 08 | One-command full replay entry point | Replay module missing | 8 tests passed and 100,000 cases generated/read back |

Cycle 03 transparently retains its first red log, which also has an `AttributeError` from accessing a missing constant. A tool-computed boundary check showed the initial expected maximum length of 78 was wrong: the uint256 maximum display has **72 + 1 + 6 = 79** characters. Before implementing that slice, the test was corrected to 79 and the missing constant changed to an explicit assertion. `03_bounds_RED_corrected.log` records the rerun with four intended assertion failures and no test errors. No implementation was changed to accommodate an incorrect boundary.

`08_replay_GREEN.log` captures the actual one-command run, including all current test methods, 100,000 published/read-back cases, totals, zero mismatches and dataset hash. `final_replay.log` captures the final independent rerun after documentation completion. Current source files do not retain incomplete historical implementations; these logs record the actual observed failures and successes.

The logs preserve unittest's original progress-line whitespace. `.gitattributes` exempts only captured log files from Git's end-of-line whitespace check, rather than altering the historical output. Source and documentation still receive the normal `git diff --check` checks.

Signed off by enueex — https://x.com/AjaPawang
