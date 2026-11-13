from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openrouter_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.3,
    )
