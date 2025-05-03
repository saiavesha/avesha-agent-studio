# QA Agent Prototype

This repository contains a simplified Python prototype for generating pytest test cases automatically from GitHub pull request diffs using LangChain and OpenAI. It fetches a PR diff, chunks large diffs, and invokes a TestGenerator agent to output JSON-formatted tests.

## 🚀 Features

* Fetch Git diff for any PR branch from a specified remote
* Chunk oversized diffs to respect model context limits
* Generate pytest test code using OpenAI LLMs (configurable model)
* Fallback to `gpt-3.5-turbo` if the desired model is not available

## 📦 Prerequisites

* Python 3.9+
* Git locally installed and configured
* A GitHub personal access token with `repo` scopes (set as `GITHUB_TOKEN`)
* OpenAI API key (set as `OPENAI_API_KEY`)
* Conda (optional) or virtualenv for environment management

## 🔧 Installation

1. **Clone this repo**

   ```bash
   git clone https://github.com/your-org/qa_agent_project.git
   cd qa_agent_project
   ```

2. **Create and activate a virtual environment**

   ```bash
   conda create -n qa_agent python=3.9 -y
   conda activate qa_agent
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Ensure `python-dotenv` is installed**

   ```bash
   python -m pip install python-dotenv
   ```

## ⚙️ Configuration

Create a `.env` file in the project root with:

```dotenv
OPENAI_API_KEY=sk-your_openai_key
GITHUB_TOKEN=ghp-your_github_token
OPENAI_MODEL=gpt-4              # or gpt-3.5-turbo
MODEL_TEMP=0.2                  # optional temperature
```

## 📋 Usage

1. **Fetch PR refs** (if needed):

   ```bash
   git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'
   ```

2. **Run the script**

   ```bash
   python main.py \
     --pr 42 \
     --repo-path /path/to/your/local/repo \
     --remote origin
   ```

* `--pr`: PR number to diff against `origin/main`.
* `--repo-path`: Path to the local clone of your repository.
* `--remote`: Remote name (default: `origin`).

The script will:

1. Fetch the PR branch refs
2. Diff `origin/main` vs `origin/pr/<PR>`
3. Chunk the diff if too large
4. Call the TestGenerator agent per chunk
5. Print combined JSON test definitions

## 🧪 Testing

Run unit tests with:

```bash
pytest
```

## 🛠 Troubleshooting

* **ModuleNotFoundError: No module named 'langchain'**

  ```bash
  python -m pip install langchain langchain-openai langchain-community
  ```

* **Model not found or context length errors**

  * Edit `.env` to use a supported model (e.g., `gpt-3.5-turbo`).
  * The script auto-falls back to `gpt-3.5-turbo` if the chosen model isn’t available.

* **Invalid Git repo path**

  * Ensure `--repo-path` points to a valid local Git clone containing a `.git` directory.

## 📖 Further Reading

* [LangChain Documentation](https://python.langchain.com/docs/)
* [OpenAI Python SDK](https://github.com/openai/openai-python)
* [tiktoken Tokenizer](https://github.com/openai/tiktoken)

---

Happy testing! 🎉
