# agents/github_ops.py
from github import Github

class GitHubOpsAgent:
    def __init__(self, token: str):
        self.gh = Github(token)

    def create_check_run(self, repo_name: str, sha: str, conclusion: str, output: dict):
        repo = self.gh.get_repo(repo_name)
        repo.create_check_run(
            name="QA Maestro",
            head_sha=sha,
            conclusion=conclusion,
            output=output
        )

    def open_issue(self, repo_name: str, title: str, body: str):
        repo = self.gh.get_repo(repo_name)
        repo.create_issue(title=title, body=body)
