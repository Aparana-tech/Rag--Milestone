import logging
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
import config

logger = logging.getLogger(__name__)

class IntentClassification(BaseModel):
    intent: str = Field(description="The classified intent: 'Factual_Query', 'Advisory_Query', or 'Comparative_Query'")

# The refusal message mandated by the requirements
REFUSAL_MESSAGE = "I can only provide factual mutual fund details. I cannot offer investment advice. Please refer to AMFI/SEBI for educational resources: https://www.amfiindia.com/investor-corner"

def classify_intent(query: str) -> str:
    """
    Zero-shot classifier to determine the intent of the user query.
    """
    llm = ChatGroq(
        model=config.LLM_MODEL,
        api_key=config.GROQ_API_KEY,
        temperature=0.0
    )
    
    # We use with_structured_output to enforce the intent categories
    structured_llm = llm.with_structured_output(IntentClassification)
    
    prompt = PromptTemplate.from_template(
        """You are an Intent Classifier for a Mutual Fund AI Assistant.
        Your job is to classify the user's query into exactly ONE of the following three categories:
        
        1. Factual_Query: The user is asking for factual details about a mutual fund (e.g., NAV, AUM, holdings, expense ratio, fund managers, exit load).
        2. Advisory_Query: The user is asking for financial advice, recommendations, opinions, or whether they should invest/buy/sell a fund.
        3. Comparative_Query: The user is asking to compare two or more mutual funds against each other.
        
        User Query: {query}
        """
    )
    
    try:
        chain = prompt | structured_llm
        result = chain.invoke({"query": query})
        return result.intent
    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        # Default to Factual to allow retrieval to attempt an answer, rather than hard-blocking
        return "Factual_Query"

def process_guardrails(query: str) -> dict:
    """
    Routing logic. If intent is Advisory or Comparative, return refusal.
    Returns a dict with 'passed' boolean, 'intent', and 'response' if blocked.
    """
    intent = classify_intent(query)
    
    if intent in ["Advisory_Query", "Comparative_Query"]:
        return {
            "passed": False,
            "intent": intent,
            "response": REFUSAL_MESSAGE
        }
        
    return {
        "passed": True,
        "intent": intent,
        "response": None
    }
