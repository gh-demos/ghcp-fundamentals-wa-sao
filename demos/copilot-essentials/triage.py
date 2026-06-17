#!/usr/bin/env python3
"""
Quick log triage utility
────────────────────────
  • Accepts   *.log  or  *.log.gz
  • Filters   last N minutes (sliding window)
  • Tallies   (status‑code, endpoint) pairs
  • Optional  --status 499,321 for focused searching

  A noisy incident page reveals a spike in 321 or 499 errors, but the observability stack is lagging. You need a quick, local log sweep to spot patterns and counts.
"""

from pathlib import Path
from datetime import datetime, timedelta, timezone
import argparse
import gzip
import re
import sys
from collections import Counter
from typing import Iterable, Tuple

LOG_PATTERN = re.compile(
    r'^\S+ \S+ \S+ \[(?P<timestamp>[^\]]+)\] "\S+ (?P<path>\S+) \S+" (?P<status>\d{3})'
)

# ---------------------------------------------------------------------------
# ✨ Function placeholders – let Copilot write the bodies ✨
# ---------------------------------------------------------------------------

def read_lines(file_path: Path) -> Iterable[str]:
    """Open plain or gzipped log file and yield each line (stripped)."""
    if file_path.suffix == ".gz":
        with gzip.open(file_path, "rt", encoding="utf-8") as f:
            for line in f:
                yield line.strip()
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                yield line.strip()


def parse_line(line: str) -> Tuple[datetime, int, str] | None:
    """Return (timestamp_utc, status_code_int, url_path) or None if malformed."""
    # parse_line prompt:
#   "Use a compiled regex for common/combined log format; pull timestamp,
#    status, and path. Convert the timestamp '[15/Jul/2025:14:23:41 +0000]'
#    to a timezone‑aware UTC datetime. Return None if the line doesn't match."
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    timestamp_str = match.group("timestamp")
    status_str = match.group("status")
    path = match.group("path")

    timestamp_utc = datetime.strptime(timestamp_str, "%d/%b/%Y:%H:%M:%S %z").astimezone(timezone.utc)
    status_code = int(status_str)

    return timestamp_utc, status_code, path


def triage(
    lines: Iterable[str],
    minutes: int,
    wanted_status: set[int] | None
) -> Counter[Tuple[int, str]]:
    """Aggregate counts for lines within the window and matching status filter."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=minutes)

    counts: Counter[Tuple[int, str]] = Counter()
    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            continue

        timestamp_utc, status_code, path = parsed
        if timestamp_utc < window_start or timestamp_utc > now:
            continue
        if wanted_status is not None and status_code not in wanted_status:
            continue

        counts[(status_code, path)] += 1

    return counts


def render(counter: Counter[Tuple[int, str]], top: int) -> None:
    """Pretty‑print a Markdown‑style table of the top offenders."""
    print("| Rank | Status | Path | Hits |")
    print("|------|--------|------|------|")
    for i, ((status, path), hits) in enumerate(counter.most_common(top), start=1):
        print(f"| {i} | {status} | {path} | {hits} |")


def main() -> None:
    """Wire everything together with argparse CLI options."""
    parser = argparse.ArgumentParser(description="Quick log triage utility")
    parser.add_argument("file", nargs="?", type=Path, help="Path to .log or .log.gz file")
    parser.add_argument("--file", dest="file_arg", type=Path, help="Path to .log or .log.gz file")
    parser.add_argument("--minutes", type=int, default=15, help="Time window in minutes (default: 15)")
    parser.add_argument("--status", type=str, help="Comma-separated list of status codes to filter (e.g. 499,321)")
    parser.add_argument("--top", type=int, default=10, help="Number of top offenders to display (default: 10)")
    args = parser.parse_args()

    file_path = args.file_arg or args.file
    if file_path is None:
        parser.error("either positional file or --file must be provided")

    if args.minutes < 0:
        parser.error("--minutes must be >= 0")
    if args.top < 1:
        parser.error("--top must be >= 1")

    wanted_status: set[int] | None = None
    if args.status:
        try:
            wanted_status = {int(code.strip()) for code in args.status.split(",") if code.strip()}
        except ValueError:
            parser.error("--status must be a comma-separated list of integers")

    counter = triage(read_lines(file_path), args.minutes, wanted_status)
    if not counter:
        print("No matches found.", file=sys.stderr)
        raise SystemExit(1)

    render(counter, args.top)


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# 📝 Copilot prompts – copy these into each empty function or keep them here
# ---------------------------------------------------------------------------
# read_lines prompt:
#   "Implement read_lines(file_path) so it transparently handles .log or .log.gz,
#    opens in text mode (UTF‑8), and yields one stripped line at a time."

# parse_line prompt:
#   "Use a compiled regex for common/combined log format; pull timestamp,
#    status, and path. Convert the timestamp '[15/Jul/2025:14:23:41 +0000]'
#    to a timezone‑aware UTC datetime. Return None if the line doesn't match."

# triage prompt:
#   "Stream through lines, parse each; skip malformed. Keep only entries whose
#    timestamp is within <minutes> of datetime.utcnow() and, if wanted_status
#    is provided, whose status is in that set. Use a Counter keyed by
#    (status_code, path)."

# render prompt:
#   "Print the top <top> (status, path) pairs from the Counter in descending
#    order of hits, formatted as a Markdown table: Rank | Status | Path | Hits."

# main prompt:
#   "Add argparse arguments:
#       --file (positional, required)
#       --minutes (int, default 15)
#       --status  (comma‑separated list of ints, optional)
#       --top     (int, default 10)
#    Parse args, build wanted_status set, call triage(), then render().
#    Exit with status‑code 1 if no matches were found."
