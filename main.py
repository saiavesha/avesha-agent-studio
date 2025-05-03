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
import os

from dotenv import load_dotenv
import tiktoken

from agents.test_generator import TestGeneratorAgent

# ─────────────── Token‐based chunking ───────────────
def chunk_text_by_token(text: str, max_tokens: int, model: str):
    enc = tiktoken.encoding_for_model(model)
    token_ids = enc.encode(text)
    chunks, start = [], 0
    newline_id = enc.encode("\n")[0]
    while start < len(token_ids):
        end = min(start + max_tokens, len(token_ids))
        # Back up to nearest newline token for clean splits
        while end < len(token_ids) and token_ids[end] != newline_id:
            end -= 1
        if end == start:  # no newline found, just split flat
            end = min(start + max_tokens, len(token_ids))
        chunk = enc.decode(token_ids[start:end])
        chunks.append(chunk)
        start = end
    return chunks

# ─────────────── Git diff fetcher ───────────────
def get_git_diff(pr_number: int, repo_path: Path, remote: str) -> str:
    subprocess.run(
        ["git", "fetch", remote, f"+refs/pull/*/head:refs/remotes/{remote}/pr/*"],
        cwd=repo_path, check=True
    )
    result = subprocess.run(
        ["git", "diff", f"{remote}/release-1.2.0...{remote}/pr/{pr_number}"],
        cwd=repo_path, capture_output=True, text=True, check=True
    )
    return result.stdout

# ─────────────── Main ───────────────
def main():
    
    load_dotenv()
    # 1) Choose model, fallback logic
    desired_model = os.getenv("OPENAI_MODEL", "gpt-4")
    temp = float(os.getenv("MODEL_TEMP", 0.2))

    # Test if the desired model exists, else fallback
    try:
        TestGeneratorAgent(model=desired_model, temp=temp) \
            .chain.llm.create(messages=[{"role": "system", "content": "ping"}], max_tokens=1)
        model = desired_model
    except InvalidRequestError as e:
        print(f"⚠️  Model {desired_model!r} not available, falling back to gpt-3.5-turbo")
        model = "gpt-3.5-turbo"

    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    agent = TestGeneratorAgent(model=model, temp=temp)

    # 2) Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr",        type=int,   required=True)
    parser.add_argument("--repo-path", type=Path,  default=".")
    parser.add_argument("--remote",    type=str,   default="origin")
    args = parser.parse_args()

    if not (args.repo_path / ".git").exists():
        print("Error: not a git repo", file=sys.stderr)
        sys.exit(1)

    # 3) Fetch diff
    diff = get_git_diff(args.pr, args.repo_path, args.remote)
    print("Fetched diff:", len(diff), "chars")

    # 4) Chunk to avoid context limits
    # Leave ~500 tokens headroom for prompt + response
    max_input_tokens = 16000  
    diff_chunks = chunk_text_by_token(diff, max_input_tokens, model)

    print(f"– Split into {len(diff_chunks)} chunk(s) for model={model}")

    # 5) Generate tests over each chunk
    all_results = []
    for idx, chunk in enumerate(diff_chunks, start=1):
        print(f"\n>>> Processing chunk {idx}/{len(diff_chunks)} …")
        try:
            result = agent.generate(chunk)
        except InvalidRequestError as err:
            # If still too big, you could further split or abort
            print("❌ Chunk too large even after splitting:", err, file=sys.stderr)
            sys.exit(1)
        all_results.append(result)

    # 6) Output combined results
    print("\n=== COMBINED GENERATED TESTS ===")
    for i, tests in enumerate(all_results, start=1):
        print(f"\n--- tests from chunk {i} ---\n", tests)

if __name__ == "__main__":
    main()
