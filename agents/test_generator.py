import json
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType

def _generate_tests(diff: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior QA engineer."),
        ("user", "Given this diff:\n{diff}\n"
                 "Generate pytest code in JSON with keys: "
                 "file_path, test_name, test_body.")
    ])
    chain = prompt | ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    return chain.invoke({"diff": diff})

GenerateTestsTool = Tool(
    name="generate_tests",
    func=_generate_tests,
    description="Produce pytest test code from a git diff in JSON format."
)

class TestGeneratorAgent:
    def __init__(self, model="gpt-3.5-turbo", temp=0.2):
        llm = ChatOpenAI(model=model, temperature=temp)
        # Choose one of the options from §3 above:
        tools = [GenerateTestsTool]
        # tools = load_tools(["terminal"], llm=llm, allow_dangerous_tools=True) + [GenerateTestsTool]

        self.agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True           # retry on malformed outputs :contentReference[oaicite:8]{index=8}
        )

    def generate(self, diff: str):
        output = self.agent.run(f"Process this git diff and generate tests:\n{diff}")
        return json.loads(output)
