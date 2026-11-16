from crewai import LLM
from model.settings import OLLAMA_HOST, OLLAMA_MODEL

llm = LLM(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_HOST,
    temperature=0.1,
)
