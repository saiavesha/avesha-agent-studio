# agents/test_generator.py
from langchain.chains import LLMChain          # new path for LLMChain
from langchain_openai import ChatOpenAI        # comes from langchain-openai
from langchain_core.prompts import ChatPromptTemplate

class TestGeneratorAgent:
    def __init__(self, model="gpt-3.5-turbo", temp=0.2):
        self.chain = LLMChain(
            llm=ChatOpenAI(model=model, temperature=temp),
            prompt=ChatPromptTemplate.from_messages([
                ("system", "You are a senior QA engineer."),
                ("user",
                 "Given this diff:\n{diff}\nGenerate pytest code in JSON "
                 "with keys: file_path, test_name, test_body.")
            ]),
        )

    def generate(self, diff: str) -> str:
        return self.chain.invoke({"diff": diff})
