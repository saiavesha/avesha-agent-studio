# tools/github_tool.py
from langchain.tools import Tool
import subprocess

def get_git_diff(pr_number: int) -> str:
    """Fetch the git diff for a given PR number from origin/main."""
    result = subprocess.run(
        ["git", "diff", f"origin/main...origin/pr/{pr_number}"],
        capture_output=True, text=True
    )
    return result.stdout

GitDiffTool = Tool.from_function(
    func=get_git_diff,
    name="get_git_diff",
    description="Fetch the git diff for a given PR number"
)
