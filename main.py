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
import subprocess, argparse, sys, os
from pathlib import Path
from dotenv import load_dotenv
import tiktoken

from agents.test_generator import TestGeneratorAgent

def get_git_diff(pr: int, repo: Path, remote: str) -> str:
    subprocess.run(
        ["git", "fetch", remote, f"+refs/pull/*/head:refs/remotes/{remote}/pr/*"],
        cwd=repo, check=True
    )
    res = subprocess.run(
        ["git", "diff", f"{remote}/release-1.2.0...{remote}/pr/{pr}"],
        cwd=repo, capture_output=True, text=True, check=True
    )
    return res.stdout

def chunk_text_by_token(text: str, max_tokens: int, model: str):
    enc = tiktoken.encoding_for_model(model)  # tokenizer :contentReference[oaicite:10]{index=10}
    ids = enc.encode(text)
    chunks, i = [], 0
    newline_id = enc.encode("\n")[0]
    while i < len(ids):
        j = min(i + max_tokens, len(ids))
        while j < len(ids) and ids[j] != newline_id:
            j -= 1
        if j == i:
            j = min(i + max_tokens, len(ids))
        chunks.append(enc.decode(ids[i:j]))
        i = j
    return chunks

def main():
    load_dotenv()  # load OPENAI_API_KEY, OPENAI_MODEL :contentReference[oaicite:11]{index=11}
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--repo-path", type=Path, default=".")
    parser.add_argument("--remote", type=str, default="origin")
    args = parser.parse_args()

    if not (args.repo_path / ".git").exists():
        print("Not a git repo", file=sys.stderr); sys.exit(1)

    # 1. fetch diff
    diff = get_git_diff(args.pr, args.repo_path, args.remote)
    print(f"Fetched diff ({len(diff)} chars)")

    # 2. chunk to fit model context (e.g. leave headroom) :contentReference[oaicite:12]{index=12}
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    chunks = chunk_text_by_token(diff, max_tokens=1500, model=model)
    print(f"Split into {len(chunks)} chunk(s) for model {model}")

    # 3. invoke agent on each chunk
    agent = TestGeneratorAgent(model=model, temp=float(os.getenv("MODEL_TEMP", 0.2)))
    all_tests = []
    for idx, chunk in enumerate(chunks, start=1):
        print(f"▶️ Chunk {idx}/{len(chunks)}")
        tests = agent.generate(chunk)
        all_tests.extend(tests)

    # 4. output combined result
    print("\n=== GENERATED TESTS ===")
    print(all_tests)

if __name__ == "__main__":
    main()
