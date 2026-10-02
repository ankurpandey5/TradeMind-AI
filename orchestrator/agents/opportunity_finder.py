import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load API Key from .env relative to this file
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../.env')
)
load_dotenv(dotenv_path=env_path)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


def execute_opportunity_search(prompt: str) -> str:
    system_instructions = """
    You are the 'Lead Opportunity Scout' for this company.
    Task: Extract trade opportunities for Indian MSMEs based on the input
    find opportunity & potential clients in global markets.

    CRITICAL: Output ONLY a valid JSON object. No markdown formatting,
    no code blocks, no preamble.

    JSON Structure:
    {
        "message": "A concise summary of the opportunity search results. Will be rendered on chat screen keep is consise end with a note of completion.",
        "opportunities": [
            {
                "type": "demand",
                "longitude": float,
                "latitude": float,
                "title": "string",
                "country": "string",
                "note": "A sharp, data-driven insight including the 📈 Opportunity, 🎯 Strategic Action, and ⚠️ Risk Factor."
            }
        ]
    }
    """

    try:
        response = llm.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(content=prompt)
        ])

        return response.content

    except Exception as e:
        return f"Opportunity Finder Error: {str(e)}"