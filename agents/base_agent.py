# agents/base_agent.py
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class BaseAgent:
    def __init__(self, llm_model="gpt-3.5-turbo", temperature=0.2):
        self.llm = ChatOpenAI(model=llm_model, temperature=temperature)

    def run_chain(self, prompt_template: ChatPromptTemplate, inputs: dict):
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        return chain.run(inputs)
