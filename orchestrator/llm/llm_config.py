import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# TradeMind-AI project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


def get_llm(
    model: str = "gemini-2.5-flash",
    temperature: float = 0.3
):
    """
    Creates and returns the configured LLM for TradeMind agents.
    """

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in TradeMind-AI/.env"
        )

    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key
    )