# orchestrator.py
from tools.github_tool import GitDiffTool
from agents.data_retrieval import DataRetrievalAgent
from agents.test_generator import TestGeneratorAgent
from agents.flaky_detector import FlakyDetectorAgent
from agents.evaluator import EvaluatorAgent
from agents.github_ops import GitHubOpsAgent

class QAOrchestrator:
    def __init__(self, gh_token, duckdb_path, pg_conn_str, flake_model):
        self.dt = DataRetrievalAgent(duckdb_path, pg_conn_str)
        self.tg = TestGeneratorAgent()
        self.fd = FlakyDetectorAgent(flake_model)
        self.ev = EvaluatorAgent()
        self.gh = GitHubOpsAgent(gh_token)

    def run_pipeline(self, pr_number, repo_name, sha):
        # 1. Fetch diff
        diff = GitDiffTool.run(pr_number)

        # 2. Generate tests
        tests_json = self.tg.generate(diff)

        # 3. For each test, check flakiness
        flaky_scores = {}
        for test in tests_json:
            hist = self.dt.fetch_historical_failures(test["test_name"])
            features = {"flip_rate": len(hist)/max(len(hist)+1,1)}
            flaky_scores[test["test_name"]] = self.fd.score(features)

        # 4. Evaluate overall quality
        all_pass = all(self.ev.score(t["test_body"], reference="") for t in tests_json)

        # 5. Report back to GitHub
        output = {"title": "QA Maestro Report", "summary": str(flaky_scores)}
        if all_pass:
            self.gh.create_check_run(repo_name, sha, "success", output)
        else:
            self.gh.create_check_run(repo_name, sha, "failure", output)
            self.gh.open_issue(repo_name, "Flaky/Failed Tests Detected", str(flaky_scores))

        return {"tests": tests_json, "flaky": flaky_scores, "passed": all_pass}
