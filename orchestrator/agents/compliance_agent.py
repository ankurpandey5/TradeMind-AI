import os
import json

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from orchestrator.llm import get_llm

load_dotenv()

llm = get_llm(temperature=0.2)

tavily_search = TavilySearchResults(max_results=5)


def execute_compliance_check(prompt: str) -> str:
    """
    Performs a live web search for current trade-compliance
    information and uses Gemini to analyze the results.
    """

    try:
        # ----------------------------------------------------
        # 1. Search the web for current compliance information
        # ----------------------------------------------------

        search_queries = [
            f"{prompt} export requirements official government",
            f"{prompt} import requirements official government",
            f"{prompt} customs duties HS code official",
            f"{prompt} certifications standards labeling official",
            f"{prompt} restricted prohibited goods official",
        ]

        search_results = []

        for query in search_queries:
            results = tavily_search.invoke(query)
            search_results.extend(results)

        # ----------------------------------------------------
        # 2. Convert search results into context for Gemini
        # ----------------------------------------------------

        web_context = json.dumps(search_results, indent=2, ensure_ascii=False)

        # ----------------------------------------------------
        # 3. Ask Gemini to analyze the retrieved information
        # ----------------------------------------------------

        system_instructions = """
You are the Compliance Agent for TradeMind-AI.

Your job is to analyze international trade compliance
using CURRENT information retrieved from web sources.

Do NOT rely only on your internal knowledge.

Analyze the trade route and product provided by the user.

Check the following areas:

1. EXPORT LEGALITY
   - Can the product legally be exported from the
     exporting country?
   - Are export licenses, permissions, or restrictions
     applicable?

2. IMPORT LEGALITY
   - Can the product legally be imported into the
     destination country?
   - Are import restrictions or prohibitions applicable?

3. REQUIRED DOCUMENTS
   - Identify important export/import documents.
   - Examples:
     commercial invoice,
     packing list,
     certificate of origin,
     customs documents,
     shipping documents.

4. CERTIFICATIONS AND STANDARDS
   - Identify applicable certifications.
   - Identify safety, technical, quality, environmental,
     or product-specific standards.

5. CUSTOMS REQUIREMENTS
   - Identify customs procedures.
   - Identify the likely HS code only when enough
     product information is available.
   - Do NOT invent an HS code.

6. DUTIES AND TAXES
   - Identify applicable duties, tariffs, VAT/GST,
     or other import taxes when supported by sources.
   - Do NOT invent exact rates.

7. LABELING AND PACKAGING
   - Identify product labeling requirements.
   - Identify packaging, language, warnings,
     markings, or other requirements.

8. RESTRICTED OR PROHIBITED GOODS
   - Identify whether the product may be restricted,
     controlled, sanctioned, or prohibited.
   - Mention required licenses if applicable.

9. COMPLIANCE RISKS
   - Identify risks that could delay, prevent,
     or increase the cost of the shipment.

10. RECOMMENDED ACTIONS
   - Give practical steps the exporter should take
     before proceeding.

IMPORTANT RULES:

- Prefer official government and regulatory sources.
- Treat search results as evidence, not automatically as truth.
- Clearly distinguish confirmed information from
  information that requires verification.
- Do not invent regulations, certifications,
  HS codes, tax rates, or requirements.
- If the retrieved information is insufficient,
  explicitly say that verification is required.
- Include the source URL for important claims.

Return ONLY valid JSON.

Required JSON structure:

{
    "message": "...",

    "export_legality": [],

    "import_legality": [],

    "documents": [],

    "certifications_standards": [],

    "customs_requirements": [],

    "duties_taxes": [],

    "labeling_packaging": [],

    "restricted_prohibited": [],

    "compliance_risks": [],

    "recommended_actions": [],

    "sources": []
}
"""

        human_message = f"""
USER TRADE REQUEST:
{prompt}

LIVE WEB SEARCH RESULTS:
{web_context}

Analyze the request using the retrieved web information.
"""

        response = llm.invoke(
            [
                SystemMessage(content=system_instructions),
                HumanMessage(content=human_message),
            ]
        )

        # ----------------------------------------------------
        # 4. Validate that Gemini returned JSON
        # ----------------------------------------------------

        result = response.content

        try:
            parsed_result = json.loads(result)

            # Return normalized JSON
            return json.dumps(parsed_result, ensure_ascii=False)

        except json.JSONDecodeError:
            return json.dumps(
                {
                    "message": "Compliance analysis returned invalid JSON.",
                    "export_legality": [],
                    "import_legality": [],
                    "documents": [],
                    "certifications_standards": [],
                    "customs_requirements": [],
                    "duties_taxes": [],
                    "labeling_packaging": [],
                    "restricted_prohibited": [],
                    "compliance_risks": [],
                    "recommended_actions": [],
                    "sources": [],
                    "raw_output": result,
                }
            )

    except Exception as e:

        return json.dumps(
            {
                "message": "Compliance Agent failed.",
                "error": str(e),
                "export_legality": [],
                "import_legality": [],
                "documents": [],
                "certifications_standards": [],
                "customs_requirements": [],
                "duties_taxes": [],
                "labeling_packaging": [],
                "restricted_prohibited": [],
                "compliance_risks": [],
                "recommended_actions": [],
                "sources": [],
            }
        )
