import os
from dotenv import load_dotenv

load_dotenv()

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Web search (Tavily)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# TTS
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "openai")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


def get_llm():
    """Return the configured LLM. Swap providers by changing LLM_PROVIDER in .env."""
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=LLM_MODEL, api_key=OPENAI_API_KEY)
    elif LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=LLM_MODEL, api_key=ANTHROPIC_API_KEY)
    elif LLM_PROVIDER == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=GOOGLE_API_KEY)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER='{LLM_PROVIDER}'. Choose: openai, anthropic, google")
