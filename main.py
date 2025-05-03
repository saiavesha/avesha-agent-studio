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




# main.py
#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import tiktoken
from agents.test_generator import TestGeneratorAgent

# Utility: chunk text by token count

def chunk_text_by_token(text: str, max_tokens: int, model: str):
    enc = tiktoken.encoding_for_model(model)
    token_ids = enc.encode(text)
    chunks, start = [], 0
    newline_id = enc.encode("\n")[0]
    while start < len(token_ids):
        end = min(start + max_tokens, len(token_ids))
        # Back up to newline for clean split
        while end < len(token_ids) and token_ids[end] != newline_id:
            end -= 1
        if end == start:
            end = min(start + max_tokens, len(token_ids))
        chunks.append(enc.decode(token_ids[start:end]))
        start = end
    return chunks

# Fetch diff for a PR

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

# Main entry point

def main():
    load_dotenv()
    # Determine model & temperature
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    temp = float(os.getenv("MODEL_TEMP", 0.2))

    # Parse CLI args
    parser = argparse.ArgumentParser(description="Fetch PR diff & generate tests")
    parser.add_argument("--pr", type=int, required=True, help="Pull Request number")
    parser.add_argument("--repo-path", type=Path, default=".", help="Local git repo path")
    parser.add_argument("--remote", type=str, default="origin", help="Git remote name")
    args = parser.parse_args()

    if not (args.repo_path / ".git").exists():
        print(f"Error: {args.repo_path} is not a git repository", file=sys.stderr)
        sys.exit(1)

    # Fetch and chunk diff
    diff = get_git_diff(args.pr, args.repo_path, args.remote)
    print(f"Fetched diff ({len(diff)} chars)")

    max_tokens = 1500  # leave headroom
    chunks = chunk_text_by_token(diff, max_tokens, model)
    print(f"Split into {len(chunks)} chunk(s) for model={model}")

    # Initialize agent
    agent = TestGeneratorAgent(model=model, temp=temp)
    all_tests = []

    # Process each chunk
    for idx, chunk in enumerate(chunks, start=1):
        print(f"▶️ Chunk {idx}/{len(chunks)}")
        result = agent.generate(chunk)
        if isinstance(result, list):
            all_tests.extend(result)
        else:
            # Raw fallback
            print("Raw agent output:\n", result)

    # Output combined tests
    print("\n=== GENERATED TESTS ===")
    for test in all_tests:
        print(test)

if __name__ == "__main__":
    main()