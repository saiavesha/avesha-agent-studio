#!/usr/bin/env python3
import subprocess
import argparse
import sys
from pathlib import Path

def get_git_diff(pr_number: int, repo_path: Path, remote: str) -> str:
    """
    1. Fetch all PR heads from the specified remote into refs/remotes/<remote>/pr/<num>
    2. Diff remote/main against remote/pr/<pr_number>
    """
    # 1. fetch PR refs
    try:
        subprocess.run(
            ["git", "fetch", remote, f"+refs/pull/*/head:refs/remotes/{remote}/pr/*"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[fetch error] {e.stderr}", file=sys.stderr)
        sys.exit(e.returncode)

    # 2. run the diff
    try:
        result = subprocess.run(
            ["git", "diff", f"{remote}/main...{remote}/pr/{pr_number}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[diff error] {e.stderr}", file=sys.stderr)
        sys.exit(e.returncode)

def main():
    parser = argparse.ArgumentParser(description="Fetch git diff for a PR")
    parser.add_argument("--pr",        type=int,           required=True,      help="Pull Request number")
    parser.add_argument("--repo-path", type=Path,         default=".",       help="Path to your local git repo")
    parser.add_argument("--remote",    type=str,           default="origin",  help="Remote name (e.g. origin)")
    args = parser.parse_args()

    # sanity check
    if not (args.repo_path / ".git").exists():
        print(f"Error: {args.repo_path} is not a git repo", file=sys.stderr)
        sys.exit(1)

    diff = get_git_diff(args.pr, args.repo_path, args.remote)
    print(diff)

if __name__ == "__main__":
    main()
    
    
# python main.py --pr 253 --repo-path /c/Users/Sai/Downloads/Avesha/autoscaling/smart-scaler/rlautoscaler/git-repos/rlautoscaler --remote origin