# # main.py
# import os
# from dotenv import load_dotenv
# from fastapi import FastAPI, Request
# from fastapi.responses import StreamingResponse
# import asyncio
# from pydantic import BaseModel
# from orchestrator import QAOrchestrator

# load_dotenv()
# app = FastAPI()

# # Load config
# GH_TOKEN = os.getenv("GITHUB_TOKEN")
# DUCKDB_PATH = os.getenv("DUCKDB_PATH", ":memory:")
# PG_CONN = os.getenv("PG_CONN", None)
# FLAKE_MODEL = os.getenv("FLAKE_MODEL_PATH", "flake_model.txt")

# orch = QAOrchestrator(GH_TOKEN, DUCKDB_PATH, PG_CONN, FLAKE_MODEL)

# class WebhookPayload(BaseModel):
#     pr_number: int
#     repo: str
#     sha: str

# async def event_stream(pipeline_results):
#     """Yields Server-Sent Events for each step."""
#     for step, result in pipeline_results.items():
#         yield f"event: {step}\ndata: {result}\n\n"
#         await asyncio.sleep(0.1)

# @app.post("/run")
# async def run_agent(payload: WebhookPayload):
#     # Kick off pipeline
#     results = orch.run_pipeline(payload.pr_number, payload.repo, payload.sha)
#     # Stream back to UI
#     return StreamingResponse(event_stream(results), media_type="text/event-stream")


#!/usr/bin/env python3
import subprocess
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
import os

from agents.test_generator import TestGeneratorAgent

def get_git_diff(pr_number: int, repo_path: Path, remote: str) -> str:
    """
    1. Fetch all PR heads from the specified remote into refs/remotes/<remote>/pr/<num>
    2. Diff remote/main against remote/pr/<pr_number>
    """
    # 1. fetch PR refs
    subprocess.run(
        ["git", "fetch", remote, f"+refs/pull/*/head:refs/remotes/{remote}/pr/*"],
        cwd=repo_path,
        check=True,
    )
    # 2. run the diff
    result = subprocess.run(
        ["git", "diff", f"{remote}/main...{remote}/pr/{pr_number}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

def main():
    # Load OpenAI key from .env
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("Error: set OPENAI_API_KEY in your .env", file=sys.stderr)
        sys.exit(1)
    os.environ["OPENAI_API_KEY"] = openai_key

    parser = argparse.ArgumentParser(description="Fetch PR diff & generate tests")
    parser.add_argument("--pr",        type=int,   required=True,     help="Pull Request number")
    parser.add_argument("--repo-path", type=Path,  default=".",        help="Path to your local git repo")
    parser.add_argument("--remote",    type=str,   default="origin",   help="Git remote name")
    args = parser.parse_args()

    # sanity check
    if not (args.repo_path / ".git").exists():
        print(f"Error: {args.repo_path} is not a git repo", file=sys.stderr)
        sys.exit(1)

    # 1. fetch diff
    diff = get_git_diff(args.pr, args.repo_path, args.remote)
    print("=== DIFF ===\n", diff)

    # 2. generate tests
    agent = TestGeneratorAgent(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temp=float(os.getenv("MODEL_TEMP", 0.2))
    )
    tests_json = agent.generate(diff)

    print("\n=== GENERATED TESTS ===\n", tests_json)

if __name__ == "__main__":
    main()

