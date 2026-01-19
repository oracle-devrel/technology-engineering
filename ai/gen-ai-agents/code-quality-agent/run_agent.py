"""
File name: run_agent.py
Author: L. Saetta
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
    Entry point to run the agent from command line.
"""

import argparse
import asyncio
from agent.graph_agent import build_graph, run_agent
from agent.utils import get_console_logger

logger = get_console_logger()


def main():
    """
    Main function to run the agent from command line.
    Parses command line arguments and executes the agent graph.
    """
    default_request = (
        "Check headers and scan secrets. If you identify any secrets, "
        "report them in the risk section."
    )

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        required=True,
        help="Root directory containing python files (read-only).",
    )
    ap.add_argument(
        "--out", required=True, help="Output directory for generated artifacts."
    )
    ap.add_argument(
        "--request",
        default=default_request,
        help="User request text.",
    )
    args = ap.parse_args()

    # here we build the graph
    graph = build_graph()

    async def _run():
        st = await run_agent(
            graph, root_dir=args.root, out_dir=args.out, request=args.request
        )

        print("")
        print("\n=== AGENT SUMMARY ===")
        print(st["summary"])

        if st["header_issues"]:
            print("\nHEADER ISSUES:")
            for k, v in st["header_issues"].items():
                print(f"- {k}: {v}")

        if st["secrets"]:
            print("\nSECRETS FOUND (review ASAP):")
            for fpath, findings in st["secrets"].items():
                print(f"- {fpath}:")
                for it in findings:
                    print(f"    line {it['line']}: {it['kind']} | {it['excerpt']}")

        print("")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
