import json
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType

# Internal function that runs the test-gen prompt

def _generate_tests(diff: str) -> str:
    """
    Given a git diff, prompt the LLM to output pytest code in JSON.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior QA engineer."),
        ("user",
         "Given this diff:\n{diff}\nGenerate pytest code in JSON "
         "with keys: file_path, test_name, test_body.")
    ])
    # RunnableSequence style: prompt | llm
    chain = prompt | ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    return chain.invoke({"diff": diff})

# Expose as a LangChain Tool
GenerateTestsTool = Tool(
    name="generate_tests",
    func=_generate_tests,
    description="Produce pytest test code from a git diff in JSON format."
)

class TestGeneratorAgent:
    def __init__(self, model: str = "gpt-3.5-turbo", temp: float = 0.2):
        # Use the community ChatOpenAI implementation
        llm = ChatOpenAI(model=model, temperature=temp)
        # Only our custom test-gen tool
        tools = [GenerateTestsTool]
        # Initialize the agent with extended iteration/time settings
        self.agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=30,
            max_execution_time=60.0,
            early_stopping_method="generate"
        )

    def generate(self, diff: str):
        """
        Runs the agent; returns parsed JSON list or raw string on failure.
        """
        raw = self.agent.run(f"Process this git diff and generate tests:\n{diff}").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("⚠️ Warning: failed to parse JSON, returning raw output")
            return raw