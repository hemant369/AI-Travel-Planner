from crewai import LLM
from model.settings import OLLAMA_MODEL

llm = LLM(
    model=OLLAMA_MODEL,
)

