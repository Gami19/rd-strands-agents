from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from typing import TextIO

from utils.common import (
    build_bedrock_model,
    build_full_run_log_path,
    load_environment,
    write_json,
    write_text,
)
from utils.multiagent_graph import run_graph


class _Tee:
    def __init__(self, *streams: TextIO) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run KC workflow on strands.multiagent Graph.")
    parser.add_argument(
        "--mode",
        choices=["full", "chain-only", "recovery-only"],
        default="full",
        help="Execution mode for the multiagent graph.",
    )
    parser.add_argument(
        "--output",
        default="kc_multiagent_summary.json",
        help="Output JSON filename under standalone/skills-verify/results/",
    )
    args = parser.parse_args()

    paths = load_environment()
    log_path = build_full_run_log_path(paths, args.mode)

    log_buffer = io.StringIO()
    stdout_tee = _Tee(sys.stdout, log_buffer)
    stderr_tee = _Tee(sys.stderr, log_buffer)

    with redirect_stdout(stdout_tee), redirect_stderr(stderr_tee):
        model = build_bedrock_model()
        result = run_graph(paths, model, mode=args.mode)

    output_path = paths.results_root / args.output
    write_json(
        output_path,
        {
            "summary": result.summary,
            "graph_results": result.graph_results,
        },
    )
    print(f"[ok] workflow run complete: {output_path}")
    print(f"[ok] status: {result.status}")
    if log_path is not None:
        meta = [
            f"generated_at_utc: {datetime.now(timezone.utc).isoformat()}",
            f"command: python -X utf8 standalone/skills-verify/scripts/workflow.py --mode {args.mode}",
            f"summary_output: {output_path.as_posix()}",
            "",
        ]
        write_text(log_path, "\n".join(meta) + log_buffer.getvalue())
        print(f"[ok] full run log saved: {log_path}")


if __name__ == "__main__":
    main()

